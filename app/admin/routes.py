import os
from flask import (
    Blueprint,
    render_template,
    current_app,
    abort,
    flash,
    redirect,
    url_for,
)
from flask_login import login_required
from ..utils.helpers import admin_required
from ..models import User, Subscription, Payment, AuditLog
from .. import db

admin = Blueprint("admin", __name__)


@admin.before_request
@login_required
@admin_required
def before_request():
    """Protect all admin routes."""
    pass


@admin.route("/")
def dashboard():
    from datetime import datetime, timedelta
    from collections import defaultdict

    # Basic user metrics
    user_count = User.query.count()

    # Users registered today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_users_today = User.query.filter(User.created_at >= today_start).count()

    # Active users in last 24 hours (users with recent login)
    yesterday = datetime.now() - timedelta(days=1)
    active_users_24h = (
        User.query.filter(User.last_seen >= yesterday).count()
        if hasattr(User, "last_seen")
        else 0
    )

    # Subscription distribution
    subscription_distribution = defaultdict(int)
    for user in User.query.all():
        tier = getattr(user, "subscription_tier", "starter") or "starter"
        subscription_distribution[tier] += 1

    # Active subscriptions (non-starter tiers)
    active_subscriptions = sum(
        count for tier, count in subscription_distribution.items() if tier != "starter"
    )

    # Revenue metrics
    total_payments = (
        db.session.query(db.func.sum(Payment.amount))
        .filter(Payment.status == "captured")
        .scalar()
        or 0
    )

    # Monthly recurring revenue calculation
    monthly_revenue = 0
    mrr = 0
    for tier, count in subscription_distribution.items():
        tier_prices = {
            "starter": 0,
            "basic": 999,
            "pro": 2999,
            "premium": 9999,
            "institutional": 25000,
        }
        monthly_revenue += count * tier_prices.get(tier, 0)
        if tier != "starter":
            mrr += count * tier_prices.get(tier, 0)

    # Average revenue per user
    arpu = monthly_revenue / user_count if user_count > 0 else 0

    # Mock system alerts (in real implementation, get from monitoring system)
    system_alerts = 2
    critical_alerts = 0

    # Mock churn rate (in real implementation, calculate from cancellations)
    churn_rate = 2.3

    # Mock login sessions (in real implementation, get from session tracking)
    login_sessions_24h = user_count * 2  # Rough estimate

    # Recent administrative actions (mock data - in real implementation, get from audit log)
    recent_admin_actions = [
        {
            "description": "Updated subscription pricing tiers",
            "admin_user": "admin",
            "timestamp": datetime.now() - timedelta(hours=2),
            "type_color": "blue",
        },
        {
            "description": "Activated new user verification system",
            "admin_user": "admin",
            "timestamp": datetime.now() - timedelta(hours=5),
            "type_color": "green",
        },
        {
            "description": "Database maintenance completed",
            "admin_user": "system",
            "timestamp": datetime.now() - timedelta(hours=8),
            "type_color": "yellow",
        },
    ]

    return render_template(
        "admin/enhanced_dashboard.html",
        title="Admin Control Center",
        user_count=user_count,
        new_users_today=new_users_today,
        active_users_24h=active_users_24h,
        subscription_distribution=dict(subscription_distribution),
        active_subscriptions=active_subscriptions,
        monthly_revenue=monthly_revenue,
        mrr=mrr,
        arpu=arpu,
        system_alerts=system_alerts,
        critical_alerts=critical_alerts,
        churn_rate=churn_rate,
        login_sessions_24h=login_sessions_24h,
        recent_admin_actions=recent_admin_actions,
    )


@admin.route("/users")
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()

    # Count users registered this month
    from datetime import datetime, timedelta

    current_month = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    recent_users_count = User.query.filter(User.created_at >= current_month).count()

    return render_template(
        "admin/users.html",
        title="Manage Users",
        users=users,
        recent_users_count=recent_users_count,
    )


@admin.route("/user/<int:user_id>/toggle_plan")
def toggle_user_plan(user_id):
    user = User.query.get_or_404(user_id)
    # This is a simplified toggle. A real app would have more logic.
    if user.subscription:
        if user.subscription.plan == "pro":
            user.subscription.plan = "free"
            flash(f"User {user.username} downgraded to Free plan.", "info")
        else:
            user.subscription.plan = "pro"
            flash(f"User {user.username} upgraded to Pro plan.", "info")
    else:
        # Create a new subscription if none exists
        new_sub = Subscription(user_id=user.id, plan="pro", status="active")
        db.session.add(new_sub)
        flash(f"User {user.username} upgraded to Pro plan.", "info")

    db.session.commit()
    return redirect(url_for("admin.manage_users"))


