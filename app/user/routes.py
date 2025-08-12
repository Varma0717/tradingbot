from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from ..models import Order, Trade, Strategy, ExchangeConnection
from ..orders.manager import place_order
from .. import db, limiter
import json
import logging

logger = logging.getLogger(__name__)

user = Blueprint("user", __name__)


@user.route("/")
def index():
    """Redirect user root to automation dashboard."""
    return redirect(url_for("user.automation_dashboard"))


@user.before_request
@login_required
def before_request():
    """Protect all user routes and inject trading mode context."""
    from flask import g
    from ..models import UserPreferences

    # Get user preferences for trading mode
    preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreferences(
            user_id=current_user.id, trading_mode="paper", theme="dark"
        )
        db.session.add(preferences)
        db.session.commit()

    # Make trading mode available in all templates
    g.trading_mode = preferences.trading_mode
    g.user_preferences = preferences


@user.route("/dashboard")
def dashboard():
    """Enhanced dashboard with proper portfolio data and user profile."""
    from ..utils.portfolio_manager import PortfolioManager
    from ..utils.subscription_enforcer import get_plan_summary

    try:
        # Get comprehensive portfolio data
        portfolio_manager = PortfolioManager(current_user.id)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()

        # Get plan summary for UI controls
        plan_summary = get_plan_summary(current_user.id)

        return render_template(
            "user/unified_dashboard.html",
            title="Dashboard",
            portfolio=portfolio_data,
            plan_summary=plan_summary,
            # Legacy compatibility
            pnl={
                "daily": portfolio_data["performance"].get("daily_pnl", 0),
                "monthly": portfolio_data["performance"].get("monthly_pnl", 0),
                "total": portfolio_data["summary"].get("total_pnl", 0),
            },
            positions=portfolio_data["positions"][:5],  # Top 5 positions for dashboard
            recent_trades=portfolio_data["recent_trades"][:5],
        )

    except Exception as e:
        logger.error(f"Dashboard error for user {current_user.id}: {e}")
        # Fallback to basic dashboard
        return render_template(
            "user/dashboard.html",
            title="Dashboard",
            pnl={"daily": 0, "monthly": 0, "total": 0},
            positions=[],
            recent_trades=[],
            error="Unable to load portfolio data",
            balance=0,
            trades=[],
            recent_orders=[],
            active_strategies=Strategy.query.filter_by(
                user_id=current_user.id, is_active=True
            ).all(),
        )


def _calculate_dashboard_data(user_id, is_paper: bool, exchange_type: str):
    """Aggregate P&L, balance, positions, trades & recent orders for dashboard.

    Args:
        user_id: Current user id
        is_paper: True for paper trading filter
        exchange_type: 'stocks' or 'crypto'
    Returns:
        dict with keys pnl (dict), balance (float), positions (list), trades (list), recent_orders(list)
    """
    # Filter orders & trades
    orders_query = (
        Order.query.filter_by(user_id=user_id, exchange_type=exchange_type)
        .filter(Order.is_paper.is_(is_paper))
        .order_by(Order.created_at.desc())
    )
    recent_orders = orders_query.limit(10).all()

    trades_query = (
        Trade.query.join(Order, Trade.order_id == Order.id)
        .filter(
            Trade.user_id == user_id,
            Trade.exchange_type == exchange_type,
            Order.is_paper.is_(is_paper),
        )
        .order_by(Trade.timestamp.desc())
    )
    last_trades = trades_query.limit(25).all()

    # P&L (realized) based on trades (sell positive, buy negative)
    total_pnl = 0.0
    for t in last_trades:  # limited window; for full use a separate aggregate
        sign = 1 if t.side == "sell" else -1
        total_pnl += t.price * t.quantity * sign

    pnl_summary = {
        "daily": round(total_pnl * 0.1, 2),  # Placeholder logic
        "monthly": round(total_pnl * 0.3, 2),  # Placeholder logic
        "total": round(total_pnl, 2),
    }

    # Derive open positions from cumulative trade quantities
    position_map = {}
    for t in reversed(last_trades):  # chronological
        key = t.symbol
        if key not in position_map:
            position_map[key] = {
                "symbol": t.symbol,
                "qty": 0.0,
                "avg_price": 0.0,
                "ltp": t.price,  # use last trade price as proxy
                "pnl": 0.0,
            }
        pos = position_map[key]
        if t.side == "buy":
            # Adjust average price
            new_qty = pos["qty"] + t.quantity
            if new_qty > 0:
                pos["avg_price"] = (
                    (pos["avg_price"] * pos["qty"]) + (t.price * t.quantity)
                ) / new_qty
            pos["qty"] = new_qty
        else:  # sell
            pos["qty"] -= t.quantity
        pos["ltp"] = t.price

    # Compute unrealized P&L for positive qty positions
    positions = []
    for p in position_map.values():
        if abs(p["qty"]) > 1e-9:
            p["pnl"] = round((p["ltp"] - p["avg_price"]) * p["qty"], 2)
            # Convert floats cleanly
            p["qty"] = float(p["qty"])
            p["avg_price"] = round(float(p["avg_price"]), 2)
            p["ltp"] = round(float(p["ltp"]), 2)
            positions.append(p)

    # Simplistic balance: base + realized P&L
    starting_capital = 500000 if exchange_type == "stocks" else 5.0  # 5 BTC eg
    balance = starting_capital + pnl_summary["total"]

    # Serialize trades & orders
    def serialize_trade(t: Trade):
        return {
            "id": t.id,
            "symbol": t.symbol,
            "quantity": t.quantity,
            "price": t.price,
            "side": t.side,
            "timestamp": t.timestamp.isoformat(),
        }

    def serialize_order(o: Order):
        return {
            "id": o.id,
            "symbol": o.symbol,
            "quantity": o.quantity,
            "side": o.side,
            "status": o.status,
            "price": o.price,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }

    return {
        "pnl": pnl_summary,
        "balance": balance,
        "positions": positions,
        "trades": [serialize_trade(t) for t in last_trades],
        "recent_orders": [serialize_order(o) for o in recent_orders],
    }


@user.route("/api/dashboard")
@login_required
def api_dashboard():
    """Return JSON dashboard data filtered by trading mode & market."""
    mode = request.args.get("mode", "paper").lower()
    market = request.args.get("market", "stocks").lower()
    is_paper = mode != "live"
    if market not in ("stocks", "crypto"):
        market = "stocks"
    data = _calculate_dashboard_data(current_user.id, is_paper, market)
    return jsonify({"mode": mode, "market": market, **data})


@user.route("/orders")
def orders():
    # Initial render; client will fetch filtered data via API
    return render_template("user/orders.html", title="Orders")


@user.route("/api/orders")
@login_required
def api_orders():
    """Return orders list filtered by mode & market."""
    mode = request.args.get("mode", "paper").lower()
    market = request.args.get("market", "stocks").lower()
    is_paper = mode != "live"
    if market not in ("stocks", "crypto"):
        market = "stocks"
    orders_query = (
        Order.query.filter_by(user_id=current_user.id, exchange_type=market)
        .filter(Order.is_paper.is_(is_paper))
        .order_by(Order.created_at.desc())
    )
    orders = orders_query.limit(200).all()

    def serialize(o: Order):
        return {
            "id": o.id,
            "symbol": o.symbol,
            "side": o.side,
            "quantity": o.quantity,
            "status": o.status,
            "price": o.price,
            "is_paper": o.is_paper,
            "exchange_type": o.exchange_type,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }

    return jsonify(
        {
            "mode": mode,
            "market": market,
            "orders": [serialize(o) for o in orders],
        }
    )


