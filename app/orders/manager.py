import time
import random
from flask import current_app
from ..models import Order, Trade, AuditLog
from .. import db
from ..exchange_adapter.kite_adapter import exchange_adapter


def _get_realistic_mock_price(symbol: str) -> float:
    """Get realistic mock price for Indian stocks in paper trading."""
    # Indian stock symbols with realistic price ranges
    DEMO_STOCKS = {
        "RELIANCE": {"price_range": (2200, 2800), "volatility": 0.02},
        "TCS": {"price_range": (3200, 4000), "volatility": 0.015},
        "HDFCBANK": {"price_range": (1400, 1700), "volatility": 0.02},
        "INFY": {"price_range": (1300, 1600), "volatility": 0.018},
        "ICICIBANK": {"price_range": (900, 1100), "volatility": 0.025},
        "BHARTIARTL": {"price_range": (800, 1000), "volatility": 0.02},
        "ITC": {"price_range": (400, 500), "volatility": 0.015},
        "SBIN": {"price_range": (500, 650), "volatility": 0.03},
        "LT": {"price_range": (2800, 3500), "volatility": 0.02},
        "WIPRO": {"price_range": (400, 550), "volatility": 0.02},
        "MARUTI": {"price_range": (9000, 11000), "volatility": 0.025},
        "KOTAKBANK": {"price_range": (1600, 2000), "volatility": 0.02},
        "HCLTECH": {"price_range": (1100, 1400), "volatility": 0.02},
        "ASIANPAINT": {"price_range": (3000, 3800), "volatility": 0.018},
        "SUNPHARMA": {"price_range": (900, 1200), "volatility": 0.02},
    }

    import hashlib

    if symbol in DEMO_STOCKS:
        stock_info = DEMO_STOCKS[symbol]
        price_range = stock_info["price_range"]
        volatility = stock_info["volatility"]

        # Generate consistent price based on symbol with variation
        seed = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        base_price = random.uniform(*price_range)

        # Add realistic variation
        variation = random.uniform(-volatility, volatility)
        return base_price * (1 + variation)
    else:
        # Fallback for unknown symbols
        return random.uniform(100, 2000)


def place_order(user, order_payload):
    """
    Main function to place an order. It routes to paper or real trading
    based on the payload and user subscription.
    """
    # Create the initial order record in the database
    order = Order(
        user_id=user.id,
        symbol=order_payload["symbol"],
        quantity=order_payload["quantity"],
        order_type=order_payload["order_type"],
        side=order_payload["side"],
        price=order_payload.get("price"),
        is_paper=order_payload["is_paper"],
    )
    db.session.add(order)
    db.session.commit()

    # Log the action
    log_audit("order_placed", user, {"order_id": order.id, "payload": order_payload})

    if order_payload["is_paper"]:
        # Simulate paper trade execution
        simulate_paper_fill(order)
    else:
        # Route to real trade execution
        execute_real_order(order)

    return order


def simulate_paper_fill(order):
    """
    Simulates the filling of a paper trade order with latency and slippage.
    """
    current_app.logger.info(f"Simulating paper fill for Order ID: {order.id}")

    # Simulate network latency
    time.sleep(random.uniform(0.1, 0.5))

    # Get realistic mock price for the symbol
    mock_ltp = _get_realistic_mock_price(order.symbol)

    # Simulate slippage
    slippage = mock_ltp * random.uniform(-0.001, 0.001)  # +/- 0.1% slippage
    fill_price = mock_ltp + slippage

    # Simulate partial or full fill
    filled_quantity = int(order.quantity * random.uniform(0.8, 1.0))  # 80-100% fill

    # Create a trade record
    trade = Trade(
        order_id=order.id,
        user_id=order.user_id,
        symbol=order.symbol,
        quantity=filled_quantity,
        price=fill_price,
        side=order.side,
        fees=filled_quantity * fill_price * 0.0005,  # Mock 0.05% fee
    )

    # Update order status
    order.status = "filled" if filled_quantity == order.quantity else "partial"
    order.filled_price = fill_price
    order.filled_quantity = filled_quantity

    db.session.add(trade)
    db.session.commit()
    current_app.logger.info(f"Paper Order {order.id} filled. Trade ID: {trade.id}")
    log_audit(
        "paper_trade_filled", order.user, {"order_id": order.id, "trade_id": trade.id}
    )


def execute_real_order(order):
    """
    Sends an order to the real exchange via the adapter.
    """
    current_app.logger.info(f"Executing REAL order for Order ID: {order.id}")
    try:
        order_payload = {
            "symbol": order.symbol,
            "quantity": order.quantity,
            "order_type": order.order_type,
            "side": order.side,
            "price": order.price,
        }
        exchange_order_id = exchange_adapter.place_order(order_payload)
        order.status = "sent_to_exchange"
        order.exchange_order_id = exchange_order_id
        current_app.logger.info(
            f"Real order {order.id} sent to exchange. Exchange ID: {exchange_order_id}"
        )

        # Schedule order status check (in a real implementation, you'd use a background task)
        # For now, we'll just mark it as filled after a delay
        import time

        time.sleep(1)  # Simulate processing time
        order.status = "filled"
        order.filled_quantity = order.quantity
        order.filled_price = order.price or 100.0  # Mock fill price

    except Exception as e:
        order.status = "failed"
        order.error_message = str(e)
        current_app.logger.exception(f"Real order {order.id} failed: {e}")

    db.session.commit()


def log_audit(action, user, details):
    """Helper to create an audit log entry."""
    log = AuditLog(action=action, user_id=user.id, details=details)
    db.session.add(log)
    db.session.commit()