@admin.route("/logs")
def view_logs():
    if not current_app.config["DEBUG"]:
        abort(404)  # This page is only available in debug mode

    log_file_path = os.path.join(current_app.root_path, "..", "logs", "app_debug.log")
    try:
        with open(log_file_path, "r") as f:
            # Read last 100 lines
            log_lines = f.readlines()[-100:]
            log_content = "".join(reversed(log_lines))
    except FileNotFoundError:
        log_content = "Log file not found."

    return render_template(
        "admin/logs.html", title="System Logs", log_content=log_content
    )


@admin.route("/audit_trail")
def audit_trail():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template("admin/audit_trail.html", title="Audit Trail", logs=logs)


@admin.route("/subscriptions")
def subscription_overview():
    """Manage user subscriptions and billing"""
    from ..models import User, Subscription, Payment

    # Get all subscriptions
    subscriptions_query = Subscription.query.order_by(
        Subscription.created_at.desc()
    ).all()

    # Calculate subscription statistics
    total_revenue = (
        db.session.query(db.func.sum(Payment.amount))
        .filter(Payment.status == "captured")
        .scalar()
        or 0
    )
    active_subscriptions = Subscription.query.filter_by(status="active").count()
    trial_users = Subscription.query.filter_by(plan="free").count()
    total_users = User.query.count()
    conversion_rate = (
        (active_subscriptions / total_users * 100) if total_users > 0 else 0
    )

    # Create subscription_stats dictionary that the template expects
    subscription_stats = {
        "active_subscriptions": active_subscriptions,
        "monthly_revenue": total_revenue,
        "trial_users": trial_users,
        "conversion_rate": conversion_rate,
    }

    # Create plan_stats list that the template expects
    plan_stats = [
        {
            "name": "Free",
            "price": 0,
            "subscribers": Subscription.query.filter_by(plan="free").count(),
        },
        {
            "name": "Pro",
            "price": 2999,
            "subscribers": Subscription.query.filter_by(plan="pro").count(),
        },
    ]

    # Create recent_subscriptions list that the template expects
    recent_subs = (
        Subscription.query.order_by(Subscription.created_at.desc()).limit(5).all()
    )
    recent_subscriptions = []
    for sub in recent_subs:
        recent_subscriptions.append(
            {
                "user_email": sub.user.email,
                "plan_name": sub.plan.title(),
                "amount": 2999 if sub.plan == "pro" else 0,
                "date": sub.created_at.strftime("%b %d, %Y"),
            }
        )

    # Create subscriptions list that the template expects
    subscriptions = []
    for sub in subscriptions_query:
        subscriptions.append(
            {
                "user_name": sub.user.username,
                "user_email": sub.user.email,
                "plan_name": sub.plan.title(),
                "status": sub.status.title(),
                "start_date": sub.start_date.strftime("%b %d, %Y"),
                "next_billing": (
                    sub.end_date.strftime("%b %d, %Y") if sub.end_date else "N/A"
                ),
                "revenue": 2999 if sub.plan == "pro" else 0,
            }
        )

    return render_template(
        "admin/subscription_management.html",
        title="Subscription Management",
        subscription_stats=subscription_stats,
        plan_stats=plan_stats,
        recent_subscriptions=recent_subscriptions,
        subscriptions=subscriptions,
    )


@admin.route("/trading_oversight")
def trading_oversight():
    """Monitor all trading activity across users"""
    from ..models import Order, Strategy

    # Get recent orders across all users
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(100).all()

    # Trading statistics
    total_orders = Order.query.count()
    successful_orders = Order.query.filter_by(status="filled").count()
    total_volume = (
        db.session.query(db.func.sum(Order.quantity * Order.price)).scalar() or 0
    )

    # Active strategies
    active_strategies = Strategy.query.filter_by(is_active=True).count()

    # Create trading statistics object
    trading_stats = {
        "active_trades": total_orders,
        "daily_volume": float(total_volume or 0),
        "success_rate": round((successful_orders / max(total_orders, 1)) * 100, 2),
        "active_strategies": len(active_strategies),
    }

    return render_template(
        "admin/trading_oversight.html",
        title="Trading Oversight",
        recent_orders=recent_orders,
        total_orders=total_orders,
        successful_orders=successful_orders,
        total_volume=total_volume,
        active_strategies=active_strategies,
        trading_stats=trading_stats,
    )


