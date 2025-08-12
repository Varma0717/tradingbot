"""
Enhanced Subscription Tiers for Trade Mantra
Multi-tier value ladder with real profit-maximizing features
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SubscriptionTier(Enum):
    """Enhanced subscription tiers for maximum user value"""

    STARTER = "starter"  # Free
    TRADER = "trader"  # ₹999/month
    PRO = "pro"  # ₹2,999/month
    ELITE = "elite"  # ₹9,999/month
    INSTITUTIONAL = "institutional"  # ₹25,000/month


@dataclass
class TierLimits:
    """Limits and features for each subscription tier"""

    max_capital: int
    max_strategies: int
    max_positions: int
    max_daily_trades: int
    live_trading: bool
    ai_strategies: bool
    priority_support: bool
    custom_strategies: bool
    api_access: bool
    profit_sharing_rate: float
    success_fee: int  # per profitable trade
    monthly_maintenance: int


class EnhancedSubscriptionManager:
    """Manages enhanced subscription tiers and features"""

    TIER_LIMITS = {
        SubscriptionTier.STARTER: TierLimits(
            max_capital=10_000,
            max_strategies=3,
            max_positions=5,
            max_daily_trades=10,
            live_trading=False,
            ai_strategies=False,
            priority_support=False,
            custom_strategies=False,
            api_access=False,
            profit_sharing_rate=0.0,
            success_fee=0,
            monthly_maintenance=0,
        ),
        SubscriptionTier.TRADER: TierLimits(
            max_capital=50_000,
            max_strategies=10,
            max_positions=20,
            max_daily_trades=50,
            live_trading=True,
            ai_strategies=False,
            priority_support=False,
            custom_strategies=False,
            api_access=False,
            profit_sharing_rate=0.10,
            success_fee=100,  # ₹100 per profitable trade
            monthly_maintenance=199,
        ),
        SubscriptionTier.PRO: TierLimits(
            max_capital=200_000,
            max_strategies=25,
            max_positions=50,
            max_daily_trades=200,
            live_trading=True,
            ai_strategies=True,
            priority_support=True,
            custom_strategies=False,
            api_access=False,
            profit_sharing_rate=0.15,
            success_fee=200,
            monthly_maintenance=299,
        ),
        SubscriptionTier.ELITE: TierLimits(
            max_capital=1_000_000,
            max_strategies=50,
            max_positions=100,
            max_daily_trades=1000,
            live_trading=True,
            ai_strategies=True,
            priority_support=True,
            custom_strategies=True,
            api_access=True,
            profit_sharing_rate=0.20,
            success_fee=500,
            monthly_maintenance=999,
        ),
        SubscriptionTier.INSTITUTIONAL: TierLimits(
            max_capital=10_000_000,
            max_strategies=100,
            max_positions=500,
            max_daily_trades=10000,
            live_trading=True,
            ai_strategies=True,
            priority_support=True,
            custom_strategies=True,
            api_access=True,
            profit_sharing_rate=0.25,
            success_fee=1000,
            monthly_maintenance=2999,
        ),
    }

    TIER_PRICES = {
        SubscriptionTier.STARTER: 0,
        SubscriptionTier.TRADER: 99900,  # ₹999 in paise
        SubscriptionTier.PRO: 299900,  # ₹2,999 in paise
        SubscriptionTier.ELITE: 999900,  # ₹9,999 in paise
        SubscriptionTier.INSTITUTIONAL: 2500000,  # ₹25,000 in paise
    }

    def __init__(self):
        """Initialize the subscription manager"""
        self.tier_configs = self._initialize_tier_configs()

    def _initialize_tier_configs(self):
        """Initialize tier configurations for easy access"""
        return {
            SubscriptionTier.STARTER: {
                "name": "Starter",
                "price": 0,
                "features": ["basic_strategies", "paper_trading"],
            },
            SubscriptionTier.TRADER: {
                "name": "Basic",
                "price": 999,
                "features": [
                    "basic_strategies",
                    "paper_trading",
                    "live_trading",
                    "basic_analytics",
                ],
            },
            SubscriptionTier.PRO: {
                "name": "Pro",
                "price": 2999,
                "features": [
                    "all_strategies",
                    "ai_signals",
                    "risk_management",
                    "advanced_analytics",
                ],
            },
            SubscriptionTier.ELITE: {
                "name": "Premium",
                "price": 9999,
                "features": [
                    "all_features",
                    "priority_support",
                    "custom_strategies",
                    "api_access",
                ],
            },
            SubscriptionTier.INSTITUTIONAL: {
                "name": "Institutional",
                "price": 25000,
                "features": [
                    "enterprise_features",
                    "dedicated_support",
                    "custom_integration",
                ],
            },
        }

    def get_all_tiers(self):
        """Get all available subscription tiers"""
        return [
            {
                "name": config["name"],
                "price": config["price"],
                "features": config["features"],
                "tier": tier.value,
            }
            for tier, config in self.tier_configs.items()
        ]

    def get_subscription_status(self, user_id: str):
        """Get current subscription status for user"""
        # In production, this would query the database
        return {
            "user_id": user_id,
            "current_tier": "pro",
            "expires_at": "2024-12-31",
            "auto_renew": True,
            "next_billing": "2024-09-12",
        }

    def upgrade_subscription(self, user_id: str, tier: str):
        """Upgrade user subscription"""
        # In production, this would handle payment and database update
        return {
            "user_id": user_id,
            "new_tier": tier,
            "upgrade_date": "2024-08-12",
            "next_billing": "2024-09-12",
            "success": True,
        }

    @classmethod
    def get_tier_limits(cls, tier: SubscriptionTier) -> TierLimits:
        """Get limits for a specific tier"""
        return cls.TIER_LIMITS[tier]

    @classmethod
    def get_tier_price(cls, tier: SubscriptionTier) -> int:
        """Get price in paise for a specific tier"""
        return cls.TIER_PRICES[tier]

    @classmethod
    def can_access_feature(cls, user_tier: SubscriptionTier, feature: str) -> bool:
        """Check if user can access a specific feature"""
        limits = cls.get_tier_limits(user_tier)

        feature_map = {
            "live_trading": limits.live_trading,
            "ai_strategies": limits.ai_strategies,
            "priority_support": limits.priority_support,
            "custom_strategies": limits.custom_strategies,
            "api_access": limits.api_access,
        }

        return feature_map.get(feature, False)

    @classmethod
    def validate_trade_limits(
        cls,
        user_tier: SubscriptionTier,
        capital: int,
        daily_trades: int,
        active_positions: int,
    ) -> Dict[str, bool]:
        """Validate if trade is within tier limits"""
        limits = cls.get_tier_limits(user_tier)

        return {
            "capital_valid": capital <= limits.max_capital,
            "trades_valid": daily_trades < limits.max_daily_trades,
            "positions_valid": active_positions < limits.max_positions,
            "can_trade": all(
                [
                    capital <= limits.max_capital,
                    daily_trades < limits.max_daily_trades,
                    active_positions < limits.max_positions,
                ]
            ),
        }

    @classmethod
    def calculate_fees(
        cls, user_tier: SubscriptionTier, profit: float, is_profitable_trade: bool
    ) -> Dict[str, float]:
        """Calculate performance-based fees"""
        limits = cls.get_tier_limits(user_tier)

        fees = {
            "profit_sharing": 0.0,
            "success_fee": 0.0,
            "monthly_maintenance": limits.monthly_maintenance,
            "total_fees": limits.monthly_maintenance,
        }

        if profit > 0:
            # Profit sharing
            fees["profit_sharing"] = profit * limits.profit_sharing_rate
            fees["total_fees"] += fees["profit_sharing"]

        if is_profitable_trade and profit > 1000:  # Minimum ₹1000 profit
            # Success fee
            fees["success_fee"] = limits.success_fee
            fees["total_fees"] += fees["success_fee"]

        return fees

    @classmethod
    def get_upgrade_suggestions(
        cls, current_tier: SubscriptionTier, usage_stats: Dict
    ) -> List[Dict]:
        """Suggest upgrades based on usage patterns"""
        suggestions = []
        current_limits = cls.get_tier_limits(current_tier)

        # Check if user is hitting limits
        if usage_stats.get("capital_used", 0) > current_limits.max_capital * 0.8:
            next_tier = cls._get_next_tier(current_tier)
            if next_tier:
                suggestions.append(
                    {
                        "reason": "capital_limit",
                        "message": f"Upgrade to {next_tier.value.title()} for higher capital limits",
                        "suggested_tier": next_tier,
                        "benefit": f"Increase capital limit to ₹{cls.get_tier_limits(next_tier).max_capital:,}",
                    }
                )

        if usage_stats.get("daily_trades", 0) > current_limits.max_daily_trades * 0.8:
            next_tier = cls._get_next_tier(current_tier)
            if next_tier:
                suggestions.append(
                    {
                        "reason": "trade_limit",
                        "message": f"Upgrade to {next_tier.value.title()} for more daily trades",
                        "suggested_tier": next_tier,
                        "benefit": f"Increase daily trades to {cls.get_tier_limits(next_tier).max_daily_trades}",
                    }
                )

        if not current_limits.live_trading and usage_stats.get(
            "wants_live_trading", False
        ):
            next_tier = cls._get_next_tier(current_tier)
            if next_tier:
                suggestions.append(
                    {
                        "reason": "live_trading",
                        "message": f"Upgrade to {next_tier.value.title()} to start live trading",
                        "suggested_tier": next_tier,
                        "benefit": "Start making real money with live trading",
                    }
                )

        return suggestions

    @classmethod
    def _get_next_tier(
        cls, current_tier: SubscriptionTier
    ) -> Optional[SubscriptionTier]:
        """Get the next tier for upgrade"""
        tier_order = [
            SubscriptionTier.STARTER,
            SubscriptionTier.TRADER,
            SubscriptionTier.PRO,
            SubscriptionTier.ELITE,
            SubscriptionTier.INSTITUTIONAL,
        ]

        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass

        return None


class PerformanceBasedRevenue:
    """Manages performance-based revenue calculations"""

    @staticmethod
    def calculate_monthly_fees(
        user_tier: SubscriptionTier, monthly_trades: List[Dict]
    ) -> Dict[str, float]:
        """Calculate total monthly fees for a user"""
        limits = EnhancedSubscriptionManager.get_tier_limits(user_tier)

        total_profit = sum(trade.get("profit", 0) for trade in monthly_trades)
        profitable_trades = len(
            [t for t in monthly_trades if t.get("profit", 0) > 1000]
        )

        fees = {
            "subscription_fee": EnhancedSubscriptionManager.get_tier_price(user_tier)
            / 100,
            "profit_sharing": max(0, total_profit * limits.profit_sharing_rate),
            "success_fees": profitable_trades * limits.success_fee,
            "maintenance_fee": limits.monthly_maintenance,
            "total_revenue": 0,
        }

        fees["total_revenue"] = sum(fees.values())

        return fees

    @staticmethod
    def calculate_platform_revenue(all_users_data: List[Dict]) -> Dict[str, float]:
        """Calculate total platform revenue"""
        total_revenue = {
            "subscription_revenue": 0,
            "profit_sharing_revenue": 0,
            "success_fee_revenue": 0,
            "maintenance_revenue": 0,
            "total_monthly_revenue": 0,
        }

        for user_data in all_users_data:
            user_fees = PerformanceBasedRevenue.calculate_monthly_fees(
                user_data["tier"], user_data["monthly_trades"]
            )

            total_revenue["subscription_revenue"] += user_fees["subscription_fee"]
            total_revenue["profit_sharing_revenue"] += user_fees["profit_sharing"]
            total_revenue["success_fee_revenue"] += user_fees["success_fees"]
            total_revenue["maintenance_revenue"] += user_fees["maintenance_fee"]

        total_revenue["total_monthly_revenue"] = sum(
            [
                total_revenue["subscription_revenue"],
                total_revenue["profit_sharing_revenue"],
                total_revenue["success_fee_revenue"],
                total_revenue["maintenance_revenue"],
            ]
        )

        return total_revenue


# Example usage and testing
if __name__ == "__main__":
    # Test tier features
    print("=== Enhanced Subscription Tiers ===")

    for tier in SubscriptionTier:
        limits = EnhancedSubscriptionManager.get_tier_limits(tier)
        price = EnhancedSubscriptionManager.get_tier_price(tier)

        print(f"\n{tier.value.upper()} - ₹{price/100:,.0f}/month")
        print(f"  Max Capital: ₹{limits.max_capital:,}")
        print(f"  Max Strategies: {limits.max_strategies}")
        print(f"  Max Positions: {limits.max_positions}")
        print(f"  Live Trading: {limits.live_trading}")
        print(f"  AI Strategies: {limits.ai_strategies}")
        print(f"  Profit Sharing: {limits.profit_sharing_rate*100}%")

    # Test fee calculations
    print("\n=== Fee Calculation Example ===")
    user_tier = SubscriptionTier.PRO
    monthly_profit = 50000
    profitable_trades = 10

    monthly_trades = [
        {"profit": 5000},
        {"profit": 3000},
        {"profit": 7000},
        {"profit": 2000},
        {"profit": 8000},
        {"profit": 1500},
        {"profit": 4000},
        {"profit": 6000},
        {"profit": 2500},
        {"profit": 11000},
    ]

    fees = PerformanceBasedRevenue.calculate_monthly_fees(user_tier, monthly_trades)

    print(f"User Tier: {user_tier.value.title()}")
    print(f"Monthly Profit: ₹{sum(t['profit'] for t in monthly_trades):,}")
    print(f"Total Fees: ₹{fees['total_revenue']:,.2f}")
    print(f"  - Subscription: ₹{fees['subscription_fee']:,.2f}")
    print(f"  - Profit Sharing: ₹{fees['profit_sharing']:,.2f}")
    print(f"  - Success Fees: ₹{fees['success_fees']:,.2f}")
    print(f"  - Maintenance: ₹{fees['maintenance_fee']:,.2f}")