@user.route("/strategies")
def strategies():
    user_strategies = Strategy.query.filter_by(user_id=current_user.id).all()
    from ..strategies.top_strategies import STRATEGY_MAP

    available_strategies = list(STRATEGY_MAP.keys())
    return render_template(
        "user/strategies.html",
        title="Strategies",
        user_strategies=user_strategies,
        available_strategies=available_strategies,
    )


@user.route("/trade", methods=["POST"])
@limiter.limit("30/minute")  # Limit to 30 trades per minute
def execute_trade():
    """Enhanced trade execution with subscription enforcement."""
    from ..utils.subscription_enforcer import enforce_trading_limits

    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        symbol = data.get("symbol")
        quantity = int(data.get("quantity", 0))
        order_type = data.get("order_type")
        side = data.get("side")
        price = float(data.get("price", 0)) if data.get("price") else None
        is_paper_str = data.get("trade_mode", "paper")
        is_paper = is_paper_str == "paper"

        if not symbol or not quantity or not order_type or not side:
            if request.is_json:
                return (
                    jsonify({"success": False, "message": "All fields are required"}),
                    400,
                )
            flash("All fields are required for a trade.", "danger")
            return redirect(url_for("user.dashboard"))

        order_payload = {
            "symbol": symbol.upper(),
            "quantity": quantity,
            "order_type": order_type,
            "side": side,
            "price": price,
            "is_paper": is_paper,
        }

        # Enhanced subscription and limits enforcement
        limit_check = enforce_trading_limits(order_payload)
        if limit_check:
            if request.is_json:
                return jsonify(limit_check), 403
            flash(limit_check["message"], "warning")
            if limit_check.get("upgrade_required"):
                return redirect(url_for("payments.upgrade"))
            return redirect(url_for("user.dashboard"))

        order = place_order(current_user, order_payload)

        if request.is_json:
            return jsonify(
                {
                    "success": True,
                    "message": "Order placed successfully",
                    "order_id": order.id,
                }
            )

        flash(f"Order placed successfully! Order ID: {order.id}", "success")
        return redirect(url_for("user.dashboard"))

    except Exception as e:
        if request.is_json:
            return jsonify({"success": False, "message": str(e)}), 500
        flash(f"Failed to place order: {str(e)}", "danger")
        return redirect(url_for("user.dashboard"))


@user.route("/strategy/<int:strategy_id>/toggle", methods=["POST"])
def toggle_strategy(strategy_id):
    try:
        strategy = Strategy.query.filter_by(
            id=strategy_id, user_id=current_user.id
        ).first()
        if not strategy:
            return jsonify({"success": False, "message": "Strategy not found"}), 404

        data = request.get_json()
        strategy.is_active = data.get("active", False)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f'Strategy {"activated" if strategy.is_active else "deactivated"}',
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@user.route("/strategy/create", methods=["POST"])
def create_strategy():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()

        strategy_name = data.get("strategy_name")
        parameters = data.get("parameters", "{}")

        if isinstance(parameters, str):
            parameters = json.loads(parameters)

        strategy = Strategy(
            user_id=current_user.id,
            name=strategy_name,
            parameters=parameters,
            is_active=False,
        )

        db.session.add(strategy)
        db.session.commit()

        if request.is_json:
            return jsonify(
                {
                    "success": True,
                    "message": "Strategy created successfully",
                    "strategy_id": strategy.id,
                }
            )

        flash("Strategy created successfully!", "success")
        return redirect(url_for("user.strategies"))

    except Exception as e:
        if request.is_json:
            return jsonify({"success": False, "message": str(e)}), 500
        flash(f"Failed to create strategy: {str(e)}", "danger")
        return redirect(url_for("user.strategies"))


# API Endpoints for Real-time Updates
@user.route("/api/bot-status")
@login_required
def api_bot_status():
    """API endpoint for real-time bot status updates"""
    try:
        from ..automation.bot_manager import BotManager

        # Get bot instances
        stock_bot = BotManager.get_bot(current_user.id, bot_type="stock")
        crypto_bot = BotManager.get_bot(current_user.id, bot_type="crypto")

        # Get current statuses
        stock_status = stock_bot.get_status() if stock_bot else {"is_running": False}
        crypto_status = (
            crypto_bot.get_trading_status() if crypto_bot else {"is_running": False}
        )

        # Format response
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "stock_bot": {
                "is_running": stock_status.get("is_running", False),
                "total_trades": stock_status.get("total_trades", 0),
                "daily_pnl": round(stock_status.get("daily_pnl", 0), 2),
                "win_rate": round(stock_status.get("win_rate", 0), 1),
                "active_positions": len(stock_status.get("positions", {})),
                "strategies_active": stock_status.get("strategies_active", 0),
                "start_time": stock_status.get("start_time", ""),
                "uptime": stock_status.get("uptime", "00:00:00"),
            },
            "crypto_bot": {
                "is_running": crypto_status.get("is_running", False),
                "total_trades": crypto_status.get("total_trades", 0),
                "daily_pnl": round(crypto_status.get("daily_pnl", 0), 6),
                "win_rate": round(crypto_status.get("win_rate", 0), 1),
                "active_positions": len(crypto_status.get("active_strategies", {})),
                "strategies_active": len(
                    [
                        s
                        for s in crypto_status.get("active_strategies", {}).values()
                        if s.get("running", False)
                    ]
                ),
                "start_time": crypto_status.get("start_time", ""),
                "uptime": crypto_status.get("uptime", "00:00:00"),
            },
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "stock_bot": {"is_running": False},
                    "crypto_bot": {"is_running": False},
                }
            ),
            500,
        )


@user.route("/api/portfolio-summary")
@login_required
def api_portfolio_summary():
    """API endpoint for real-time portfolio summary"""
    try:
        from ..utils.portfolio_manager import PortfolioManager

        portfolio_manager = PortfolioManager(current_user.id)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()

        # Format for API response
        summary = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "total_value": portfolio_data["summary"].get("total_value", 0),
            "daily_pnl": portfolio_data["performance"].get("daily_pnl", 0),
            "daily_pnl_percent": portfolio_data["performance"].get(
                "daily_pnl_percent", 0
            ),
            "total_pnl": portfolio_data["summary"].get("total_pnl", 0),
            "unrealized_pnl": portfolio_data["summary"].get(
                "total_pnl", 0
            ),  # Use total_pnl as fallback
            "realized_pnl": 0,  # Default to 0 since not calculated separately
            "available_balance": portfolio_data["summary"].get("cash_balance", 0),
            "trading_mode": portfolio_data["user_info"]["trading_mode"],
            "positions_count": len(portfolio_data["positions"]),
            "active_orders": portfolio_data["summary"].get("active_orders", 0),
            "allocations": {
                "stocks": portfolio_data.get("allocations", {})
                .get("stocks", {})
                .get("percentage", 0),
                "crypto": portfolio_data.get("allocations", {})
                .get("crypto", {})
                .get("percentage", 0),
            },
        }

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@user.route("/api/recent-activity")
@login_required
def api_recent_activity():
    """API endpoint for recent trading activity"""
    try:
        # Get recent trades and orders
        recent_trades = (
            Trade.query.filter_by(user_id=current_user.id)
            .order_by(Trade.timestamp.desc())
            .limit(10)
            .all()
        )

        recent_orders = (
            Order.query.filter_by(user_id=current_user.id)
            .order_by(Order.created_at.desc())
            .limit(10)
            .all()
        )

        # Format trades
        trades_data = []
        for trade in recent_trades:
            trades_data.append(
                {
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "fees": trade.fees if trade.fees else 0,
                    "timestamp": trade.timestamp.isoformat(),
                    "exchange_type": trade.exchange_type,
                }
            )

        # Format orders
        orders_data = []
        for order in recent_orders:
            orders_data.append(
                {
                    "id": order.id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": order.quantity,
                    "price": order.price,
                    "status": order.status,
                    "is_paper": order.is_paper,
                    "exchange_type": order.exchange_type,
                    "created_at": (
                        order.created_at.isoformat() if order.created_at else None
                    ),
                }
            )

        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "recent_trades": trades_data,
                "recent_orders": orders_data,
            }
        )

    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@user.route("/api/market-overview")
