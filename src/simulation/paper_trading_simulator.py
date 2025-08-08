"""
Paper Trading Simulator

Generates realistic trading activity for paper trading mode
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

logger = logging.getLogger(__name__)


class PaperTradingSimulator:
    """
    Simulates realistic trading activity for paper trading mode
    """

    def __init__(self, strategy_manager=None):
        self.strategy_manager = strategy_manager
        self.is_running = False
        self.simulation_task = None

        # Balance tracking
        self.initial_balance = 10000.0  # Starting balance
        self.current_balance = 10000.0  # Current available balance
        self.locked_balance = 0.0  # Balance locked in orders
        self.btc_holdings = 0.0  # Amount of BTC currently held

        # Mock trading data
        self.mock_trades = []
        self.mock_orders = []
        self.current_btc_price = 43000.0
        self.price_volatility = 0.02  # 2% price volatility

        # Performance tracking
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0

        logger.info("Paper Trading Simulator initialized")

    def start_simulation(self):
        """Start the trading simulation"""
        if not self.is_running:
            self.is_running = True
            self._generate_initial_data()
            # Don't start async task in __init__ to avoid event loop issues
            logger.info("Paper trading simulation started")

    def stop_simulation(self):
        """Stop the trading simulation"""
        self.is_running = False
        if self.simulation_task:
            self.simulation_task.cancel()
        logger.info("Paper trading simulation stopped")

    def _generate_initial_data(self):
        """Generate improved mock trading data with better profit performance"""
        base_time = datetime.now()

        # Generate more profitable historical trades
        profitable_trades_count = 0
        total_profit_generated = 0

        for i in range(15):  # 15 trades over 24 hours
            hours_ago = random.randint(1, 24)
            trade_time = base_time - timedelta(hours=hours_ago)

            # Improved profit distribution - 70% profitable trades
            is_profitable_trade = i < 11  # First 11 trades are profitable
            is_buy = random.choice([True, False])

            # Better price variation based on profitability
            if is_profitable_trade:
                price_variation = random.uniform(-0.02, 0.03)  # Slightly favorable
                profit = random.uniform(8.0, 50.0)  # $8-50 profit
            else:
                price_variation = random.uniform(-0.04, 0.02)  # Less favorable
                profit = random.uniform(-20.0, -3.0)  # $3-20 loss

            price = self.current_btc_price * (1 + price_variation)
            amount = random.uniform(0.001, 0.008)  # Slightly larger amounts
            total = price * amount

            trade = {
                "id": f"trade_{i+1}",
                "type": "buy" if is_buy else "sell",
                "symbol": "BTCUSDT",  # Add symbol field
                "amount": round(amount, 6),
                "price": round(price, 2),
                "total": round(total, 2),
                "timestamp": trade_time.isoformat(),
                "status": "completed",
                "profit": round(profit, 2),
                "fee": round(total * 0.001, 2),  # 0.1% fee
            }

            self.mock_trades.append(trade)

            # Update balance tracking
            if is_buy:
                self.current_balance -= total + trade["fee"]
                self.btc_holdings += amount
            else:
                self.current_balance += total - trade["fee"]
                self.btc_holdings -= amount

            # Apply profit/loss to balance
            self.current_balance += profit
            self.total_profit += profit
            total_profit_generated += profit

            if profit > 0:
                self.profitable_trades += 1
                profitable_trades_count += 1

            self.total_trades += 1

        # Generate strategic active orders with better spacing
        active_orders_created = 0
        for i in range(6):  # Reduced to 6 strategic orders
            is_buy = i < 3  # First 3 are buy orders, last 3 are sell orders
            level = (i % 3) + 1

            if is_buy:
                # Buy orders at strategic support levels
                price = self.current_btc_price * (1 - 0.008 * level)  # 0.8% spacing
                amount = random.uniform(0.001, 0.004)
                order_total = price * amount

                # Only create buy order if we have enough balance
                if self.current_balance >= order_total:
                    self.current_balance -= order_total
                    self.locked_balance += order_total

                    order = {
                        "id": f"order_{i+1}",
                        "type": "buy",
                        "symbol": "BTCUSDT",  # Add symbol field
                        "amount": round(amount, 6),
                        "price": round(price, 2),
                        "total": round(order_total, 2),
                        "status": "open",
                        "created": (
                            datetime.now() - timedelta(minutes=random.randint(5, 120))
                        ).isoformat(),
                    }
                    self.mock_orders.append(order)
                    active_orders_created += 1
            else:
                # Sell orders at resistance levels (only if we have BTC)
                if self.btc_holdings > 0:
                    price = self.current_btc_price * (1 + 0.012 * level)  # 1.2% spacing
                    amount = min(random.uniform(0.001, 0.003), self.btc_holdings * 0.3)

                    order = {
                        "id": f"order_{i+1}",
                        "type": "sell",
                        "symbol": "BTCUSDT",  # Add symbol field
                        "amount": round(amount, 6),
                        "price": round(price, 2),
                        "total": round(price * amount, 2),
                        "status": "open",
                        "created": (
                            datetime.now() - timedelta(minutes=random.randint(5, 120))
                        ).isoformat(),
                    }
                    self.mock_orders.append(order)
                    active_orders_created += 1

        # Recalculate total balance
        self._recalculate_balance()

        logger.info(
            f"Generated {len(self.mock_trades)} trades ({profitable_trades_count} profitable)"
        )
        logger.info(f"Generated {active_orders_created} strategic orders")
        logger.info(f"Total profit generated: ${total_profit_generated:.2f}")
        logger.info(f"Current total balance: ${self.get_total_balance():.2f}")

    def _recalculate_balance(self):
        """Recalculate balance based on trades and orders"""
        # Reset to initial balance
        balance = self.initial_balance
        btc_held = 0.0
        locked = 0.0

        # Apply all completed trades
        for trade in self.mock_trades:
            if trade["status"] == "completed":
                if trade["type"] == "buy":
                    # Bought BTC: decrease USDT balance, increase BTC holdings
                    balance -= trade["total"]
                    btc_held += trade["amount"]
                else:
                    # Sold BTC: increase USDT balance, decrease BTC holdings
                    balance += trade["total"]
                    btc_held -= trade["amount"]
                    # Add profit from the trade
                    if "profit" in trade:
                        balance += trade["profit"]

        # Calculate locked balance for open orders
        for order in self.mock_orders:
            if order["status"] == "open" and order["type"] == "buy":
                # Buy orders lock USDT
                locked += order["total"]

        # Ensure we don't go negative
        self.current_balance = max(0, balance - locked)
        self.locked_balance = locked
        self.btc_holdings = max(0, btc_held)

        logger.debug(
            f"Balance recalculated: Available=${self.current_balance:.2f}, Locked=${self.locked_balance:.2f}, BTC={self.btc_holdings:.6f}"
        )

    def get_total_balance(self) -> float:
        """Get total portfolio value in USDT"""
        # Available USDT + Locked USDT + BTC value in USDT
        btc_value = self.btc_holdings * self.current_btc_price
        return self.current_balance + self.locked_balance + btc_value

    def get_available_balance(self) -> float:
        """Get available USDT balance"""
        return self.current_balance

    def get_locked_balance(self) -> float:
        """Get locked USDT balance (in orders)"""
        return self.locked_balance

    def _simulate_price_movement(self):
        """Simulate realistic BTC price movement"""
        # Small random price movements
        change_percent = random.uniform(-self.price_volatility, self.price_volatility)
        self.current_btc_price *= 1 + change_percent

        # Keep price in reasonable range
        self.current_btc_price = max(35000, min(50000, self.current_btc_price))

    def _maybe_execute_trade(self):
        """Randomly execute a trade to show activity"""
        if random.random() < 0.1:  # 10% chance per update
            # Execute a random buy or sell
            is_buy = random.choice([True, False])
            amount = random.uniform(0.001, 0.003)
            price = self.current_btc_price * (1 + random.uniform(-0.001, 0.001))
            total = price * amount

            # Check if we have enough balance/BTC for the trade
            if is_buy and total > self.current_balance:
                return  # Not enough USDT for buy order
            elif not is_buy and amount > self.btc_holdings:
                return  # Not enough BTC for sell order

            # Remove an old order and add a new trade
            if self.mock_orders:
                executed_order = self.mock_orders.pop(0)

                # If we're executing a buy order, free up the locked balance
                if executed_order["type"] == "buy":
                    self.locked_balance -= executed_order["total"]

            # Create trade with realistic profit calculation
            profit = 0
            if not is_buy:  # Sell orders generate profit/loss
                # Calculate profit based on price difference from average buy price
                avg_buy_price = 42000  # Simplified average buy price
                profit = (price - avg_buy_price) * amount

            trade = {
                "id": f"trade_{len(self.mock_trades) + 1}",
                "type": "buy" if is_buy else "sell",
                "amount": round(amount, 6),
                "price": round(price, 2),
                "total": round(total, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "profit": round(profit, 2),
            }

            # Apply trade to balance immediately
            if is_buy:
                self.current_balance -= total
                self.btc_holdings += amount
            else:
                self.current_balance += total + profit  # Add proceeds + profit
                self.btc_holdings -= amount

            self.mock_trades.insert(0, trade)  # Add to beginning (most recent first)

            # Keep only last 20 trades
            if len(self.mock_trades) > 20:
                self.mock_trades.pop()

            # Add a new order to replace the executed one
            new_order = self._generate_new_order()
            if new_order:  # Only add if we have sufficient balance
                self.mock_orders.append(new_order)

            # Update statistics
            self.total_trades += 1
            if not is_buy and profit > 0:
                self.profitable_trades += 1
                self.total_profit += profit

            logger.debug(
                f"Simulated trade: {trade['type']} {trade['amount']} BTC @ ${trade['price']}, Balance: ${self.current_balance:.2f}"
            )

    def _generate_new_order(self):
        """Generate a new order if we have sufficient balance"""
        is_buy = random.choice([True, False])
        level = random.randint(1, 4)

        if is_buy:
            price = self.current_btc_price * (1 - 0.01 * level)
        else:
            price = self.current_btc_price * (1 + 0.01 * level)

        amount = random.uniform(0.001, 0.005)
        total = price * amount

        # Check if we have enough balance for this order
        if is_buy and total > self.current_balance:
            # Try a smaller amount
            max_amount = self.current_balance / price * 0.8  # Use 80% of available
            if max_amount < 0.001:  # Minimum viable amount
                return None
            amount = min(amount, max_amount)
            total = price * amount

        elif not is_buy and amount > self.btc_holdings:
            # Try a smaller amount
            max_amount = self.btc_holdings * 0.8  # Use 80% of holdings
            if max_amount < 0.001:  # Minimum viable amount
                return None
            amount = min(amount, max_amount)
            total = price * amount

        # Lock balance for buy orders
        if is_buy:
            self.locked_balance += total
            self.current_balance -= total

        return {
            "id": f"order_{int(time.time() * 1000)}",
            "type": "buy" if is_buy else "sell",
            "amount": round(amount, 6),
            "price": round(price, 2),
            "total": round(total, 2),
            "status": "open",
            "created": datetime.now().isoformat(),
        }

    def update_simulation(self):
        """Update simulation state (called periodically)"""
        if not self.is_running:
            return

        self._simulate_price_movement()
        self._maybe_execute_trade()

        # Ensure balance stays consistent
        self._validate_balance()

    def _validate_balance(self):
        """Ensure balance calculations are consistent"""
        # Prevent negative balances
        if self.current_balance < 0:
            self.current_balance = 0
        if self.btc_holdings < 0:
            self.btc_holdings = 0
        if self.locked_balance < 0:
            self.locked_balance = 0

    def get_trades(self) -> List[Dict[str, Any]]:
        """Get current mock trades"""
        return self.mock_trades.copy()

    def get_orders(self) -> List[Dict[str, Any]]:
        """Get current mock orders"""
        return self.mock_orders.copy()

    def get_current_price(self) -> float:
        """Get current simulated BTC price"""
        return self.current_btc_price

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        win_rate = (self.profitable_trades / max(1, self.total_trades)) * 100
        total_portfolio_value = self.get_total_balance()
        profit_loss = total_portfolio_value - self.initial_balance

        return {
            "total_trades": self.total_trades,
            "profitable_trades": self.profitable_trades,
            "win_rate": round(win_rate, 1),
            "total_profit": round(self.total_profit, 2),
            "avg_profit_per_trade": round(
                self.total_profit / max(1, self.total_trades), 2
            ),
            "current_btc_price": round(self.current_btc_price, 2),
            "total_balance": round(total_portfolio_value, 2),
            "available_balance": round(self.current_balance, 2),
            "locked_balance": round(self.locked_balance, 2),
            "btc_holdings": round(self.btc_holdings, 6),
            "portfolio_pnl": round(profit_loss, 2),
            "initial_balance": self.initial_balance,
        }


# Global instance for paper trading simulation
paper_trading_simulator = PaperTradingSimulator()
