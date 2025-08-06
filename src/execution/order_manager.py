"""
Order Manager for handling order placement, execution, and tracking.
Supports multiple order types and provides comprehensive order lifecycle management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

try:
    import ccxt.async_support as ccxt
except ImportError:
    import ccxt

from ..core.config import Config
from ..core.exceptions import OrderError, InsufficientFundsError, InvalidOrderError
from ..utils.logger import get_logger
from ..utils.helpers import round_to_precision, safe_float


class OrderStatus(Enum):
    """Order status enumeration."""

    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(Enum):
    """Order type enumeration."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class Order:
    """Order object representing a trading order."""

    def __init__(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        client_order_id: Optional[str] = None,
    ):
        """
        Initialize order.

        Args:
            symbol: Trading symbol
            side: Order side ('buy' or 'sell')
            amount: Order amount
            order_type: Order type
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force
            client_order_id: Client-side order ID
        """
        self.id = client_order_id or str(uuid.uuid4())
        self.symbol = symbol
        self.side = side.lower()
        self.amount = amount
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force

        # Order tracking
        self.status = OrderStatus.PENDING
        self.exchange_order_id: Optional[str] = None
        self.filled_amount = 0.0
        self.average_price = 0.0
        self.fee = 0.0
        self.cost = 0.0

        # Timestamps
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.filled_at: Optional[datetime] = None

        # Strategy information
        self.strategy: Optional[str] = None
        self.reason: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def update_from_exchange(self, exchange_order: Dict[str, Any]):
        """
        Update order with information from exchange.

        Args:
            exchange_order: Order data from exchange
        """
        self.exchange_order_id = exchange_order.get("id")
        self.status = OrderStatus(exchange_order.get("status", "open"))
        self.filled_amount = safe_float(exchange_order.get("filled", 0))
        self.average_price = safe_float(exchange_order.get("average", 0))
        self.fee = safe_float(exchange_order.get("fee", {}).get("cost", 0))
        self.cost = safe_float(exchange_order.get("cost", 0))
        self.updated_at = datetime.now()

        if self.status == OrderStatus.FILLED:
            self.filled_at = datetime.now()

    def is_active(self) -> bool:
        """Check if order is active (open or partially filled)."""
        return self.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]

    def is_completed(self) -> bool:
        """Check if order is completed (filled, canceled, or rejected)."""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
        ]

    def remaining_amount(self) -> float:
        """Get remaining unfilled amount."""
        return max(0, self.amount - self.filled_amount)

    def fill_percentage(self) -> float:
        """Get fill percentage."""
        if self.amount == 0:
            return 0.0
        return (self.filled_amount / self.amount) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary."""
        return {
            "id": self.id,
            "exchange_order_id": self.exchange_order_id,
            "symbol": self.symbol,
            "side": self.side,
            "amount": self.amount,
            "order_type": self.order_type.value,
            "price": self.price,
            "stop_price": self.stop_price,
            "status": self.status.value,
            "filled_amount": self.filled_amount,
            "average_price": self.average_price,
            "fee": self.fee,
            "cost": self.cost,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "filled_at": self.filled_at,
            "strategy": self.strategy,
            "reason": self.reason,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """String representation of order."""
        return f"Order({self.side.upper()} {self.amount} {self.symbol} @ {self.price or 'MARKET'}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed representation of order."""
        return f"Order(id='{self.id}', symbol='{self.symbol}', side='{self.side}', amount={self.amount}, type={self.order_type.value}, status={self.status.value})"


