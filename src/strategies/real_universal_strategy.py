import time
import threading
from datetime import datetime
from ..exchanges.real_binance import RealBinanceExchange


class RealUniversalGridDCAStrategy:
    def __init__(self):
        """Initialize real grid DCA strategy"""
        self.exchange = RealBinanceExchange()
        self.is_running = False
        self.trading_pair = "DOGEUSDT"
        self.grid_levels = 5
        self.grid_spacing = 0.02  # 2% spacing between grid levels
        self.order_size_usd = 2.0  # $2 per order
        self.open_orders = {}
        self.thread = None

        print("✅ Real Universal Grid DCA Strategy initialized")

    def set_trading_pair(self, pair):
        """Set the trading pair for this strategy"""
        self.trading_pair = pair
        print(f"📊 Strategy trading pair set to: {pair}")

        # Adjust order size based on pair
        if "BTC" in pair:
            self.order_size_usd = 10.0  # Larger orders for BTC
        else:
            self.order_size_usd = 2.0  # Smaller orders for altcoins

    def calculate_grid_levels(self, current_price):
        """Calculate grid buy/sell levels around current price"""
        levels = []

        # Generate buy levels below current price
        for i in range(1, self.grid_levels + 1):
            buy_price = current_price * (1 - self.grid_spacing * i)
            levels.append({"side": "BUY", "price": buy_price})

        # Generate sell levels above current price
        for i in range(1, self.grid_levels + 1):
            sell_price = current_price * (1 + self.grid_spacing * i)
            levels.append({"side": "SELL", "price": sell_price})

        return levels

    def calculate_quantity(self, price):
        """Calculate quantity based on order size in USD"""
        return self.order_size_usd / price

    def place_grid_orders(self):
        """Place initial grid orders"""
        try:
            current_price = self.exchange.get_current_price(self.trading_pair)
            if current_price <= 0:
                print(f"❌ Invalid price for {self.trading_pair}")
                return

            print(f"📈 Current {self.trading_pair} price: ${current_price:.6f}")

            # Calculate grid levels
            levels = self.calculate_grid_levels(current_price)

            # Place orders for each level
            for level in levels:
                if not self.is_running:
                    break

                price = level["price"]
                side = level["side"]
                quantity = self.calculate_quantity(price)

                # Only place buy orders if we have sufficient balance
                if side == "BUY":
                    balance = self.exchange.get_balance()
                    if balance < self.order_size_usd:
                        print(
                            f"⚠️ Insufficient balance for buy order: ${balance:.2f} < ${self.order_size_usd}"
                        )
                        continue

                # Place the order
                result = self.exchange.place_limit_order(
                    symbol=self.trading_pair, side=side, quantity=quantity, price=price
                )

                if result["success"]:
                    self.open_orders[result["order_id"]] = {
                        "side": side,
                        "price": price,
                        "quantity": quantity,
                        "timestamp": datetime.now(),
                    }
                    print(
                        f"✅ Grid order placed: {side} {quantity:.2f} {self.trading_pair} @ ${price:.6f}"
                    )
                else:
                    print(
                        f"❌ Failed to place grid order: {result.get('error', 'Unknown error')}"
                    )

                # Small delay between orders
                time.sleep(1)

        except Exception as e:
            print(f"❌ Error placing grid orders: {e}")

    def monitor_and_replace_orders(self):
        """Monitor filled orders and replace them"""
        while self.is_running:
            try:
                # Check open orders
                for order_id in list(self.open_orders.keys()):
                    if not self.is_running:
                        break

                    # Check if order is still open
                    open_orders = self.exchange.get_open_orders(self.trading_pair)
                    open_order_ids = [str(order["orderId"]) for order in open_orders]

                    if str(order_id) not in open_order_ids:
                        # Order was filled, remove from tracking
                        filled_order = self.open_orders.pop(order_id)
                        print(
                            f"🎯 Order filled: {filled_order['side']} @ ${filled_order['price']:.6f}"
                        )

                        # Place replacement order on opposite side
                        self.place_replacement_order(filled_order)

                # Check every 30 seconds
                time.sleep(30)

            except Exception as e:
                print(f"❌ Error monitoring orders: {e}")
                time.sleep(60)  # Wait longer on error

    def place_replacement_order(self, filled_order):
        """Place a replacement order after one is filled"""
        try:
            current_price = self.exchange.get_current_price(self.trading_pair)

            if filled_order["side"] == "BUY":
                # If buy order filled, place sell order above current price
                new_price = current_price * (1 + self.grid_spacing)
                new_side = "SELL"
            else:
                # If sell order filled, place buy order below current price
                new_price = current_price * (1 - self.grid_spacing)
                new_side = "BUY"

                # Check balance for buy orders
                balance = self.exchange.get_balance()
                if balance < self.order_size_usd:
                    print(f"⚠️ Insufficient balance for replacement buy order")
                    return

            quantity = self.calculate_quantity(new_price)

            # Place replacement order
            result = self.exchange.place_limit_order(
                symbol=self.trading_pair,
                side=new_side,
                quantity=quantity,
                price=new_price,
            )

            if result["success"]:
                self.open_orders[result["order_id"]] = {
                    "side": new_side,
                    "price": new_price,
                    "quantity": quantity,
                    "timestamp": datetime.now(),
                }
                print(
                    f"🔄 Replacement order: {new_side} {quantity:.2f} @ ${new_price:.6f}"
                )

        except Exception as e:
            print(f"❌ Error placing replacement order: {e}")

    def start(self):
        """Start the strategy"""
        if self.is_running:
            print("⚠️ Strategy is already running")
            return

        self.is_running = True
        print(f"🚀 Starting Real Grid DCA Strategy for {self.trading_pair}")

        # Place initial grid orders
        self.place_grid_orders()

        # Start monitoring thread
        self.thread = threading.Thread(target=self.monitor_and_replace_orders)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the strategy"""
        if not self.is_running:
            print("⚠️ Strategy is not running")
            return

        self.is_running = False
        print(f"🛑 Stopping Real Grid DCA Strategy for {self.trading_pair}")

        # Cancel all open orders
        try:
            for order_id in list(self.open_orders.keys()):
                result = self.exchange.cancel_order(self.trading_pair, order_id)
                if result["success"]:
                    print(f"✅ Cancelled order: {order_id}")
                else:
                    print(
                        f"❌ Failed to cancel order {order_id}: {result.get('error')}"
                    )

            self.open_orders.clear()

        except Exception as e:
            print(f"❌ Error cancelling orders: {e}")

        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

    def get_status(self):
        """Get strategy status"""
        return {
            "is_running": self.is_running,
            "trading_pair": self.trading_pair,
            "open_orders_count": len(self.open_orders),
            "grid_levels": self.grid_levels,
            "order_size_usd": self.order_size_usd,
        }
