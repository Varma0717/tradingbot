"""
Portfolio Manager for tracking positions, balances, and portfolio performance.
Provides comprehensive portfolio management and risk calculation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pass

from ..core.config import Config
from ..core.exceptions import PortfolioError, InsufficientFundsError
from ..utils.logger import get_logger
from ..utils.helpers import safe_float, calculate_percentage_change
from .order_manager import Order, OrderStatus


class PositionSide(Enum):
    """Position side enumeration."""

    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


@dataclass
class Position:
    """Represents a trading position."""

    symbol: str
    side: PositionSide
    size: float
    average_price: float
    market_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def update_market_price(self, price: float):
        """Update market price and recalculate unrealized P&L."""
        self.market_price = price
        self.updated_at = datetime.now()

        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (price - self.average_price) * self.size
        elif self.side == PositionSide.SHORT:
            self.unrealized_pnl = (self.average_price - price) * self.size
        else:
            self.unrealized_pnl = 0.0

    def total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    def pnl_percentage(self) -> float:
        """Get P&L as percentage of position value."""
        if self.average_price == 0 or self.size == 0:
            return 0.0

        position_value = abs(self.average_price * self.size)
        return (self.total_pnl() / position_value) * 100

    def market_value(self) -> float:
        """Get current market value of position."""
        return self.market_price * abs(self.size)

    def is_flat(self) -> bool:
        """Check if position is flat (no position)."""
        return self.side == PositionSide.FLAT or abs(self.size) < 1e-8

    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "size": self.size,
            "average_price": self.average_price,
            "market_price": self.market_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "total_pnl": self.total_pnl(),
            "pnl_percentage": self.pnl_percentage(),
            "market_value": self.market_value(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Balance:
    """Represents account balance for a currency."""

    currency: str
    total: float
    free: float
    locked: float = 0.0

    @property
    def used(self) -> float:
        """Get used balance."""
        return max(0, self.total - self.free)

    def to_dict(self) -> Dict[str, Any]:
        """Convert balance to dictionary."""
        return {
            "currency": self.currency,
            "total": self.total,
            "free": self.free,
            "locked": self.locked,
            "used": self.used,
        }


@dataclass
class Trade:
    """Represents a completed trade."""

    id: str
    symbol: str
    side: str
    amount: float
    price: float
    fee: float
    cost: float
    timestamp: datetime
    order_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side,
            "amount": self.amount,
            "price": self.price,
            "fee": self.fee,
            "cost": self.cost,
            "timestamp": self.timestamp,
            "order_id": self.order_id,
        }


class PortfolioManager:
    """
    Portfolio manager for tracking positions, balances, and performance.
    """

    def __init__(self, config: Config):
        """
        Initialize portfolio manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Portfolio tracking
        self.positions: Dict[str, Position] = {}
        self.balances: Dict[str, Balance] = {}
        self.trades: List[Trade] = []

        # Performance tracking
        self.initial_balance = 0.0
        self.current_balance = 0.0
        self.total_realized_pnl = 0.0
        self.total_unrealized_pnl = 0.0
        self.max_balance = 0.0
        self.max_drawdown = 0.0
        self.daily_pnl = 0.0
        self.daily_start_balance = 0.0

        # Risk metrics
        self.risk_per_trade = config.risk.risk_per_trade
        self.max_position_size = config.risk.max_position_size
        self.max_daily_loss = config.risk.max_daily_loss
        self.daily_loss = 0.0

        # Performance history
        self.balance_history: List[Tuple[datetime, float]] = []
        self.pnl_history: List[Tuple[datetime, float]] = []

        # Initialize base currency
        self.base_currency = getattr(config.trading, "base_currency", "USDT")
        self.balances[self.base_currency] = Balance(self.base_currency, 0.0, 0.0)

    async def initialize(self, exchange, initial_balance: Optional[float] = None):
        """
        Initialize portfolio with current balances.

        Args:
            exchange: Exchange instance
            initial_balance: Initial balance override
        """
        try:
            if self.config.trading.mode == "paper":
                # Paper trading initialization
                paper_balance = initial_balance or self.config.trading.paper_balance
                self.initial_balance = paper_balance
                self.current_balance = paper_balance
                self.balances[self.base_currency] = Balance(
                    self.base_currency, paper_balance, paper_balance
                )

                self.logger.info(
                    f"Initialized paper portfolio with {paper_balance} {self.base_currency}"
                )
            else:
                # Live trading initialization
                balance_data = await exchange.fetch_balance()

                for currency, balance_info in balance_data.items():
                    if currency in ["free", "used", "total", "info"]:
                        continue

                    total = safe_float(balance_info.get("total", 0))
                    free = safe_float(balance_info.get("free", 0))
                    locked = safe_float(balance_info.get("used", 0))

                    if total > 0:
                        self.balances[currency] = Balance(currency, total, free, locked)

                # Calculate initial balance in base currency
                base_balance = self.balances.get(
                    self.base_currency, Balance(self.base_currency, 0, 0)
                )
                self.initial_balance = base_balance.total
                self.current_balance = base_balance.total

                self.logger.info(
                    f"Initialized live portfolio with {len(self.balances)} currencies"
                )

            self.max_balance = self.current_balance
            self.daily_start_balance = self.current_balance

            # Record initial state
            self.balance_history.append((datetime.now(), self.current_balance))
            self.pnl_history.append((datetime.now(), 0.0))

        except Exception as e:
            self.logger.error(f"Error initializing portfolio: {e}")
            raise PortfolioError(f"Portfolio initialization failed: {e}")

    async def update_positions(self, market_data: Dict[str, Dict[str, float]]):
        """
        Update positions with current market prices.

        Args:
            market_data: Market data with current prices
        """
        try:
            total_unrealized = 0.0

            for symbol, position in self.positions.items():
                if position.is_flat():
                    continue

                # Get current market price
                if symbol in market_data:
                    current_price = market_data[symbol].get(
                        "price", position.market_price
                    )
                    position.update_market_price(current_price)
                    total_unrealized += position.unrealized_pnl

            self.total_unrealized_pnl = total_unrealized

            # Update current balance
            self.current_balance = self.get_total_balance()

            # Update daily P&L (difference from initial balance)
            self.daily_pnl = self.current_balance - self.initial_balance

            # Update max balance and drawdown
            if self.current_balance > self.max_balance:
                self.max_balance = self.current_balance

            current_drawdown = (
                (self.max_balance - self.current_balance) / self.max_balance * 100
            )
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown

            # Record balance history
            now = datetime.now()
            self.balance_history.append((now, self.current_balance))
            self.pnl_history.append((now, self.get_total_pnl()))

            # Cleanup old history (keep last 1000 entries)
            if len(self.balance_history) > 1000:
                self.balance_history = self.balance_history[-1000:]
                self.pnl_history = self.pnl_history[-1000:]

        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")

    async def update_portfolio(self):
        """
        Update the entire portfolio with latest market data.
        This method is called by the bot's monitoring tasks.
        """
        try:
            # If we have an exchange connection, get latest market data
            if hasattr(self, "exchange") and self.exchange:
                # Get current positions and update with latest prices
                market_data = {}
                for symbol in self.positions.keys():
                    try:
                        # This would normally fetch from exchange
                        # For now, just update with existing data
                        pass
                    except Exception as e:
                        self.logger.warning(
                            f"Could not update market data for {symbol}: {e}"
                        )

                await self.update_positions(market_data)

            self.logger.debug("Portfolio updated successfully")
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")

    async def process_filled_order(self, order: Order):
        """
        Process a filled order and update portfolio.

        Args:
            order: Filled order
        """
        try:
            if order.status != OrderStatus.FILLED:
                return

            symbol = order.symbol
            side = order.side
            amount = order.filled_amount
            price = order.average_price
            cost = order.cost
            fee = order.fee

            # Create trade record
            trade = Trade(
                id=str(uuid.uuid4()),
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                fee=fee,
                cost=cost,
                timestamp=order.filled_at or datetime.now(),
                order_id=order.id,
            )

            self.trades.append(trade)

            # Update position
            await self._update_position(symbol, side, amount, price, fee)

            # Update balances
            await self._update_balances(order, trade)

            self.logger.info(f"Processed filled order: {order.id}")

        except Exception as e:
            self.logger.error(f"Error processing filled order {order.id}: {e}")

    async def _update_position(
        self, symbol: str, side: str, amount: float, price: float, fee: float
    ):
        """
        Update position for a trade.

        Args:
            symbol: Trading symbol
            side: Trade side
            amount: Trade amount
            price: Trade price
            fee: Trade fee
        """
        try:
            if symbol not in self.positions:
                self.positions[symbol] = Position(
                    symbol=symbol, side=PositionSide.FLAT, size=0.0, average_price=0.0
                )

            position = self.positions[symbol]

            if side == "buy":
                # Buying - increase long position or reduce short position
                if position.side == PositionSide.FLAT:
                    # New long position
                    position.side = PositionSide.LONG
                    position.size = amount
                    position.average_price = price
                elif position.side == PositionSide.LONG:
                    # Add to long position
                    total_cost = (position.size * position.average_price) + (
                        amount * price
                    )
                    position.size += amount
                    position.average_price = total_cost / position.size
                elif position.side == PositionSide.SHORT:
                    # Reduce short position
                    if amount >= abs(position.size):
                        # Close short and possibly open long
                        realized_pnl = (position.average_price - price) * abs(
                            position.size
                        )
                        position.realized_pnl += realized_pnl
                        self.total_realized_pnl += realized_pnl

                        remaining = amount - abs(position.size)
                        if remaining > 0:
                            position.side = PositionSide.LONG
                            position.size = remaining
                            position.average_price = price
                        else:
                            position.side = PositionSide.FLAT
                            position.size = 0.0
                    else:
                        # Partial close of short
                        realized_pnl = (position.average_price - price) * amount
                        position.realized_pnl += realized_pnl
                        self.total_realized_pnl += realized_pnl
                        position.size += amount  # Reduces negative size

            else:  # sell
                # Selling - increase short position or reduce long position
                if position.side == PositionSide.FLAT:
                    # New short position
                    position.side = PositionSide.SHORT
                    position.size = -amount
                    position.average_price = price
                elif position.side == PositionSide.SHORT:
                    # Add to short position
                    total_cost = (abs(position.size) * position.average_price) + (
                        amount * price
                    )
                    position.size -= amount
                    position.average_price = total_cost / abs(position.size)
                elif position.side == PositionSide.LONG:
                    # Reduce long position
                    if amount >= position.size:
                        # Close long and possibly open short
                        realized_pnl = (price - position.average_price) * position.size
                        position.realized_pnl += realized_pnl
                        self.total_realized_pnl += realized_pnl

                        remaining = amount - position.size
                        if remaining > 0:
                            position.side = PositionSide.SHORT
                            position.size = -remaining
                            position.average_price = price
                        else:
                            position.side = PositionSide.FLAT
                            position.size = 0.0
                    else:
                        # Partial close of long
                        realized_pnl = (price - position.average_price) * amount
                        position.realized_pnl += realized_pnl
                        self.total_realized_pnl += realized_pnl
                        position.size -= amount

            # Update position timestamp
            position.updated_at = datetime.now()

            # Clean up flat positions
            if position.is_flat():
                position.size = 0.0
                position.side = PositionSide.FLAT

        except Exception as e:
            self.logger.error(f"Error updating position for {symbol}: {e}")

    async def _update_balances(self, order: Order, trade: Trade):
        """
        Update balances for a trade.

        Args:
            order: Order object
            trade: Trade object
        """
        try:
            if self.config.trading.mode == "paper":
                # Paper trading balance updates
                base_balance = self.balances.get(
                    self.base_currency, Balance(self.base_currency, 0, 0)
                )

                if order.side == "buy":
                    # Deduct cost from base currency
                    base_balance.total -= trade.cost + trade.fee
                    base_balance.free -= trade.cost + trade.fee
                else:
                    # Add proceeds to base currency
                    base_balance.total += trade.cost - trade.fee
                    base_balance.free += trade.cost - trade.fee

                self.balances[self.base_currency] = base_balance

            # Note: In live trading, balances would be updated by fetching from exchange

        except Exception as e:
            self.logger.error(f"Error updating balances: {e}")

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        risk_amount: Optional[float] = None,
    ) -> float:
        """
        Calculate position size based on risk management.

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_amount: Risk amount override

        Returns:
            Calculated position size
        """
        try:
            # Get available balance
            base_balance = self.balances.get(
                self.base_currency, Balance(self.base_currency, 0, 0)
            )
            available_balance = base_balance.free

            # Calculate risk amount
            if risk_amount is None:
                risk_amount = available_balance * (self.risk_per_trade / 100)

            # Calculate position size based on risk
            if stop_loss_price and stop_loss_price != entry_price:
                # Risk-based sizing with stop loss
                risk_per_unit = abs(entry_price - stop_loss_price)
                position_size = risk_amount / risk_per_unit
            else:
                # Maximum position size based on available balance
                max_position_value = available_balance * (self.max_position_size / 100)
                position_size = max_position_value / entry_price

            # Apply maximum position size limit
            max_value = available_balance * (self.max_position_size / 100)
            max_size = max_value / entry_price
            position_size = min(position_size, max_size)

            return max(0, position_size)

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0

    def can_open_position(
        self, symbol: str, side: str, amount: float, price: float
    ) -> bool:
        """
        Check if a position can be opened.

        Args:
            symbol: Trading symbol
            side: Position side
            amount: Position amount
            price: Entry price

        Returns:
            True if position can be opened
        """
        try:
            # Check available balance
            required_margin = amount * price
            base_balance = self.balances.get(
                self.base_currency, Balance(self.base_currency, 0, 0)
            )

            if required_margin > base_balance.free:
                return False

            # Check daily loss limit
            if self.daily_loss >= self.max_daily_loss:
                return False

            # Check maximum position size
            position_value = amount * price
            max_position_value = base_balance.total * (self.max_position_size / 100)

            if position_value > max_position_value:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking position capability: {e}")
            return False

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position object or None
        """
        return self.positions.get(symbol)

    def get_positions(self) -> Dict[str, Position]:
        """Get all positions."""
        return {k: v for k, v in self.positions.items() if not v.is_flat()}

    def get_balance(self, currency: str) -> Optional[Balance]:
        """
        Get balance for currency.

        Args:
            currency: Currency code

        Returns:
            Balance object or None
        """
        return self.balances.get(currency)

    def get_balances(self) -> Dict[str, Balance]:
        """Get all balances."""
        return self.balances.copy()

    def get_portfolio(self) -> Dict[str, Any]:
        """
        Get complete portfolio information.
        This method is called by the bot's monitoring tasks.

        Returns:
            Dict containing portfolio information
        """
        try:
            portfolio_info = {
                "positions": {
                    symbol: pos.to_dict() for symbol, pos in self.positions.items()
                },
                "balances": {
                    currency: balance.to_dict()
                    for currency, balance in self.balances.items()
                },
                "total_balance": self.get_total_balance(),
                "total_pnl": self.get_total_pnl(),
                "current_balance": self.current_balance,
                "max_balance": self.max_balance,
                "max_drawdown": self.max_drawdown,
                "daily_pnl": self.daily_pnl,
                "balance_history_length": len(self.balance_history),
                "pnl_history_length": len(self.pnl_history),
            }
            return portfolio_info
        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {
                "positions": {},
                "balances": {},
                "total_balance": 0.0,
                "total_pnl": 0.0,
                "current_balance": self.current_balance,
                "max_balance": self.max_balance,
                "max_drawdown": self.max_drawdown,
                "daily_pnl": self.daily_pnl,
                "balance_history_length": 0,
                "pnl_history_length": 0,
            }

    def get_total_balance(self) -> float:
        """Get total portfolio balance in base currency."""
        total = 0.0

        # Add base currency balance
        base_balance = self.balances.get(
            self.base_currency, Balance(self.base_currency, 0, 0)
        )
        total += base_balance.total

        # Add unrealized P&L from positions
        total += self.total_unrealized_pnl

        return total

    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.total_realized_pnl + self.total_unrealized_pnl

    def get_portfolio_performance(self) -> Dict[str, Any]:
        """
        Get portfolio performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        try:
            total_balance = self.get_total_balance()
            total_pnl = self.get_total_pnl()

            # Calculate returns
            total_return = 0.0
            total_return_pct = 0.0
            if self.initial_balance > 0:
                total_return = total_balance - self.initial_balance
                total_return_pct = (total_return / self.initial_balance) * 100

            # Calculate win rate
            winning_trades = len([t for t in self.trades if self._is_winning_trade(t)])
            total_trades = len(self.trades)
            win_rate = (
                (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            )

            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = self._calculate_sharpe_ratio()

            return {
                "initial_balance": self.initial_balance,
                "current_balance": total_balance,
                "total_pnl": total_pnl,
                "realized_pnl": self.total_realized_pnl,
                "unrealized_pnl": self.total_unrealized_pnl,
                "total_return": total_return,
                "total_return_pct": total_return_pct,
                "max_balance": self.max_balance,
                "max_drawdown": self.max_drawdown,
                "win_rate": win_rate,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades,
                "sharpe_ratio": sharpe_ratio,
                "active_positions": len(self.get_positions()),
                "daily_loss": self.daily_loss,
            }

        except Exception as e:
            self.logger.error(f"Error calculating portfolio performance: {e}")
            return {}

    def _is_winning_trade(self, trade: Trade) -> bool:
        """
        Check if a trade is winning based on realized P&L.

        Args:
            trade: Trade object

        Returns:
            True if winning trade
        """
        # This is a simplified check - in reality, you'd need to track
        # the complete trade cycle (entry and exit)
        # For now, we'll use a basic heuristic
        return True  # Placeholder

    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio for the portfolio.

        Returns:
            Sharpe ratio
        """
        try:
            if len(self.pnl_history) < 2:
                return 0.0

            # Get daily returns
            returns = []
            for i in range(1, len(self.pnl_history)):
                prev_pnl = self.pnl_history[i - 1][1]
                curr_pnl = self.pnl_history[i][1]
                daily_return = curr_pnl - prev_pnl
                returns.append(daily_return)

            if not returns:
                return 0.0

            # Calculate Sharpe ratio
            mean_return = (
                np.mean(returns) if "np" in globals() else sum(returns) / len(returns)
            )
            std_return = np.std(returns) if "np" in globals() else 0.0

            if std_return == 0:
                return 0.0

            # Annualized Sharpe ratio (assuming daily data)
            sharpe = (mean_return / std_return) * (252**0.5)  # 252 trading days
            return sharpe

        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics.

        Returns:
            Dictionary with risk metrics
        """
        try:
            total_balance = self.get_total_balance()

            # Calculate position concentration
            position_values = [
                pos.market_value()
                for pos in self.positions.values()
                if not pos.is_flat()
            ]
            total_position_value = sum(position_values)
            max_position_value = max(position_values) if position_values else 0.0

            concentration = (
                (max_position_value / total_position_value * 100)
                if total_position_value > 0
                else 0.0
            )

            # Calculate leverage
            leverage = (
                total_position_value / total_balance if total_balance > 0 else 0.0
            )

            return {
                "max_drawdown": self.max_drawdown,
                "daily_loss": self.daily_loss,
                "max_daily_loss": self.max_daily_loss,
                "concentration": concentration,
                "leverage": leverage,
                "position_count": len(self.get_positions()),
                "total_position_value": total_position_value,
                "available_balance": self.balances.get(
                    self.base_currency, Balance(self.base_currency, 0, 0)
                ).free,
            }

        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}

    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of each trading day)."""
        # Store the current balance as the new daily starting point
        self.daily_start_balance = self.current_balance
        self.daily_loss = 0.0
        self.daily_pnl = 0.0
        self.logger.info("Daily metrics reset")

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary.

        Returns:
            Dictionary with portfolio summary
        """
        try:
            return {
                "performance": self.get_portfolio_performance(),
                "risk_metrics": self.get_risk_metrics(),
                "positions": {
                    symbol: pos.to_dict()
                    for symbol, pos in self.get_positions().items()
                },
                "balances": {
                    currency: balance.to_dict()
                    for currency, balance in self.balances.items()
                },
                "recent_trades": [
                    trade.to_dict() for trade in self.trades[-10:]
                ],  # Last 10 trades
                "last_updated": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error generating portfolio summary: {e}")
            return {}

    async def save_state(self, database_manager):
        """
        Save portfolio state to database.

        Args:
            database_manager: Database manager instance
        """
        try:
            # Save positions
            for position in self.positions.values():
                if not position.is_flat():
                    await database_manager.save_position(position.to_dict())

            # Save trades
            for trade in self.trades[-100:]:  # Save last 100 trades
                await database_manager.save_trade(trade.to_dict())

            # Save portfolio metrics
            performance = self.get_portfolio_performance()
            await database_manager.save_portfolio_metrics(performance)

            self.logger.info("Portfolio state saved to database")

        except Exception as e:
            self.logger.error(f"Error saving portfolio state: {e}")

    async def load_state(self, database_manager):
        """
        Load portfolio state from database.

        Args:
            database_manager: Database manager instance
        """
        try:
            # Load positions
            positions_data = await database_manager.get_active_positions()
            for pos_data in positions_data:
                position = Position(
                    symbol=pos_data["symbol"],
                    side=PositionSide(pos_data["side"]),
                    size=pos_data["size"],
                    average_price=pos_data["average_price"],
                    market_price=pos_data.get("market_price", 0.0),
                )
                position.realized_pnl = pos_data.get("realized_pnl", 0.0)
                position.created_at = pos_data.get("created_at", datetime.now())
                position.updated_at = pos_data.get("updated_at", datetime.now())

                self.positions[position.symbol] = position

            # Load recent trades
            trades_data = await database_manager.get_recent_trades(limit=100)
            for trade_data in trades_data:
                trade = Trade(
                    id=trade_data["id"],
                    symbol=trade_data["symbol"],
                    side=trade_data["side"],
                    amount=trade_data["amount"],
                    price=trade_data["price"],
                    fee=trade_data["fee"],
                    cost=trade_data["cost"],
                    timestamp=trade_data["timestamp"],
                    order_id=trade_data["order_id"],
                )
                self.trades.append(trade)

            self.logger.info(
                f"Portfolio state loaded: {len(self.positions)} positions, {len(self.trades)} trades"
            )

        except Exception as e:
            self.logger.error(f"Error loading portfolio state: {e}")

    def __str__(self) -> str:
        """String representation of portfolio."""
        total_balance = self.get_total_balance()
        total_pnl = self.get_total_pnl()
        active_positions = len(self.get_positions())

        return f"Portfolio(balance={total_balance:.2f} {self.base_currency}, pnl={total_pnl:.2f}, positions={active_positions})"
