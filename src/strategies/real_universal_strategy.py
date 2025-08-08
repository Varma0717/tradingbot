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
        """Place initial grid orders - start with just one buy order"""
        try:
            current_price = self.exchange.get_current_price(self.trading_pair)
            if current_price <= 0:
                print(f"❌ Invalid price for {self.trading_pair}")
                return

            print(f"📈 Current {self.trading_pair} price: ${current_price:.6f}")

            # Get current balance
            balance = self.exchange.get_balance()
            print(f"💰 Available balance: ${balance:.2f}")

            # Only place ONE initial buy order below current price
            # This is a conservative approach for small balances
            buy_price = current_price * (
                1 - self.grid_spacing
            )  # 2% below current price
            quantity = self.calculate_quantity(buy_price)

            if balance >= self.order_size_usd:
                print(
                    f"🎯 Placing initial buy order: {quantity:.2f} {self.trading_pair} @ ${buy_price:.6f}"
                )

                result = self.exchange.place_limit_order(
                    symbol=self.trading_pair,
                    side="BUY",
                    quantity=quantity,
                    price=buy_price,
                )

                if result["success"]:
                    self.open_orders[result["order_id"]] = {
                        "side": "BUY",
                        "price": buy_price,
                        "quantity": quantity,
                        "timestamp": datetime.now(),
                    }
                    print(
                        f"✅ Initial buy order placed: {quantity:.2f} {self.trading_pair} @ ${buy_price:.6f}"
                    )
                    print(
                        f"📊 Strategy will place sell order when this buy order fills"
                    )
                else:
                    print(
                        f"❌ Failed to place initial order: {result.get('error', 'Unknown error')}"
                    )
            else:
                print(
                    f"⚠️ Insufficient balance for any orders: ${balance:.2f} < ${self.order_size_usd}"
                )

        except Exception as e:
            print(f"❌ Error placing initial order: {e}")

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

                        # Get actual filled quantity from Binance
                        try:
                            order_details = self.exchange.client.get_order(
                                symbol=self.trading_pair, orderId=int(order_id)
                            )
                            actual_filled_qty = float(
                                order_details.get(
                                    "executedQty", filled_order["quantity"]
                                )
                            )
                            filled_order["quantity"] = actual_filled_qty
                            print(
                                f"🎯 Order filled: {filled_order['side']} {actual_filled_qty:.2f} @ ${filled_order['price']:.6f}"
                            )
                        except Exception as e:
                            print(f"⚠️ Could not get actual filled quantity: {e}")
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

                # Use the exact quantity that was bought, not recalculated
                quantity = filled_order["quantity"]

                # Get actual DOGE balance to verify we have enough to sell
                account = self.exchange.client.get_account()
                doge_balance = 0.0
                for balance in account["balances"]:
                    if balance["asset"] == "DOGE":
                        doge_balance = float(balance["free"])
                        break

                print(f"💰 DOGE balance available: {doge_balance:.2f}")

                if doge_balance < quantity:
                    print(
                        f"⚠️ Insufficient DOGE balance: {doge_balance:.2f} < {quantity:.2f}"
                    )
                    return

            else:
                # If sell order filled, place buy order below current price
                new_price = current_price * (1 - self.grid_spacing)
                new_side = "BUY"

                # Check USDT balance for buy orders
                balance = self.exchange.get_balance()
                if balance < self.order_size_usd:
                    print(f"⚠️ Insufficient balance for replacement buy order")
                    return

                # Calculate quantity for buy order based on USD amount
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
            else:
                print(
                    f"⚠️ Failed to place replacement order: {result.get('error', 'Unknown error')}"
                )
                print(f"💡 Strategy will continue monitoring existing orders")

        except Exception as e:
            print(f"❌ Error placing replacement order: {e}")
            print(f"💡 Strategy will continue monitoring existing orders")

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

    def get_trades(self):
        """Get completed trades from Binance API"""
        try:
            # Get recent trades from Binance
            trades = self.exchange.get_account_trades(self.trading_pair, limit=50)

            # Convert to our internal format
            formatted_trades = []
            for trade in trades:
                try:
                    formatted_trades.append(
                        {
                            "id": trade.get("id"),
                            "symbol": trade.get("symbol"),
                            "side": "buy" if trade.get("isBuyer") else "sell",
                            "amount": float(trade.get("qty", 0)),
                            "price": float(trade.get("price", 0)),
                            "cost": float(trade.get("quoteQty", 0)),
                            "fee": float(trade.get("commission", 0)),
                            "fee_currency": trade.get("commissionAsset"),
                            "timestamp": datetime.fromtimestamp(
                                trade.get("time", 0) / 1000
                            ).isoformat(),
                            "profit": self._calculate_trade_profit(trade),
                        }
                    )
                except Exception as e:
                    print(f"❌ Error formatting trade: {e}")
                    continue

            return formatted_trades
        except Exception as e:
            print(f"❌ Error getting trades: {e}")
            return []

    def _calculate_trade_profit(self, trade):
        """Calculate profit for a trade (simplified calculation)"""
        try:
            # This is a simplified calculation - in reality you'd need to track
            # the corresponding buy/sell pairs to calculate actual profit
            return 0.0  # TODO: Implement proper profit calculation
        except Exception as e:
            return 0.0

    def get_analytics(self):
        """Get trading analytics including win rate, total profit, etc."""
        try:
            trades = self.get_trades()
            if not trades:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "total_profit": 0.0,
                    "total_volume": 0.0,
                    "average_profit_per_trade": 0.0,
                }

            total_trades = len(trades)
            total_profit = sum(trade.get("profit", 0) for trade in trades)
            total_volume = sum(trade.get("cost", 0) for trade in trades)
            winning_trades = len([t for t in trades if t.get("profit", 0) > 0])
            losing_trades = len([t for t in trades if t.get("profit", 0) < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "total_profit": round(total_profit, 4),
                "total_volume": round(total_volume, 2),
                "average_profit_per_trade": (
                    round(total_profit / total_trades, 4) if total_trades > 0 else 0
                ),
            }
        except Exception as e:
            print(f"❌ Error calculating analytics: {e}")
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "total_volume": 0.0,
                "average_profit_per_trade": 0.0,
            }

    def get_active_orders(self):
        """Get all currently active orders from Binance"""
        try:
            active_orders = []

            # Get all open orders from Binance for all symbols
            all_open_orders = self.exchange.client.get_open_orders()

            for order in all_open_orders:
                # Convert Binance order format to our format
                active_orders.append(
                    {
                        "id": str(order["orderId"]),
                        "symbol": order["symbol"],
                        "side": order["side"],
                        "amount": float(order["origQty"]),
                        "price": float(order["price"]),
                        "total": float(order["origQty"]) * float(order["price"]),
                        "type": order["type"].lower(),
                        "status": "open",
                        "created": datetime.fromtimestamp(
                            order["time"] / 1000
                        ).isoformat(),
                    }
                )

            print(f"📊 Found {len(active_orders)} active orders on Binance")
            return active_orders

        except Exception as e:
            print(f"❌ Error getting active orders from Binance: {e}")
            # Fallback to internal tracking
            try:
                active_orders = []
                for order_id, order_info in self.open_orders.items():
                    active_orders.append(
                        {
                            "id": order_id,
                            "symbol": self.trading_pair,
                            "side": order_info["side"],
                            "amount": order_info["quantity"],
                            "price": order_info["price"],
                            "total": order_info["quantity"] * order_info["price"],
                            "type": "limit",
                            "status": "open",
                            "created": (
                                order_info["timestamp"].isoformat()
                                if order_info.get("timestamp")
                                else None
                            ),
                        }
                    )
                return active_orders
            except Exception as e2:
                print(f"❌ Error with fallback order tracking: {e2}")
                return []