@login_required
def api_market_overview():
    """API endpoint for market overview data"""
    try:
        # Mock market data - in production this would come from real market feeds
        market_data = {
            "indices": {
                "nifty50": {
                    "value": 21735.60,
                    "change": 145.30,
                    "change_percent": 0.67,
                    "status": "open",
                },
                "sensex": {
                    "value": 72240.26,
                    "change": 498.58,
                    "change_percent": 0.69,
                    "status": "open",
                },
                "bitcoin": {
                    "value": 43875.50,
                    "change": 1250.25,
                    "change_percent": 2.93,
                    "status": "24h",
                },
                "ethereum": {
                    "value": 2650.80,
                    "change": -45.20,
                    "change_percent": -1.68,
                    "status": "24h",
                },
            },
            "news": [
                {
                    "title": "RBI keeps repo rate unchanged at 6.50%",
                    "time": "2 hours ago",
                    "sentiment": "neutral",
                },
                {
                    "title": "Tech stocks rally on strong Q4 results",
                    "time": "4 hours ago",
                    "sentiment": "positive",
                },
                {
                    "title": "Bitcoin surges past $43,000 mark",
                    "time": "6 hours ago",
                    "sentiment": "positive",
                },
            ],
        }

        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "market_data": market_data,
            }
        )

    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@user.route("/api/performance-chart")
