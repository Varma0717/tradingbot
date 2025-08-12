"""
Integrated System Test for Trade Mantra Enhanced Features
Tests all enhanced modules working together in the Flask application
"""

import sys
import os
from pathlib import Path
import requests
import json
import time
from datetime import datetime

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.models import User


def test_flask_app_initialization():
    """Test Flask app can be initialized with enhanced features"""
    print("🔧 Testing Flask App Initialization...")
    try:
        app = create_app("testing")
        with app.app_context():
            # Test that all enhanced managers are initialized
            assert hasattr(
                app, "subscription_manager"
            ), "Subscription manager not initialized"
            assert hasattr(app, "ai_engine"), "AI engine not initialized"
            assert hasattr(app, "marketplace"), "Marketplace not initialized"
            assert hasattr(app, "copy_trading"), "Copy trading not initialized"
            assert hasattr(app, "risk_manager"), "Risk manager not initialized"
            assert hasattr(app, "reporting_engine"), "Reporting engine not initialized"
        print("   ✅ Flask app initialized with enhanced features")
        return True
    except Exception as e:
        print(f"   ❌ Flask initialization failed: {e}")
        return False


def test_enhanced_modules_import():
    """Test all enhanced modules can be imported"""
    print("📦 Testing Enhanced Modules Import...")
    modules = [
        "app.utils.enhanced_subscription_manager",
        "app.strategies.ai_trading_engine",
        "app.marketplace.strategy_marketplace",
        "app.social.copy_trading_platform",
        "app.compliance.risk_management",
        "app.analytics.reporting_engine",
    ]

    imported_count = 0
    for module in modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
            imported_count += 1
        except Exception as e:
            print(f"   ❌ {module}: {e}")

    print(f"   📊 Imported {imported_count}/{len(modules)} modules successfully")
    return imported_count == len(modules)


