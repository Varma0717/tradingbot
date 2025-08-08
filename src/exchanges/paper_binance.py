import logging
import time
from datetime import datetime
import random


class PaperBinanceExchange:
    def __init__(self):
        """Initialize paper trading exchange with simulated balance"""
        self.paper_balance = 1000.0  # Start with $1000 paper money
        self.positions = {}
        self.trades = []
        self.orders = {}
        self.order_id_counter = 1

        # Simulated prices (we'll use random variations)
        self.price_cache = {
            "BTCUSDT": 45000.0,
            "DOGEUSDT": 0.08,
            "ETHUSDT": 3000.0,
        }

        print("✅ Paper Binance Exchange initialized with $1000")

    def get_balance(self):
        """Get current paper USDT balance"""
        print(f"Paper Binance USDT Balance: ${self.paper_balance:.2f}")
        return self.paper_balance

    def get_current_price(self, symbol):
        """Get simulated current price for a symbol"""
        try:
            # Get base price
            base_price = self.price_cache.get(symbol, 1.0)

            # Add some random variation (+/- 2%)
            variation = random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + variation)

            # Update cache with new price
            self.price_cache[symbol] = current_price

            return current_price
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return 1.0

    def _get_symbol_precision(self, symbol):
        """Get price and quantity precision for a symbol (simulated)"""
        # Return reasonable precision values for common symbols
        precision_map = {
            "BTCUSDT": (2, 6),  # price precision, quantity precision
            "ETHUSDT": (2, 5),
            "DOGEUSDT": (6, 0),
        }
        return precision_map.get(symbol, (2, 2))

    def place_limit_order(self, symbol, side, quantity, price):
        """Place a simulated limit order"""
        try:
            order_id = f"paper_{self.order_id_counter}"
            self.order_id_counter += 1

            # Calculate order value
            order_value = quantity * price

            # Check if we have enough balance for buy orders
            if side.upper() == "BUY" and order_value > self.paper_balance:
                print(
                    f"❌ Insufficient paper balance for order: ${order_value:.2f} needed, ${self.paper_balance:.2f} available"
                )
                return None

            # Create simulated order
            order = {
                "orderId": order_id,
                "symbol": symbol,
                "side": side.upper(),
                "type": "LIMIT",
                "quantity": quantity,
                "price": price,
                "status": "NEW",
                "time": int(time.time() * 1000),
                "created_at": datetime.now().isoformat(),
            }

            self.orders[order_id] = order

            # Simulate immediate fill for simplicity
            self._simulate_fill(order_id)

            print(f"✅ Paper order placed: {side} {quantity} {symbol} at ${price}")
            return order

        except Exception as e:
            print(f"❌ Error placing paper order: {e}")
            return None

    def _simulate_fill(self, order_id):
        """Simulate order fill"""
        try:
            order = self.orders.get(order_id)
            if not order:
                return

            symbol = order["symbol"]
            side = order["side"]
            quantity = float(order["quantity"])
            price = float(order["price"])

            # Update order status
            order["status"] = "FILLED"

            # Update balance and positions
            if side == "BUY":
                # Deduct USDT balance
                cost = quantity * price
                self.paper_balance -= cost

                # Add to position
                if symbol not in self.positions:
                    self.positions[symbol] = 0
                self.positions[symbol] += quantity

                print(
                    f"📈 Paper BUY filled: {quantity} {symbol} at ${price} (Cost: ${cost:.2f})"
                )

            elif side == "SELL":
                # Add USDT balance
                revenue = quantity * price
                self.paper_balance += revenue

                # Remove from position
                if symbol in self.positions:
                    self.positions[symbol] -= quantity
                    if self.positions[symbol] <= 0:
                        del self.positions[symbol]

                print(
                    f"📉 Paper SELL filled: {quantity} {symbol} at ${price} (Revenue: ${revenue:.2f})"
                )

            # Record trade
            trade = {
                "id": order_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "profit": 0,  # Could calculate profit here
            }
            self.trades.append(trade)

        except Exception as e:
            print(f"❌ Error simulating fill: {e}")

    def place_market_order(self, symbol, side, quantity):
        """Place a simulated market order"""
        try:
            # Get current price
            current_price = self.get_current_price(symbol)

            # Place as limit order at current price
            return self.place_limit_order(symbol, side, quantity, current_price)

        except Exception as e:
            print(f"❌ Error placing paper market order: {e}")
            return None

    def get_order_status(self, symbol, order_id):
        """Get status of a paper order"""
        order = self.orders.get(order_id)
        if order:
            return order["status"]
        return "NOT_FOUND"

    def cancel_order(self, symbol, order_id):
        """Cancel a paper order"""
        if order_id in self.orders:
            self.orders[order_id]["status"] = "CANCELED"
            print(f"❌ Paper order {order_id} canceled")
            return True
        return False

    def get_positions(self):
        """Get current paper positions"""
        return self.positions.copy()

    def get_trades(self):
        """Get all paper trades"""
        return self.trades.copy()

    def reset_balance(self, new_balance=1000.0):
        """Reset paper balance for testing"""
        self.paper_balance = new_balance
        self.positions = {}
        self.trades = []
        self.orders = {}
        print(f"💰 Paper balance reset to ${new_balance}")

    def get_account_info(self):
        """Get simulated account information"""
        return {
            "balances": [
                {"asset": "USDT", "free": str(self.paper_balance), "locked": "0.0"}
            ],
            "positions": self.positions,
            "total_trades": len(self.trades),
        }
