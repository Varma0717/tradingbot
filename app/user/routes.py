from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from ..models import Order, Trade, Strategy
from ..orders.manager import place_order
from .. import db, limiter
import json

user = Blueprint("user", __name__)


@user.route("/")
def index():
    """Redirect user root to dashboard."""
    return redirect(url_for("user.dashboard"))


@user.before_request
@login_required
def before_request():
    """Protect all user routes."""
    pass


@user.route("/dashboard")
def dashboard():
    # Get real data from database
    recent_orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )
    last_10_trades = (
        Trade.query.filter_by(user_id=current_user.id)
        .order_by(Trade.timestamp.desc())
        .limit(10)
        .all()
    )
    active_strategies = Strategy.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()

    # Calculate P&L from trades
    total_pnl = sum(
        [
            (trade.price * trade.quantity * (1 if trade.side == "sell" else -1))
            for trade in Trade.query.filter_by(user_id=current_user.id).all()
        ]
    )

    pnl_summary = {
        "daily": total_pnl * 0.1,  # Mock daily calculation
        "monthly": total_pnl * 0.3,  # Mock monthly calculation
        "total": total_pnl,
    }

    balance = 500000.00 + total_pnl  # Starting balance + P&L

    # Mock active positions
    active_positions = [
        {
            "symbol": "RELIANCE",
            "qty": 10,
            "avg_price": 2450.00,
            "ltp": 2465.00,
            "pnl": 150.00,
        },
        {
            "symbol": "TCS",
            "qty": 20,
            "avg_price": 3300.00,
            "ltp": 3280.00,
            "pnl": -400.00,
        },
    ]

    return render_template(
        "user/dashboard.html",
        title="Dashboard",
        pnl=pnl_summary,
        balance=balance,
        positions=active_positions,
        trades=last_10_trades,
        recent_orders=recent_orders,
        active_strategies=active_strategies,
    )


@user.route("/orders")
def orders():
    page = request.args.get("page", 1, type=int)
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )
    return render_template("user/orders.html", title="Orders", orders=orders)


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


@user.route("/billing")
def billing():
    return render_template("user/billing.html", title="Billing & Subscription")


@user.route("/trade", methods=["POST"])
@limiter.limit("30/minute")  # Limit to 30 trades per minute
def execute_trade():
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

        # Subscription check for real trades
        if not is_paper and not current_user.has_pro_plan:
            if request.is_json:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Pro plan required for real trading",
                        }
                    ),
                    403,
                )
            flash("You need a Pro plan to place real trades.", "warning")
            return redirect(url_for("user.dashboard"))

        order_payload = {
            "symbol": symbol.upper(),
            "quantity": quantity,
            "order_type": order_type,
            "side": side,
            "price": price,
            "is_paper": is_paper,
        }

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


# API Endpoints
@user.route("/api/dashboard/data")
@limiter.limit("60/minute")  # Limit API calls for real-time updates
def api_dashboard_data():
    """API endpoint for real-time dashboard updates"""
    try:
        # Get fresh data
        last_trades = (
            Trade.query.filter_by(user_id=current_user.id)
            .order_by(Trade.timestamp.desc())
            .limit(5)
            .all()
        )

        # Calculate P&L
        total_pnl = sum(
            [
                (trade.price * trade.quantity * (1 if trade.side == "sell" else -1))
                for trade in Trade.query.filter_by(user_id=current_user.id).all()
            ]
        )

        pnl_data = {
            "daily": total_pnl * 0.1,
            "monthly": total_pnl * 0.3,
            "total": total_pnl,
        }

        # Mock positions (in real app, calculate from current holdings)
        positions = [
            {"symbol": "RELIANCE", "quantity": 10, "avg_price": 2450.00, "pnl": 150.00},
            {"symbol": "TCS", "quantity": 20, "avg_price": 3300.00, "pnl": -400.00},
        ]

        recent_trades = [
            {
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": trade.quantity,
                "price": trade.price,
                "timestamp": trade.timestamp.isoformat(),
            }
            for trade in last_trades
        ]

        return jsonify(
            {"pnl": pnl_data, "positions": positions, "recent_trades": recent_trades}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