@login_required
def api_performance_chart():
    """API endpoint for performance chart data"""
    try:
        from ..utils.portfolio_manager import PortfolioManager

        portfolio_manager = PortfolioManager(current_user.id)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()

        # Generate mock performance data - in production this would be calculated from historical trades
        import random
        from datetime import timedelta

        chart_data = []
        base_value = 100000  # Starting portfolio value
        current_date = datetime.now() - timedelta(days=30)

        for i in range(30):
            # Simulate daily performance
            daily_change = random.uniform(
                -2, 3
            )  # Random daily change between -2% and +3%
            base_value *= 1 + daily_change / 100

            chart_data.append(
                {
                    "date": (current_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "value": round(base_value, 2),
                    "daily_pnl": round(base_value * daily_change / 100, 2),
                    "daily_pnl_percent": round(daily_change, 2),
                }
            )

        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "chart_data": chart_data,
                "current_value": portfolio_data["summary"]["total_value"],
                "total_return": portfolio_data["performance"].get(
                    "total_return_pct", 0
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance chart: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@user.route("/analytics")
@login_required
def analytics():
    """Enhanced analytics page with real performance metrics."""
    from ..utils.portfolio_manager import PortfolioManager
    from ..utils.subscription_enforcer import SubscriptionEnforcer, get_plan_summary

    try:
        # Check subscription access for analytics
        plan_summary = get_plan_summary(current_user.id)

        # Check if user can access analytics (Pro feature)
        if plan_summary["plan"]["plan"] != "pro" or not plan_summary["features"].get(
            "live_trading", False
        ):
            return render_template(
                "user/analytics.html",
                error="Analytics feature requires Pro subscription",
                plan_summary=plan_summary,
                upgrade_required=True,
                analytics=None,  # Add analytics as None for template
            )

        # Get comprehensive portfolio data for analytics
        portfolio_manager = PortfolioManager(current_user.id)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()

        # Calculate advanced analytics metrics
        performance = portfolio_data["performance"]
        analytics_data = {
            "performance_metrics": {
                "total_return": performance.get("total_return_pct", 0),
                "sharpe_ratio": performance.get("sharpe_ratio", 0),
                "max_drawdown": performance.get("max_drawdown", 0),
                "win_rate": performance.get("win_rate", 0),
                "profit_factor": performance.get("profit_factor", 0),
                "average_gain": performance.get("avg_gain", 0),
                "average_loss": performance.get("avg_loss", 0),
            },
            "monthly_returns": _calculate_monthly_returns(current_user.id),
            "trading_stats": {
                "total_trades": performance.get("total_trades", 0),
                "winning_trades": performance.get("winning_trades", 0),
                "losing_trades": performance.get("losing_trades", 0),
                "consecutive_wins": performance.get("max_consecutive_wins", 0),
                "consecutive_losses": performance.get("max_consecutive_losses", 0),
            },
            "risk_metrics": {
                "var_95": performance.get("value_at_risk", 0),
                "volatility": performance.get("volatility", 0),
                "beta": performance.get("beta", 0),
                "correlation_market": performance.get("market_correlation", 0),
            },
            "portfolio_breakdown": {
                "total_value": portfolio_data["summary"]["total_value"],
                "positions": len(portfolio_data["positions"]),
                "exchanges": len(portfolio_data["exchange_details"]),
                "strategies": portfolio_data["summary"].get("active_strategies", 0),
            },
            "top_performing_strategies": _get_top_strategies(current_user.id),
        }

        return render_template(
            "user/analytics.html",
            analytics=analytics_data,
            portfolio=portfolio_data,
            plan_summary=plan_summary,
            user_info=portfolio_data["user_info"],
        )

    except Exception as e:
        logger.error(f"Analytics error for user {current_user.id}: {e}")
        return render_template(
            "user/analytics.html",
            error="Unable to load analytics data",
            plan_summary=get_plan_summary(current_user.id),
            analytics=None,  # Add analytics as None for template
        )


@user.route("/api/demo-portfolio/generate", methods=["POST"])
@login_required
def generate_demo_portfolio():
    """Generate demo portfolio data for paper trading users."""
    try:
        from ..utils.demo_portfolio import DemoPortfolioGenerator

        # Only allow for paper trading mode
        from ..models import UserPreferences

        preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not preferences or preferences.trading_mode != "paper":
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Demo portfolio generation is only available in paper trading mode",
                    }
                ),
                400,
            )

        # Generate demo portfolio
        result = DemoPortfolioGenerator.generate_demo_portfolio(current_user.id)

        if result["status"] == "created":
            return jsonify(
                {
                    "success": True,
                    "message": "Demo portfolio generated successfully",
                    "data": result["summary"],
                }
            )
        elif result["status"] == "exists":
            return (
                jsonify({"success": False, "message": "Demo portfolio already exists"}),
                409,
            )
        else:
            return (
                jsonify(
                    {"success": False, "message": "Failed to generate demo portfolio"}
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Error generating demo portfolio for user {current_user.id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


@user.route("/api/demo-portfolio/reset", methods=["POST"])
@login_required
def reset_demo_portfolio():
    """Reset demo portfolio data for paper trading users."""
    try:
        from ..utils.demo_portfolio import DemoPortfolioGenerator

        # Only allow for paper trading mode
        from ..models import UserPreferences

        preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not preferences or preferences.trading_mode != "paper":
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Demo portfolio reset is only available in paper trading mode",
                    }
                ),
                400,
            )

        # Reset and regenerate demo portfolio
        DemoPortfolioGenerator.reset_demo_portfolio(current_user.id)
        result = DemoPortfolioGenerator.generate_demo_portfolio(current_user.id)

        if result["status"] == "created":
            return jsonify(
                {
                    "success": True,
                    "message": "Demo portfolio reset and regenerated successfully",
                    "data": result["summary"],
                }
            )
        else:
            return (
                jsonify(
                    {"success": False, "message": "Failed to reset demo portfolio"}
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Error resetting demo portfolio for user {current_user.id}: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500


def _calculate_monthly_returns(user_id: int) -> list:
    """Calculate monthly returns from trade history."""
    from ..models import Trade
    from datetime import datetime, timedelta
    import calendar

    try:
        # Get last 6 months of trade data
        six_months_ago = datetime.now() - timedelta(days=180)
        trades = Trade.query.filter(
            Trade.user_id == user_id, Trade.created_at >= six_months_ago
        ).all()

        # Group trades by month and calculate returns
        monthly_data = {}
        for trade in trades:
            month_key = trade.created_at.strftime("%Y-%m")
            month_name = calendar.month_abbr[trade.created_at.month]

            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_name,
                    "return": 0.0,
                    "trades": 0,
                }

            if trade.pnl:
                monthly_data[month_key]["return"] += float(trade.pnl)
            monthly_data[month_key]["trades"] += 1

        # Convert to list and sort by date
        monthly_returns = list(monthly_data.values())
        return monthly_returns[-6:]  # Last 6 months

    except Exception as e:
        logger.error(f"Error calculating monthly returns: {e}")
        return [
            {"month": "Jan", "return": 0, "trades": 0},
            {"month": "Feb", "return": 0, "trades": 0},
            {"month": "Mar", "return": 0, "trades": 0},
            {"month": "Apr", "return": 0, "trades": 0},
            {"month": "May", "return": 0, "trades": 0},
            {"month": "Jun", "return": 0, "trades": 0},
        ]


def _get_top_strategies(user_id: int) -> list:
    """Get top performing strategies for the user."""
    try:
        # Mock data for now - in a real implementation this would query strategy performance
        return [
            {
                "name": "RSI Mean Reversion",
                "return": 12.5,
                "trades": 45,
                "win_rate": 68.9,
                "status": "active",
            },
            {
                "name": "Moving Average Crossover",
                "return": 8.3,
                "trades": 32,
                "win_rate": 62.5,
                "status": "active",
            },
            {
                "name": "Bollinger Bands",
                "return": 6.7,
                "trades": 28,
                "win_rate": 57.1,
                "status": "paused",
            },
        ]
    except Exception as e:
        logger.error(f"Error getting top strategies: {e}")
        return []


@user.route("/settings")
@login_required
def settings():
    """User account and trading settings"""
    # Get user's exchange connections
    exchange_connections = ExchangeConnection.query.filter_by(
        user_id=current_user.id
    ).all()

    # Create a dict for easy lookup
    connections_dict = {conn.exchange_name: conn for conn in exchange_connections}

    return render_template("user/settings.html", exchange_connections=connections_dict)


@user.route("/settings", methods=["POST"])
@login_required
def update_settings():
    """Update user settings"""
    try:
        # Get form data
        risk_level = request.form.get("risk_level")
        max_position_size = request.form.get("max_position_size")
        stop_loss_default = request.form.get("stop_loss_default")
        take_profit_default = request.form.get("take_profit_default")
        notifications_email = "notifications_email" in request.form
        notifications_sms = "notifications_sms" in request.form
        auto_trading = "auto_trading" in request.form

        # Update user settings (in real app, save to database)
        flash("Settings updated successfully!", "success")

    except Exception as e:
        flash(f"Error updating settings: {str(e)}", "error")

    return redirect(url_for("user.settings"))


@user.route("/api/connect/<exchange>")
@login_required
def connect_exchange(exchange):
    """Redirect user to exchange API setup page"""

    # Exchange API setup URLs
    exchange_urls = {
        "binance": "https://www.binance.com/en/my/settings/api-management",
        "zerodha": "https://kite.trade/connect/login",
        "upstox": "https://api.upstox.com/index/dialog",
        "angelbroking": "https://smartapi.angelbroking.com/",
        "iifl": "https://www.iifl.com/market-research/api",
        "fyers": "https://api.fyers.in/",
        "aliceblue": "https://ant.aliceblueonline.com/",
    }

    if exchange not in exchange_urls:
        flash("Unsupported exchange selected.", "error")
        return redirect(url_for("user.settings"))

    # Create or update exchange connection record
    connection = ExchangeConnection.query.filter_by(
        user_id=current_user.id, exchange_name=exchange
    ).first()

    if not connection:
        connection = ExchangeConnection(
            user_id=current_user.id, exchange_name=exchange, status="pending"
        )
        db.session.add(connection)
    else:
        connection.status = "pending"
        connection.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        flash(f"Setting up connection to {connection.get_display_name()}...", "info")

        # Show the connection setup page with instructions and external link
        return render_template(
            "user/exchange_connect.html",
            exchange=exchange,
            exchange_url=exchange_urls[exchange],
            connection=connection,
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Error initiating connection: {str(e)}", "error")
        return redirect(url_for("user.settings"))


@user.route("/api/redirect/<exchange>")
@login_required
def redirect_to_exchange(exchange):
    """Direct redirect to exchange API portal"""

    # Exchange API setup URLs
    exchange_urls = {
        "binance": "https://www.binance.com/en/my/settings/api-management",
        "zerodha": "https://kite.trade/connect/login",
        "upstox": "https://api.upstox.com/index/dialog",
        "angelbroking": "https://smartapi.angelbroking.com/",
        "iifl": "https://www.iifl.com/market-research/api",
        "fyers": "https://api.fyers.in/",
        "aliceblue": "https://ant.aliceblueonline.com/",
    }

    if exchange in exchange_urls:
        return redirect(exchange_urls[exchange])
    else:
        flash("Unsupported exchange selected.", "error")
        return redirect(url_for("user.settings"))


@user.route("/api/callback/<exchange>", methods=["GET", "POST"])
@login_required
def exchange_callback(exchange):
    """Handle exchange API callback (simulated)"""

    connection = ExchangeConnection.query.filter_by(
        user_id=current_user.id, exchange_name=exchange
    ).first()

    if not connection:
        flash("No pending connection found.", "error")
        return redirect(url_for("user.settings"))

    # Simulate successful connection (in real app, this would verify API credentials)
    if request.method == "POST":
        api_key = request.form.get("api_key", "").strip()
        api_secret = request.form.get("api_secret", "").strip()

        # Handle Binance-specific environment selection
        environment = (
            request.form.get("environment", "live") if exchange == "binance" else "live"
        )

        if api_key and api_secret:
            # In real implementation, these would be encrypted before storing
            connection.api_key = (
                api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else api_key
            )
            connection.api_secret = (
                "***" + api_secret[-4:] if len(api_secret) > 4 else "***"
            )

            # For Binance, store environment info in exchange_name
            if exchange == "binance" and environment == "testnet":
                connection.exchange_name = "binance_testnet"
            else:
                connection.exchange_name = exchange

            connection.status = "connected"
            connection.last_connected = datetime.utcnow()
            connection.error_message = None

            try:
                db.session.commit()
                flash(
                    f"Successfully connected to {connection.get_display_name()}!",
                    "success",
                )
            except Exception as e:
                db.session.rollback()
                flash(f"Error saving connection: {str(e)}", "error")
        else:
            flash("API key and secret are required.", "error")
            return render_template(
                "user/exchange_connect.html", exchange=exchange, connection=connection
            )

    return redirect(url_for("user.settings"))


@user.route("/api/disconnect/<exchange>", methods=["POST"])
@login_required
def disconnect_exchange(exchange):
    """Disconnect from exchange"""

    connection = ExchangeConnection.query.filter_by(
        user_id=current_user.id, exchange_name=exchange
    ).first()

    if connection:
        connection.status = "disconnected"
        connection.api_key = None
        connection.api_secret = None
        connection.access_token = None
        connection.last_connected = None
        connection.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            flash(f"Disconnected from {connection.get_display_name()}.", "info")
        except Exception as e:
            db.session.rollback()
            flash(f"Error disconnecting: {str(e)}", "error")
    else:
        flash("Connection not found.", "error")

    return redirect(url_for("user.settings"))


@user.route("/help")
@login_required
def help():
    """Help and support center"""
    help_topics = [
        {
            "category": "Getting Started",
            "topics": [
                {
                    "title": "Account Setup",
                    "description": "How to set up your trading account",
                },
                {
                    "title": "First Strategy",
                    "description": "Creating your first trading strategy",
                },
                {
                    "title": "Understanding Dashboard",
                    "description": "Navigate the trading dashboard",
                },
            ],
        },
        {
            "category": "Trading Strategies",
            "topics": [
                {
                    "title": "Strategy Types",
                    "description": "Different types of trading strategies",
                },
                {
                    "title": "Risk Management",
                    "description": "Managing risk in your trades",
                },
                {
                    "title": "Backtesting",
                    "description": "Testing strategies with historical data",
                },
            ],
        },
        {
            "category": "Account Management",
            "topics": [
                {
                    "title": "Billing & Subscription",
                    "description": "Managing your subscription",
                },
                {
                    "title": "API Integration",
                    "description": "Connecting external brokers",
                },
                {
                    "title": "Security Settings",
                    "description": "Keeping your account secure",
                },
            ],
        },
    ]

    recent_updates = [
        {
            "date": "2024-01-15",
            "title": "New Portfolio Analytics",
            "description": "Enhanced analytics dashboard with risk metrics",
        },
        {
            "date": "2024-01-10",
            "title": "Mobile App Update",
            "description": "Improved mobile trading experience",
        },
        {
            "date": "2024-01-05",
            "title": "Strategy Builder 2.0",
            "description": "New drag-and-drop strategy builder",
        },
    ]

    return render_template(
        "user/help.html", help_topics=help_topics, recent_updates=recent_updates
    )


# ============================================================================
# AUTOMATED TRADING ROUTES - One-Click Trading Bot for Indian Stock Market
# ============================================================================


@user.route("/automation/start", methods=["POST"])
@limiter.limit("5 per minute")
def start_automated_trading():
    """Start automated trading bot with comprehensive strategies."""
    try:
        from ..automation.bot_manager import BotManager

        bot = BotManager.get_bot(current_user.id, bot_type="stock")
        result = bot.start_automated_trading()

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error starting automated trading: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Failed to start automated trading: {str(e)}",
                }
            ),
            500,
        )


