"""
Subscription Enforcement System
Handles Pro vs Free plan restrictions for trading functionality.
"""

from functools import wraps
from flask import current_app, g, jsonify, flash, redirect, url_for, request
from flask_login import current_user
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class SubscriptionEnforcer:
    """
    Centralized subscription plan enforcement.
    Ensures Pro features are only available to Pro subscribers.
    """

    @staticmethod
    def get_user_plan_info(user_id: int) -> Dict[str, Any]:
        """Get comprehensive user plan information"""
        try:
            from ..models import User, Subscription, UserPreferences
            from sqlalchemy.orm import joinedload

            user = User.query.options(
                joinedload(User.subscription), joinedload(User.preferences)
            ).get(user_id)

            if not user:
                return {"plan": "free", "active": False, "trading_mode": "paper"}

            # Get subscription info
            subscription = user.subscription
            if subscription and subscription.is_active and subscription.plan == "pro":
                plan_info = {
                    "plan": "pro",
                    "active": True,
                    "start_date": subscription.start_date,
                    "end_date": subscription.end_date,
                    "days_remaining": None,
                }

                if subscription.end_date:
                    days_remaining = (subscription.end_date - datetime.utcnow()).days
                    plan_info["days_remaining"] = max(0, days_remaining)

            else:
                plan_info = {
                    "plan": "free",
                    "active": True,
                    "start_date": None,
                    "end_date": None,
                    "days_remaining": None,
                }

            # Get trading preferences
            preferences = user.preferences
            if preferences:
                plan_info["trading_mode"] = preferences.trading_mode
                plan_info["default_exchange_type"] = preferences.default_exchange_type
                plan_info["risk_level"] = preferences.risk_level
                plan_info["max_position_size"] = preferences.max_position_size
                plan_info["daily_loss_limit"] = preferences.daily_loss_limit
            else:
                plan_info.update(
                    {
                        "trading_mode": "paper",
                        "default_exchange_type": "stocks",
                        "risk_level": "medium",
                        "max_position_size": 10000.0,
                        "daily_loss_limit": 5000.0,
                    }
                )

            return plan_info

        except Exception as e:
            current_app.logger.error(f"Failed to get plan info for user {user_id}: {e}")
            return {"plan": "free", "active": False, "trading_mode": "paper"}

    @staticmethod
    def can_access_live_trading(user_id: int) -> Dict[str, Any]:
        """Check if user can access live trading"""
        plan_info = SubscriptionEnforcer.get_user_plan_info(user_id)

        # Pro plan required for live trading
        if plan_info["plan"] != "pro" or not plan_info["active"]:
            return {
                "allowed": False,
                "reason": "Pro subscription required for live trading",
                "upgrade_required": True,
            }

        # Check if subscription is expiring soon
        if plan_info["days_remaining"] is not None and plan_info["days_remaining"] <= 3:
            return {
                "allowed": True,
                "warning": f"Subscription expires in {plan_info['days_remaining']} days",
                "renewal_required": True,
            }

        return {"allowed": True}

    @staticmethod
    def can_place_order(user_id: int, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check if user can place a specific order"""
        plan_info = SubscriptionEnforcer.get_user_plan_info(user_id)

        # Check if it's a live order
        is_live_order = not order_payload.get("is_paper", False)

        if is_live_order:
            live_check = SubscriptionEnforcer.can_access_live_trading(user_id)
            if not live_check["allowed"]:
                return live_check

        # Check daily order limits
        order_limits = SubscriptionEnforcer.get_daily_limits(user_id)
        current_orders = SubscriptionEnforcer.get_daily_order_count(user_id)

        if current_orders >= order_limits["max_orders_per_day"]:
            return {
                "allowed": False,
                "reason": f"Daily order limit reached ({order_limits['max_orders_per_day']})",
                "upgrade_required": plan_info["plan"] == "free",
            }

        # Check position size limits
        order_value = float(order_payload.get("quantity", 0)) * float(
            order_payload.get("price", 0)
        )
        if order_value > plan_info["max_position_size"]:
            return {
                "allowed": False,
                "reason": f"Order value exceeds position size limit (₹{plan_info['max_position_size']:,.0f})",
                "upgrade_required": plan_info["plan"] == "free",
            }

        return {"allowed": True}

    @staticmethod
    def get_daily_limits(user_id: int) -> Dict[str, int]:
        """Get daily trading limits based on subscription plan"""
        plan_info = SubscriptionEnforcer.get_user_plan_info(user_id)

        if plan_info["plan"] == "pro":
            return {
                "max_orders_per_day": 1000,
                "max_strategies": 50,
                "max_positions": 100,
            }
        else:
            return {"max_orders_per_day": 50, "max_strategies": 3, "max_positions": 10}

    @staticmethod
    def get_daily_order_count(user_id: int) -> int:
        """Get today's order count for user"""
        try:
            from ..models import Order
            from sqlalchemy import func

            today = datetime.now().date()

            count = Order.query.filter(
                Order.user_id == user_id, func.date(Order.created_at) == today
            ).count()

            return count

        except Exception as e:
            current_app.logger.error(f"Failed to get daily order count: {e}")
            return 0

    @staticmethod
    def get_feature_access(user_id: int) -> Dict[str, bool]:
        """Get feature access matrix for user"""
        plan_info = SubscriptionEnforcer.get_user_plan_info(user_id)
        is_pro = plan_info["plan"] == "pro" and plan_info["active"]

        return {
            "live_trading": is_pro,
            "advanced_strategies": is_pro,
            "analytics_dashboard": is_pro,
            "api_access": is_pro,
            "priority_support": is_pro,
            "custom_indicators": is_pro,
            "backtesting": is_pro,
            "paper_trading": True,  # Always available
            "basic_strategies": True,  # Always available
            "portfolio_view": True,  # Always available
        }


def require_pro_plan(f):
    """Decorator to enforce Pro plan requirement"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return (
                    jsonify({"success": False, "message": "Authentication required"}),
                    401,
                )
            return redirect(url_for("auth.login"))

        access_check = SubscriptionEnforcer.can_access_live_trading(current_user.id)
        if not access_check["allowed"]:
            if request.is_json:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": access_check["reason"],
                            "upgrade_required": access_check.get(
                                "upgrade_required", False
                            ),
                        }
                    ),
                    403,
                )
            flash(access_check["reason"], "warning")
            return redirect(url_for("payments.upgrade"))

        # Set warning if subscription expiring
        if access_check.get("warning"):
            g.subscription_warning = access_check["warning"]

        return f(*args, **kwargs)

    return decorated_function


def require_plan_features(*required_features):
    """Decorator to check specific feature access"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return (
                        jsonify(
                            {"success": False, "message": "Authentication required"}
                        ),
                        401,
                    )
                return redirect(url_for("auth.login"))

            features = SubscriptionEnforcer.get_feature_access(current_user.id)

            for feature in required_features:
                if not features.get(feature, False):
                    if request.is_json:
                        return (
                            jsonify(
                                {
                                    "success": False,
                                    "message": f"Pro subscription required for {feature.replace('_', ' ')}",
                                    "upgrade_required": True,
                                }
                            ),
                            403,
                        )
                    flash(
                        f"Pro subscription required for {feature.replace('_', ' ')}",
                        "warning",
                    )
                    return redirect(url_for("payments.upgrade"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def enforce_trading_limits(order_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate order against trading limits"""
    if not current_user.is_authenticated:
        return {"success": False, "message": "Authentication required"}

    check_result = SubscriptionEnforcer.can_place_order(current_user.id, order_payload)

    if not check_result["allowed"]:
        return {
            "success": False,
            "message": check_result["reason"],
            "upgrade_required": check_result.get("upgrade_required", False),
        }

    return None  # No restrictions


def get_plan_summary(user_id: int) -> Dict[str, Any]:
    """Get comprehensive plan summary for UI display"""
    plan_info = SubscriptionEnforcer.get_user_plan_info(user_id)
    features = SubscriptionEnforcer.get_feature_access(user_id)
    limits = SubscriptionEnforcer.get_daily_limits(user_id)

    return {
        "plan": plan_info,
        "features": features,
        "limits": limits,
        "current_usage": {
            "orders_today": SubscriptionEnforcer.get_daily_order_count(user_id),
            "max_orders": limits["max_orders_per_day"],
        },
    }
