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
                'id': 'strategy_1',
                'name': 'AI Momentum Strategy',
                'creator': 'Algo Master',
                'price': 2999,
                'rating': 4.8,
                'subscribers': 150,
                'annual_return': 35.5,
                'category': 'Momentum'
            },
            {
                'id': 'strategy_2',
                'name': 'Options Scalping Pro',
                'creator': 'Options Expert',
                'price': 4999,
                'rating': 4.6,
                'subscribers': 85,
                'annual_return': 42.8,
                'category': 'Options'
            },
            {
                'id': 'strategy_3',
                'name': 'Mean Reversion Master',
                'creator': 'Quant Trader',
                'price': 1999,
                'rating': 4.4,
                'subscribers': 200,
                'annual_return': 28.3,
                'category': 'Mean Reversion'
            }
        ]

    def purchase_strategy(self, user_id: str, strategy_id: str) -> Dict:
        """Purchase a strategy (simplified for demo)"""
        strategies = {s['id']: s for s in self.get_available_strategies()}
        if strategy_id not in strategies:
            raise ValueError("Strategy not found")
        
        strategy = strategies[strategy_id]
        return {
            'user_id': user_id,
            'strategy_id': strategy_id,
            'strategy_name': strategy['name'],
            'price': strategy['price'],
            'purchase_date': datetime.now().isoformat(),
            'access_granted': True
        }

    def get_creator_earnings(self, creator_id: str) -> Dict:
        """Get earnings for a strategy creator"""
        # Mock data for integration testing
        creators = {
            'creator_1': {
                'creator_id': 'creator_1',
                'name': 'Algo Master',
                'total_earnings': 600000,
                'total_strategies': 5,
                'avg_rating': 4.8,
                'experience_years': 8
            },
            'creator_2': {
                'creator_id': 'creator_2',
                'name': 'Options Expert',
                'total_earnings': 420000,
                'total_strategies': 3,
                'avg_rating': 4.6,
                'experience_years': 5
            }
        }
        
        return creators.get(creator_id, {'error': 'Creator not found'})

    def calculate_platform_revenue(self) -> float:
        """Calculate total platform revenue from marketplace"""
        strategies = self.get_available_strategies()
        total_revenue = 0
        for strategy in strategies:
            monthly_revenue = strategy['price'] * strategy['subscribers']
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
        print(f"  • {strategy['name']}: ₹{strategy['price']}/month ({strategy['subscribers']} subscribers)")
    
    # Calculate platform revenue
    revenue = marketplace.calculate_platform_revenue()
    print(f"\nPlatform Revenue: ₹{revenue:,.2f}")
    
    # Show creator earnings
    creator_earnings = marketplace.get_creator_earnings('creator_1')
    print(f"\nTop Creator Earnings:")
    print(f"  • {creator_earnings['name']}: ₹{creator_earnings['total_earnings']:,}/total")
    
    return True


if __name__ == "__main__":
    demo_marketplace()
                'name': 'Options Scalping Pro',
                'creator': 'Options Expert',
                'price': 4999,
                'rating': 4.6,
                'subscribers': 85,
                'annual_return': 42.8,
                'category': 'Options'
            }
        ]om datetime import datetime, timedelta
import json
import uuid
from decimal import Decimal


class StrategyCategory(Enum):
    """Strategy categories for marketplace"""

    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    OPTIONS = "options"
    INTRADAY = "intraday"
    SWING = "swing"
    LONG_TERM = "long_term"
    AI_POWERED = "ai_powered"
    SECTOR_SPECIFIC = "sector_specific"
    CRYPTO = "crypto"


class StrategyTier(Enum):
    """Strategy pricing tiers"""

    BASIC = "basic"  # ₹199-499/month
    PREMIUM = "premium"  # ₹999-2999/month
    ELITE = "elite"  # ₹4999-9999/month
    INSTITUTIONAL = "institutional"  # ₹15000+/month


