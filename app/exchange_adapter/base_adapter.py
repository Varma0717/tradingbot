"""
Base Exchange Adapter Interface
Defines the standard interface that all exchange adapters must implement
for consistent real-money trading across different brokers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from flask import current_app
import pandas as pd
from datetime import datetime


class BaseExchangeAdapter(ABC):
    """
    Abstract base class for all exchange adapters.
    Ensures consistent interface for real-money trading.
    """

    def __init__(self, user_id: int, exchange_name: str):
        self.user_id = user_id
        self.exchange_name = exchange_name
        self.is_connected = False
        self.api_key = None
        self.api_secret = None
        self.access_token = None
        self.paper_trading = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the exchange/broker.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Close connection to the exchange/broker.
        """
        pass

    @abstractmethod
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open for trading.
        """
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balances, margins, etc.
        """
        pass

    @abstractmethod
    def get_balances(self) -> List[Dict[str, Any]]:
        """
        Get current account balances.
        Returns list of assets with free, locked, and total amounts.
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current open positions.
        """
        pass

    @abstractmethod
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time market data for a symbol.
        """
        pass

    @abstractmethod
    def get_historical_data(
        self, symbol: str, interval: str, limit: int
    ) -> pd.DataFrame:
        """
        Get historical price data.
        """
        pass

    @abstractmethod
    def place_order(self, order_payload: Dict[str, Any]) -> str:
        """
        Place a trading order.
        Returns order ID if successful.
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get status of a specific order.
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.
        Returns True if successful.
        """
        pass

    @abstractmethod
    def get_order_history(
        self, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get order history.
        """
        pass

    @abstractmethod
    def validate_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate order parameters before placing.
        Returns validation result with success/error info.
        """
        pass

    def get_display_name(self) -> str:
        """
        Get human-readable display name for the exchange.
        """
        display_names = {
            "zerodha": "Zerodha Kite",
            "upstox": "Upstox",
            "angelbroking": "Angel Broking",
            "fyers": "Fyers",
            "binance": "Binance",
            "binance_testnet": "Binance Testnet",
        }
        return display_names.get(self.exchange_name, self.exchange_name.title())

    def log_trade(self, order_payload: Dict[str, Any], order_id: str, status: str):
        """
        Log trade for audit purposes.
        """
        try:
            from ..models import AuditLog, db

            audit_log = AuditLog(
                user_id=self.user_id,
                action=f"TRADE_{status}",
                details=f"Order {order_id}: {order_payload['side']} {order_payload['quantity']} {order_payload['symbol']}",
                ip_address="127.0.0.1",  # Will be replaced with actual IP
            )
            db.session.add(audit_log)
            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Failed to log trade: {e}")


class PaperTradingMixin:
    """
    Mixin class to provide paper trading functionality.
    """

    def simulate_order_execution(self, order_payload: Dict[str, Any]) -> str:
        """
        Simulate order execution for paper trading.
        """
        import random
        import time

        # Generate realistic order ID
        order_id = f"PAPER_{int(time.time())}_{random.randint(1000, 9999)}"

        # Log the paper trade
        current_app.logger.info(f"PAPER TRADE: {order_payload}")

        # Store in database as completed order
        try:
            from ..models import Order, db

            order = Order(
                user_id=self.user_id,
                symbol=order_payload["symbol"],
                quantity=float(order_payload["quantity"]),
                order_type=order_payload.get("order_type", "market"),
                side=order_payload["side"],
                price=float(order_payload.get("price", 0)),
                status="filled",
                exchange=self.exchange_name,
                order_id=order_id,
                is_paper=True,
            )
            db.session.add(order)
            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Failed to save paper trade: {e}")

        return order_id

    def get_paper_positions(self) -> List[Dict[str, Any]]:
        """
        Calculate positions from paper trades.
        """
        try:
            from ..models import Order
            from sqlalchemy import func

            # Get all filled paper orders for this user
            orders = Order.query.filter_by(
                user_id=self.user_id, is_paper=True, status="filled"
            ).all()

            # Calculate positions by symbol
            positions = {}
            for order in orders:
                if order.symbol not in positions:
                    positions[order.symbol] = {
                        "symbol": order.symbol,
                        "quantity": 0,
                        "average_price": 0,
                        "total_cost": 0,
                    }

                # Add or subtract quantity based on side
                if order.side.lower() == "buy":
                    positions[order.symbol]["quantity"] += order.quantity
                    positions[order.symbol]["total_cost"] += (
                        order.quantity * order.price
                    )
                else:
                    positions[order.symbol]["quantity"] -= order.quantity
                    positions[order.symbol]["total_cost"] -= (
                        order.quantity * order.price
                    )

                # Recalculate average price
                if positions[order.symbol]["quantity"] > 0:
                    positions[order.symbol]["average_price"] = (
                        positions[order.symbol]["total_cost"]
                        / positions[order.symbol]["quantity"]
                    )

            # Filter out zero positions and add current market data
            active_positions = []
            for symbol, pos in positions.items():
                if abs(pos["quantity"]) > 0.001:  # Filter out very small positions
                    try:
                        current_price = self.get_current_price(symbol)
                        pos["current_price"] = current_price
                        pos["pnl"] = (current_price - pos["average_price"]) * pos[
                            "quantity"
                        ]
                        pos["pnl_percent"] = (
                            (current_price - pos["average_price"])
                            / pos["average_price"]
                        ) * 100
                        active_positions.append(pos)
                    except:
                        # If can't get current price, still include position
                        pos["current_price"] = pos["average_price"]
                        pos["pnl"] = 0
                        pos["pnl_percent"] = 0
                        active_positions.append(pos)

            return active_positions

        except Exception as e:
            current_app.logger.error(f"Failed to calculate paper positions: {e}")
            return []

    def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol.
        Override in specific adapters.
        """
        return 100.0  # Placeholder
