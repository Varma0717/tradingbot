"""
Demo Portfolio Generator for Paper Trading
Generates realistic demo trades and portfolio data for new paper trading users.
"""

import random
from datetime import datetime, timedelta
from flask import current_app
from ..models import Order, Trade, User, db
from ..orders.manager import log_audit


class DemoPortfolioGenerator:
    """Generates demo portfolio data for paper trading users."""

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

    STARTING_BALANCE = 100000.0  # ₹1 Lakh starting demo balance

    @classmethod
    def generate_demo_portfolio(cls, user_id: int, num_trades: int = 15) -> dict:
        """
        Generate a realistic demo portfolio for a paper trading user.

        Args:
            user_id: The user ID to generate demo data for
            num_trades: Number of demo trades to generate (default: 15)

        Returns:
            Dict with portfolio summary
        """
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Check if user already has demo data
            existing_orders = Order.query.filter_by(
                user_id=user_id, is_paper=True
            ).count()
            if existing_orders > 5:  # Already has substantial demo data
                current_app.logger.info(
                    f"User {user_id} already has demo portfolio data"
                )
                return {"status": "exists", "message": "Demo portfolio already exists"}

            current_app.logger.info(f"Generating demo portfolio for user {user_id}")

            # Generate demo trades over the last 30 days
            demo_summary = cls._create_demo_trades(user_id, num_trades)

            # Log the demo portfolio creation
            log_audit(
                "demo_portfolio_created",
                user,
                {
                    "trades_generated": num_trades,
                    "portfolio_value": demo_summary.get("total_value", 0),
                    "starting_balance": cls.STARTING_BALANCE,
                },
            )

            return {
                "status": "created",
                "message": "Demo portfolio generated successfully",
                "summary": demo_summary,
            }

        except Exception as e:
            current_app.logger.error(
                f"Error generating demo portfolio for user {user_id}: {str(e)}"
            )
            raise

    @classmethod
    def _create_demo_trades(cls, user_id: int, num_trades: int) -> dict:
        """Create realistic demo trades and calculate portfolio summary."""

        total_invested = 0
        total_current_value = 0
        positions = {}

        # Generate trades over the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        for i in range(num_trades):
            # Select random stock
            symbol = random.choice(list(cls.DEMO_STOCKS.keys()))
            stock_info = cls.DEMO_STOCKS[symbol]

            # Generate random trade date within the last 30 days
            trade_date = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )

            # Determine trade type (70% buy, 30% sell for realistic portfolio)
            is_buy = random.random() < 0.7
            side = "buy" if is_buy else "sell"

            # Calculate realistic quantity based on investment amount
            investment_amount = random.uniform(5000, 15000)  # ₹5k to ₹15k per trade
            entry_price = random.uniform(*stock_info["price_range"])
            quantity = max(1, int(investment_amount / entry_price))

            # Calculate current price with some volatility
            volatility = stock_info["volatility"]
            days_elapsed = (datetime.now() - trade_date).days
            price_change = random.uniform(
                -volatility * days_elapsed, volatility * days_elapsed
            )
            current_price = entry_price * (1 + price_change)

            # Create the order
            order = Order(
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                order_type="market",
                side=side,
                status="filled",
                price=entry_price,
                filled_price=entry_price,
                filled_quantity=quantity,
                is_paper=True,
                created_at=trade_date,
                updated_at=trade_date,
            )

            db.session.add(order)
            db.session.flush()  # Get the order ID

            # Create corresponding trade
            fees = quantity * entry_price * 0.0005  # 0.05% fees
            trade = Trade(
                order_id=order.id,
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                price=entry_price,
                side=side,
                fees=fees,
                created_at=trade_date,
                updated_at=trade_date,
            )

            db.session.add(trade)

            # Update position tracking
            if symbol not in positions:
                positions[symbol] = {
                    "quantity": 0,
                    "total_cost": 0,
                    "current_price": current_price,
                }

            if side == "buy":
                positions[symbol]["quantity"] += quantity
                positions[symbol]["total_cost"] += quantity * entry_price
                total_invested += quantity * entry_price
            else:
                # Sell trade - reduce position
                if positions[symbol]["quantity"] >= quantity:
                    avg_cost = (
                        positions[symbol]["total_cost"] / positions[symbol]["quantity"]
                        if positions[symbol]["quantity"] > 0
                        else entry_price
                    )
                    positions[symbol]["quantity"] -= quantity
                    positions[symbol]["total_cost"] -= quantity * avg_cost
                    total_invested -= quantity * avg_cost

        # Commit all trades
        db.session.commit()

        # Calculate current portfolio value
        for symbol, position in positions.items():
            if position["quantity"] > 0:
                current_value = position["quantity"] * position["current_price"]
                total_current_value += current_value

        # Calculate cash remaining
        cash_remaining = cls.STARTING_BALANCE - total_invested
        total_portfolio_value = total_current_value + cash_remaining

        # Calculate P&L
        total_pnl = total_current_value - (total_invested if total_invested > 0 else 0)
        pnl_percentage = (total_pnl / total_invested * 100) if total_invested > 0 else 0

        return {
            "total_trades": num_trades,
            "total_invested": total_invested,
            "current_value": total_current_value,
            "cash_remaining": cash_remaining,
            "total_portfolio_value": total_portfolio_value,
            "total_pnl": total_pnl,
            "pnl_percentage": pnl_percentage,
            "active_positions": len(
                [p for p in positions.values() if p["quantity"] > 0]
            ),
            "positions": positions,
        }

    @classmethod
    def get_demo_portfolio_status(cls, user_id: int) -> dict:
        """Check if user has demo portfolio data."""
        order_count = Order.query.filter_by(user_id=user_id, is_paper=True).count()
        trade_count = Trade.query.filter_by(user_id=user_id).count()

        return {
            "has_demo_data": order_count > 0,
            "order_count": order_count,
            "trade_count": trade_count,
        }

    @classmethod
    def reset_demo_portfolio(cls, user_id: int):
        """Reset/clear existing demo portfolio data."""
        try:
            # Delete existing trades first (due to foreign key constraints)
            Trade.query.filter_by(user_id=user_id).delete()

            # Delete existing paper orders
            Order.query.filter_by(user_id=user_id, is_paper=True).delete()

            db.session.commit()
            current_app.logger.info(f"Demo portfolio reset for user {user_id}")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error resetting demo portfolio for user {user_id}: {str(e)}"
            )
            raise