@user.route("/automation/stop", methods=["POST"])
@limiter.limit("5 per minute")
def stop_automated_trading():
    """Stop automated trading bot and close all positions."""
    try:
        from ..automation.bot_manager import BotManager

        bot = BotManager.get_bot(current_user.id, bot_type="stock")
        result = bot.stop_automated_trading()

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error stopping automated trading: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Failed to stop automated trading: {str(e)}",
                }
            ),
            500,
        )


@user.route("/automation/status")
def get_automation_status():
    """Get current status of automated trading bot."""
    try:
        from ..automation.bot_manager import BotManager

        bot = BotManager.get_bot(current_user.id, bot_type="stock")
        status = bot.get_status()

        return jsonify({"success": True, "status": status})

    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        return (
            jsonify({"success": False, "message": f"Failed to get status: {str(e)}"}),
            500,
        )


@user.route("/automation")
def automation_dashboard():
    """Automated trading dashboard page."""
    try:
        from ..automation.bot_manager import BotManager

        bot = BotManager.get_bot(current_user.id, bot_type="stock")
        status = bot.get_status()

        # Get all connected exchanges
        all_exchanges = ExchangeConnection.query.filter_by(
            user_id=current_user.id, status="connected"
        ).all()

        # Separate stock and crypto exchanges
        stock_exchanges = []
        crypto_exchanges = []

        for exchange in all_exchanges:
            if exchange.exchange_name in ["binance", "binance_testnet"]:
                crypto_exchanges.append(exchange)
            else:
                stock_exchanges.append(exchange)

        # Get market-specific statistics
        stock_stats = {
            "total_trades": 12,  # Placeholder data
            "win_rate": 68.5,
            "daily_pnl": 1250.50,
            "open_positions": 3,
            "strategies_active": 2,
        }

        crypto_stats = {
            "total_trades": 8,  # Placeholder data
            "win_rate": 72.0,
            "daily_pnl": 0.0024,
            "open_positions": 1,
            "strategies_active": 1,
        }

        # Get active trading sessions (placeholder data)
        stock_sessions = [
            {
                "strategy_name": "RSI Momentum",
                "symbol": "RELIANCE",
                "start_time": datetime.now().replace(hour=10, minute=30),
                "pnl": 450.75,
                "trades_count": 3,
                "entry_price": 2840.50,
                "current_price": 2855.25,
                "quantity": 10,
            },
            {
                "strategy_name": "Bollinger Bands",
                "symbol": "TCS",
                "start_time": datetime.now().replace(hour=11, minute=15),
                "pnl": -125.30,
                "trades_count": 1,
                "entry_price": 3950.00,
                "current_price": 3937.45,
                "quantity": 5,
            },
        ]

        crypto_sessions = [
            {
                "strategy_name": "Crypto Momentum",
                "symbol": "BTCUSDT",
                "start_time": datetime.now().replace(hour=9, minute=45),
                "pnl": 0.0012,
                "trades_count": 2,
                "entry_price": 43250.50,
                "current_price": 43875.25,
                "quantity": 0.001,
            }
        ]

        # For backward compatibility
        has_exchange_connection = bool(all_exchanges)
        exchange_connection = all_exchanges[0] if all_exchanges else None

        return render_template(
            "user/automation.html",
            automation_status=status,
            has_exchange_connection=has_exchange_connection,
            exchange_connection=exchange_connection,
            stock_exchanges=stock_exchanges,
            crypto_exchanges=crypto_exchanges,
            stock_stats=stock_stats,
            crypto_stats=crypto_stats,
            stock_sessions=stock_sessions,
            crypto_sessions=crypto_sessions,
        )

    except Exception as e:
        logger.error(f"Error loading automation dashboard: {e}")
        flash("Error loading automation dashboard", "error")
        return redirect(url_for("user.dashboard"))


# ============================================================================
# CRYPTOCURRENCY TRADING ROUTES - Binance Integration
# ============================================================================


@user.route("/automation/start-crypto", methods=["POST"])
@limiter.limit("5 per minute")
def start_crypto_trading():
    """Start cryptocurrency trading bot with Binance."""
    try:
        from ..automation.bot_manager import BotManager

        # Get bot instance from manager (persistent across requests)
        crypto_engine = BotManager.get_bot(current_user.id, bot_type="crypto")

        # Get request data
        data = request.get_json() or {}
        strategies = data.get(
            "strategies",
            ["crypto_momentum", "crypto_mean_reversion", "crypto_breakout"],
        )
        is_paper = data.get("is_paper", True)  # Default to paper trading

        result = crypto_engine.start_trading(
            user_id=current_user.id, strategy_names=strategies, is_paper=is_paper
        )

        return jsonify(
            {
                "success": result.get("status") == "success",
                "message": result.get("message"),
                "details": result.get("results", {}),
            }
        )

    except Exception as e:
        logger.error(f"Error starting crypto trading: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Failed to start crypto trading: {str(e)}",
                }
            ),
            500,
        )


@user.route("/automation/stop-crypto", methods=["POST"])
@limiter.limit("5 per minute")
def stop_crypto_trading():
    """Stop cryptocurrency trading bot."""
    try:
        from ..automation.bot_manager import BotManager

        crypto_engine = BotManager.get_bot(current_user.id, bot_type="crypto")
        result = crypto_engine.stop_trading()

        return jsonify(
            {
                "success": result.get("status") == "success",
                "message": result.get("message"),
            }
        )

    except Exception as e:
        logger.error(f"Error stopping crypto trading: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Failed to stop crypto trading: {str(e)}",
                }
            ),
            500,
        )


