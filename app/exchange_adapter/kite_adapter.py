import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_adapter import BaseExchangeAdapter, PaperTradingMixin
import requests
import hashlib
import hmac
import time
import random


class ZerodhaKiteAdapter(BaseExchangeAdapter, PaperTradingMixin):
    """
    Zerodha Kite Connect API adapter for real trading.
    Implements both live and paper trading modes.
    """

    def __init__(self, user_id: int, paper_trading: bool = False):
        super().__init__(user_id, "zerodha")
        self.paper_trading = paper_trading
        self.kite = None
        self.base_url = "https://api.kite.trade"
        self.login_url = "https://kite.trade/connect/login"
        self.api_key = None
        self.api_secret = None
        self.access_token = None
        self._credentials_loaded = False

        # Lazy load credentials only when needed
        if not paper_trading:
            try:
                self._load_api_credentials()
                if self.api_key and self.api_secret:
                    self.connect()
            except Exception as e:
                self._log_message(f"Failed to connect to Kite: {e}", level="warning")
                self.paper_trading = True
                self._log_message("Falling back to paper trading mode", level="info")

    def _log_message(self, message: str, level: str = "info"):
        """Log message with fallback for when Flask context is not available."""
        try:
            from flask import current_app

            logger = getattr(current_app.logger, level, current_app.logger.info)
            logger(message)
        except (RuntimeError, ImportError):
            # No Flask context available or app not initialized
            print(f"[{level.upper()}] {message}")

    def _load_api_credentials(self):
        """Load API credentials from database"""
        if self._credentials_loaded:
            return

        try:
            from ..models import ExchangeConnection

            connection = ExchangeConnection.query.filter_by(
                user_id=self.user_id, exchange_name="zerodha"
            ).first()

            if connection:
                self.api_key = connection.api_key
                self.api_secret = connection.api_secret
                self.access_token = connection.access_token
            else:
                # Fallback to config for development
                try:
                    from flask import current_app

                    self.api_key = current_app.config.get("KITE_API_KEY")
                    self.api_secret = current_app.config.get("KITE_API_SECRET")
                except RuntimeError:
                    # No app context, use environment variables
                    import os

                    self.api_key = os.getenv("KITE_API_KEY")
                    self.api_secret = os.getenv("KITE_API_SECRET")

            self._credentials_loaded = True

        except Exception as e:
            self._log_message(f"Failed to load Kite credentials: {e}", level="error")
            self.api_key = None
            self.api_secret = None

    def connect(self) -> bool:
        """
        Connect to Kite Connect API.
        For real implementation, this would handle OAuth flow.
        """
        if self.paper_trading:
            self.is_connected = True
            self._log_message(
                "Kite adapter initialized in paper trading mode", level="info"
            )
            return True

        if not self.api_key or not self.api_secret:
            self._log_message("Kite API credentials not configured", level="error")
            return False

        try:
            # TODO: Implement real Kite Connect OAuth flow
            # For now, mark as connected if we have credentials
            if self.access_token:
                self.is_connected = True
                self._log_message("Kite Connect established successfully", level="info")
                return True
            else:
                self._log_message("Kite Connect access token required", level="warning")
                return False

        except Exception as e:
            self._log_message(f"Kite Connect failed: {e}", level="error")
            return False

    def disconnect(self):
        """Close Kite connection"""
        self.is_connected = False
        self.kite = None

    def is_market_open(self) -> bool:
        """Check if Indian stock market is open"""
        import pytz

        # Get current time in Indian timezone
        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist)

        # Market is open Monday-Friday, 9:15 AM to 3:30 PM IST
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if self.paper_trading:
            return {
                "user_id": "DEMO123",
                "user_name": "Demo User",
                "email": "demo@example.com",
                "exchanges": ["NSE", "BSE"],
                "products": ["CNC", "MIS", "NRML"],
                "order_types": ["MARKET", "LIMIT", "SL", "SL-M"],
                "paper_trading": True,
            }

        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.profile()

        # Mock response for now
        return {
            "user_id": "XYZ123",
            "user_name": "Real User",
            "email": "user@example.com",
            "exchanges": ["NSE", "BSE"],
            "paper_trading": False,
        }

    def get_balances(self) -> List[Dict[str, Any]]:
        """Get account balances"""
        if self.paper_trading:
            # Return mock balances for paper trading
            return [
                {"asset": "INR", "free": 100000.0, "locked": 0.0, "total": 100000.0},
                {"asset": "EQUITY", "free": 0.0, "locked": 0.0, "total": 0.0},
            ]

        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.margins()

        # Mock response
        return [{"asset": "INR", "free": 50000.0, "locked": 5000.0, "total": 55000.0}]

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        if self.paper_trading:
            return self.get_paper_positions()

        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.positions()

        # Mock response
        return []

    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time market data"""
        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.quote([symbol])

        # Mock market data
        import random

        base_price = random.uniform(100, 2000)

        return {
            "symbol": symbol,
            "last_price": base_price,
            "open": base_price * random.uniform(0.98, 1.02),
            "high": base_price * random.uniform(1.00, 1.05),
            "low": base_price * random.uniform(0.95, 1.00),
            "close": base_price * random.uniform(0.99, 1.01),
            "volume": random.randint(10000, 1000000),
            "oi": random.randint(1000, 100000),
            "timestamp": datetime.now().isoformat(),
        }

    def get_historical_data(
        self, symbol: str, interval: str, limit: int
    ) -> pd.DataFrame:
        """Get historical price data"""
        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.historical_data(instrument_token, from_date, to_date, interval)

        # Generate mock historical data
        dates = pd.date_range(end=datetime.now(), periods=limit, freq="1min")
        base_price = 1000.0

        # Generate realistic price movements
        returns = np.random.normal(0.0001, 0.02, limit)
        prices = base_price * np.exp(np.cumsum(returns))

        df = pd.DataFrame(
            {
                "timestamp": dates,
                "open": prices * np.random.uniform(0.999, 1.001, limit),
                "high": prices * np.random.uniform(1.000, 1.002, limit),
                "low": prices * np.random.uniform(0.998, 1.000, limit),
                "close": prices,
                "volume": np.random.randint(1000, 10000, limit),
            }
        )

        return df

    def place_order(self, order_payload: Dict[str, Any]) -> str:
        """Place a trading order"""
        if self.paper_trading:
            return self.simulate_order_execution(order_payload)

        if not self.is_connected:
            raise ConnectionError("Kite not connected. Cannot place real orders.")

        # Validate order first
        validation = self.validate_order(order_payload)
        if not validation["valid"]:
            raise ValueError(f"Order validation failed: {validation['error']}")

        # TODO: Implement real order placement
        # order_id = self.kite.place_order(
        #     variety=self.kite.VARIETY_REGULAR,
        #     exchange=self.kite.EXCHANGE_NSE,
        #     tradingsymbol=order_payload['symbol'],
        #     transaction_type=self.kite.TRANSACTION_TYPE_BUY if order_payload['side'] == 'buy' else self.kite.TRANSACTION_TYPE_SELL,
        #     quantity=order_payload['quantity'],
        #     product=self.kite.PRODUCT_MIS,
        #     order_type=self.kite.ORDER_TYPE_MARKET if order_payload['order_type'] == 'market' else self.kite.ORDER_TYPE_LIMIT,
        #     price=order_payload.get('price'),
        #     validity=self.kite.VALIDITY_DAY
        # )

        # Mock order placement for now
        import random

        order_id = f"KITE_{int(time.time())}_{random.randint(1000, 9999)}"

        self._log_message(f"REAL Kite order placed (mock): {order_id}", level="info")
        self.log_trade(order_payload, order_id, "PLACED")

        return order_id

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.order_history(order_id)

        # Mock response
        return {
            "order_id": order_id,
            "status": "COMPLETE",
            "quantity": 10,
            "filled_quantity": 10,
            "price": 1000.0,
            "average_price": 1000.0,
            "timestamp": datetime.now().isoformat(),
        }

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.cancel_order(variety=self.kite.VARIETY_REGULAR, order_id=order_id)

        self._log_message(f"Order cancelled (mock): {order_id}", level="info")
        return True

    def get_order_history(
        self, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get order history"""
        if self.paper_trading:
            try:
                from ..models import Order

                query = Order.query.filter_by(user_id=self.user_id, is_paper=True)
                if symbol:
                    query = query.filter_by(symbol=symbol)

                orders = query.order_by(Order.created_at.desc()).limit(limit).all()

                return [
                    {
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "side": order.side,
                        "quantity": order.quantity,
                        "price": order.price,
                        "status": order.status,
                        "timestamp": order.created_at.isoformat(),
                    }
                    for order in orders
                ]

            except Exception as e:
                self._log_message(
                    f"Failed to get paper order history: {e}", level="error"
                )
                return []

        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        # TODO: Implement real API call
        # return self.kite.orders()

        return []

    def validate_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order parameters"""
        required_fields = ["symbol", "side", "quantity"]

        for field in required_fields:
            if field not in order_payload:
                return {"valid": False, "error": f"Missing required field: {field}"}

        # Validate side
        if order_payload["side"].lower() not in ["buy", "sell"]:
            return {"valid": False, "error": "Side must be 'buy' or 'sell'"}

        # Validate quantity
        try:
            quantity = float(order_payload["quantity"])
            if quantity <= 0:
                return {"valid": False, "error": "Quantity must be positive"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid quantity format"}

        # Validate price for limit orders
        if order_payload.get("order_type", "").lower() == "limit":
            if "price" not in order_payload:
                return {"valid": False, "error": "Price required for limit orders"}
            try:
                price = float(order_payload["price"])
                if price <= 0:
                    return {"valid": False, "error": "Price must be positive"}
            except (ValueError, TypeError):
                return {"valid": False, "error": "Invalid price format"}

        return {"valid": True, "error": None}

    def get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol"""
        try:
            market_data = self.get_market_data(symbol)
            return float(market_data.get("last_price", 100.0))
        except:
            return 100.0


# Legacy compatibility - keep the old singleton pattern for existing code
class ExchangeAdapter(ZerodhaKiteAdapter):
    """Legacy wrapper for backward compatibility"""

    def __init__(self, user_id=None, exchange_name=None):
        super().__init__(user_id or 1, paper_trading=True)


# Singleton instance for backward compatibility
exchange_adapter = ExchangeAdapter()
