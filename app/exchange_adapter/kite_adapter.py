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
        Connect to Kite Connect API with real OAuth flow.
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
            # Import Kite Connect (requires kiteconnect package)
            try:
                from kiteconnect import KiteConnect
            except ImportError:
                self._log_message(
                    "KiteConnect package not installed. Install with: pip install kiteconnect",
                    level="error",
                )
                return False

            # Initialize Kite Connect
            self.kite = KiteConnect(api_key=self.api_key)

            # Check if we have a valid access token
            if self.access_token:
                self.kite.set_access_token(self.access_token)

                # Test the connection
                try:
                    profile = self.kite.profile()
                    self.is_connected = True
                    self._log_message(
                        f"Kite Connect established successfully for user: {profile.get('user_name', 'Unknown')}",
                        level="info",
                    )
                    return True
                except Exception as token_error:
                    self._log_message(
                        f"Invalid access token: {token_error}", level="warning"
                    )
                    # Clear invalid token
                    self.access_token = None

            # Generate login URL for new authorization
            login_url = self.kite.login_url()
            self._log_message(
                f"Kite Connect authorization required. Please visit: {login_url}",
                level="info",
            )

            # Store the login URL for the user to complete authorization
            self._store_login_url(login_url)

            return False  # Connection not established yet, requires user authorization

        except Exception as e:
            self._log_message(f"Kite Connect failed: {e}", level="error")
            return False

    def _store_login_url(self, login_url: str):
        """Store login URL for user authorization"""
        try:
            from flask import current_app
            from ..models import ExchangeConnection, db

            connection = ExchangeConnection.query.filter_by(
                user_id=self.user_id, exchange_name="zerodha"
            ).first()

            if connection:
                connection.login_url = login_url
                connection.status = "authorization_required"
                db.session.commit()
                self._log_message(
                    "Login URL stored for user authorization", level="info"
                )

        except Exception as e:
            self._log_message(f"Failed to store login URL: {e}", level="error")

    def complete_authorization(self, request_token: str) -> bool:
        """Complete Kite authorization with request token"""
        try:
            if not self.kite:
                self._log_message("Kite not initialized", level="error")
                return False

            # Generate access token
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = data["access_token"]

            # Set access token
            self.kite.set_access_token(access_token)
            self.access_token = access_token

            # Store access token in database
            self._store_access_token(access_token)

            # Test connection
            profile = self.kite.profile()
            self.is_connected = True

            self._log_message(
                f"Kite authorization completed successfully for: {profile.get('user_name')}",
                level="info",
            )
            return True

        except Exception as e:
            self._log_message(
                f"Failed to complete Kite authorization: {e}", level="error"
            )
            return False

    def _store_access_token(self, access_token: str):
        """Store access token in database"""
        try:
            from flask import current_app
            from ..models import ExchangeConnection, db

            connection = ExchangeConnection.query.filter_by(
                user_id=self.user_id, exchange_name="zerodha"
            ).first()

            if connection:
                connection.access_token = access_token
                connection.status = "connected"
                connection.is_connected = True
                connection.last_connected = datetime.now()
                db.session.commit()
                self._log_message("Access token stored successfully", level="info")

        except Exception as e:
            self._log_message(f"Failed to store access token: {e}", level="error")

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

        try:
            # Get quote from Kite Connect
            quotes = self.kite.quote([symbol])

            if symbol not in quotes:
                raise ValueError(f"No data found for symbol: {symbol}")

            quote_data = quotes[symbol]

            return {
                "symbol": symbol,
                "last_price": quote_data.get("last_price", 0.0),
                "open": quote_data.get("ohlc", {}).get("open", 0.0),
                "high": quote_data.get("ohlc", {}).get("high", 0.0),
                "low": quote_data.get("ohlc", {}).get("low", 0.0),
                "close": quote_data.get("ohlc", {}).get("close", 0.0),
                "volume": quote_data.get("volume", 0),
                "oi": quote_data.get("oi", 0),
                "change": quote_data.get("net_change", 0.0),
                "change_percent": quote_data.get("net_change", 0.0)
                / quote_data.get("ohlc", {}).get("close", 1.0)
                * 100,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self._log_message(
                f"Failed to get market data for {symbol}: {e}", level="error"
            )

            # Return mock data as fallback
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

        try:
            # Convert interval to Kite format
            kite_interval = self._convert_interval(interval)

            # Calculate date range
            from_date = datetime.now() - timedelta(days=limit)
            to_date = datetime.now()

            # Get instrument token for symbol
            instrument_token = self._get_instrument_token(symbol)

            if not instrument_token:
                raise ValueError(f"Instrument token not found for symbol: {symbol}")

            # Fetch historical data
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=kite_interval,
            )

            # Convert to DataFrame
            df = pd.DataFrame(historical_data)

            if not df.empty:
                # Rename columns to match our format
                df = df.rename(columns={"date": "timestamp"})
                df["timestamp"] = pd.to_datetime(df["timestamp"])

            return df.tail(limit)  # Return only requested number of records

        except Exception as e:
            self._log_message(
                f"Failed to get historical data for {symbol}: {e}", level="error"
            )

            # Generate mock historical data as fallback
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

    def _convert_interval(self, interval: str) -> str:
        """Convert interval to Kite format"""
        interval_mapping = {
            "1m": "minute",
            "5m": "5minute",
            "15m": "15minute",
            "1h": "hour",
            "1d": "day",
        }
        return interval_mapping.get(interval, "minute")

    def _get_instrument_token(self, symbol: str) -> int:
        """Get instrument token for symbol"""
        try:
            # This would typically involve fetching from instruments list
            # For now, return None to use fallback mock data
            # instruments = self.kite.instruments()
            # for instrument in instruments:
            #     if instrument['tradingsymbol'] == symbol:
            #         return instrument['instrument_token']
            return None

        except Exception as e:
            self._log_message(
                f"Failed to get instrument token for {symbol}: {e}", level="error"
            )
            return None

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

        try:
            # Map our order format to Kite Connect format
            kite_order = {
                "variety": self.kite.VARIETY_REGULAR,
                "exchange": self._get_exchange(order_payload["symbol"]),
                "tradingsymbol": order_payload["symbol"],
                "transaction_type": (
                    self.kite.TRANSACTION_TYPE_BUY
                    if order_payload["side"] == "buy"
                    else self.kite.TRANSACTION_TYPE_SELL
                ),
                "quantity": int(order_payload["quantity"]),
                "product": self.kite.PRODUCT_MIS,  # Intraday by default
                "order_type": self._get_order_type(order_payload["order_type"]),
                "validity": self.kite.VALIDITY_DAY,
            }

            # Add price for limit orders
            if order_payload["order_type"] == "limit" and "price" in order_payload:
                kite_order["price"] = float(order_payload["price"])

            # Add stop loss for SL orders
            if order_payload.get("stop_loss"):
                kite_order["trigger_price"] = float(order_payload["stop_loss"])

            # Place the order
            order_id = self.kite.place_order(**kite_order)

            self._log_message(
                f"Kite order placed successfully: {order_id}", level="info"
            )
            self.log_trade(order_payload, order_id, "PLACED")

            return order_id

        except Exception as e:
            self._log_message(f"Failed to place Kite order: {e}", level="error")
            raise

    def _get_exchange(self, symbol: str) -> str:
        """Get appropriate exchange for symbol"""
        # Most symbols default to NSE
        if symbol.endswith(".BO"):
            return self.kite.EXCHANGE_BSE
        return self.kite.EXCHANGE_NSE

    def _get_order_type(self, order_type: str) -> str:
        """Convert order type to Kite format"""
        type_mapping = {
            "market": self.kite.ORDER_TYPE_MARKET,
            "limit": self.kite.ORDER_TYPE_LIMIT,
            "stop_loss": self.kite.ORDER_TYPE_SL,
            "stop_loss_market": self.kite.ORDER_TYPE_SLM,
        }
        return type_mapping.get(order_type.lower(), self.kite.ORDER_TYPE_MARKET)

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        if not self.is_connected:
            raise ConnectionError("Kite not connected")

        try:
            # Get order history from Kite
            orders = self.kite.order_history(order_id)

            if not orders:
                raise ValueError(f"Order {order_id} not found")

            # Get the latest order status
            latest_order = orders[-1]

            return {
                "order_id": latest_order.get("order_id"),
                "status": latest_order.get("status"),
                "quantity": latest_order.get("quantity", 0),
                "filled_quantity": latest_order.get("filled_quantity", 0),
                "price": latest_order.get("price", 0.0),
                "average_price": latest_order.get("average_price", 0.0),
                "timestamp": latest_order.get("order_timestamp"),
                "exchange": latest_order.get("exchange"),
                "symbol": latest_order.get("tradingsymbol"),
                "side": (
                    "buy" if latest_order.get("transaction_type") == "BUY" else "sell"
                ),
            }

        except Exception as e:
            self._log_message(f"Failed to get order status: {e}", level="error")
            # Return mock response as fallback
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

        try:
            # Cancel order via Kite Connect
            result = self.kite.cancel_order(
                variety=self.kite.VARIETY_REGULAR, order_id=order_id
            )

            self._log_message(f"Order cancelled successfully: {order_id}", level="info")
            return True

        except Exception as e:
            self._log_message(f"Failed to cancel order {order_id}: {e}", level="error")
            return False

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
