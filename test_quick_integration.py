#!/usr/bin/env python3
"""
Quick Integration Test for Trade Mantra Enhanced System
Tests all 6 enhanced modules with correct method names
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import create_app, db
from app.models import User, TradingBotStatus


def test_enhanced_features():
    """Test that all enhanced features are functional"""
    try:
        app = create_app("development")  # Use development config for MySQL
        with app.app_context():
            print("🔗 Testing Enhanced Features Integration...")

            print("   🎯 Testing Subscription Manager...")
            from app.utils.enhanced_subscription_manager import (
                EnhancedSubscriptionManager,
            )

            sm = EnhancedSubscriptionManager()
            tiers = sm.get_all_tiers()
            print(f"     ✅ Subscription tiers available ({len(tiers)} tiers)")

            print("   🤖 Testing AI Engine...")
            from app.strategies.ai_trading_engine import AITradingEngine

            ai_engine = AITradingEngine()
            signals = ai_engine.generate_trading_signals()
            print(f"     ✅ AI signals generated ({len(signals)} signals)")

            print("   🏪 Testing Marketplace...")
            from app.marketplace.strategy_marketplace import StrategyMarketplace

            marketplace = StrategyMarketplace()
            strategies = marketplace.get_available_strategies()
            print(
                f"     ✅ Marketplace strategies available ({len(strategies)} strategies)"
            )

            print("   👥 Testing Social Trading...")
            from app.social.copy_trading_platform import CopyTradingPlatform

            social = CopyTradingPlatform()
            traders = social.get_top_traders()
            print(
                f"     ✅ Social trading platform functional ({len(traders)} traders)"
            )

            print("   ⚠️ Testing Risk Management...")
            from app.compliance.risk_management import RiskManager

            risk_mgr = RiskManager()
            risk_metrics = risk_mgr.calculate_portfolio_risk(user_id=1, positions=[])
            print(f"     ✅ Risk metrics calculated (VaR: {risk_metrics['var']}%)")

            print("   📊 Testing Reporting Engine...")
            from app.analytics.reporting_engine import ReportingEngine

            reporter = ReportingEngine()
            report = reporter.generate_performance_report(user_id=1)
            print(f"     ✅ Performance reports generated ({len(report)} metrics)")

            print("   🎉 All enhanced features integrated successfully!")
            return True

    except Exception as e:
        print(f"   ❌ Enhanced features test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_quick_demo():
    """Run a quick demo of all integrated features"""
    try:
        app = create_app("development")  # Use development config for MySQL
        with app.app_context():
            print("\n📋 TRADE MANTRA QUICK DEMO")
            print("=" * 40)

            # Subscription Demo
            from app.utils.enhanced_subscription_manager import (
                EnhancedSubscriptionManager,
            )

            sm = EnhancedSubscriptionManager()
            tiers = sm.get_all_tiers()
            print(f"\n💎 Available Subscription Tiers:")
            for tier in tiers:
                print(f"   • {tier['name']}: ₹{tier['price']}/month")

            # AI Engine Demo
            from app.strategies.ai_trading_engine import AITradingEngine

            ai_engine = AITradingEngine()
            signals = ai_engine.generate_trading_signals()
            print(f"\n🤖 AI Trading Signals:")
            for signal in signals:
                print(
                    f"   • {signal['symbol']}: {signal['action']} (Confidence: {signal['confidence']}%)"
                )

            # Marketplace Demo
            from app.marketplace.strategy_marketplace import StrategyMarketplace

            marketplace = StrategyMarketplace()
            strategies = marketplace.get_available_strategies()
            marketplace_stats = marketplace.get_marketplace_stats()
            print(f"\n🏪 Strategy Marketplace:")
            print(f"   • Available Strategies: {len(strategies)}")
            print(f"   • Platform Revenue: ₹{marketplace_stats['total_revenue']:,.2f}")

            # Social Trading Demo
            from app.social.copy_trading_platform import CopyTradingPlatform

            social = CopyTradingPlatform()
            traders = social.get_top_traders()
            print(f"\n👥 Social Trading Platform:")
            print(f"   • Total Traders: {len(traders)}")

            # Risk Management Demo
            from app.compliance.risk_management import RiskManager

            risk_mgr = RiskManager()
            risk_metrics = risk_mgr.calculate_portfolio_risk(user_id=1, positions=[])
            print(f"\n⚠️ Risk Management:")
            print(f"   • Portfolio VaR: {risk_metrics['var']}%")
            print(f"   • Risk Level: {risk_metrics['risk_level']}")

            # Analytics Demo
            from app.analytics.reporting_engine import ReportingEngine

            reporter = ReportingEngine()
            report = reporter.generate_performance_report(user_id=1)
            print(f"\n📊 Analytics Engine:")
            print(f"   • Report Metrics: {len(report)}")

            print(f"\n🚀 System Status: FULLY INTEGRATED")
            print(f"✅ All 6 enhanced modules operational!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Trade Mantra Enhanced Features Test")
    print("=" * 50)

    # Test enhanced features integration
    if test_enhanced_features():
        print("\n🎉 INTEGRATION SUCCESSFUL!")
        print("📊 All enhanced features functional with MySQL!")
        run_quick_demo()
    else:
        print("\n❌ Integration test failed")
