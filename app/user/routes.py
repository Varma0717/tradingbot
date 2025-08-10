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


@user.route("/analytics")
@login_required
def analytics():
    """Portfolio analytics and performance metrics"""
    # Sample analytics data
    analytics_data = {
        "performance_metrics": {
            "total_return": 28.5,
            "sharpe_ratio": 1.85,
            "max_drawdown": -8.2,
            "win_rate": 68.5,
            "profit_factor": 2.1,
        },
        "monthly_returns": [
            {"month": "Jan", "return": 3.2},
            {"month": "Feb", "return": 5.1},
            {"month": "Mar", "return": -1.8},
            {"month": "Apr", "return": 7.3},
            {"month": "May", "return": 4.6},
            {"month": "Jun", "return": 2.9},
        ],
        "top_performing_strategies": [
            {"name": "Mean Reversion Pro", "return": 15.2, "trades": 45},
            {"name": "Momentum Scalper", "return": 12.8, "trades": 127},
            {"name": "Swing Trader Elite", "return": 8.5, "trades": 23},
        ],
        "risk_metrics": {
            "var_95": 2850,
            "beta": 0.85,
            "volatility": 12.3,
            "correlation_market": 0.72,
        },
    }
    return render_template("user/analytics.html", analytics=analytics_data)


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
                    # Get active positions and recent trades
                    for strategy, position in stock_status.get("positions", {}).items():
                        if position.get("quantity", 0) != 0:
                            stock_sessions.append(
                                {
                                    "strategy_name": strategy.replace("_", " ").title(),
                                    "symbol": position.get("symbol", "UNKNOWN"),
                                    "start_time": stock_status.get(
                                        "start_time", datetime.now().strftime("%H:%M")
                                    ),
                                    "pnl": round(position.get("unrealized_pnl", 0), 2),
                                    "trades_count": stock_status.get("total_trades", 0),
                                    "entry_price": round(
                                        position.get("avg_price", 0), 2
                                    ),
                                    "current_price": round(
                                        position.get("current_price", 0), 2
                                    ),
                                    "quantity": position.get("quantity", 0),
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
                    if strategy_data.get("active_positions"):
                        for position in strategy_data.get("active_positions", []):
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
    """Portfolio overview for automated trading."""
    try:
        from flask import g

        # Get current trading mode from preferences
        trading_mode = getattr(g, "trading_mode", "paper")

        # Filter orders based on trading mode
        base_query_stocks = Order.query.filter_by(
            user_id=current_user.id,
            exchange_type="stocks",
            is_paper=(trading_mode == "paper"),
        )

        base_query_crypto = Order.query.filter_by(
            user_id=current_user.id,
            exchange_type="crypto",
            is_paper=(trading_mode == "paper"),
        )

        # Get both stock and crypto orders for current trading mode
        stock_orders = (
            base_query_stocks.order_by(Order.created_at.desc()).limit(20).all()
        )

        crypto_orders = (
            base_query_crypto.order_by(Order.created_at.desc()).limit(20).all()
        )

        # Calculate portfolio metrics based on trading mode
        total_orders = len(stock_orders) + len(crypto_orders)

        # Portfolio data varies based on trading mode
        if trading_mode == "live":
            portfolio_data = {
                "total_value": 150000.00,
                "daily_pnl": 2500.00,
                "total_pnl": 12500.00,
                "stock_allocation": 60.0,
                "crypto_allocation": 40.0,
                "active_positions": 8,
                "trading_mode": "live",
                "mode_label": "Live Trading",
            }
        else:
            portfolio_data = {
                "total_value": 100000.00,  # Virtual starting amount
                "daily_pnl": 1200.00,  # Simulated gains
                "total_pnl": 5800.00,  # Total simulated P&L
                "stock_allocation": 65.0,
                "crypto_allocation": 35.0,
                "active_positions": 5,
                "trading_mode": "paper",
                "mode_label": "Paper Trading",
            }

        return render_template(
            "user/portfolio.html",
            portfolio=portfolio_data,
            stock_orders=stock_orders,
            crypto_orders=crypto_orders,
            total_orders=total_orders,
        )

    except Exception as e:
        logger.error(f"Error loading portfolio: {e}")
        flash("Error loading portfolio", "error")
        return redirect(url_for("user.dashboard"))


@user.route("/risk-management")
def risk_management():
    """Risk management settings for automated trading."""
    return render_template("user/risk_management.html")


@user.route("/market-research")
def market_research():
    """Market research and analysis tools."""
    return render_template("user/market_research.html")


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