class OrderManager:
    """
    Order manager for handling order lifecycle and execution.
    """

    def __init__(self, config: Config):
        """
        Initialize order manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Exchange connection
        self.exchange = None
        self._initialize_exchange()

        # Order tracking
        self.active_orders: Dict[str, Order] = {}
        self.completed_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []

        # Order execution settings
        self.max_retries = 3
        self.retry_delay = 1.0
        self.order_timeout = 300  # 5 minutes

        # Rate limiting
        self.last_order_time = datetime.min
        self.min_order_interval = 1.0  # 1 second between orders

    def _initialize_exchange(self):
        """Initialize exchange connection for order execution."""
        try:
            exchange_name = self.config.trading.exchange
            exchange_config = self.config.get_exchange_config(exchange_name)

            # Create exchange instance
            exchange_class = getattr(ccxt, exchange_name.lower(), None)
            if not exchange_class:
                raise OrderError(f"Unsupported exchange: {exchange_name}")

            self.exchange = exchange_class(
                {
                    "apiKey": exchange_config.api_key,
                    "secret": exchange_config.secret_key,
                    "sandbox": exchange_config.sandbox,
                    "enableRateLimit": True,
                    "timeout": exchange_config.timeout * 1000,
                }
            )

            # Add passphrase if required (e.g., Coinbase Pro)
            if hasattr(exchange_config, "passphrase") and exchange_config.passphrase:
                self.exchange.passphrase = exchange_config.passphrase

            self.logger.info(f"Initialized order manager for {exchange_name}")

        except Exception as e:
            self.logger.error(f"Failed to initialize exchange: {e}")
            raise OrderError(f"Exchange initialization failed: {e}")

    async def create_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        strategy: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Order]:
        """
        Create and submit a trading order.

        Args:
            symbol: Trading symbol
            side: Order side ('buy' or 'sell')
            amount: Order amount
            order_type: Order type
            price: Limit price (optional)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            strategy: Strategy name (optional)
            reason: Order reason (optional)
            metadata: Additional metadata (optional)

        Returns:
            Order object if successful, None otherwise
        """
        try:
            # Validate order parameters
            self._validate_order_params(symbol, side, amount, order_type, price)

            # Check paper trading mode
            if self.config.trading.mode == "paper":
                return await self._create_paper_order(
                    symbol, side, amount, order_type, price, strategy, reason, metadata
                )

            # Rate limiting
            await self._rate_limit_check()

            # Create order object
            order = Order(
                symbol=symbol,
                side=side,
                amount=amount,
                order_type=OrderType(order_type.lower()),
                price=price,
            )

            order.strategy = strategy
            order.reason = reason
            order.metadata = metadata or {}

            # Submit order to exchange
            success = await self._submit_order(order)

            if success:
                # Track order
                self.active_orders[order.id] = order
                self.order_history.append(order)

                self.logger.info(f"Order created: {order}")

                # Create stop loss and take profit orders if specified
                if stop_loss:
                    await self._create_stop_loss_order(order, stop_loss)

                if take_profit:
                    await self._create_take_profit_order(order, take_profit)

                return order
            else:
                self.logger.error(f"Failed to submit order: {order}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None

    async def _create_paper_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str,
        price: Optional[float],
        strategy: Optional[str],
        reason: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Order:
        """
        Create a paper trading order (simulation).

        Args:
            symbol: Trading symbol
            side: Order side
            amount: Order amount
            order_type: Order type
            price: Limit price
            strategy: Strategy name
            reason: Order reason
            metadata: Additional metadata

        Returns:
            Paper order object
        """
        order = Order(
            symbol=symbol,
            side=side,
            amount=amount,
            order_type=OrderType(order_type.lower()),
            price=price,
        )

        order.strategy = strategy
        order.reason = reason
        order.metadata = metadata or {}
        order.exchange_order_id = f"paper_{order.id}"

        # Simulate immediate fill for market orders
        if order_type.lower() == "market":
            # Get current market price
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                fill_price = ticker["last"]

                order.status = OrderStatus.FILLED
                order.filled_amount = amount
                order.average_price = fill_price
                order.cost = amount * fill_price
                order.filled_at = datetime.now()

                self.logger.info(f"Paper order filled: {order}")
            except Exception as e:
                self.logger.error(f"Error simulating paper order: {e}")
                order.status = OrderStatus.REJECTED
        else:
            # Limit orders remain open in simulation
            order.status = OrderStatus.OPEN

        # Track order
        if order.status == OrderStatus.FILLED:
            self.completed_orders[order.id] = order
        else:
            self.active_orders[order.id] = order

        self.order_history.append(order)

        return order

    def _validate_order_params(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str,
        price: Optional[float],
    ):
        """
        Validate order parameters.

        Args:
            symbol: Trading symbol
            side: Order side
            amount: Order amount
            order_type: Order type
            price: Limit price

        Raises:
            InvalidOrderError: If parameters are invalid
        """
        if not symbol:
            raise InvalidOrderError("Symbol is required")

        if side.lower() not in ["buy", "sell"]:
            raise InvalidOrderError(f"Invalid side: {side}")

        if amount <= 0:
            raise InvalidOrderError(f"Amount must be positive: {amount}")

        if order_type.lower() not in ["market", "limit", "stop", "stop_limit"]:
            raise InvalidOrderError(f"Invalid order type: {order_type}")

        if order_type.lower() in ["limit", "stop_limit"] and price is None:
            raise InvalidOrderError("Price is required for limit orders")

        if price is not None and price <= 0:
            raise InvalidOrderError(f"Price must be positive: {price}")

    async def _submit_order(self, order: Order) -> bool:
        """
        Submit order to exchange.

        Args:
            order: Order to submit

        Returns:
            True if successful
        """
        try:
            # Prepare order parameters
            params = {}

            if order.order_type == OrderType.MARKET:
                exchange_order = await self.exchange.create_market_order(
                    order.symbol, order.side, order.amount, params=params
                )
            elif order.order_type == OrderType.LIMIT:
                exchange_order = await self.exchange.create_limit_order(
                    order.symbol, order.side, order.amount, order.price, params=params
                )
            else:
                raise OrderError(f"Unsupported order type: {order.order_type}")

            # Update order with exchange response
            order.update_from_exchange(exchange_order)
            order.status = OrderStatus.OPEN

            self.logger.info(f"Order submitted to exchange: {order.exchange_order_id}")
            return True

        except ccxt.InsufficientFunds as e:
            self.logger.error(f"Insufficient funds for order: {e}")
            order.status = OrderStatus.REJECTED
            raise InsufficientFundsError(f"Insufficient funds: {e}")

        except ccxt.InvalidOrder as e:
            self.logger.error(f"Invalid order: {e}")
            order.status = OrderStatus.REJECTED
            raise InvalidOrderError(f"Invalid order: {e}")

        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            order.status = OrderStatus.REJECTED
            return False

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful
        """
        try:
            if order_id not in self.active_orders:
                self.logger.warning(f"Order not found: {order_id}")
                return False

            order = self.active_orders[order_id]

            if self.config.trading.mode == "paper":
                # Paper trading cancellation
                order.status = OrderStatus.CANCELED
                order.updated_at = datetime.now()

                # Move to completed orders
                del self.active_orders[order_id]
                self.completed_orders[order_id] = order

                self.logger.info(f"Paper order canceled: {order_id}")
                return True

            # Cancel on exchange
            if order.exchange_order_id:
                await self.exchange.cancel_order(order.exchange_order_id, order.symbol)

                order.status = OrderStatus.CANCELED
                order.updated_at = datetime.now()

                # Move to completed orders
                del self.active_orders[order_id]
                self.completed_orders[order_id] = order

                self.logger.info(f"Order canceled: {order_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error canceling order {order_id}: {e}")
            return False

    async def update_orders(self):
        """Update status of all active orders."""
        try:
            if not self.active_orders:
                return

            if self.config.trading.mode == "paper":
                # Paper trading - simulate order updates
                await self._update_paper_orders()
                return

            # Update orders from exchange
            for order_id, order in list(self.active_orders.items()):
                try:
                    if order.exchange_order_id:
                        exchange_order = await self.exchange.fetch_order(
                            order.exchange_order_id, order.symbol
                        )

                        order.update_from_exchange(exchange_order)

                        # Move completed orders
                        if order.is_completed():
                            del self.active_orders[order_id]
                            self.completed_orders[order_id] = order

                            if order.status == OrderStatus.FILLED:
                                self.logger.info(f"Order filled: {order}")

                except Exception as e:
                    self.logger.error(f"Error updating order {order_id}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error updating orders: {e}")

    async def _update_paper_orders(self):
        """Update paper trading orders."""
        try:
            for order_id, order in list(self.active_orders.items()):
                if order.order_type == OrderType.LIMIT:
                    # Check if limit order should be filled
                    try:
                        ticker = await self.exchange.fetch_ticker(order.symbol)
                        current_price = ticker["last"]

                        should_fill = False
                        if order.side == "buy" and current_price <= order.price:
                            should_fill = True
                        elif order.side == "sell" and current_price >= order.price:
                            should_fill = True

                        if should_fill:
                            order.status = OrderStatus.FILLED
                            order.filled_amount = order.amount
                            order.average_price = order.price
                            order.cost = order.amount * order.price
                            order.filled_at = datetime.now()

                            # Move to completed orders
                            del self.active_orders[order_id]
                            self.completed_orders[order_id] = order

                            self.logger.info(f"Paper limit order filled: {order}")

                    except Exception as e:
                        self.logger.error(f"Error checking paper order {order_id}: {e}")

        except Exception as e:
            self.logger.error(f"Error updating paper orders: {e}")

    async def get_filled_orders(self) -> List[Order]:
        """
        Get list of recently filled orders.

        Returns:
            List of filled orders
        """
        filled_orders = []

        for order in self.completed_orders.values():
            if order.status == OrderStatus.FILLED and order.filled_at:
                # Only include orders filled in the last hour
                time_since_fill = datetime.now() - order.filled_at
                if time_since_fill.total_seconds() < 3600:
                    filled_orders.append(order)

        return filled_orders

    async def _create_stop_loss_order(
        self, parent_order: Order, stop_loss_price: float
    ):
        """
        Create stop loss order for a filled order.

        Args:
            parent_order: Parent order
            stop_loss_price: Stop loss price
        """
        try:
            if parent_order.status != OrderStatus.FILLED:
                return

            # Create opposite side order
            stop_side = "sell" if parent_order.side == "buy" else "buy"

            stop_order = await self.create_order(
                symbol=parent_order.symbol,
                side=stop_side,
                amount=parent_order.filled_amount,
                order_type="stop",
                price=stop_loss_price,
                strategy=parent_order.strategy,
                reason=f"Stop loss for {parent_order.id}",
                metadata={
                    "parent_order_id": parent_order.id,
                    "order_class": "stop_loss",
                },
            )

            if stop_order:
                self.logger.info(f"Stop loss order created: {stop_order.id}")

        except Exception as e:
            self.logger.error(f"Error creating stop loss order: {e}")

    async def _create_take_profit_order(
        self, parent_order: Order, take_profit_price: float
    ):
        """
        Create take profit order for a filled order.

        Args:
            parent_order: Parent order
            take_profit_price: Take profit price
        """
        try:
            if parent_order.status != OrderStatus.FILLED:
                return

            # Create opposite side order
            profit_side = "sell" if parent_order.side == "buy" else "buy"

            profit_order = await self.create_order(
                symbol=parent_order.symbol,
                side=profit_side,
                amount=parent_order.filled_amount,
                order_type="limit",
                price=take_profit_price,
                strategy=parent_order.strategy,
                reason=f"Take profit for {parent_order.id}",
                metadata={
                    "parent_order_id": parent_order.id,
                    "order_class": "take_profit",
                },
            )

            if profit_order:
                self.logger.info(f"Take profit order created: {profit_order.id}")

        except Exception as e:
            self.logger.error(f"Error creating take profit order: {e}")

    async def _rate_limit_check(self):
        """Check and enforce rate limits."""
        current_time = datetime.now()
        time_since_last = (current_time - self.last_order_time).total_seconds()

        if time_since_last < self.min_order_interval:
            sleep_time = self.min_order_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_order_time = datetime.now()

    async def check_connectivity(self) -> bool:
        """
        Check exchange connectivity.

        Returns:
            True if connected
        """
        try:
            if self.config.trading.mode == "paper":
                return True

            await self.exchange.fetch_balance()
            return True

        except Exception as e:
            self.logger.error(f"Connectivity check failed: {e}")
            return False

    def get_active_orders(self) -> Dict[str, Order]:
        """Get all active orders."""
        return self.active_orders.copy()

    def get_completed_orders(self) -> Dict[str, Order]:
        """Get all completed orders."""
        return self.completed_orders.copy()

    def get_order_history(self) -> List[Order]:
        """Get order history."""
        return self.order_history.copy()

    def get_order_stats(self) -> Dict[str, Any]:
        """
        Get order statistics.

        Returns:
            Dictionary with order statistics
        """
        total_orders = len(self.order_history)
        filled_orders = len(
            [o for o in self.order_history if o.status == OrderStatus.FILLED]
        )
        canceled_orders = len(
            [o for o in self.order_history if o.status == OrderStatus.CANCELED]
        )
        rejected_orders = len(
            [o for o in self.order_history if o.status == OrderStatus.REJECTED]
        )

        return {
            "total_orders": total_orders,
            "active_orders": len(self.active_orders),
            "filled_orders": filled_orders,
            "canceled_orders": canceled_orders,
            "rejected_orders": rejected_orders,
            "fill_rate": (
                (filled_orders / total_orders * 100) if total_orders > 0 else 0.0
            ),
        }

    async def close(self):
        """Close order manager and exchange connections."""
        try:
            # Cancel all active orders
            for order_id in list(self.active_orders.keys()):
                await self.cancel_order(order_id)

            # Close exchange connection
            if self.exchange and hasattr(self.exchange, "close"):
                await self.exchange.close()

            self.logger.info("Order manager closed")

        except Exception as e:
            self.logger.error(f"Error closing order manager: {e}")
