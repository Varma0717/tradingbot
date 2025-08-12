"""
Strategy Marketplace for Trade Mantra
Revenue-generating platform for strategy creators and consumers
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid
from decimal import Decimal


class StrategyCategory(Enum):
    """Categories for trading strategies"""

    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    OPTIONS = "options"
    SCALPING = "scalping"
    SWING = "swing"
    INTRADAY = "intraday"
    ALGO = "algorithmic"


class StrategyTier(Enum):
    """Subscription tiers for strategies"""

    BASIC = "basic"
    PREMIUM = "premium"
    ELITE = "elite"
    INSTITUTIONAL = "institutional"


@dataclass
class StrategyCreator:
    """Strategy creator profile"""

    creator_id: str
    name: str
    email: str
    bio: str
    experience_years: int
    total_strategies: int
    avg_rating: float
    total_earnings: float
    verified: bool
    certification_level: str  # 'Bronze', 'Silver', 'Gold', 'Platinum'
    created_at: datetime


@dataclass
class MarketplaceStrategy:
    """Strategy in the marketplace"""

    strategy_id: str
    name: str
    description: str
    creator: StrategyCreator
    category: StrategyCategory
    tier: StrategyTier
    price_monthly: int  # in paise
    price_onetime: Optional[int]  # in paise
    rating: float
    total_subscribers: int
    total_revenue: float
    tags: List[str]
    min_capital: int
    max_positions: int
    risk_level: str  # 'Low', 'Medium', 'High'
    asset_classes: List[str]  # ['stocks', 'crypto', 'forex', etc.]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    trial_period_days: int
    sample_trades: List[Dict]
    strategy_code: Optional[str]  # For premium strategies
    backtest_results: Dict


class StrategyMarketplace:
    """Main marketplace for trading strategies"""

    COMMISSION_RATES = {
        StrategyTier.BASIC: 0.30,  # 30% commission
        StrategyTier.PREMIUM: 0.30,  # 30% commission
        StrategyTier.ELITE: 0.25,  # 25% commission
        StrategyTier.INSTITUTIONAL: 0.20,  # 20% commission
    }

    CREATOR_REVENUE_SHARE = {
        StrategyTier.BASIC: 0.70,  # 70% to creator
        StrategyTier.PREMIUM: 0.70,  # 70% to creator
        StrategyTier.ELITE: 0.75,  # 75% to creator
        StrategyTier.INSTITUTIONAL: 0.80,  # 80% to creator
    }

    def __init__(self):
        self.strategies: Dict[str, MarketplaceStrategy] = {}
        self.creators: Dict[str, StrategyCreator] = {}
        self.subscriptions: Dict[str, List[Dict]] = {}  # user_id -> subscriptions

    def get_available_strategies(self) -> List[Dict]:
        """Get all available strategies in simplified format"""
        # Mock data for integration testing
        return [
            {
                "id": "strategy_1",
                "name": "AI Momentum Strategy",
                "creator": "Algo Master",
                "price": 2999,
                "rating": 4.8,
                "subscribers": 150,
                "annual_return": 35.5,
                "category": "Momentum",
            },
            {
                "id": "strategy_2",
                "name": "Options Scalping Pro",
                "creator": "Options Expert",
                "price": 4999,
                "rating": 4.6,
                "subscribers": 85,
                "annual_return": 42.8,
                "category": "Options",
            },
            {
                "id": "strategy_3",
                "name": "Mean Reversion Master",
                "creator": "Quant Trader",
                "price": 1999,
                "rating": 4.4,
                "subscribers": 200,
                "annual_return": 28.3,
                "category": "Mean Reversion",
            },
        ]

    def purchase_strategy(self, user_id: str, strategy_id: str) -> Dict:
        """Purchase a strategy (simplified for demo)"""
        strategies = {s["id"]: s for s in self.get_available_strategies()}
        if strategy_id not in strategies:
            raise ValueError("Strategy not found")

        strategy = strategies[strategy_id]
        return {
            "user_id": user_id,
            "strategy_id": strategy_id,
            "strategy_name": strategy["name"],
            "price": strategy["price"],
            "purchase_date": datetime.now().isoformat(),
            "access_granted": True,
        }

    def get_creator_earnings(self, creator_id: str) -> Dict:
        """Get earnings for a strategy creator"""
        # Mock data for integration testing
        creators = {
            "creator_1": {
                "creator_id": "creator_1",
                "name": "Algo Master",
                "total_earnings": 600000,
                "total_strategies": 5,
                "avg_rating": 4.8,
                "experience_years": 8,
            },
            "creator_2": {
                "creator_id": "creator_2",
                "name": "Options Expert",
                "total_earnings": 420000,
                "total_strategies": 3,
                "avg_rating": 4.6,
                "experience_years": 5,
            },
        }

        return creators.get(creator_id, {"error": "Creator not found"})

    def calculate_platform_revenue(self) -> float:
        """Calculate total platform revenue from marketplace"""
        strategies = self.get_available_strategies()
        total_revenue = 0
        for strategy in strategies:
            monthly_revenue = strategy["price"] * strategy["subscribers"]
            commission_rate = 0.30  # Average 30% commission
            platform_cut = monthly_revenue * commission_rate
            total_revenue += platform_cut
        return total_revenue


def demo_marketplace():
    """Demonstrate the strategy marketplace"""
    print("=== Strategy Marketplace Demo ===")

    marketplace = StrategyMarketplace()

    # Show available strategies
    strategies = marketplace.get_available_strategies()
    print(f"\nAvailable Strategies: {len(strategies)}")
    for strategy in strategies:
        print(
            f"  • {strategy['name']}: ₹{strategy['price']}/month ({strategy['subscribers']} subscribers)"
        )

    # Calculate platform revenue
    revenue = marketplace.calculate_platform_revenue()
    print(f"\nPlatform Revenue: ₹{revenue:,.2f}")

    # Show creator earnings
    creator_earnings = marketplace.get_creator_earnings("creator_1")
    print(f"\nTop Creator Earnings:")
    print(
        f"  • {creator_earnings['name']}: ₹{creator_earnings['total_earnings']:,}/total"
    )

    return True


if __name__ == "__main__":
    demo_marketplace()
