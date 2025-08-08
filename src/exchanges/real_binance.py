import os
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class RealBinanceExchange:
    def __init__(self):
        """Initialize real Binance exchange with API credentials"""
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET_KEY")

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Binance API credentials not found in environment variables"
            )

        try:
            self.client = Client(self.api_key, self.api_secret)
            # Test connection
            self.client.get_account()
            print("✅ Binance API connection established successfully")
        except Exception as e:
            print(f"❌ Failed to connect to Binance API: {e}")
            raise

    def get_balance(self):
        """Get current USDT balance from Binance"""
        try:
            account = self.client.get_account()
            for balance in account["balances"]:
                if balance["asset"] == "USDT":
                    free_balance = float(balance["free"])
                    print(f"Real Binance USDT Balance: ${free_balance:.2f}")
                    return free_balance
            return 0.0
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0.0

    def get_current_price(self, symbol):
        """Get current price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker["price"])
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return 0.0

    def _get_symbol_precision(self, symbol):
        """Get price and quantity precision for a symbol"""
        try:
            symbol_info = self.client.get_symbol_info(symbol)

            price_precision = 2  # Default
            quantity_precision = 2  # Default

            for filter_info in symbol_info["filters"]:
                if filter_info["filterType"] == "PRICE_FILTER":
                    tick_size = float(filter_info["tickSize"])
                    # Calculate precision from tick size more accurately
                    tick_str = f"{tick_size:.20f}".rstrip("0")
                    if "." in tick_str:
                        price_precision = len(tick_str.split(".")[1])
                    else:
                        price_precision = 0

                elif filter_info["filterType"] == "LOT_SIZE":
                    step_size = float(filter_info["stepSize"])
                    # Calculate precision from step size more accurately
                    step_str = f"{step_size:.20f}".rstrip("0")
                    if "." in step_str:
                        quantity_precision = len(step_str.split(".")[1])
                    else:
                        quantity_precision = 0

            print(
                f"Symbol {symbol} precision: price={price_precision}, quantity={quantity_precision}"
            )
            return price_precision, quantity_precision

        except Exception as e:
            print(f"Error getting precision for {symbol}: {e}")
            return 2, 2  # Default precision

    def place_limit_order(self, symbol, side, quantity, price):
        """Place a limit order on Binance"""
        try:
            # Get symbol precision
            price_precision, quantity_precision = self._get_symbol_precision(symbol)

            # Format price and quantity with correct precision
            formatted_price = f"{price:.{price_precision}f}"
            formatted_quantity = f"{quantity:.{quantity_precision}f}"

            print(
                f"Placing {side} order: {formatted_quantity} {symbol} @ ${formatted_price}"
            )

            # Place the order
            order = self.client.order_limit(
                symbol=symbol,
                side=side,
                quantity=formatted_quantity,
                price=formatted_price,
            )

            print(f"✅ Order placed successfully: {order['orderId']}")
            return {
                "success": True,
                "order_id": order["orderId"],
                "symbol": symbol,
                "side": side,
                "quantity": formatted_quantity,
                "price": formatted_price,
                "status": order["status"],
            }

        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.message}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg, "code": e.code}
        except Exception as e:
            error_msg = f"Order placement error: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def get_open_orders(self, symbol):
        """Get open orders for a symbol"""
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            return orders
        except Exception as e:
            print(f"Error getting open orders: {e}")
            return []

    def cancel_order(self, symbol, order_id):
        """Cancel an order"""
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            print(f"✅ Order {order_id} cancelled successfully")
            return {"success": True, "result": result}
        except Exception as e:
            error_msg = f"Error cancelling order {order_id}: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def get_order_history(self, symbol, limit=10):
        """Get recent order history"""
        try:
            orders = self.client.get_all_orders(symbol=symbol, limit=limit)
            return orders
        except Exception as e:
            print(f"Error getting order history: {e}")
            return []