@admin.route("/risk_management")
def risk_management():
    """Risk monitoring and control"""
    # Risk metrics
    high_risk_users = (
        User.query.join(Subscription).filter(Subscription.plan == "pro").limit(10).all()
    )

    risk_alerts = [
        {
            "type": "Position Size",
            "user": "trader1",
            "severity": "High",
            "message": "Position exceeds 5% portfolio limit",
        },
        {
            "type": "Drawdown",
            "user": "investor1",
            "severity": "Medium",
            "message": "Daily drawdown exceeds 2%",
        },
        {
            "type": "Leverage",
            "user": "trader2",
            "severity": "Low",
            "message": "Leverage ratio approaching limit",
        },
    ]

    return render_template(
        "admin/risk_management.html",
        title="Risk Management",
        high_risk_users=high_risk_users,
        risk_alerts=risk_alerts,
    )


@admin.route("/system_health")
def system_health():
    """System monitoring and health checks"""
    import psutil
    import os

    # System metrics
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = (
        psutil.disk_usage("/").percent
        if os.name != "nt"
        else psutil.disk_usage("C:").percent
    )

    # Service status
    services = [
        {"name": "Trading Engine", "status": "Online", "uptime": "99.9%"},
        {"name": "Market Data Feed", "status": "Online", "uptime": "99.8%"},
        {"name": "Order Management", "status": "Online", "uptime": "100%"},
        {"name": "Risk Engine", "status": "Online", "uptime": "99.9%"},
    ]

    return render_template(
        "admin/system_health.html",
        title="System Health",
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
        services=services,
    )


@admin.route("/subscription_management")
def subscription_management():
    """Manage subscription plans and pricing"""
    from collections import defaultdict

    # Get subscription statistics
    subscription_stats = defaultdict(int)
    for user in User.query.all():
        tier = getattr(user, "subscription_tier", "starter") or "starter"
        subscription_stats[tier] += 1

    # Enhanced subscription data with pricing
    subscription_tiers = [
        {
            "name": "Starter",
            "price": 0,
            "users": subscription_stats["starter"],
            "features": ["Basic Trading", "Market Data", "1 Strategy"],
            "monthly_revenue": 0,
        },
        {
            "name": "Basic",
            "price": 999,
            "users": subscription_stats["basic"],
            "features": ["Advanced Trading", "Real-time Data", "5 Strategies"],
            "monthly_revenue": subscription_stats["basic"] * 999,
        },
        {
            "name": "Pro",
            "price": 2999,
            "users": subscription_stats["pro"],
            "features": ["AI Signals", "Risk Management", "15 Strategies"],
            "monthly_revenue": subscription_stats["pro"] * 2999,
        },
        {
            "name": "Premium",
            "price": 9999,
            "users": subscription_stats["premium"],
            "features": ["Copy Trading", "Advanced Analytics", "Unlimited"],
            "monthly_revenue": subscription_stats["premium"] * 9999,
        },
        {
            "name": "Institutional",
            "price": 25000,
            "users": subscription_stats["institutional"],
            "features": ["White Label", "Custom Integration", "Dedicated Support"],
            "monthly_revenue": subscription_stats["institutional"] * 25000,
        },
    ]

    total_mrr = sum(tier["monthly_revenue"] for tier in subscription_tiers)

    return render_template(
        "admin/subscription_management.html",
        title="Subscription Management",
        subscription_tiers=subscription_tiers,
        total_mrr=total_mrr,
    )


@admin.route("/payments_overview")
def payments_overview():
    """Overview of payments and financial metrics"""
    from datetime import datetime, timedelta

    # Payment statistics
    total_payments = Payment.query.filter_by(status="captured").count()
    total_revenue = (
        db.session.query(db.func.sum(Payment.amount))
        .filter(Payment.status == "captured")
        .scalar()
        or 0
    )

    # Recent payments
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(10).all()

    # Monthly revenue trend (mock data)
    monthly_trend = [
        {"month": "Jan", "revenue": 45000},
        {"month": "Feb", "revenue": 52000},
        {"month": "Mar", "revenue": 48000},
        {"month": "Apr", "revenue": 61000},
        {"month": "May", "revenue": 58000},
        {"month": "Jun", "revenue": 67000},
    ]

    return render_template(
        "admin/payments_overview.html",
        title="Payments Overview",
        total_payments=total_payments,
        total_revenue=total_revenue,
        recent_payments=recent_payments,
        monthly_trend=monthly_trend,
    )


@admin.route("/strategy_management")
def strategy_management():
    """Manage and approve trading strategies"""
    from ..models import Strategy

    strategies = Strategy.query.order_by(Strategy.created_at.desc()).all()
    pending_approval = Strategy.query.filter_by(status="pending").count()
    active_strategies = Strategy.query.filter_by(is_active=True).count()

    return render_template(
        "admin/strategy_management.html",
        title="Strategy Management",
        strategies=strategies,
        pending_approval=pending_approval,
        active_strategies=active_strategies,
    )
