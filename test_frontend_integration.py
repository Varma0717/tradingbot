#!/usr/bin/env python3
"""
Test Enhanced Frontend Implementation
"""

from app import create_app

app = create_app()
with app.app_context():
    print("🚀 Testing Enhanced Frontend Implementation")
    print("=" * 60)

    # Test if templates exist
    import os

    template_dir = "app/templates/user"
    templates = [
        "dashboard.html",
        "portfolio.html",
        "analytics.html",
        "automation.html",
    ]

    for template in templates:
        template_path = os.path.join(template_dir, template)
        if os.path.exists(template_path):
            print(f"✅ Template exists: {template}")
        else:
            print(f"❌ Template missing: {template}")

    # Test backend integration
    try:
        from app.utils.portfolio_manager import PortfolioManager
        from app.utils.subscription_enforcer import get_plan_summary

        # Test with user ID 1 (should exist from our tests)
        portfolio_manager = PortfolioManager(1)
        portfolio_data = portfolio_manager.get_comprehensive_portfolio()
        plan_summary = get_plan_summary(1)

        print(f"✅ Portfolio Manager works: {len(portfolio_data)} keys")
        print(
            f'✅ Subscription Enforcer works: plan = {plan_summary.get("plan", "unknown")}'
        )
        print("✅ Backend integration successful!")

        # Test data structure
        print("\n📊 Portfolio Data Structure:")
        if portfolio_data:
            print(f'  - Summary: {list(portfolio_data.get("summary", {}).keys())}')
            print(f'  - Positions: {len(portfolio_data.get("positions", []))}')
            print(f'  - Recent trades: {len(portfolio_data.get("recent_trades", []))}')
            print(
                f'  - Performance metrics: {list(portfolio_data.get("performance", {}).keys())}'
            )

        print("\n💳 Plan Summary:")
        if plan_summary:
            print(f'  - Plan: {plan_summary.get("plan", "unknown")}')
            print(
                f'  - Live trading: {plan_summary.get("live_trading_enabled", False)}'
            )
            print(
                f'  - Daily orders: {plan_summary.get("orders_today", 0)}/{plan_summary.get("daily_order_limit", 0)}'
            )

    except Exception as e:
        print(f"❌ Backend integration error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ Frontend implementation test completed!")