@user.route("/automation/crypto-status")
def get_crypto_status():
    """Get current status of cryptocurrency trading."""
    try:
        from ..automation.bot_manager import BotManager

        crypto_engine = BotManager.get_bot(current_user.id, bot_type="crypto")

        # Get recent crypto orders
        crypto_orders = (
            Order.query.filter_by(user_id=current_user.id, exchange_type="crypto")
            .order_by(Order.created_at.desc())
            .limit(10)
            .all()
        )

        # Calculate crypto performance
        crypto_trades = Trade.query.filter_by(
            user_id=current_user.id, exchange_type="crypto"
        ).all()

        total_trades = len(crypto_trades)
        winning_trades = len(
            [t for t in crypto_trades if t.side == "sell" and t.price > 0]
        )
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Get portfolio summary
        portfolio = crypto_engine.get_portfolio_summary(current_user.id)

        status = {
            "is_running": crypto_engine.is_running,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "daily_pnl": 0.0,  # Calculate from recent trades
            "open_positions": (
                len(portfolio.get("portfolio", [])) if "portfolio" in portfolio else 0
            ),
            "strategies_active": 3 if crypto_engine.is_running else 0,
            "portfolio": portfolio,
        }

        return jsonify({"success": True, "status": status})

    except Exception as e:
        logger.error(f"Error getting crypto status: {e}")
        return (
            jsonify(
                {"success": False, "message": f"Failed to get crypto status: {str(e)}"}
            ),
            500,
        )


@user.route("/crypto/status", methods=["GET"])
@login_required
def crypto_bot_status():
    """Get current cryptocurrency trading bot status."""
    try:
        from ..automation.bot_manager import BotManager

        crypto_bot = BotManager.get_bot(current_user.id, bot_type="crypto")
        status = crypto_bot.get_trading_status()

        return jsonify({"success": True, "status": status})

    except Exception as e:
        logger.error(f"Error getting crypto status: {e}")
        return (
            jsonify(
                {"success": False, "message": f"Failed to get crypto status: {str(e)}"}
            ),
            500,
        )


@user.route("/crypto/portfolio")
def crypto_portfolio():
    """Get cryptocurrency portfolio details."""
    try:
        from ..automation.bot_manager import BotManager

        crypto_engine = BotManager.get_bot(current_user.id, bot_type="crypto")
        portfolio = crypto_engine.get_portfolio_summary(current_user.id)

        return jsonify({"success": True, "portfolio": portfolio})

    except Exception as e:
        logger.error(f"Error getting crypto portfolio: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Failed to get crypto portfolio: {str(e)}",
                }
            ),
            500,
        )


@user.route("/test-bot-api")
@login_required
def test_bot_api():
    """Test page for bot API endpoints"""
    return render_template("test_bot_api.html")


@user.route("/automation/sessions", methods=["GET"])
@login_required
def get_trading_sessions():
    """Get current active trading sessions for both stock and crypto markets."""
    try:
        from ..automation.bot_manager import BotManager
        from datetime import datetime

        # Get real bot instances
        stock_bot = BotManager.get_bot(current_user.id, bot_type="stock")
        crypto_bot = BotManager.get_bot(current_user.id, bot_type="crypto")

        # Get real stock sessions data
        stock_sessions = []
        try:
            if hasattr(stock_bot, "is_running") and stock_bot.is_running:
                stock_status = stock_bot.get_status()
                if stock_status.get("is_running"):
                    # Show running strategies with their positions
                    positions = stock_status.get("positions", {})
                    strategies_active = stock_status.get("strategies_active", 0)

                    if positions:
                        # If there are active positions, show each position
                        for strategy, position in positions.items():
                            if position.get("quantity", 0) != 0:
                                stock_sessions.append(
                                    {
                                        "strategy_name": strategy.replace(
                                            "_", " "
                                        ).title(),
                                        "symbol": position.get("symbol", "UNKNOWN"),
                                        "start_time": stock_status.get(
                                            "start_time",
                                            datetime.now().strftime("%H:%M"),
                                        ),
                                        "pnl": round(
                                            position.get("unrealized_pnl", 0), 2
                                        ),
                                        "trades_count": stock_status.get(
                                            "total_trades", 0
                                        ),
                                        "entry_price": round(
                                            position.get("avg_price", 0), 2
                                        ),
                                        "current_price": round(
                                            position.get("current_price", 0), 2
                                        ),
                                        "quantity": position.get("quantity", 0),
                                    }
                                )
                    elif strategies_active > 0:
                        # If no positions but strategies are active, show strategy is monitoring
                        stock_sessions.append(
                            {
                                "strategy_name": "Multi Strategy Engine",
                                "symbol": "MONITORING",
                                "start_time": datetime.now().strftime("%H:%M"),
                                "pnl": round(stock_status.get("daily_pnl", 0), 2),
                                "trades_count": stock_status.get("total_trades", 0),
                                "entry_price": 0.0,
                                "current_price": 0.0,
                                "quantity": 0.0,
                            }
                        )
        except Exception as e:
            logger.warning(f"Error getting stock sessions: {e}")

        # Get real crypto sessions data
        crypto_sessions = []
        try:
            if hasattr(crypto_bot, "is_running") and crypto_bot.is_running:
                crypto_status = crypto_bot.get_trading_status()

                # Get active strategies and their performance
                active_strategies = crypto_status.get("active_strategies", {})
                for strategy_name, strategy_data in active_strategies.items():
                    # Show running strategies even without active positions
                    active_positions = strategy_data.get("active_positions", [])

                    if active_positions:
                        # If there are active positions, show each position
                        for position in active_positions:
                            crypto_sessions.append(
                                {
                                    "strategy_name": strategy_name.replace(
                                        "_", " "
                                    ).title(),
                                    "symbol": position.get("symbol", "UNKNOWN"),
                                    "start_time": strategy_data.get(
                                        "start_time",
                                        datetime.now().strftime("%H:%M UTC"),
                                    ),
                                    "pnl": round(position.get("unrealized_pnl", 0), 6),
                                    "trades_count": strategy_data.get(
                                        "trades_count", 0
                                    ),
                                    "entry_price": round(
                                        position.get("entry_price", 0), 4
                                    ),
                                    "current_price": round(
                                        position.get("current_price", 0), 4
                                    ),
                                    "quantity": round(position.get("quantity", 0), 6),
                                }
                            )
                    else:
                        # If no active positions, show strategy is running
                        crypto_sessions.append(
                            {
                                "strategy_name": strategy_name.replace(
                                    "_", " "
                                ).title(),
                                "symbol": "MONITORING",
                                "start_time": strategy_data.get(
                                    "start_time",
                                    datetime.now().strftime("%H:%M UTC"),
                                ),
                                "pnl": 0.0,
                                "trades_count": strategy_data.get("trades_count", 0),
                                "entry_price": 0.0,
                                "current_price": 0.0,
                                "quantity": 0.0,
                            }
                        )
        except Exception as e:
            logger.warning(f"Error getting crypto sessions: {e}")

        return jsonify(
            {
                "success": True,
                "data": {
                    "stock_sessions": stock_sessions,
                    "crypto_sessions": crypto_sessions,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error fetching trading sessions: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to fetch trading sessions",
                    "error": str(e),
                }
            ),
            500,
        )


# ============================================================================
# AUTOMATED TRADING FEATURES - Professional Trading Company Pages
# ============================================================================


