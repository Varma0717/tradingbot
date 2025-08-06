"""
Real trading engine with Binance integration.
Handles order execution, position management, and trading logic.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal

import ccxt
import pandas as pd
import numpy as np

from ..core.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TradingSignal:
    """Trading signal data structure."""

    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    price: float
    quantity: float
    confidence: float
    timestamp: datetime
    strategy: str
    reason: str


@dataclass
class Position:
    """Position data structure."""

    symbol: str
    side: str  # 'long', 'short'
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime


class BinanceTradingEngine:
    """Real trading engine with Binance integration."""

    def __init__(self, config: Config):
        self.config = config
        self.exchange = None
        self.positions: Dict[str, Position] = {}
        self.active_orders: Dict[str, dict] = {}
        self.balance_cache = {}
        self.last_balance_update = None
        self.running = False

        self._initialize_exchange()

    def _initialize_exchange(self):
        """Initialize Binance exchange connection."""
        try:
            # Get Binance configuration from exchanges dict
            binance_config = None
            for exchange_name, exchange_config in self.config.exchanges.items():
                if exchange_name.lower() == "binance":
                    binance_config = exchange_config
                    break

            if not binance_config:
                raise ValueError("Binance configuration not found in exchanges")

            self.exchange = ccxt.binance(
                {
                    "apiKey": binance_config.api_key,
                    "secret": binance_config.secret_key,
                    "sandbox": binance_config.sandbox,
                    "enableRateLimit": True,
                    "options": {
                        "defaultType": "spot",  # spot, future, margin
                    },
                }
            )

            # Test connection
            self.exchange.load_markets()
            logger.info("Binance exchange initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise

    async def start(self):
        """Start the trading engine."""
        self.running = True
        logger.info("Trading engine started")

        # Start background tasks
        tasks = [
            asyncio.create_task(self._update_positions()),
            asyncio.create_task(self._monitor_orders()),
            asyncio.create_task(self._update_balance()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Trading engine error: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop the trading engine."""
        self.running = False
        logger.info("Trading engine stopped")

    def get_balance(self, force_refresh: bool = False) -> Dict:
        """Get account balance."""
        try:
            # Use cache if recent
            if (
                not force_refresh
                and self.last_balance_update
                and datetime.now() - self.last_balance_update < timedelta(minutes=1)
            ):
                return self.balance_cache

            balance = self.exchange.fetch_balance()
            self.balance_cache = balance
            self.last_balance_update = datetime.now()

            return balance

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {}

    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker information for a symbol."""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    def get_orderbook(self, symbol: str, limit: int = 100) -> Dict:
        """Get orderbook for a symbol."""
        try:
            return self.exchange.fetch_order_book(symbol, limit)
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {}

    def get_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 100
    ) -> pd.DataFrame:
        """Get OHLCV data for technical analysis."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def place_market_order(
        self, symbol: str, side: str, amount: float
    ) -> Optional[Dict]:
        """Place a market order."""
        try:
            if self.config.trading.mode == "paper":
                # Paper trading - simulate order
                order = self._simulate_market_order(symbol, side, amount)
                logger.info(f"Paper trade: {side} {amount} {symbol}")
                return order
            else:
                # Live trading
                order = self.exchange.create_market_order(symbol, side, amount)
                logger.info(f"Live order placed: {order['id']}")
                return order

        except Exception as e:
            logger.error(f"Error placing {side} order for {symbol}: {e}")
            return None

    def place_limit_order(
        self, symbol: str, side: str, amount: float, price: float
    ) -> Optional[Dict]:
        """Place a limit order."""
        try:
            if self.config.trading.mode == "paper":
                # Paper trading - simulate order
                order = self._simulate_limit_order(symbol, side, amount, price)
                logger.info(f"Paper limit order: {side} {amount} {symbol} @ {price}")
                return order
            else:
                # Live trading
                order = self.exchange.create_limit_order(symbol, side, amount, price)
                logger.info(f"Live limit order placed: {order['id']}")
                return order

        except Exception as e:
            logger.error(f"Error placing limit {side} order for {symbol}: {e}")
            return None

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        try:
            if self.config.trading.mode == "paper":
                # Paper trading - remove from active orders
                if order_id in self.active_orders:
                    del self.active_orders[order_id]
                    logger.info(f"Paper order cancelled: {order_id}")
                    return True
            else:
                # Live trading
                result = self.exchange.cancel_order(order_id, symbol)
                logger.info(f"Live order cancelled: {order_id}")
                return True

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders."""
        try:
            if self.config.trading.mode == "paper":
                # Return paper trading orders
                orders = list(self.active_orders.values())
                if symbol:
                    orders = [o for o in orders if o["symbol"] == symbol]
                return orders
            else:
                # Live trading
                return self.exchange.fetch_open_orders(symbol)

        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    def _simulate_market_order(self, symbol: str, side: str, amount: float) -> Dict:
        """Simulate a market order for paper trading."""
        ticker = self.get_ticker(symbol)
        price = ticker.get("last", 0)

        order = {
            "id": f"paper_{datetime.now().timestamp()}",
            "symbol": symbol,
            "type": "market",
            "side": side,
            "amount": amount,
            "price": price,
            "cost": amount * price,
            "filled": amount,
            "remaining": 0,
            "status": "closed",
            "timestamp": datetime.now().timestamp() * 1000,
            "datetime": datetime.now().isoformat(),
        }

        return order

    def _simulate_limit_order(
        self, symbol: str, side: str, amount: float, price: float
    ) -> Dict:
        """Simulate a limit order for paper trading."""
        order_id = f"paper_{datetime.now().timestamp()}"

        order = {
            "id": order_id,
            "symbol": symbol,
            "type": "limit",
            "side": side,
            "amount": amount,
            "price": price,
            "cost": amount * price,
            "filled": 0,
            "remaining": amount,
            "status": "open",
            "timestamp": datetime.now().timestamp() * 1000,
            "datetime": datetime.now().isoformat(),
        }

        # Add to active orders
        self.active_orders[order_id] = order

        return order

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders."""
        try:
            if self.config.trading.mode == "paper":
                # Return paper trading orders
                orders = list(self.active_orders.values())
                if symbol:
                    orders = [o for o in orders if o["symbol"] == symbol]
                return orders
            else:
                # Live trading
                return self.exchange.fetch_open_orders(symbol)
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order."""
        try:
            if self.config.trading.mode == "paper":
                # Paper trading - remove from active orders
                if order_id in self.active_orders:
                    del self.active_orders[order_id]
                    logger.info(f"Paper order cancelled: {order_id}")
                    return True
                return False
            else:
                # Live trading
                result = self.exchange.cancel_order(order_id, symbol)
                logger.info(f"Live order cancelled: {order_id}")
                return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def stop(self):
        """Stop the trading engine."""
        self.running = False
        logger.info("Trading engine stopped")

    async def place_market_order_async(
        self, symbol: str, side: str, amount: float, strategy: str = "manual"
    ) -> Optional[Dict]:
        """Async version of place_market_order for API compatibility."""
        return self.place_market_order(symbol, side, amount)

    async def place_limit_order_async(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        strategy: str = "manual",
    ) -> Optional[Dict]:
        """Async version of place_limit_order for API compatibility."""
        return self.place_limit_order(symbol, side, amount, price)

    async def cancel_order_async(self, order_id: str) -> bool:
        """Async version of cancel_order for API compatibility."""
        return self.cancel_order(order_id)

    async def _update_positions(self):
        """Update position information."""
        while self.running:
            try:
                # Update positions logic here
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error updating positions: {e}")
                await asyncio.sleep(60)

    async def _monitor_orders(self):
        """Monitor and update order status."""
        while self.running:
            try:
                # Monitor orders logic here
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error monitoring orders: {e}")
                await asyncio.sleep(30)

    async def _update_balance(self):
        """Update balance information."""
        while self.running:
            try:
                self.get_balance(force_refresh=True)
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error updating balance: {e}")
                await asyncio.sleep(120)


# Global trading engine instance
_trading_engine = None


def get_trading_engine() -> BinanceTradingEngine:
    """Get the global trading engine instance."""
    global _trading_engine
    if _trading_engine is None:
        config = Config()
        _trading_engine = BinanceTradingEngine(config)
    return _trading_engine