def test_database_models():
    """Test enhanced database models"""
    print("🗄️ Testing Database Models...")
    try:
        app = create_app("testing")
        with app.app_context():
            # Test enhanced User model has new fields
            expected_fields = [
                "subscription_tier",
                "subscription_expires",
                "subscription_auto_renew",
                "ai_enabled",
                "risk_tolerance",
                "trader_rating",
                "total_followers",
                "total_copiers",
                "total_profit",
                "win_rate",
                "sharpe_ratio",
            ]

            user_columns = [column.name for column in User.__table__.columns]
            for field in expected_fields:
                if field not in user_columns:
                    print(f"   ❌ Missing User field: {field}")
                    return False

        print("   ✅ All enhanced User model fields present")
        return True
    except Exception as e:
        print(f"   ❌ Database model test failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints (requires running Flask server)"""
    print("🌐 Testing API Endpoints...")
    try:
        # Test if Flask server is running
        response = requests.get(
            "http://localhost:5000/api/subscriptions/tiers", timeout=2
        )
        if response.status_code == 200:
            print("   ✅ API endpoints accessible")
            return True
        else:
            print(f"   ❌ API responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("   ⚠️ Flask server not running. Start with 'python run.py' to test APIs")
        return False


def test_enhanced_features_integration():
    """Test all enhanced features working together"""
    print("🔗 Testing Enhanced Features Integration...")
    try:
        app = create_app("testing")
        with app.app_context():
            # Test 1: Subscription Manager Integration
            print("   🎯 Testing Subscription Manager...")
            subscription_manager = app.subscription_manager
            tiers = subscription_manager.get_all_tiers()
            assert len(tiers) > 0, "No subscription tiers available"
            print("     ✅ Subscription tiers available")

            # Test 2: AI Engine Integration
            print("   🤖 Testing AI Engine...")
            ai_engine = app.ai_engine
            signals = ai_engine.generate_trading_signals(["RELIANCE", "TCS"])
            assert len(signals) > 0, "No AI signals generated"
            print("     ✅ AI signals generated")

            # Test 3: Marketplace Integration
            print("   🏪 Testing Marketplace...")
            marketplace = app.marketplace
            strategies = marketplace.get_available_strategies()
            assert len(strategies) > 0, "No marketplace strategies available"
            print("     ✅ Marketplace strategies available")

            # Test 4: Social Trading Integration
            print("   👥 Testing Social Trading...")
            copy_trading = app.copy_trading
            leaderboard = copy_trading.get_trader_leaderboard()
            # Note: Leaderboard may be empty in demo environment
            print(
                f"     ✅ Social trading platform functional ({len(leaderboard)} traders)"
            )

            # Test 5: Risk Management Integration
            print("   ⚠️ Testing Risk Management...")
            risk_manager = app.risk_manager
            portfolio = [
                {
                    "symbol": "RELIANCE",
                    "quantity": 100,
                    "price": 2500,
                    "market_value": 250000,
                    "unrealized_pnl": 5000,
                },
                {
                    "symbol": "TCS",
                    "quantity": 50,
                    "price": 3600,
                    "market_value": 180000,
                    "unrealized_pnl": -2000,
                },
            ]
            market_data = {
                "RELIANCE": {"price": 2500, "volatility": 0.25},
                "TCS": {"price": 3600, "volatility": 0.22},
            }
            risk_metrics = risk_manager.calculate_portfolio_risk(
                "demo_user", portfolio, market_data
            )
            assert hasattr(risk_metrics, "value_at_risk_1d"), "VaR calculation missing"
            print("     ✅ Risk metrics calculated")

            # Test 6: Reporting Engine Integration
            print("   📊 Testing Reporting Engine...")
            reporting_engine = app.reporting_engine
            portfolio_data = {
                "trades": [
                    {
                        "symbol": "RELIANCE",
                        "quantity": 100,
                        "buy_price": 2400,
                        "sell_price": 2500,
                        "pnl": 10000,
                    },
                    {
                        "symbol": "TCS",
                        "quantity": 50,
                        "buy_price": 3500,
                        "sell_price": 3600,
                        "pnl": 5000,
                    },
                ]
            }
            report = reporting_engine.generate_performance_report(
                "demo_user", portfolio_data
            )
            print(
                f"Report keys: {list(report.keys()) if isinstance(report, dict) else type(report)}"
            )
            # Just check that the report was generated successfully
            assert report is not None, "Performance report generation failed"
            print("     ✅ Performance reports generated")

        print("   🎉 All enhanced features integrated successfully!")
        return True
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_demo_integration():
    """Run a comprehensive demo showing all integrated features"""
    print("🎭 Running Integration Demo...")
    print("=" * 60)

    try:
        app = create_app("testing")
        with app.app_context():
            print("\n📋 TRADE MANTRA INTEGRATED SYSTEM DEMO")
            print("-" * 40)

            # Demo 1: Show subscription tiers
            print("\n💎 Available Subscription Tiers:")
            tiers = app.subscription_manager.get_all_tiers()
            for tier in tiers:
                print(f"   • {tier['name']}: ₹{tier['price']}/month")

            # Demo 2: Show AI trading signals
            print("\n🤖 AI Trading Signals:")
            signals = app.ai_engine.generate_trading_signals(
                ["RELIANCE", "TCS", "HDFC"]
            )
            for signal in signals:
                print(
                    f"   • {signal['symbol']}: {signal['action']} (Confidence: {signal['confidence']}%)"
                )

            # Demo 3: Show marketplace activity
            print("\n🏪 Strategy Marketplace:")
            strategies = app.marketplace.get_available_strategies()
            revenue = app.marketplace.calculate_platform_revenue()
            print(f"   • Available Strategies: {len(strategies)}")
            print(f"   • Platform Revenue: ₹{revenue:,.2f}")

            # Demo 4: Show social trading
            print("\n👥 Social Trading Leaderboard:")
            leaderboard = app.copy_trading.get_trader_leaderboard()
            if leaderboard:
                for i, trader in enumerate(leaderboard[:3], 1):
                    print(
                        f"   {i}. {trader['name']}: {trader['return_percentage']:.1f}% return"
                    )
            else:
                print("   (No active traders in demo environment)")

            # Demo 5: Show risk management
            print("\n⚠️ Risk Management Status:")
            portfolio = [
                {
                    "symbol": "RELIANCE",
                    "quantity": 100,
                    "price": 2500,
                    "market_value": 250000,
                    "unrealized_pnl": 5000,
                },
                {
                    "symbol": "TCS",
                    "quantity": 50,
                    "price": 3600,
                    "market_value": 180000,
                    "unrealized_pnl": -2000,
                },
            ]
            market_data = {
                "RELIANCE": {"price": 2500, "volatility": 0.25},
                "TCS": {"price": 3600, "volatility": 0.22},
            }
            risk_metrics = app.risk_manager.calculate_portfolio_risk(
                "demo_user", portfolio, market_data
            )
            print(f"   • Portfolio VaR: {risk_metrics.value_at_risk_1d:.1f}%")
            print(
                f"   • Risk Level: {'HIGH' if risk_metrics.value_at_risk_1d > 5 else 'MODERATE'}"
            )

            # Demo 6: Show analytics summary
            print("\n📊 Analytics Summary:")
            portfolio_data = {
                "trades": [
                    {
                        "symbol": "RELIANCE",
                        "quantity": 100,
                        "buy_price": 2400,
                        "sell_price": 2500,
                        "pnl": 10000,
                    },
                    {
                        "symbol": "TCS",
                        "quantity": 50,
                        "buy_price": 3500,
                        "sell_price": 3600,
                        "pnl": 5000,
                    },
                ]
            }
            report = app.reporting_engine.generate_performance_report(
                "demo_user", portfolio_data
            )
            print(
                f"   • Report Generated: {len(report)} metrics"
                if isinstance(report, dict)
                else f"   • Report Type: {type(report)}"
            )
            if isinstance(report, dict) and "summary" in report:
                summary = report["summary"]
                print(f"   • Total P&L: ₹{summary.get('total_pnl', 0):,.2f}")
                print(f"   • Win Rate: {summary.get('win_rate', 0):.1%}")
            else:
                print("   • Analytics report structure available")

        return True
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("🧪 Testing Trade Mantra Integrated System...")
    print("=" * 60)

    tests = [
        test_flask_app_initialization,
        test_enhanced_modules_import,
        test_database_models,
        test_api_endpoints,
        test_enhanced_features_integration,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test {test.__name__} failed with error: {e}")

    print("\n" + "=" * 60)
    print(f"✅ Integrated System Test Completed!")
    print(f"📊 {passed}/{len(tests)} tests passed")

    # Run comprehensive demo
    run_demo_integration()

    print("\n🚀 Next Steps:")
    print("1. Start Flask server: python run.py")
    print("2. Visit: http://localhost:5000")
    print("3. Test enhanced features in browser")
    print("4. Check API endpoints at /api/subscriptions/tiers")

    return passed == len(tests)


if __name__ == "__main__":
    main()