@user.route("/portfolio")
def portfolio():
    """Enhanced portfolio overview with real data from PortfolioManager."""
    try:
        from ..utils.portfolio_manager import PortfolioManager
        from ..utils.subscription_enforcer import SubscriptionEnforcer, get_plan_summary

        # Get comprehensive portfolio data using our enhanced manager
        portfolio_manager = PortfolioManager(current_user.id)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()

        # Get subscription and plan info
        plan_summary = get_plan_summary(current_user.id)

        # Structure data for template
        portfolio_summary = {
            "total_value": portfolio_data["summary"].get("total_value", 0),
            "total_pnl": portfolio_data["summary"].get("total_pnl", 0),
            "daily_pnl": portfolio_data["performance"].get("daily_pnl", 0),
            "monthly_pnl": portfolio_data["performance"].get("monthly_pnl", 0),
            "unrealized_pnl": portfolio_data["summary"].get("unrealized_pnl", 0),
            "realized_pnl": portfolio_data["summary"].get("realized_pnl", 0),
            "total_invested": portfolio_data["summary"].get("total_invested", 0),
            "available_balance": portfolio_data["summary"].get("available_balance", 0),
            "trading_mode": portfolio_data["user_info"].get("trading_mode", "paper"),
            "positions_count": len(portfolio_data.get("positions", [])),
            "active_orders": portfolio_data["summary"].get("active_orders", 0),
        }

        # Calculate allocations
        stock_value = sum(
            pos["market_value"]
            for pos in portfolio_data["positions"]
            if pos.get("exchange") == "zerodha"
        )
        crypto_value = sum(
            pos["market_value"]
            for pos in portfolio_data["positions"]
            if pos.get("exchange") == "binance"
        )
        total_portfolio = stock_value + crypto_value

        allocations = {
            "stocks": (
                (stock_value / total_portfolio * 100) if total_portfolio > 0 else 0
            ),
            "crypto": (
                (crypto_value / total_portfolio * 100) if total_portfolio > 0 else 0
            ),
        }

        return render_template(
            "user/portfolio.html",
            title="Portfolio",
            portfolio=portfolio_summary,
            positions=portfolio_data["positions"],
            recent_trades=portfolio_data["recent_trades"],
            performance=portfolio_data["performance"],
            allocations=allocations,
            exchange_details=portfolio_data["exchange_details"],
            plan_summary=plan_summary,
            user_info=portfolio_data["user_info"],
        )

    except Exception as e:
        logger.error(f"Portfolio error for user {current_user.id}: {e}")
        # Fallback with error message
        fallback_portfolio = {
            "total_value": 0,
            "total_pnl": 0,
            "daily_pnl": 0,
            "monthly_pnl": 0,
            "unrealized_pnl": 0,
            "realized_pnl": 0,
            "total_invested": 0,
            "available_balance": 0,
            "trading_mode": "paper",
            "positions_count": 0,
            "active_orders": 0,
        }
        return render_template(
            "user/portfolio.html",
            title="Portfolio",
            error="Unable to load portfolio data. Please try again later.",
            portfolio=fallback_portfolio,
            positions=[],
            recent_trades=[],
            allocations={"stocks": 0, "crypto": 0},
            exchange_details={},
            plan_summary={
                "plan": {"plan": "free", "active": True},
                "features": {"live_trading": False},
                "limits": {"max_orders_per_day": 10},
                "current_usage": {"orders_today": 0, "max_orders": 10},
            },
            user_info={"trading_mode": "paper"},
            performance={"daily_pnl": 0, "monthly_pnl": 0, "yearly_pnl": 0},
        )


@user.route("/billing")
def billing():
    """Billing page for subscription management."""
    from ..utils.subscription_enforcer import get_plan_summary

    try:
        plan_summary = get_plan_summary(current_user.id)
        return render_template("user/billing.html", plan_summary=plan_summary)
    except Exception as e:
        logger.error(f"Billing page error: {e}")
        return render_template(
            "user/billing.html", error="Unable to load billing information"
        )