@dataclass
class StrategyPerformance:
    """Strategy performance metrics"""

    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    profit_factor: float
    volatility: float
    beta: float
    alpha: float
    sortino_ratio: float
    calmar_ratio: float


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
    performance: StrategyPerformance
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
        # Temporarily disable sample data for integration testing
        # self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample strategies and creators for demo purposes"""
        # Create sample creators
        sample_creators = [
            StrategyCreator(
                creator_id="creator_1",
                name="Algo Master",
                email="algo@example.com",
                bio="Expert in algorithmic trading",
                experience_years=8,
                total_strategies=5,
                avg_rating=4.8,
                total_earnings=600000,
                verified=True,
                certification_level="Platinum",
                created_at=datetime.now() - timedelta(days=365),
            ),
            StrategyCreator(
                creator_id="creator_2",
                name="Momentum King",
                email="momentum@example.com",
                bio="Specialist in momentum strategies",
                experience_years=5,
                total_strategies=3,
                avg_rating=4.6,
                total_earnings=420000,
                verified=True,
                certification_level="Gold",
                created_at=datetime.now() - timedelta(days=200),
            ),
        ]

        for creator in sample_creators:
            self.creators[creator.creator_id] = creator

        # Create sample strategies
        sample_strategies = [
            MarketplaceStrategy(
                strategy_id="strategy_1",
                creator_id="creator_1",
                name="AI Momentum Strategy",
                description="Advanced momentum strategy using AI signals",
                category="Momentum",
                tier=StrategyTier.PREMIUM,
                price_monthly=2999,
                performance_metrics={
                    "annual_return": 35.5,
                    "sharpe_ratio": 2.1,
                    "max_drawdown": 8.2,
                },
                subscribers=150,
                rating=4.8,
                created_at=datetime.now() - timedelta(days=90),
                tags=["AI", "Momentum", "High-frequency"],
                is_active=True,
                backtest_results={"total_return": 45.2, "win_rate": 68.5},
            ),
            MarketplaceStrategy(
                strategy_id="strategy_2",
                creator_id="creator_2",
                name="Options Scalping Pro",
                description="Professional options scalping strategy",
                category="Options",
                tier=StrategyTier.ELITE,
                price_monthly=4999,
                performance_metrics={
                    "annual_return": 42.8,
                    "sharpe_ratio": 2.5,
                    "max_drawdown": 12.1,
                },
                subscribers=85,
                rating=4.6,
                created_at=datetime.now() - timedelta(days=60),
                tags=["Options", "Scalping", "High-yield"],
                is_active=True,
                backtest_results={"total_return": 55.3, "win_rate": 72.1},
            ),
        ]

        for strategy in sample_strategies:
            self.strategies[strategy.strategy_id] = strategy

    def get_available_strategies(self) -> List[Dict]:
        """Get all available strategies in simplified format"""
        return [
            {
                "id": strategy.strategy_id,
                "name": strategy.name,
                "creator": self.creators[strategy.creator_id].name,
                "price": strategy.price_monthly,
                "rating": strategy.rating,
                "subscribers": strategy.subscribers,
                "annual_return": strategy.performance_metrics.get("annual_return", 0),
                "category": strategy.category,
            }
            for strategy in self.strategies.values()
            if strategy.is_active
        ]

    def purchase_strategy(self, user_id: str, strategy_id: str) -> Dict:
        """Purchase a strategy (simplified for demo)"""
        if strategy_id not in self.strategies:
            raise ValueError("Strategy not found")

        strategy = self.strategies[strategy_id]
        return {
            "user_id": user_id,
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "price": strategy.price_monthly,
            "purchase_date": datetime.now().isoformat(),
            "access_granted": True,
        }

    def get_creator_earnings(self, creator_id: str) -> Dict:
        """Get earnings for a strategy creator"""
        if creator_id not in self.creators:
            return {"error": "Creator not found"}

        creator = self.creators[creator_id]
        return {
            "creator_id": creator_id,
            "name": creator.name,
            "total_earnings": creator.total_earnings,
            "total_strategies": creator.total_strategies,
            "avg_rating": creator.avg_rating,
            "experience_years": creator.experience_years,
        }

    def calculate_platform_revenue(self) -> float:
        """Calculate total platform revenue from marketplace"""
        total_revenue = 0
        for strategy in self.strategies.values():
            if strategy.is_active:
                monthly_revenue = strategy.price_monthly * strategy.subscribers
                commission_rate = self.COMMISSION_RATES[strategy.tier]
                platform_cut = monthly_revenue * commission_rate
                total_revenue += platform_cut
        return total_revenue

    def create_strategy_listing(self, creator_id: str, strategy_data: Dict) -> str:
        """Create a new strategy listing"""
        strategy_id = str(uuid.uuid4())

        creator = self.creators.get(creator_id)
        if not creator:
            raise ValueError("Creator not found")

        # Validate strategy data
        required_fields = ["name", "description", "category", "tier", "price_monthly"]
        for field in required_fields:
            if field not in strategy_data:
                raise ValueError(f"Missing required field: {field}")

        # Create performance object
        performance = StrategyPerformance(
            annual_return=strategy_data.get("annual_return", 0),
            max_drawdown=strategy_data.get("max_drawdown", 0),
            sharpe_ratio=strategy_data.get("sharpe_ratio", 0),
            win_rate=strategy_data.get("win_rate", 0),
            total_trades=strategy_data.get("total_trades", 0),
            profit_factor=strategy_data.get("profit_factor", 1),
            volatility=strategy_data.get("volatility", 0),
            beta=strategy_data.get("beta", 1),
            alpha=strategy_data.get("alpha", 0),
            sortino_ratio=strategy_data.get("sortino_ratio", 0),
            calmar_ratio=strategy_data.get("calmar_ratio", 0),
        )

        strategy = MarketplaceStrategy(
            strategy_id=strategy_id,
            name=strategy_data["name"],
            description=strategy_data["description"],
            creator=creator,
            category=StrategyCategory(strategy_data["category"]),
            tier=StrategyTier(strategy_data["tier"]),
            price_monthly=strategy_data["price_monthly"],
            price_onetime=strategy_data.get("price_onetime"),
            performance=performance,
            rating=0.0,
            total_subscribers=0,
            total_revenue=0.0,
            tags=strategy_data.get("tags", []),
            min_capital=strategy_data.get("min_capital", 10000),
            max_positions=strategy_data.get("max_positions", 10),
            risk_level=strategy_data.get("risk_level", "Medium"),
            asset_classes=strategy_data.get("asset_classes", ["stocks"]),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            trial_period_days=strategy_data.get("trial_period_days", 7),
            sample_trades=strategy_data.get("sample_trades", []),
            strategy_code=strategy_data.get("strategy_code"),
            backtest_results=strategy_data.get("backtest_results", {}),
        )

        self.strategies[strategy_id] = strategy
        return strategy_id

    def subscribe_to_strategy(
        self, user_id: str, strategy_id: str, subscription_type: str = "monthly"
    ) -> Dict:
        """Subscribe user to a strategy"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            raise ValueError("Strategy not found")

        if not strategy.is_active:
            raise ValueError("Strategy is not active")

        # Calculate pricing
        if subscription_type == "monthly":
            price = strategy.price_monthly
        elif subscription_type == "onetime" and strategy.price_onetime:
            price = strategy.price_onetime
        else:
            raise ValueError("Invalid subscription type")

        # Create subscription record
        subscription = {
            "subscription_id": str(uuid.uuid4()),
            "user_id": user_id,
            "strategy_id": strategy_id,
            "subscription_type": subscription_type,
            "price_paid": price,
            "start_date": datetime.now(),
            "end_date": (
                datetime.now() + timedelta(days=30)
                if subscription_type == "monthly"
                else None
            ),
            "trial_end_date": datetime.now()
            + timedelta(days=strategy.trial_period_days),
            "status": "active",
            "created_at": datetime.now(),
        }

        # Add to user subscriptions
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = []
        self.subscriptions[user_id].append(subscription)

        # Update strategy metrics
        strategy.total_subscribers += 1
        strategy.total_revenue += price / 100  # Convert from paise to rupees

        # Calculate creator earnings
        creator_share = self.CREATOR_REVENUE_SHARE[strategy.tier]
        creator_earnings = (price / 100) * creator_share
        strategy.creator.total_earnings += creator_earnings

        return {
            "subscription_id": subscription["subscription_id"],
            "price_paid": price,
            "trial_period_days": strategy.trial_period_days,
            "creator_earnings": creator_earnings,
            "platform_commission": (price / 100) - creator_earnings,
        }

    def search_strategies(self, filters: Dict) -> List[MarketplaceStrategy]:
        """Search strategies with filters"""
        results = list(self.strategies.values())

        # Apply filters
        if "category" in filters:
            results = [s for s in results if s.category.value == filters["category"]]

        if "tier" in filters:
            results = [s for s in results if s.tier.value == filters["tier"]]

        if "min_return" in filters:
            results = [
                s
                for s in results
                if s.performance.annual_return >= filters["min_return"]
            ]

        if "max_drawdown" in filters:
            results = [
                s
                for s in results
                if s.performance.max_drawdown <= filters["max_drawdown"]
            ]

        if "min_rating" in filters:
            results = [s for s in results if s.rating >= filters["min_rating"]]

        if "asset_class" in filters:
            results = [s for s in results if filters["asset_class"] in s.asset_classes]

        if "max_price" in filters:
            results = [s for s in results if s.price_monthly <= filters["max_price"]]

        if "risk_level" in filters:
            results = [s for s in results if s.risk_level == filters["risk_level"]]

        # Sort by relevance (rating * subscribers)
        results.sort(key=lambda x: x.rating * x.total_subscribers, reverse=True)

        return results

    def get_trending_strategies(self, limit: int = 10) -> List[MarketplaceStrategy]:
        """Get trending strategies based on recent subscriptions"""
        # Mock trending algorithm - in production, would use time-weighted metrics
        all_strategies = [s for s in self.strategies.values() if s.is_active]

        # Sort by combination of recent subscribers and performance
        trending_score = lambda s: (
            s.total_subscribers * 0.4
            + s.performance.annual_return * 0.3
            + s.rating * 0.3
        )

        all_strategies.sort(key=trending_score, reverse=True)
        return all_strategies[:limit]

    def get_top_creators(self, limit: int = 10) -> List[StrategyCreator]:
        """Get top strategy creators"""
        all_creators = list(self.creators.values())

        # Sort by total earnings and rating
        creator_score = lambda c: c.total_earnings * 0.6 + c.avg_rating * 1000 * 0.4
        all_creators.sort(key=creator_score, reverse=True)

        return all_creators[:limit]

    def calculate_creator_earnings(
        self, creator_id: str, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Calculate creator earnings for a period"""
        creator = self.creators.get(creator_id)
        if not creator:
            raise ValueError("Creator not found")

        # Get creator's strategies
        creator_strategies = [
            s for s in self.strategies.values() if s.creator.creator_id == creator_id
        ]

        total_earnings = 0
        total_subscriptions = 0
        strategy_breakdown = []

        for strategy in creator_strategies:
            # Mock calculation - in production, would query actual subscription data
            strategy_earnings = (
                strategy.total_revenue * self.CREATOR_REVENUE_SHARE[strategy.tier]
            )
            total_earnings += strategy_earnings
            total_subscriptions += strategy.total_subscribers

            strategy_breakdown.append(
                {
                    "strategy_name": strategy.name,
                    "strategy_id": strategy.strategy_id,
                    "subscribers": strategy.total_subscribers,
                    "revenue": strategy.total_revenue,
                    "creator_earnings": strategy_earnings,
                    "commission_rate": self.COMMISSION_RATES[strategy.tier],
                }
            )

        return {
            "creator_id": creator_id,
            "creator_name": creator.name,
            "period_start": start_date,
            "period_end": end_date,
            "total_earnings": total_earnings,
            "total_subscriptions": total_subscriptions,
            "total_strategies": len(creator_strategies),
            "avg_earnings_per_strategy": (
                total_earnings / len(creator_strategies) if creator_strategies else 0
            ),
            "strategy_breakdown": strategy_breakdown,
        }

    def get_platform_revenue_summary(
        self, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Calculate platform revenue summary"""
        total_revenue = 0
        total_creator_earnings = 0
        total_platform_commission = 0

        tier_breakdown = {
            tier: {"revenue": 0, "strategies": 0, "subscribers": 0}
            for tier in StrategyTier
        }

        for strategy in self.strategies.values():
            strategy_revenue = strategy.total_revenue
            creator_share = self.CREATOR_REVENUE_SHARE[strategy.tier]
            platform_commission = (
                strategy_revenue * self.COMMISSION_RATES[strategy.tier]
            )

            total_revenue += strategy_revenue
            total_creator_earnings += strategy_revenue * creator_share
            total_platform_commission += platform_commission

            # Tier breakdown
            tier_breakdown[strategy.tier]["revenue"] += strategy_revenue
            tier_breakdown[strategy.tier]["strategies"] += 1
            tier_breakdown[strategy.tier]["subscribers"] += strategy.total_subscribers

        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_revenue": total_revenue,
            "total_creator_earnings": total_creator_earnings,
            "total_platform_commission": total_platform_commission,
            "platform_commission_rate": (
                total_platform_commission / total_revenue if total_revenue > 0 else 0
            ),
            "total_strategies": len(self.strategies),
            "total_active_strategies": len(
                [s for s in self.strategies.values() if s.is_active]
            ),
            "total_creators": len(self.creators),
            "tier_breakdown": {
                tier.value: data for tier, data in tier_breakdown.items()
            },
        }

    def create_creator_profile(self, creator_data: Dict) -> str:
        """Create a new strategy creator profile"""
        creator_id = str(uuid.uuid4())

        creator = StrategyCreator(
            creator_id=creator_id,
            name=creator_data["name"],
            email=creator_data["email"],
            bio=creator_data.get("bio", ""),
            experience_years=creator_data.get("experience_years", 0),
            total_strategies=0,
            avg_rating=0.0,
            total_earnings=0.0,
            verified=creator_data.get("verified", False),
            certification_level=creator_data.get("certification_level", "Bronze"),
            created_at=datetime.now(),
        )

        self.creators[creator_id] = creator
        return creator_id

    def rate_strategy(
        self, user_id: str, strategy_id: str, rating: float, review: str = ""
    ) -> None:
        """Rate a strategy"""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        strategy = self.strategies.get(strategy_id)
        if not strategy:
            raise ValueError("Strategy not found")

        # Check if user is subscribed
        user_subscriptions = self.subscriptions.get(user_id, [])
        is_subscribed = any(
            sub["strategy_id"] == strategy_id and sub["status"] == "active"
            for sub in user_subscriptions
        )

        if not is_subscribed:
            raise ValueError("You must be subscribed to rate this strategy")

        # Update strategy rating (simplified - in production, would maintain all ratings)
        # For demo, just update the average
        current_total = strategy.rating * strategy.total_subscribers
        new_total = current_total + rating
        strategy.rating = (
            new_total / (strategy.total_subscribers + 1)
            if strategy.total_subscribers > 0
            else rating
        )


# Demo data generator
def generate_demo_marketplace_data():
    """Generate demo data for the marketplace"""
    marketplace = StrategyMarketplace()

    # Create demo creators
    creators_data = [
        {
            "name": "Rakesh Jhunjhunwala Jr.",
            "email": "rakesh@trademantra.com",
            "bio": "Former fund manager with 15 years experience. Specialized in value investing and momentum strategies.",
            "experience_years": 15,
            "verified": True,
            "certification_level": "Platinum",
        },
        {
            "name": "Priya Algo Trader",
            "email": "priya@algorithms.com",
            "bio": "Quantitative analyst and algorithmic trader. Expert in high-frequency and statistical arbitrage.",
            "experience_years": 8,
            "verified": True,
            "certification_level": "Gold",
        },
        {
            "name": "Mumbai Options Master",
            "email": "options@mumbai.com",
            "bio": "Options trading specialist with focus on income generation strategies.",
            "experience_years": 12,
            "verified": True,
            "certification_level": "Gold",
        },
    ]

    creator_ids = []
    for creator_data in creators_data:
        creator_id = marketplace.create_creator_profile(creator_data)
        creator_ids.append(creator_id)

    # Create demo strategies
    strategies_data = [
        {
            "name": "AI Momentum Master",
            "description": "AI-powered momentum strategy that identifies strong trending stocks using machine learning",
            "category": "ai_powered",
            "tier": "elite",
            "price_monthly": 999900,  # ₹9,999
            "annual_return": 0.35,
            "max_drawdown": -0.12,
            "sharpe_ratio": 2.4,
            "win_rate": 0.68,
            "total_trades": 156,
            "tags": ["AI", "Momentum", "Machine Learning"],
            "min_capital": 100000,
            "risk_level": "High",
            "asset_classes": ["stocks", "crypto"],
            "trial_period_days": 14,
        },
        {
            "name": "Nifty Mean Reversion Pro",
            "description": "Statistical mean reversion strategy optimized for Nifty stocks with risk management",
            "category": "mean_reversion",
            "tier": "premium",
            "price_monthly": 299900,  # ₹2,999
            "annual_return": 0.22,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.9,
            "win_rate": 0.72,
            "total_trades": 89,
            "tags": ["Mean Reversion", "Nifty", "Statistical"],
            "min_capital": 50000,
            "risk_level": "Medium",
            "asset_classes": ["stocks"],
            "trial_period_days": 7,
        },
        {
            "name": "Options Income Generator",
            "description": "Conservative options selling strategy for steady monthly income",
            "category": "options",
            "tier": "premium",
            "price_monthly": 199900,  # ₹1,999
            "annual_return": 0.18,
            "max_drawdown": -0.05,
            "sharpe_ratio": 2.1,
            "win_rate": 0.85,
            "total_trades": 45,
            "tags": ["Options", "Income", "Conservative"],
            "min_capital": 200000,
            "risk_level": "Low",
            "asset_classes": ["stocks"],
            "trial_period_days": 10,
        },
        {
            "name": "Crypto Arbitrage Bot",
            "description": "Automated arbitrage opportunities across multiple crypto exchanges",
            "category": "arbitrage",
            "tier": "institutional",
            "price_monthly": 2500000,  # ₹25,000
            "annual_return": 0.45,
            "max_drawdown": -0.03,
            "sharpe_ratio": 3.2,
            "win_rate": 0.92,
            "total_trades": 2340,
            "tags": ["Crypto", "Arbitrage", "High Frequency"],
            "min_capital": 1000000,
            "risk_level": "Low",
            "asset_classes": ["crypto"],
            "trial_period_days": 3,
        },
        {
            "name": "Intraday Scalper",
            "description": "Fast-paced intraday scalping strategy for active traders",
            "category": "intraday",
            "tier": "basic",
            "price_monthly": 49900,  # ₹499
            "annual_return": 0.28,
            "max_drawdown": -0.15,
            "sharpe_ratio": 1.6,
            "win_rate": 0.61,
            "total_trades": 520,
            "tags": ["Intraday", "Scalping", "High Frequency"],
            "min_capital": 25000,
            "risk_level": "High",
            "asset_classes": ["stocks"],
            "trial_period_days": 5,
        },
    ]

    for i, strategy_data in enumerate(strategies_data):
        creator_id = creator_ids[i % len(creator_ids)]
        strategy_id = marketplace.create_strategy_listing(creator_id, strategy_data)

        # Add some mock subscriptions
        for j in range(strategy_data.get("subscribers", 50)):
            user_id = f"user_{j}"
            try:
                marketplace.subscribe_to_strategy(user_id, strategy_id)
            except:
                pass  # Skip if already subscribed

    return marketplace


# Example usage
if __name__ == "__main__":
    print("=== Strategy Marketplace Demo ===")

    # Generate demo marketplace
    marketplace = generate_demo_marketplace_data()

    print(f"\nMarketplace Summary:")
    print(f"Total Strategies: {len(marketplace.strategies)}")
    print(f"Total Creators: {len(marketplace.creators)}")

    # Show trending strategies
    print(f"\n=== Trending Strategies ===")
    trending = marketplace.get_trending_strategies(3)
    for strategy in trending:
        print(f"\n📈 {strategy.name}")
        print(f"   Creator: {strategy.creator.name}")
        print(f"   Price: ₹{strategy.price_monthly/100:,.0f}/month")
        print(f"   Return: {strategy.performance.annual_return*100:.1f}%")
        print(f"   Subscribers: {strategy.total_subscribers}")
        print(f"   Rating: {strategy.rating:.1f}/5.0")

    # Show top creators
    print(f"\n=== Top Creators ===")
    top_creators = marketplace.get_top_creators(3)
    for creator in top_creators:
        print(f"\n🏆 {creator.name}")
        print(f"   Experience: {creator.experience_years} years")
        print(f"   Total Earnings: ₹{creator.total_earnings:,.0f}")
        print(f"   Certification: {creator.certification_level}")
        print(f"   Verified: {'✅' if creator.verified else '❌'}")

    # Platform revenue summary
    revenue_summary = marketplace.get_platform_revenue_summary(
        datetime.now() - timedelta(days=30), datetime.now()
    )

    print(f"\n=== Platform Revenue Summary ===")
    print(f"Total Revenue: ₹{revenue_summary['total_revenue']:,.0f}")
    print(f"Creator Earnings: ₹{revenue_summary['total_creator_earnings']:,.0f}")
    print(f"Platform Commission: ₹{revenue_summary['total_platform_commission']:,.0f}")
    print(f"Commission Rate: {revenue_summary['platform_commission_rate']*100:.1f}%")
