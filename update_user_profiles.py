#!/usr/bin/env python3
"""
Update Existing Users with Enhanced Profile Data
Populates all new enhanced User model fields with realistic data
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app, db
from app.models import User, TradingBotStatus


def update_enhanced_user_data():
    """Update existing users with enhanced profile data"""
    app = create_app("development")

    with app.app_context():
        try:
            print("🔄 Updating existing users with enhanced profile data...")

            # Enhanced user profiles with different tiers and characteristics
            enhanced_profiles = {
                "admin": {
                    "subscription_tier": "institutional",
                    "subscription_expires": datetime.now() + timedelta(days=365),
                    "subscription_auto_renew": True,
                    "ai_enabled": True,
                    "risk_tolerance": 0.8,  # High risk tolerance for admin
                    "trader_rating": 4.9,
                    "total_followers": 1250,
                    "total_copiers": 89,
                    "total_profit": 45670.89,
                    "win_rate": 78.5,
                    "sharpe_ratio": 2.34,
                },
                "trader": {
                    "subscription_tier": "pro",
                    "subscription_expires": datetime.now() + timedelta(days=180),
                    "subscription_auto_renew": True,
                    "ai_enabled": True,
                    "risk_tolerance": 0.6,  # Moderate-high risk tolerance
                    "trader_rating": 4.2,
                    "total_followers": 567,
                    "total_copiers": 34,
                    "total_profit": 12340.56,
                    "win_rate": 65.2,
                    "sharpe_ratio": 1.87,
                },
                "testuser": {
                    "subscription_tier": "basic",
                    "subscription_expires": datetime.now() + timedelta(days=30),
                    "subscription_auto_renew": False,
                    "ai_enabled": False,
                    "risk_tolerance": 0.3,  # Conservative risk tolerance
                    "trader_rating": 3.1,
                    "total_followers": 45,
                    "total_copiers": 3,
                    "total_profit": 892.34,
                    "win_rate": 52.1,
                    "sharpe_ratio": 0.95,
                },
            }

            updated_count = 0

            for username, profile_data in enhanced_profiles.items():
                user = User.query.filter_by(username=username).first()
                if user:
                    print(f"\n📝 Updating user: {username}")

                    # Update all enhanced fields
                    for field, value in profile_data.items():
                        setattr(user, field, value)
                        print(f"   ✅ {field}: {value}")

                    updated_count += 1
                else:
                    print(f"   ❌ User {username} not found")

            # Commit all changes
            db.session.commit()
            print(
                f"\n🎉 Successfully updated {updated_count} users with enhanced profiles!"
            )

            return True

        except Exception as e:
            print(f"❌ Failed to update user profiles: {e}")
            db.session.rollback()
            return False


def create_trading_bot_status_records():
    """Create TradingBotStatus records for existing users"""
    app = create_app("development")

    with app.app_context():
        try:
            print("\n🤖 Creating TradingBotStatus records for users...")

            users = User.query.all()
            bot_configs = {
                "admin": {
                    "is_running": True,
                    "bot_type": "stock",
                    "strategies": ["momentum", "mean_reversion", "breakout"],
                    "total_trades": 245,
                    "daily_pnl": 1250.75,
                    "win_rate": 72.5,
                    "open_positions": 8,
                    "strategies_active": 3,
                },
                "trader": {
                    "is_running": True,
                    "bot_type": "stock",
                    "strategies": ["momentum", "rsi_strategy"],
                    "total_trades": 134,
                    "daily_pnl": 567.89,
                    "win_rate": 65.2,
                    "open_positions": 5,
                    "strategies_active": 2,
                },
                "testuser": {
                    "is_running": False,
                    "bot_type": "stock",
                    "strategies": ["simple_moving_average"],
                    "total_trades": 23,
                    "daily_pnl": -45.23,
                    "win_rate": 47.8,
                    "open_positions": 1,
                    "strategies_active": 1,
                },
            }

            created_count = 0

            for user in users:
                # Check if bot status already exists
                existing_bot = TradingBotStatus.query.filter_by(
                    user_id=user.id, bot_type="stock"
                ).first()

                if not existing_bot and user.username in bot_configs:
                    config = bot_configs[user.username]

                    bot_status = TradingBotStatus(
                        user_id=user.id,
                        is_running=config["is_running"],
                        bot_type=config["bot_type"],
                        strategies=config["strategies"],
                        started_at=(
                            datetime.now() - timedelta(hours=6)
                            if config["is_running"]
                            else None
                        ),
                        total_trades=config["total_trades"],
                        daily_pnl=config["daily_pnl"],
                        win_rate=config["win_rate"],
                        open_positions=config["open_positions"],
                        strategies_active=config["strategies_active"],
                        last_heartbeat=datetime.now() if config["is_running"] else None,
                    )

                    db.session.add(bot_status)
                    print(f"   ✅ Created bot status for {user.username}")
                    created_count += 1
                else:
                    print(f"   ⚠️ Bot status already exists for {user.username}")

            db.session.commit()
            print(f"\n🎉 Created {created_count} new TradingBotStatus records!")

            return True

        except Exception as e:
            print(f"❌ Failed to create bot status records: {e}")
            db.session.rollback()
            return False


def display_updated_user_credentials():
    """Display updated user credentials for frontend testing"""
    app = create_app("development")

    with app.app_context():
        try:
            print("\n" + "=" * 60)
            print("🎭 UPDATED USER CREDENTIALS FOR FRONTEND TESTING")
            print("=" * 60)

            users = User.query.all()

            for user in users:
                print(f"\n👤 {user.username.upper()} USER:")
                print(f"   📧 Email: {user.email}")
                print(
                    f"   🔑 Password: password123"
                )  # Standard password for all test users
                print(f"   🎯 Role: {user.username}")
                print(f"   💎 Subscription: {user.subscription_tier}")
                print(f"   🤖 AI Enabled: {'Yes' if user.ai_enabled else 'No'}")
                print(f"   ⚖️ Risk Tolerance: {user.risk_tolerance}")
                print(f"   ⭐ Trader Rating: {user.trader_rating}/5.0")
                print(f"   👥 Followers: {user.total_followers}")
                print(f"   💰 Total Profit: ₹{user.total_profit:,.2f}")
                print(f"   📈 Win Rate: {user.win_rate}%")

                # Check bot status
                bot_status = TradingBotStatus.query.filter_by(user_id=user.id).first()
                if bot_status:
                    print(
                        f"   🤖 Bot Status: {'Running' if bot_status.is_running else 'Stopped'}"
                    )
                    print(f"   📊 Active Strategies: {bot_status.strategies_active}")
                    print(f"   💹 Daily P&L: ₹{bot_status.daily_pnl:,.2f}")

            print(f"\n🌐 ACCESS URLs:")
            print(f"   🏠 Main Dashboard: http://localhost:5000/")
            print(f"   👤 User Dashboard: http://localhost:5000/user/dashboard")
            print(f"   👨‍💼 Admin Dashboard: http://localhost:5000/admin/")
            print(f"   📊 Trading Dashboard: http://localhost:5000/user/automation")
            print(f"   🎯 Login Page: http://localhost:5000/login")

            print(f"\n📋 TESTING CHECKLIST:")
            print(f"   ✅ Enhanced subscription tiers visible")
            print(f"   ✅ AI features enabled for pro/institutional users")
            print(f"   ✅ Social trading stats displayed")
            print(f"   ✅ Risk management settings")
            print(f"   ✅ Bot management interface")
            print(f"   ✅ Performance analytics")

        except Exception as e:
            print(f"❌ Failed to display credentials: {e}")


def reset_user_passwords():
    """Reset all user passwords to 'password123' for easy testing"""
    app = create_app("development")

    with app.app_context():
        try:
            users = User.query.all()
            password_hash = generate_password_hash("password123")

            for user in users:
                user.password_hash = password_hash

            db.session.commit()
            print("🔑 All user passwords reset to 'password123'")
            return True

        except Exception as e:
            print(f"❌ Failed to reset passwords: {e}")
            return False


if __name__ == "__main__":
    print("🚀 TRADE MANTRA USER PROFILE ENHANCEMENT")
    print("=" * 60)

    success = True

    # 1. Reset passwords for easy testing
    if not reset_user_passwords():
        success = False

    # 2. Update users with enhanced profile data
    if not update_enhanced_user_data():
        success = False

    # 3. Create bot status records
    if not create_trading_bot_status_records():
        success = False

    # 4. Display credentials for testing
    display_updated_user_credentials()

    if success:
        print(f"\n🎉 USER PROFILE ENHANCEMENT COMPLETE!")
        print(f"🚀 Ready for frontend testing with enhanced features!")
    else:
        print(f"\n❌ Some operations failed. Check errors above.")