@user.route("/api/portfolio")
@login_required
def api_portfolio():
    """Enhanced JSON API for portfolio data with subscription enforcement."""
    from ..utils.portfolio_manager import PortfolioManager
    from ..utils.subscription_enforcer import get_plan_summary

    try:
        # Get comprehensive portfolio data
        portfolio_manager = PortfolioManager(current_user.id)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()

        # Get plan summary for feature restrictions
        plan_summary = get_plan_summary(current_user.id)

        return jsonify(
            {
                "success": True,
                "portfolio": portfolio_data,
                "plan": plan_summary,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"API portfolio error for user {current_user.id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@user.route("/api/portfolio/legacy")
@login_required
def api_portfolio_legacy():
    """Legacy JSON data for portfolio page (backward compatibility)."""
    mode = request.args.get("mode", "paper").lower()
    market = request.args.get("market", "stocks").lower()
    if market not in ("stocks", "crypto"):
        market = "stocks"
    trading_mode = "live" if mode == "live" else "paper"

    # Use the new PortfolioManager for legacy route
    from ..utils.portfolio_manager import PortfolioManager
    from ..models import Order

    try:
        portfolio_manager = PortfolioManager(current_user.id)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()

        # Get orders for legacy format
        is_paper = trading_mode == "paper"
        stock_orders = (
            Order.query.filter_by(
                user_id=current_user.id, exchange_type="stocks", is_paper=is_paper
            )
            .order_by(Order.created_at.desc())
            .limit(50)
            .all()
        )

        crypto_orders = (
            Order.query.filter_by(
                user_id=current_user.id, exchange_type="crypto", is_paper=is_paper
            )
            .order_by(Order.created_at.desc())
            .limit(50)
            .all()
        )

        def serialize_order(o: Order):
            return {
                "id": o.id,
                "symbol": o.symbol,
                "side": o.side,
                "quantity": o.quantity,
                "price": o.price,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }

        # Convert new portfolio format to legacy format
        legacy_portfolio = {
            "total_value": portfolio_data["summary"]["total_value"],
            "daily_pnl": portfolio_data["summary"]["daily_pnl"],
            "total_pnl": portfolio_data["summary"]["total_pnl"],
            "stock_allocation": portfolio_data["allocations"]["stocks"]["percentage"],
            "crypto_allocation": portfolio_data["allocations"]["crypto"]["percentage"],
            "stock_value": portfolio_data["allocations"]["stocks"]["value"],
            "crypto_value": portfolio_data["allocations"]["crypto"]["value"],
            "active_positions": len(portfolio_data["positions"]),
            "trading_mode": trading_mode,
            "mode_label": "Live Trading" if trading_mode == "live" else "Paper Trading",
        }

        # Select market-specific value
        selected_value = (
            legacy_portfolio["stock_value"]
            if market == "stocks"
            else legacy_portfolio["crypto_value"]
        )

        response = {
            "success": True,
            "mode": trading_mode,
            "market": market,
            "portfolio": {**legacy_portfolio, "selected_value": selected_value},
            "stock_orders": [serialize_order(o) for o in stock_orders],
            "crypto_orders": [serialize_order(o) for o in crypto_orders],
            "counts": {"stock": len(stock_orders), "crypto": len(crypto_orders)},
        }
        return jsonify(response)

    except Exception as e:
        logger.error(f"Legacy portfolio API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@user.route("/risk-management")
def risk_management():
    """Risk management settings for automated trading."""
    return render_template("user/risk_management.html")


@user.route("/market-research")
def market_research():
    """Market research and analysis tools."""
    return render_template("user/analytics.html")


@user.route("/strategy-library")
def strategy_library():
    """Strategy library with pre-built automated strategies."""
    return render_template("user/strategy_library.html")


@user.route("/watchlists")
def watchlists():
    """Watchlists for automated trading monitoring."""
    return render_template("user/watchlists.html")


@user.route("/market-calendar")
def market_calendar():
    """Market calendar for trading schedule."""
    return render_template("user/market_calendar.html")


@user.route("/education")
def education():
    """Education center for automated trading."""
    return render_template("user/education.html")


@user.route("/community")
def community():
    """Community forum for TradeMantra users."""
    return render_template("user/community.html")


@user.route("/support")
def support():
    """Support center and help."""
    return render_template("user/support.html")


@user.route("/account-statement")
def account_statement():
    """Account statement and trading history."""
    return render_template("user/account_statement.html")


@user.route("/tax-reports")
def tax_reports():
    """Tax reports and documentation."""
    return render_template("user/tax_reports.html")


# API Endpoints for User Preferences
@user.route("/preferences/api", methods=["GET"])
@login_required
def get_user_preferences():
    """Get user preferences including trading mode."""
    from ..models import UserPreferences

    preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()

    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreferences(
            user_id=current_user.id,
            trading_mode="paper",
            default_exchange_type="stocks",
            theme="dark",
        )
        db.session.add(preferences)
        db.session.commit()

    return jsonify(
        {
            "success": True,
            "trading_mode": preferences.trading_mode,
            "default_exchange_type": preferences.default_exchange_type,
            "risk_level": preferences.risk_level,
            "max_position_size": float(preferences.max_position_size),
            "daily_loss_limit": float(preferences.daily_loss_limit),
            "theme": preferences.theme,
            "notifications_enabled": preferences.notifications_enabled,
            "email_alerts": preferences.email_alerts,
            "sms_alerts": preferences.sms_alerts,
        }
    )


@user.route("/preferences/api", methods=["POST"])
@login_required
def update_user_preferences():
    """Update user preferences including trading mode."""
    from ..models import UserPreferences

    try:
        data = request.get_json()

        preferences = UserPreferences.query.filter_by(user_id=current_user.id).first()

        if not preferences:
            preferences = UserPreferences(user_id=current_user.id)
            db.session.add(preferences)

        # Update provided fields
        if "trading_mode" in data:
            if data["trading_mode"] not in ["paper", "live"]:
                return jsonify({"success": False, "error": "Invalid trading mode"}), 400
            preferences.trading_mode = data["trading_mode"]

            # Log the trading mode change for audit
            from ..models import AuditLog

            audit_log = AuditLog(
                user_id=current_user.id,
                action=f"Trading mode changed to {data['trading_mode'].upper()}",
                details={
                    "previous_mode": (
                        preferences.trading_mode if preferences else "paper"
                    ),
                    "new_mode": data["trading_mode"],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            db.session.add(audit_log)

        if "default_exchange_type" in data:
            preferences.default_exchange_type = data["default_exchange_type"]

        if "risk_level" in data:
            preferences.risk_level = data["risk_level"]

        if "max_position_size" in data:
            preferences.max_position_size = float(data["max_position_size"])

        if "daily_loss_limit" in data:
            preferences.daily_loss_limit = float(data["daily_loss_limit"])

        if "theme" in data:
            preferences.theme = data["theme"]

        if "notifications_enabled" in data:
            preferences.notifications_enabled = bool(data["notifications_enabled"])

        if "email_alerts" in data:
            preferences.email_alerts = bool(data["email_alerts"])

        if "sms_alerts" in data:
            preferences.sms_alerts = bool(data["sms_alerts"])

        db.session.commit()

        return jsonify({"success": True, "message": "Preferences updated successfully"})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user preferences: {e}")
        return jsonify({"success": False, "error": "Failed to update preferences"}), 500


# AI TRADING FEATURES
@user.route("/ai-signals")
@login_required
def ai_signals():
    """AI-powered trading signals dashboard."""
    from ..strategies.ai_trading_engine import AITradingEngine

    # Check if user has AI access
    if not current_user.ai_enabled:
        flash(
            "AI features are only available for Pro and Institutional subscribers.",
            "warning",
        )
        return redirect(url_for("user.dashboard"))

    try:
        ai_engine = AITradingEngine()

        # Get AI signals for user's watchlist/portfolio
        portfolio_symbols = [
            "RELIANCE",
            "TCS",
            "INFY",
            "HDFCBANK",
            "ICICIBANK",
        ]  # Example symbols

        signals = []
        for symbol in portfolio_symbols:
            signal = ai_engine.generate_signal(symbol)
            if signal:
                signals.append(
                    {
                        "symbol": signal.symbol,
                        "action": signal.action.value,
                        "confidence": round(signal.confidence * 100, 1),
                        "price_target": signal.price_target,
                        "stop_loss": signal.stop_loss,
                        "strategy": signal.strategy_type.value,
                        "reasoning": signal.reasoning,
                        "created_at": signal.created_at.strftime("%H:%M"),
                    }
                )

        return render_template(
            "user/ai_signals.html",
            title="AI Trading Signals",
            signals=signals,
            user=current_user,
        )

    except Exception as e:
        logger.error(f"Error loading AI signals: {e}")
        flash("Unable to load AI signals at this time.", "danger")
        return redirect(url_for("user.dashboard"))


@user.route("/ai-portfolio-optimization")
@login_required
def ai_portfolio_optimization():
    """AI-powered portfolio optimization suggestions."""
    from ..strategies.ai_trading_engine import AITradingEngine

    # Check if user has AI access
    if not current_user.ai_enabled:
        flash(
            "AI features are only available for Pro and Institutional subscribers.",
            "warning",
        )
        return redirect(url_for("user.dashboard"))

    try:
        ai_engine = AITradingEngine()

        # Get portfolio optimization suggestions
        optimization = ai_engine.optimize_portfolio(current_user.id)

        return render_template(
            "user/ai_portfolio_optimization.html",
            title="AI Portfolio Optimization",
            optimization=optimization,
            user=current_user,
        )

    except Exception as e:
        logger.error(f"Error loading portfolio optimization: {e}")
        flash("Unable to load portfolio optimization at this time.", "danger")
        return redirect(url_for("user.dashboard"))


@user.route("/ai-market-analysis")
@login_required
def ai_market_analysis():
    """AI-powered market analysis and insights."""
    from ..strategies.ai_trading_engine import AITradingEngine

    # Check if user has AI access
    if not current_user.ai_enabled:
        flash(
            "AI features are only available for Pro and Institutional subscribers.",
            "warning",
        )
        return redirect(url_for("user.dashboard"))

    try:
        ai_engine = AITradingEngine()

        # Get market analysis
        analysis = ai_engine.get_market_analysis()

        return render_template(
            "user/ai_market_analysis.html",
            title="AI Market Analysis",
            analysis=analysis,
            user=current_user,
        )

    except Exception as e:
        logger.error(f"Error loading market analysis: {e}")
        flash("Unable to load market analysis at this time.", "danger")
        return redirect(url_for("user.dashboard"))


@user.route("/api/ai/signals")
@login_required
def api_ai_signals():
    """API endpoint for real-time AI signals."""
    from ..strategies.ai_trading_engine import AITradingEngine

    if not current_user.ai_enabled:
        return jsonify({"error": "AI features not available"}), 403

    try:
        ai_engine = AITradingEngine()
        symbols = request.args.getlist("symbols") or ["RELIANCE", "TCS", "INFY"]

        signals = []
        for symbol in symbols:
            signal = ai_engine.generate_signal(symbol)
            if signal:
                signals.append(
                    {
                        "symbol": signal.symbol,
                        "action": signal.action.value,
                        "confidence": signal.confidence,
                        "price_target": signal.price_target,
                        "stop_loss": signal.stop_loss,
                        "strategy": signal.strategy_type.value,
                        "reasoning": signal.reasoning,
                        "timestamp": signal.created_at.isoformat(),
                    }
                )

        return jsonify({"signals": signals, "count": len(signals)})

    except Exception as e:
        logger.error(f"Error generating AI signals: {e}")
        return jsonify({"error": "Failed to generate signals"}), 500
