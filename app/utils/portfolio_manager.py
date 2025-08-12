"""
Enhanced Portfolio Management System
Handles real vs paper trading portfolios with proper data segregation.
"""

from flask import current_app
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from ..utils.subscription_enforcer import SubscriptionEnforcer


class PortfolioManager:
    """
    Manages user portfolios with separation between paper and live trading.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.plan_info = SubscriptionEnforcer.get_user_plan_info(user_id)

    def get_comprehensive_portfolio(self) -> Dict[str, Any]:
        """Get complete portfolio data including positions, P&L, and performance"""

        # Determine trading mode
        trading_mode = self.plan_info.get("trading_mode", "paper")
        is_live_capable = self.plan_info["plan"] == "pro" and self.plan_info["active"]

        portfolio_data = {
            "user_info": {
                "user_id": self.user_id,
                "plan": self.plan_info["plan"],
                "trading_mode": trading_mode,
                "live_capable": is_live_capable,
            },
            "summary": self._get_portfolio_summary(trading_mode),
            "positions": self._get_all_positions(trading_mode),
            "performance": self._get_performance_metrics(trading_mode),
            "recent_trades": self._get_recent_trades(trading_mode),
            "exchange_details": self._get_exchange_connections(trading_mode),
            "allocations": self._get_allocations(trading_mode),
        }

        return portfolio_data

    def _get_portfolio_summary(self, trading_mode: str) -> Dict[str, Any]:
        """Get portfolio summary metrics"""

        if trading_mode == "paper":
            return self._get_paper_portfolio_summary()
        else:
            return self._get_live_portfolio_summary()

    def _get_paper_portfolio_summary(self) -> Dict[str, Any]:
        """Calculate paper trading portfolio summary"""
        try:
            from ..models import Order
            from .demo_portfolio import DemoPortfolioGenerator
            from sqlalchemy import func

            # Get all paper orders for this user
            orders = Order.query.filter_by(
                user_id=self.user_id, is_paper=True, status="filled"
            ).all()

            # Auto-generate demo portfolio for new users with no trades
            if len(orders) == 0:
                current_app.logger.info(
                    f"No paper trades found for user {self.user_id}, generating demo portfolio"
                )
                try:
                    demo_result = DemoPortfolioGenerator.generate_demo_portfolio(
                        self.user_id
                    )
                    if demo_result["status"] == "created":
                        # Reload orders after demo generation
                        orders = Order.query.filter_by(
                            user_id=self.user_id, is_paper=True, status="filled"
                        ).all()
                        current_app.logger.info(
                            f"Generated {len(orders)} demo trades for user {self.user_id}"
                        )
                except Exception as e:
                    current_app.logger.error(
                        f"Failed to generate demo portfolio for user {self.user_id}: {e}"
                    )

            total_invested = 0
            total_current_value = 0
            total_trades = len(orders)

            # Calculate positions
            positions = {}
            for order in orders:
                if order.symbol not in positions:
                    positions[order.symbol] = {
                        "quantity": 0,
                        "invested": 0,
                        "avg_price": 0,
                    }

                if order.side.lower() == "buy":
                    positions[order.symbol]["quantity"] += order.quantity
                    positions[order.symbol]["invested"] += order.quantity * order.price
                else:
                    positions[order.symbol]["quantity"] -= order.quantity
                    positions[order.symbol]["invested"] -= order.quantity * order.price

            # Calculate current values and P&L
            total_pnl = 0
            for symbol, pos in positions.items():
                if pos["quantity"] > 0:
                    total_invested += pos["invested"]
                    # Use mock current price for demo
                    current_price = self._get_mock_current_price(symbol)
                    current_value = pos["quantity"] * current_price
                    total_current_value += current_value
                    position_pnl = current_value - pos["invested"]
                    total_pnl += position_pnl

            return {
                "total_value": total_current_value,
                "total_invested": total_invested,
                "total_pnl": total_pnl,
                "pnl_percentage": (
                    (total_pnl / total_invested * 100) if total_invested > 0 else 0
                ),
                "cash_balance": 100000.0
                - total_invested,  # Starting with 100k paper money
                "total_trades": total_trades,
                "trading_mode": "paper",
            }

        except Exception as e:
            current_app.logger.error(f"Failed to calculate paper portfolio: {e}")
            return {
                "total_value": 100000.0,
                "total_invested": 0.0,
                "total_pnl": 0.0,
                "pnl_percentage": 0.0,
                "cash_balance": 100000.0,
                "total_trades": 0,
                "trading_mode": "paper",
            }

    def _get_live_portfolio_summary(self) -> Dict[str, Any]:
        """Get live trading portfolio summary from connected exchanges"""
        try:
            total_value = 0
            total_pnl = 0
            exchange_values = []

            # Get data from connected exchanges
            exchange_connections = self._get_user_exchange_connections()

            for exchange in exchange_connections:
                try:
                    adapter = self._get_exchange_adapter(exchange)
                    if adapter and adapter.is_connected:

                        # Get account balances
                        balances = adapter.get_balances()
                        positions = adapter.get_positions()

                        exchange_value = 0
                        exchange_pnl = 0

                        # Calculate values from balances and positions
                        for balance in balances:
                            if balance["asset"] in ["INR", "USDT", "USD"]:
                                exchange_value += balance["total"]

                        for position in positions:
                            position_value = position["quantity"] * position.get(
                                "current_price", position.get("average_price", 0)
                            )
                            position_pnl = position.get("pnl", 0)
                            exchange_value += position_value
                            exchange_pnl += position_pnl

                        total_value += exchange_value
                        total_pnl += exchange_pnl

                        exchange_values.append(
                            {
                                "exchange": exchange["exchange_name"],
                                "value": exchange_value,
                                "pnl": exchange_pnl,
                            }
                        )

                except Exception as e:
                    current_app.logger.error(
                        f"Failed to get data from {exchange['exchange_name']}: {e}"
                    )
                    continue

            # Get recent trades count
            total_trades = self._get_live_trades_count()

            return {
                "total_value": total_value,
                "total_invested": total_value - total_pnl,
                "total_pnl": total_pnl,
                "pnl_percentage": (
                    (total_pnl / (total_value - total_pnl) * 100)
                    if (total_value - total_pnl) > 0
                    else 0
                ),
                "cash_balance": self._get_available_cash(),
                "total_trades": total_trades,
                "trading_mode": "live",
                "exchange_breakdown": exchange_values,
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get live portfolio summary: {e}")
            # Return empty live portfolio
            return {
                "total_value": 0.0,
                "total_invested": 0.0,
                "total_pnl": 0.0,
                "pnl_percentage": 0.0,
                "cash_balance": 0.0,
                "total_trades": 0,
                "trading_mode": "live",
            }

    def _get_all_positions(self, trading_mode: str) -> List[Dict[str, Any]]:
        """Get all current positions"""
        if trading_mode == "paper":
            return self._get_paper_positions()
        else:
            return self._get_live_positions()

    def _get_paper_positions(self) -> List[Dict[str, Any]]:
        """Calculate paper trading positions from orders"""
        try:
            from ..models import Order

            orders = Order.query.filter_by(
                user_id=self.user_id, is_paper=True, status="filled"
            ).all()

            positions = {}
            for order in orders:
                if order.symbol not in positions:
                    positions[order.symbol] = {
                        "symbol": order.symbol,
                        "quantity": 0,
                        "average_price": 0,
                        "total_cost": 0,
                        "exchange": (
                            "zerodha" if order.exchange_type == "stocks" else "binance"
                        ),
                    }

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

            # Filter active positions and add market data
            active_positions = []
            for symbol, pos in positions.items():
                if abs(pos["quantity"]) >= 0.001:  # Filter out tiny positions

                    # Calculate average price
                    if pos["quantity"] > 0:
                        pos["average_price"] = pos["total_cost"] / pos["quantity"]

                    # Get current market price
                    current_price = self._get_mock_current_price(symbol)
                    pos["current_price"] = current_price
                    pos["market_value"] = pos["quantity"] * current_price
                    pos["pnl"] = pos["market_value"] - pos["total_cost"]
                    pos["pnl_percentage"] = (
                        (pos["pnl"] / abs(pos["total_cost"]) * 100)
                        if pos["total_cost"] != 0
                        else 0
                    )

                    # Remove total_cost from output (internal calculation)
                    pos.pop("total_cost", None)
                    active_positions.append(pos)

            return active_positions

        except Exception as e:
            current_app.logger.error(f"Failed to get paper positions: {e}")
            return []

    def _get_live_positions(self) -> List[Dict[str, Any]]:
        """Get live trading positions from exchanges"""
        all_positions = []

        try:
            exchange_connections = self._get_user_exchange_connections()

            for exchange in exchange_connections:
                try:
                    adapter = self._get_exchange_adapter(exchange)
                    if adapter and adapter.is_connected:
                        positions = adapter.get_positions()

                        # Add exchange info to each position
                        for pos in positions:
                            pos["exchange"] = exchange["exchange_name"]
                            all_positions.append(pos)

                except Exception as e:
                    current_app.logger.error(
                        f"Failed to get positions from {exchange['exchange_name']}: {e}"
                    )
                    continue

            return all_positions

        except Exception as e:
            current_app.logger.error(f"Failed to get live positions: {e}")
            return []

    def _get_performance_metrics(self, trading_mode: str) -> Dict[str, Any]:
        """Calculate performance metrics"""
        try:
            if trading_mode == "paper":
                return self._calculate_paper_performance()
            else:
                return self._calculate_live_performance()

        except Exception as e:
            current_app.logger.error(f"Failed to calculate performance: {e}")
            return {
                "daily_pnl": 0.0,
                "weekly_pnl": 0.0,
                "monthly_pnl": 0.0,
                "win_rate": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
            }

    def _calculate_paper_performance(self) -> Dict[str, Any]:
        """Calculate performance from paper trades"""
        try:
            from ..models import Order
            from sqlalchemy import func

            # Get orders from different time periods
            now = datetime.now()
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            orders = Order.query.filter_by(
                user_id=self.user_id, is_paper=True, status="filled"
            ).all()

            # Simple P&L calculation (this would be more sophisticated in real system)
            daily_trades = [o for o in orders if o.created_at >= day_ago]
            weekly_trades = [o for o in orders if o.created_at >= week_ago]
            monthly_trades = [o for o in orders if o.created_at >= month_ago]

            # Mock performance calculations
            daily_pnl = len(daily_trades) * 50  # Mock: Rs 50 profit per trade
            weekly_pnl = len(weekly_trades) * 45
            monthly_pnl = len(monthly_trades) * 40

            total_trades = len(orders)
            winning_trades = int(total_trades * 0.6)  # Mock 60% win rate

            return {
                "daily_pnl": daily_pnl,
                "weekly_pnl": weekly_pnl,
                "monthly_pnl": monthly_pnl,
                "win_rate": (
                    (winning_trades / total_trades * 100) if total_trades > 0 else 0
                ),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "sharpe_ratio": 1.5,  # Mock value
                "max_drawdown": -5.2,  # Mock value
            }

        except Exception as e:
            current_app.logger.error(f"Failed to calculate paper performance: {e}")
            return {}

    def _calculate_live_performance(self) -> Dict[str, Any]:
        """Calculate performance from live trading data"""
        # This would integrate with exchange APIs to get real performance data
        # For now, return basic structure
        return {
            "daily_pnl": 0.0,
            "weekly_pnl": 0.0,
            "monthly_pnl": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }

    def _get_recent_trades(
        self, trading_mode: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent trades"""
        try:
            from ..models import Order

            query = Order.query.filter_by(user_id=self.user_id)

            if trading_mode == "paper":
                query = query.filter_by(is_paper=True)
            else:
                query = query.filter_by(is_paper=False)

            orders = query.order_by(Order.created_at.desc()).limit(limit).all()

            return [
                {
                    "id": order.id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": order.quantity,
                    "price": order.price,
                    "status": order.status,
                    "timestamp": order.created_at.isoformat(),
                    "exchange": (
                        "zerodha" if order.exchange_type == "stocks" else "binance"
                    ),
                }
                for order in orders
            ]

        except Exception as e:
            current_app.logger.error(f"Failed to get recent trades: {e}")
            return []

    def _get_exchange_connections(self, trading_mode: str) -> List[Dict[str, Any]]:
        """Get exchange connection details"""
        try:
            from ..models import ExchangeConnection

            connections = ExchangeConnection.query.filter_by(user_id=self.user_id).all()

            exchange_details = []
            for conn in connections:

                try:
                    if trading_mode == "live":
                        # Get real data from exchange
                        adapter = self._get_exchange_adapter_from_connection(conn)
                        if adapter and adapter.is_connected:
                            balances = adapter.get_balances()
                            account_info = adapter.get_account_info()

                            exchange_details.append(
                                {
                                    "name": conn.get_display_name(),
                                    "exchange_name": conn.exchange_name,
                                    "connected": True,
                                    "balances": balances,
                                    "account_info": account_info,
                                    "trading_mode": "live",
                                }
                            )
                        else:
                            exchange_details.append(
                                {
                                    "name": conn.get_display_name(),
                                    "exchange_name": conn.exchange_name,
                                    "connected": False,
                                    "error": "Connection failed",
                                    "trading_mode": "live",
                                }
                            )
                    else:
                        # Paper trading mode
                        exchange_details.append(
                            {
                                "name": conn.get_display_name(),
                                "exchange_name": conn.exchange_name,
                                "connected": True,
                                "balances": [
                                    {
                                        "asset": "INR",
                                        "free": 100000.0,
                                        "total": 100000.0,
                                    }
                                ],
                                "trading_mode": "paper",
                            }
                        )

                except Exception as e:
                    current_app.logger.error(
                        f"Failed to get data for {conn.exchange_name}: {e}"
                    )
                    exchange_details.append(
                        {
                            "name": conn.get_display_name(),
                            "exchange_name": conn.exchange_name,
                            "connected": False,
                            "error": str(e),
                            "trading_mode": trading_mode,
                        }
                    )

            return exchange_details

        except Exception as e:
            current_app.logger.error(f"Failed to get exchange connections: {e}")
            return []

    def _get_user_exchange_connections(self):
        """Get user's exchange connections"""
        try:
            from ..models import ExchangeConnection

            return ExchangeConnection.query.filter_by(user_id=self.user_id).all()
        except:
            return []

    def _get_exchange_adapter(self, exchange_connection):
        """Get appropriate exchange adapter"""
        try:
            if exchange_connection["exchange_name"] in [
                "zerodha",
                "upstox",
                "angelbroking",
            ]:
                from ..exchange_adapter.kite_adapter import ZerodhaKiteAdapter

                return ZerodhaKiteAdapter(
                    self.user_id,
                    paper_trading=self.plan_info["trading_mode"] == "paper",
                )
            elif exchange_connection["exchange_name"] in ["binance", "binance_testnet"]:
                from ..exchange_adapter.binance_adapter import BinanceAdapter

                return BinanceAdapter(
                    self.user_id,
                    force_paper_mode=self.plan_info["trading_mode"] == "paper",
                )
            else:
                return None
        except Exception as e:
            current_app.logger.error(
                f"Failed to get adapter for {exchange_connection['exchange_name']}: {e}"
            )
            return None

    def _get_exchange_adapter_from_connection(self, conn):
        """Get adapter from connection object"""
        exchange_dict = {
            "exchange_name": conn.exchange_name,
            "api_key": conn.api_key,
            "api_secret": conn.api_secret,
        }
        return self._get_exchange_adapter(exchange_dict)

    def _get_mock_current_price(self, symbol: str) -> float:
        """Get mock current price for paper trading"""
        import random
        import hashlib
        from .demo_portfolio import DemoPortfolioGenerator

        # Use realistic Indian stock prices if available
        if symbol in DemoPortfolioGenerator.DEMO_STOCKS:
            stock_info = DemoPortfolioGenerator.DEMO_STOCKS[symbol]
            price_range = stock_info["price_range"]
            volatility = stock_info["volatility"]

            # Generate consistent "random" price based on symbol with daily variation
            seed = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            base_price = random.uniform(*price_range)

            # Add some realistic daily variation
            daily_variation = random.uniform(-volatility, volatility)
            return base_price * (1 + daily_variation)
        else:
            # Fallback for unknown symbols
            seed = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            base_price = random.uniform(100, 2000)
            daily_variation = random.uniform(-0.05, 0.05)
            return base_price * (1 + daily_variation)

    def _get_available_cash(self) -> float:
        """Get available cash across all exchanges"""
        try:
            total_cash = 0
            exchange_connections = self._get_user_exchange_connections()

            for exchange in exchange_connections:
                adapter = self._get_exchange_adapter(exchange)
                if adapter and adapter.is_connected:
                    balances = adapter.get_balances()
                    for balance in balances:
                        if balance["asset"] in ["INR", "USDT", "USD"]:
                            total_cash += balance["free"]

            return total_cash
        except:
            return 0.0

    def _get_live_trades_count(self) -> int:
        """Get count of live trades"""
        try:
            from ..models import Order

            return Order.query.filter_by(user_id=self.user_id, is_paper=False).count()
        except:
            return 0

    def _get_allocations(self, trading_mode: str) -> Dict[str, Any]:
        """Calculate portfolio allocations by asset type"""
        try:
            positions = self._get_all_positions(trading_mode)

            stocks_value = 0
            crypto_value = 0

            for position in positions:
                market_value = position.get("market_value", 0)
                exchange = position.get("exchange", "")

                # Categorize by exchange type
                if exchange in [
                    "zerodha",
                    "upstox",
                    "angelbroking",
                    "iifl",
                    "fyers",
                    "aliceblue",
                ]:
                    stocks_value += market_value
                elif exchange in ["binance", "binance_testnet"]:
                    crypto_value += market_value
                else:
                    # Default categorization based on symbol patterns
                    symbol = position.get("symbol", "")
                    if any(
                        crypto in symbol.upper()
                        for crypto in ["BTC", "ETH", "USDT", "BNB"]
                    ):
                        crypto_value += market_value
                    else:
                        stocks_value += market_value

            total_value = stocks_value + crypto_value

            return {
                "stocks": {
                    "value": stocks_value,
                    "percentage": (
                        (stocks_value / total_value * 100) if total_value > 0 else 0
                    ),
                },
                "crypto": {
                    "value": crypto_value,
                    "percentage": (
                        (crypto_value / total_value * 100) if total_value > 0 else 0
                    ),
                },
                "total_value": total_value,
            }

        except Exception as e:
            current_app.logger.error(f"Error calculating allocations: {e}")
            return {
                "stocks": {"value": 0, "percentage": 0},
                "crypto": {"value": 0, "percentage": 0},
                "total_value": 0,
            }
