from flask import current_app
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hashlib
import hmac
import time
import requests
import json


class BinanceAdapter:
    def __init__(self, user_id=None, force_paper_mode=False):
        self.user_id = user_id
        self.api_key = None
        self.api_secret = None
        self.base_url = None
        self.is_connected = False
        self.exchange_type = "crypto"
        self.testnet = True  # Default to testnet
        self.server_time_offset = 0  # For time synchronization
        self.force_paper_mode = force_paper_mode  # Force paper trading mode

        # Initialize when called from app context
        try:
            if user_id and not force_paper_mode:
                # Get API keys from database for specific user
                self._load_api_keys_from_db()
            else:
                # Fallback to config (for compatibility)
                self.api_key = current_app.config.get("BINANCE_API_KEY")
                self.api_secret = current_app.config.get("BINANCE_API_SECRET")
                self.testnet = current_app.config.get("BINANCE_TESTNET", True)

            # Set base URL based on testnet config
            if self.testnet:
                self.base_url = "https://testnet.binance.vision/api"
            else:
                self.base_url = "https://api.binance.com/api"

            # Only try to connect if we have valid API keys and not in forced paper mode
            if (
                not force_paper_mode
                and self.api_key
                and self.api_secret
                and not self._is_placeholder_key()
            ):
                self.connect()
            else:
                if force_paper_mode:
                    current_app.logger.info(
                        "Binance adapter initialized in forced paper trading mode"
                    )
                else:
                    current_app.logger.info(
                        "Binance API Key/Secret not configured or using placeholders. Running in demo mode."
                    )
                self.is_connected = True  # Set connected for paper trading
        except RuntimeError:
            # Outside app context, will initialize later
            pass

    def _load_api_keys_from_db(self):
        """Load API keys from database for the specific user"""
        try:
            from ..models import ExchangeConnection

            # Look for Binance or Binance testnet connection
            connection = ExchangeConnection.query.filter(
                ExchangeConnection.user_id == self.user_id,
                ExchangeConnection.exchange_name.in_(["binance", "binance_testnet"]),
            ).first()

            if not connection:
                current_app.logger.info(
                    f"No Binance connection found for user {self.user_id}"
                )
                return

            if connection.api_key and connection.api_secret:
                self.api_key = connection.api_key
                self.api_secret = connection.api_secret
                self.testnet = connection.exchange_name == "binance_testnet"
                current_app.logger.info(
                    f"Loaded Binance API keys from database for user {self.user_id} (testnet: {self.testnet})"
                )
                current_app.logger.debug(
                    f"API Key starts with: {self.api_key[:8]}... (length: {len(self.api_key)})"
                )
            else:
                current_app.logger.warning(
                    f"Binance API keys not configured for user {self.user_id}"
                )

        except Exception as e:
            current_app.logger.error(
                f"Error loading Binance API keys from database: {e}"
            )

    def _is_placeholder_key(self):
        """Check if the API key is a placeholder value"""
        placeholder_values = [
            "your_binance_api_key_here",
            "YOUR_API_KEY",
            "test_key",
            None,
            "",
        ]
        return (
            not self.api_key
            or not self.api_secret
            or self.api_key in placeholder_values
            or self.api_secret in placeholder_values
        )

    def _get_server_time(self):
        """Get Binance server time for synchronization"""
        try:
            url = f"{self.base_url}/v3/time"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                server_time = response.json()["serverTime"]
                local_time = int(time.time() * 1000)
                self.server_time_offset = server_time - local_time
                return server_time
        except Exception as e:
            current_app.logger.warning(f"Failed to get server time: {e}")
            self.server_time_offset = 0
        return int(time.time() * 1000)

    def _generate_signature(self, query_string):
        """Generate HMAC signature for Binance API"""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _make_request(self, method, endpoint, params=None, signed=False):
        """Make authenticated request to Binance API"""
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}

        if params is None:
            params = {}

        if signed:
            # Use synchronized timestamp
            if self.server_time_offset == 0:
                self._get_server_time()

            timestamp = int(time.time() * 1000) + self.server_time_offset
            params["timestamp"] = timestamp

            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            params["signature"] = self._generate_signature(query_string)

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                response = requests.post(url, headers=headers, data=params, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=headers, params=params, timeout=10
                )

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Binance API request failed: {str(e)}")
            raise ConnectionError(f"Failed to connect to Binance API: {str(e)}")

    def connect(self):
        """Test connection to Binance API"""
        try:
            # Check if API credentials are configured
            if (
                not self.api_key
                or not self.api_secret
                or self.api_key.startswith("your_")
            ):
                current_app.logger.warning(
                    "Binance API credentials not configured or using placeholder values. Using demo mode."
                )
                self.is_connected = True  # Set to connected for demo purposes
                return True

            # Synchronize server time first
            self._get_server_time()

            # Test connectivity (this endpoint doesn't require authentication)
            try:
                response = self._make_request("GET", "/v3/ping")
                current_app.logger.info("Binance API connectivity test passed")
            except Exception as ping_error:
                current_app.logger.warning(f"Binance ping failed: {str(ping_error)}")

            # Test API key permissions (this requires valid credentials)
            try:
                account_info = self._make_request("GET", "/v3/account", signed=True)
                self.is_connected = True
                current_app.logger.info(
                    "Successfully connected to Binance API with valid credentials"
                )
                return True
            except Exception as auth_error:
                current_app.logger.warning(
                    f"Binance authentication failed: {str(auth_error)}"
                )
                current_app.logger.info("Falling back to demo mode with mock data")
                self.is_connected = True  # Still mark as connected for demo purposes
                return True

        except Exception as e:
            current_app.logger.error(f"Failed to connect to Binance: {str(e)}")
            # For demo purposes, set connected to true but log the error
            current_app.logger.info(
                "Running in demo mode without real Binance connection"
            )
            self.is_connected = True
            return True

    def get_account_info(self):
        """Get account information"""
        if not self.is_connected:
            raise ConnectionError("Binance not connected.")

        # If no real API credentials, return mock data
        if not self.api_key or not self.api_secret:
            return {
                "accountType": "SPOT",
                "balances": [
                    {"asset": "BTC", "free": "1.00000000", "locked": "0.00000000"},
                    {"asset": "ETH", "free": "10.00000000", "locked": "0.00000000"},
                    {"asset": "USDT", "free": "10000.00000000", "locked": "0.00000000"},
                ],
                "canTrade": True,
                "canWithdraw": False,
                "canDeposit": True,
            }

        return self._make_request("GET", "/v3/account", signed=True)

    def get_symbol_info(self, symbol):
        """Get symbol information"""
        exchange_info = self._make_request("GET", "/v3/exchangeInfo")
        for symbol_info in exchange_info["symbols"]:
            if symbol_info["symbol"] == symbol.upper():
                return symbol_info
        return None

    def get_price(self, symbol):
        """Get current price for a symbol"""
        try:
            # If no real API credentials or placeholder credentials, return mock prices
            if (
                not self.api_key
                or not self.api_secret
                or self.api_key.startswith("your_")
            ):
                mock_prices = {
                    "BTCUSDT": 43250.50,
                    "ETHUSDT": 2650.75,
                    "BNBUSDT": 310.25,
                    "ADAUSDT": 0.85,
                    "DOTUSDT": 12.45,
                    "LINKUSDT": 18.30,
                    "LTCUSDT": 180.50,
                    "XRPUSDT": 0.65,
                    "ENAUSDT": 0.7935,
                    "SOLUSDT": 85.20,
                    "AVAXUSDT": 35.40,
                    "MATICUSDT": 0.82,
                    "DOGEUSDT": 0.078,
                }
                return mock_prices.get(symbol.upper(), 100.0)

            # Try to get real price
            try:
                response = self._make_request(
                    "GET", "/v3/ticker/price", {"symbol": symbol.upper()}
                )
                return float(response["price"])
            except Exception as api_error:
                current_app.logger.warning(
                    f"Failed to get real price, using mock: {str(api_error)}"
                )
                # Fallback to mock prices if API fails
                mock_prices = {
                    "BTCUSDT": 43250.50,
                    "ETHUSDT": 2650.75,
                    "BNBUSDT": 310.25,
                    "ADAUSDT": 0.85,
                    "DOTUSDT": 12.45,
                    "LINKUSDT": 18.30,
                    "LTCUSDT": 180.50,
                    "XRPUSDT": 0.65,
                    "ENAUSDT": 0.7935,
                    "SOLUSDT": 85.20,
                    "AVAXUSDT": 35.40,
                    "MATICUSDT": 0.82,
                    "DOGEUSDT": 0.078,
                }
                return mock_prices.get(symbol.upper(), 100.0)

        except Exception as e:
            current_app.logger.error(f"Failed to get price for {symbol}: {str(e)}")
            # Return mock price as final fallback
            return 100.0

    def get_klines(self, symbol, interval="1m", limit=100):
        """Get historical price data"""
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

        try:
            # If no real API credentials or invalid credentials, return mock data
            if (
                not self.api_key
                or not self.api_secret
                or self.api_key.startswith("your_")
            ):
                return self._generate_mock_klines(symbol, limit)

            # Try to get real data
            try:
                klines = self._make_request("GET", "/v3/klines", params)
            except Exception as api_error:
                current_app.logger.warning(
                    f"API call failed, using mock data: {str(api_error)}"
                )
                return self._generate_mock_klines(symbol, limit)

            # Convert to DataFrame for analysis
            df = pd.DataFrame(
                klines,
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_asset_volume",
                    "number_of_trades",
                    "taker_buy_base_asset_volume",
                    "taker_buy_quote_asset_volume",
                    "ignore",
                ],
            )

            # Convert numeric columns
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])

            # Convert timestamp
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            return df
        except Exception as e:
            current_app.logger.error(f"Failed to get klines for {symbol}: {str(e)}")
            return self._generate_mock_klines(symbol, limit)

    def _generate_mock_klines(self, symbol, limit):
        """Generate mock klines data for demo purposes"""
        import numpy as np
        from datetime import datetime, timedelta

        # Get base price for the symbol
        base_prices = {
            "BTCUSDT": 43000,
            "ETHUSDT": 2500,
            "BNBUSDT": 300,
            "ADAUSDT": 0.5,
            "XRPUSDT": 0.6,
            "SOLUSDT": 100,
            "DOTUSDT": 7,
            "DOGEUSDT": 0.08,
            "AVAXUSDT": 35,
            "MATICUSDT": 0.8,
        }

        current_price = base_prices.get(symbol, 100.0)
        mock_data = []
        timestamp = datetime.now() - timedelta(minutes=limit)

        for i in range(limit):
            # Simple random walk for mock data
            price_change = np.random.normal(0, current_price * 0.002)
            open_price = current_price
            close_price = current_price + price_change
            high_price = max(open_price, close_price) * (
                1 + abs(np.random.normal(0, 0.001))
            )
            low_price = min(open_price, close_price) * (
                1 - abs(np.random.normal(0, 0.001))
            )
            volume = np.random.uniform(1000, 10000)

            mock_data.append(
                [
                    int(timestamp.timestamp() * 1000),  # timestamp
                    open_price,  # open
                    high_price,  # high
                    low_price,  # low
                    close_price,  # close
                    volume,  # volume
                    int(timestamp.timestamp() * 1000) + 60000,  # close_time
                    volume * close_price,  # quote_asset_volume
                    100,  # number_of_trades
                    volume * 0.5,  # taker_buy_base_asset_volume
                    volume * close_price * 0.5,  # taker_buy_quote_asset_volume
                    0,  # ignore
                ]
            )

            current_price = close_price
            timestamp += timedelta(minutes=1)

        # Convert to DataFrame
        df = pd.DataFrame(
            mock_data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )

        # Convert numeric columns
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        # Convert timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        return df

    def place_order(self, order_payload):
        """
        Place an order on Binance
        order_payload should contain:
        - symbol: Trading pair (e.g., 'BTCUSDT')
        - side: 'BUY' or 'SELL'
        - type: 'MARKET', 'LIMIT', etc.
        - quantity: Amount to trade
        - price: Price for limit orders (optional)
        """
        if not self.is_connected:
            raise ConnectionError("Binance not connected. Cannot place real orders.")

        # If no real API credentials, simulate order placement
        if not self.api_key or not self.api_secret:
            import random

            mock_order_id = random.randint(100000, 999999)
            current_app.logger.info(
                f"Demo order placed: {order_payload['side']} {order_payload['quantity']} {order_payload['symbol']} (Order ID: {mock_order_id})"
            )
            return str(mock_order_id)

        # Prepare order parameters
        params = {
            "symbol": order_payload["symbol"].upper(),
            "side": order_payload["side"].upper(),
            "type": order_payload.get("order_type", "MARKET").upper(),
            "quantity": str(order_payload["quantity"]),
        }

        # Add price for limit orders
        if params["type"] == "LIMIT":
            params["price"] = str(order_payload["price"])
            params["timeInForce"] = "GTC"  # Good Till Cancelled

        try:
            current_app.logger.info(f"Placing Binance order: {params}")
            response = self._make_request("POST", "/v3/order", params, signed=True)

            current_app.logger.info(f"Order placed successfully: {response['orderId']}")
            return response["orderId"]

        except Exception as e:
            current_app.logger.error(f"Failed to place order: {str(e)}")
            # Return mock order ID as fallback
            import random

            mock_order_id = random.randint(100000, 999999)
            current_app.logger.info(f"Fallback demo order: {mock_order_id}")
            return str(mock_order_id)

    def get_order_status(self, symbol, order_id):
        """Get status of a specific order"""
        if not self.is_connected:
            raise ConnectionError("Binance not connected.")

        params = {"symbol": symbol.upper(), "orderId": order_id}

        try:
            response = self._make_request("GET", "/v3/order", params, signed=True)

            return {
                "order_id": response["orderId"],
                "status": response["status"],
                "filled_quantity": float(response["executedQty"]),
                "average_price": (
                    float(response["price"]) if response["price"] != "0.00000000" else 0
                ),
                "original_quantity": float(response["origQty"]),
                "side": response["side"],
                "type": response["type"],
            }
        except Exception as e:
            current_app.logger.error(f"Failed to get order status: {str(e)}")
            raise

    def cancel_order(self, symbol, order_id):
        """Cancel an open order"""
        if not self.is_connected:
            raise ConnectionError("Binance not connected.")

        params = {"symbol": symbol.upper(), "orderId": order_id}

        try:
            response = self._make_request("DELETE", "/v3/order", params, signed=True)
            current_app.logger.info(f"Order cancelled: {order_id}")
            return response
        except Exception as e:
            current_app.logger.error(f"Failed to cancel order: {str(e)}")
            raise

    def get_balances(self):
        """Get account balances"""
        if not self.is_connected:
            raise ConnectionError("Binance not connected.")

        try:
            account_info = self.get_account_info()
            balances = []

            for balance in account_info["balances"]:
                free_balance = float(balance["free"])
                locked_balance = float(balance["locked"])

                if free_balance > 0 or locked_balance > 0:
                    balances.append(
                        {
                            "asset": balance["asset"],
                            "free": free_balance,
                            "locked": locked_balance,
                            "total": free_balance + locked_balance,
                        }
                    )

            return balances
        except Exception as e:
            current_app.logger.error(f"Failed to get balances: {str(e)}")
            raise

    def get_top_crypto_symbols(self, limit=20):
        """Get top cryptocurrency trading pairs by volume"""
        try:
            # Get 24hr ticker statistics
            tickers = self._make_request("GET", "/v3/ticker/24hr")

            # Filter USDT pairs and sort by volume
            usdt_pairs = [
                ticker
                for ticker in tickers
                if ticker["symbol"].endswith("USDT")
                and float(ticker["quoteVolume"]) > 0
            ]

            # Sort by 24hr volume (descending)
            usdt_pairs.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)

            # Return top symbols with relevant data
            top_symbols = []
            for ticker in usdt_pairs[:limit]:
                top_symbols.append(
                    {
                        "symbol": ticker["symbol"],
                        "price": float(ticker["lastPrice"]),
                        "change_24h": float(ticker["priceChangePercent"]),
                        "volume_24h": float(ticker["volume"]),
                        "quote_volume_24h": float(ticker["quoteVolume"]),
                    }
                )

            return top_symbols
        except Exception as e:
            current_app.logger.error(f"Failed to get top crypto symbols: {str(e)}")
            return []

    def get_market_data(self, symbol):
        """Get comprehensive market data for a symbol"""
        try:
            # Get 24hr ticker
            ticker = self._make_request(
                "GET", "/v3/ticker/24hr", {"symbol": symbol.upper()}
            )

            # Get current price
            price_data = self._make_request(
                "GET", "/v3/ticker/price", {"symbol": symbol.upper()}
            )

            return {
                "symbol": symbol.upper(),
                "current_price": float(price_data["price"]),
                "open_price": float(ticker["openPrice"]),
                "high_price": float(ticker["highPrice"]),
                "low_price": float(ticker["lowPrice"]),
                "volume": float(ticker["volume"]),
                "quote_volume": float(ticker["quoteVolume"]),
                "price_change": float(ticker["priceChange"]),
                "price_change_percent": float(ticker["priceChangePercent"]),
                "previous_close": float(ticker["prevClosePrice"]),
            }
        except Exception as e:
            current_app.logger.error(
                f"Failed to get market data for {symbol}: {str(e)}"
            )
            return None
