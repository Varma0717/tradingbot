"""
Social Trading Platform for Trade Mantra
Copy trading, social feeds, and trader rankings
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid
from decimal import Decimal
import numpy as np


class TraderTier(Enum):
    """Trader performance tiers"""

    BRONZE = "bronze"  # < 15% annual return
    SILVER = "silver"  # 15-25% annual return
    GOLD = "gold"  # 25-40% annual return
    PLATINUM = "platinum"  # 40-60% annual return
    DIAMOND = "diamond"  # > 60% annual return


class PostType(Enum):
    """Types of social posts"""

    TRADE_IDEA = "trade_idea"
    MARKET_ANALYSIS = "market_analysis"
    PERFORMANCE_UPDATE = "performance_update"
    EDUCATIONAL = "educational"
    CELEBRATION = "celebration"
    WARNING = "warning"


@dataclass
class TraderProfile:
    """Professional trader profile"""

    trader_id: str
    username: str
    display_name: str
    bio: str
    avatar_url: Optional[str]
    tier: TraderTier
    verified: bool

    # Performance metrics
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    total_followers: int
    total_copiers: int

    # Earnings from copy trading
    monthly_earnings: float
    total_earnings: float

    # Trading preferences
    risk_level: str
    preferred_assets: List[str]
    trading_style: str  # 'Conservative', 'Moderate', 'Aggressive'
    avg_holding_period: int  # in days

    # Social metrics
    total_posts: int
    total_likes: int
    response_rate: float  # How often they respond to comments

    created_at: datetime
    last_active: datetime


@dataclass
class SocialPost:
    """Social media post from trader"""

    post_id: str
    trader_id: str
    trader_username: str
    post_type: PostType
    title: str
    content: str
    images: List[str]
    trade_symbol: Optional[str]
    trade_direction: Optional[str]  # 'BUY', 'SELL'
    target_price: Optional[float]
    stop_loss: Optional[float]
    confidence: Optional[float]

    likes: int
    comments: int
    shares: int
    views: int

    created_at: datetime
    updated_at: datetime
    is_premium: bool  # Premium content for paid followers


@dataclass
class CopyTradingConfig:
    """Copy trading configuration"""

    config_id: str
    follower_id: str
    trader_id: str

    # Copy settings
    copy_percentage: float  # Percentage of portfolio to allocate
    max_position_size: float  # Maximum position size
    risk_multiplier: float  # Risk adjustment (0.5 = half risk, 2.0 = double risk)

    # Filters
    min_confidence: float  # Only copy trades with confidence >= this
    allowed_symbols: List[str]  # Empty = all symbols
    blocked_symbols: List[str]
    max_drawdown_stop: float  # Stop copying if trader's drawdown exceeds this

    # Status
    is_active: bool
    total_copied_trades: int
    total_profit: float

    created_at: datetime
    last_trade_copied: Optional[datetime]


@dataclass
class CopiedTrade:
    """Record of a copied trade"""

    trade_id: str
    original_trade_id: str
    follower_id: str
    trader_id: str

    symbol: str
    direction: str  # 'BUY', 'SELL'
    quantity: int
    entry_price: float
    current_price: float
    target_price: Optional[float]
    stop_loss: Optional[float]

    original_quantity: int  # Original trader's quantity
    copy_ratio: float  # follower_quantity / original_quantity

    status: str  # 'OPEN', 'CLOSED', 'STOPPED'
    profit_loss: float

    opened_at: datetime
    closed_at: Optional[datetime]


class SocialTradingPlatform:
    """Main social trading platform"""

    COPY_TRADING_FEES = {
        TraderTier.BRONZE: 0.10,  # 10% of profits
        TraderTier.SILVER: 0.15,  # 15% of profits
        TraderTier.GOLD: 0.20,  # 20% of profits
        TraderTier.PLATINUM: 0.25,  # 25% of profits
        TraderTier.DIAMOND: 0.30,  # 30% of profits
    }

    PLATFORM_COMMISSION = 0.30  # 30% of copy trading fees

    def __init__(self):
        self.traders: Dict[str, TraderProfile] = {}
        self.posts: Dict[str, SocialPost] = {}
        self.copy_configs: Dict[str, List[CopyTradingConfig]] = (
            {}
        )  # follower_id -> configs
        self.copied_trades: Dict[str, CopiedTrade] = {}
        self.trader_rankings: List[str] = []  # Ordered list of trader IDs

    def create_trader_profile(self, user_id: str, profile_data: Dict) -> str:
        """Create a professional trader profile"""
        trader_id = user_id  # Use user_id as trader_id

        # Calculate tier based on performance
        annual_return = profile_data.get("annual_return", 0)
        tier = self._calculate_trader_tier(annual_return)

        trader = TraderProfile(
            trader_id=trader_id,
            username=profile_data["username"],
            display_name=profile_data.get("display_name", profile_data["username"]),
            bio=profile_data.get("bio", ""),
            avatar_url=profile_data.get("avatar_url"),
            tier=tier,
            verified=profile_data.get("verified", False),
            annual_return=annual_return,
            max_drawdown=profile_data.get("max_drawdown", 0),
            sharpe_ratio=profile_data.get("sharpe_ratio", 0),
            win_rate=profile_data.get("win_rate", 0),
            total_trades=profile_data.get("total_trades", 0),
            total_followers=0,
            total_copiers=0,
            monthly_earnings=0,
            total_earnings=0,
            risk_level=profile_data.get("risk_level", "Medium"),
            preferred_assets=profile_data.get("preferred_assets", ["stocks"]),
            trading_style=profile_data.get("trading_style", "Moderate"),
            avg_holding_period=profile_data.get("avg_holding_period", 7),
            total_posts=0,
            total_likes=0,
            response_rate=0.8,
            created_at=datetime.now(),
            last_active=datetime.now(),
        )

        self.traders[trader_id] = trader
        self._update_trader_rankings()

        return trader_id

    def create_social_post(self, trader_id: str, post_data: Dict) -> str:
        """Create a social media post"""
        trader = self.traders.get(trader_id)
        if not trader:
            raise ValueError("Trader not found")

        post_id = str(uuid.uuid4())

        post = SocialPost(
            post_id=post_id,
            trader_id=trader_id,
            trader_username=trader.username,
            post_type=PostType(post_data["post_type"]),
            title=post_data["title"],
            content=post_data["content"],
            images=post_data.get("images", []),
            trade_symbol=post_data.get("trade_symbol"),
            trade_direction=post_data.get("trade_direction"),
            target_price=post_data.get("target_price"),
            stop_loss=post_data.get("stop_loss"),
            confidence=post_data.get("confidence"),
            likes=0,
            comments=0,
            shares=0,
            views=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_premium=post_data.get("is_premium", False),
        )

        self.posts[post_id] = post
        trader.total_posts += 1

        return post_id

    def setup_copy_trading(
        self, follower_id: str, trader_id: str, config_data: Dict
    ) -> str:
        """Set up copy trading configuration"""
        trader = self.traders.get(trader_id)
        if not trader:
            raise ValueError("Trader not found")

        config_id = str(uuid.uuid4())

        config = CopyTradingConfig(
            config_id=config_id,
            follower_id=follower_id,
            trader_id=trader_id,
            copy_percentage=config_data.get("copy_percentage", 10.0),  # 10% default
            max_position_size=config_data.get("max_position_size", 50000),
            risk_multiplier=config_data.get("risk_multiplier", 1.0),
            min_confidence=config_data.get("min_confidence", 0.7),
            allowed_symbols=config_data.get("allowed_symbols", []),
            blocked_symbols=config_data.get("blocked_symbols", []),
            max_drawdown_stop=config_data.get("max_drawdown_stop", 0.20),  # 20%
            is_active=True,
            total_copied_trades=0,
            total_profit=0,
            created_at=datetime.now(),
            last_trade_copied=None,
        )

        if follower_id not in self.copy_configs:
            self.copy_configs[follower_id] = []

        self.copy_configs[follower_id].append(config)
        trader.total_copiers += 1

        return config_id

    def execute_copy_trade(self, original_trade: Dict, trader_id: str) -> List[str]:
        """Execute copy trades for all followers of a trader"""
        copied_trade_ids = []

        # Find all followers copying this trader
        for follower_id, configs in self.copy_configs.items():
            for config in configs:
                if (
                    config.trader_id == trader_id
                    and config.is_active
                    and self._should_copy_trade(original_trade, config)
                ):

                    copied_trade_id = self._create_copied_trade(
                        original_trade, config, follower_id
                    )
                    copied_trade_ids.append(copied_trade_id)

        return copied_trade_ids

    def _should_copy_trade(self, trade: Dict, config: CopyTradingConfig) -> bool:
        """Determine if a trade should be copied based on config"""
        # Check confidence threshold
        if trade.get("confidence", 0) < config.min_confidence:
            return False

        # Check symbol filters
        symbol = trade.get("symbol", "")
        if config.allowed_symbols and symbol not in config.allowed_symbols:
            return False

        if symbol in config.blocked_symbols:
            return False

        # Check trader's recent performance (stop if drawdown too high)
        trader = self.traders.get(config.trader_id)
        if trader and trader.max_drawdown < -config.max_drawdown_stop:
            return False

        return True

    def _create_copied_trade(
        self, original_trade: Dict, config: CopyTradingConfig, follower_id: str
    ) -> str:
        """Create a copied trade record"""
        trade_id = str(uuid.uuid4())

        # Calculate position size based on copy settings
        original_value = original_trade["quantity"] * original_trade["price"]
        copy_value = original_value * config.risk_multiplier

        # Apply position size limits
        copy_value = min(copy_value, config.max_position_size)
        copy_quantity = int(copy_value / original_trade["price"])

        copied_trade = CopiedTrade(
            trade_id=trade_id,
            original_trade_id=original_trade["trade_id"],
            follower_id=follower_id,
            trader_id=config.trader_id,
            symbol=original_trade["symbol"],
            direction=original_trade["direction"],
            quantity=copy_quantity,
            entry_price=original_trade["price"],
            current_price=original_trade["price"],
            target_price=original_trade.get("target_price"),
            stop_loss=original_trade.get("stop_loss"),
            original_quantity=original_trade["quantity"],
            copy_ratio=copy_quantity / original_trade["quantity"],
            status="OPEN",
            profit_loss=0,
            opened_at=datetime.now(),
            closed_at=None,
        )

        self.copied_trades[trade_id] = copied_trade
        config.total_copied_trades += 1
        config.last_trade_copied = datetime.now()

        return trade_id

    def get_trader_leaderboard(
        self, time_period: str = "monthly", limit: int = 50
    ) -> List[TraderProfile]:
        """Get trader leaderboard"""
        traders = list(self.traders.values())

        # Sort by performance score
        def performance_score(trader):
            return (
                trader.annual_return * 0.4
                + trader.sharpe_ratio * 0.3
                + trader.win_rate * 0.2
                + (1 - abs(trader.max_drawdown)) * 0.1
            )

        traders.sort(key=performance_score, reverse=True)
        return traders[:limit]

    def get_social_feed(self, user_id: str, limit: int = 20) -> List[SocialPost]:
        """Get personalized social feed"""
        # Get followed traders (mock implementation)
        followed_traders = self._get_followed_traders(user_id)

        # Get posts from followed traders
        feed_posts = []
        for post in self.posts.values():
            if (
                post.trader_id in followed_traders or not followed_traders
            ):  # Show all if no follows
                feed_posts.append(post)

        # Sort by engagement and recency
        def engagement_score(post):
            days_old = max(1, (datetime.now() - post.created_at).days)  # Minimum 1 day
            return (
                post.likes * 0.4
                + post.comments * 0.3
                + post.shares * 0.2
                + post.views * 0.1
            ) * (1 / days_old)

        feed_posts.sort(key=engagement_score, reverse=True)
        return feed_posts[:limit]

    def _get_followed_traders(self, user_id: str) -> List[str]:
        """Get list of traders followed by user (mock)"""
        # In production, this would query the follows table
        return list(self.traders.keys())[:5]  # Mock: follow top 5 traders

    def get_copy_trading_performance(self, follower_id: str) -> Dict:
        """Get copy trading performance summary"""
        configs = self.copy_configs.get(follower_id, [])

        total_profit = 0
        total_trades = 0
        active_copies = 0

        trader_performance = {}

        for config in configs:
            if config.is_active:
                active_copies += 1

            total_trades += config.total_copied_trades
            total_profit += config.total_profit

            trader_performance[config.trader_id] = {
                "trader_name": self.traders[config.trader_id].display_name,
                "trades_copied": config.total_copied_trades,
                "profit": config.total_profit,
                "last_copied": config.last_trade_copied,
            }

        return {
            "total_profit": total_profit,
            "total_trades": total_trades,
            "active_copies": active_copies,
            "avg_profit_per_trade": (
                total_profit / total_trades if total_trades > 0 else 0
            ),
            "trader_breakdown": trader_performance,
        }

    def calculate_trader_earnings(
        self, trader_id: str, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Calculate earnings for a trader from copy trading"""
        trader = self.traders.get(trader_id)
        if not trader:
            raise ValueError("Trader not found")

        total_earnings = 0
        total_copied_profit = 0
        total_followers_profit = 0

        # Calculate from all copied trades
        for trade in self.copied_trades.values():
            if (
                trade.trader_id == trader_id
                and trade.opened_at >= start_date
                and trade.opened_at <= end_date
            ):

                if trade.profit_loss > 0:  # Only charge on profitable trades
                    fee_rate = self.COPY_TRADING_FEES[trader.tier]
                    trader_earnings = trade.profit_loss * fee_rate
                    platform_commission = trader_earnings * self.PLATFORM_COMMISSION

                    total_earnings += trader_earnings - platform_commission
                    total_copied_profit += trade.profit_loss
                    total_followers_profit += trade.profit_loss

        return {
            "trader_id": trader_id,
            "trader_name": trader.display_name,
            "period_start": start_date,
            "period_end": end_date,
            "total_earnings": total_earnings,
            "total_followers_profit": total_followers_profit,
            "fee_rate": self.COPY_TRADING_FEES[trader.tier],
            "earnings_per_follower": (
                total_earnings / trader.total_copiers if trader.total_copiers > 0 else 0
            ),
        }

    def _calculate_trader_tier(self, annual_return: float) -> TraderTier:
        """Calculate trader tier based on performance"""
        if annual_return >= 0.60:
            return TraderTier.DIAMOND
        elif annual_return >= 0.40:
            return TraderTier.PLATINUM
        elif annual_return >= 0.25:
            return TraderTier.GOLD
        elif annual_return >= 0.15:
            return TraderTier.SILVER
        else:
            return TraderTier.BRONZE

    def _update_trader_rankings(self):
        """Update global trader rankings"""
        traders = list(self.traders.values())

        def ranking_score(trader):
            return (
                trader.annual_return * 0.3
                + trader.sharpe_ratio * 0.2
                + trader.total_copiers * 0.001  # Normalize followers
                + trader.win_rate * 0.2
                + (1 - abs(trader.max_drawdown)) * 0.15
                + (trader.total_earnings / 10000) * 0.15  # Normalize earnings
            )

        traders.sort(key=ranking_score, reverse=True)
        self.trader_rankings = [t.trader_id for t in traders]


# Demo data generator
def generate_demo_social_trading_data():
    """Generate demo data for social trading platform"""
    platform = SocialTradingPlatform()

    # Create demo traders
    traders_data = [
        {
            "username": "momentum_king",
            "display_name": "Momentum King 👑",
            "bio": "Professional momentum trader with 8+ years experience. Focus on breakout patterns and trend following.",
            "annual_return": 0.65,
            "max_drawdown": -0.12,
            "sharpe_ratio": 2.8,
            "win_rate": 0.74,
            "total_trades": 234,
            "risk_level": "High",
            "preferred_assets": ["stocks", "crypto"],
            "trading_style": "Aggressive",
            "verified": True,
        },
        {
            "username": "value_master",
            "display_name": "Value Master 📈",
            "bio": "Long-term value investor following Buffett principles. Conservative approach with steady returns.",
            "annual_return": 0.28,
            "max_drawdown": -0.06,
            "sharpe_ratio": 2.2,
            "win_rate": 0.82,
            "total_trades": 45,
            "risk_level": "Low",
            "preferred_assets": ["stocks"],
            "trading_style": "Conservative",
            "verified": True,
        },
        {
            "username": "options_wizard",
            "display_name": "Options Wizard 🎭",
            "bio": "Options trading specialist. Income generation through premium collection strategies.",
            "annual_return": 0.42,
            "max_drawdown": -0.08,
            "sharpe_ratio": 2.5,
            "win_rate": 0.88,
            "total_trades": 156,
            "risk_level": "Medium",
            "preferred_assets": ["stocks", "options"],
            "trading_style": "Moderate",
            "verified": True,
        },
        {
            "username": "crypto_ninja",
            "display_name": "Crypto Ninja 🥷",
            "bio": "Cryptocurrency trading expert. DeFi and altcoin specialist with institutional experience.",
            "annual_return": 0.95,
            "max_drawdown": -0.25,
            "sharpe_ratio": 2.1,
            "win_rate": 0.68,
            "total_trades": 445,
            "risk_level": "High",
            "preferred_assets": ["crypto"],
            "trading_style": "Aggressive",
            "verified": True,
        },
        {
            "username": "algo_trader",
            "display_name": "Algo Trader 🤖",
            "bio": "Quantitative algorithmic trader. Statistical arbitrage and market neutral strategies.",
            "annual_return": 0.35,
            "max_drawdown": -0.04,
            "sharpe_ratio": 3.1,
            "win_rate": 0.91,
            "total_trades": 1250,
            "risk_level": "Low",
            "preferred_assets": ["stocks", "forex"],
            "trading_style": "Conservative",
            "verified": True,
        },
    ]

    trader_ids = []
    for i, trader_data in enumerate(traders_data):
        trader_id = f"trader_{i+1}"
        platform.create_trader_profile(trader_id, trader_data)
        trader_ids.append(trader_id)

    # Create demo social posts
    posts_data = [
        {
            "trader_id": trader_ids[0],
            "post_type": "trade_idea",
            "title": "🚀 RELIANCE Breakout Alert!",
            "content": "RELIANCE breaking above 2550 resistance with volume. Target 2650, SL 2480. Strong momentum pattern developing.",
            "trade_symbol": "RELIANCE",
            "trade_direction": "BUY",
            "target_price": 2650,
            "stop_loss": 2480,
            "confidence": 0.85,
        },
        {
            "trader_id": trader_ids[1],
            "post_type": "market_analysis",
            "title": "📊 Market Analysis: Banking Sector",
            "content": "Banking sector showing strong fundamentals. HDFC Bank and ICICI Bank looking attractive for long-term positions. RBI policy supportive.",
            "confidence": 0.75,
        },
        {
            "trader_id": trader_ids[2],
            "post_type": "trade_idea",
            "title": "🎯 NIFTY Covered Call Strategy",
            "content": "Setting up covered call on NIFTY 18000 CE. Premium collection of ₹45. Probability of profit 78%.",
            "trade_symbol": "NIFTY",
            "trade_direction": "SELL",
            "confidence": 0.92,
        },
        {
            "trader_id": trader_ids[3],
            "post_type": "performance_update",
            "title": "🎉 +40% This Month!",
            "content": "Amazing month in crypto! BTC and ETH positions printed money. DeFi tokens also performing well. Risk management key!",
            "confidence": 0.88,
        },
        {
            "trader_id": trader_ids[4],
            "post_type": "educational",
            "title": "📚 Understanding Sharpe Ratio",
            "content": "Sharpe ratio measures risk-adjusted returns. Higher is better. My strategies target 2.5+ Sharpe ratio for consistent performance.",
            "confidence": 0.95,
        },
    ]

    for post_data in posts_data:
        platform.create_social_post(post_data["trader_id"], post_data)

    # Add some mock likes and engagement
    for post in platform.posts.values():
        post.likes = np.random.randint(15, 150)
        post.comments = np.random.randint(3, 25)
        post.shares = np.random.randint(1, 15)
        post.views = np.random.randint(100, 1000)

    # Set up some copy trading relationships
    for follower_id in [f"user_{i}" for i in range(1, 11)]:
        for trader_id in trader_ids[:3]:  # Each follower copies top 3 traders
            platform.setup_copy_trading(
                follower_id,
                trader_id,
                {
                    "copy_percentage": np.random.uniform(5, 20),
                    "risk_multiplier": np.random.uniform(0.5, 1.5),
                    "min_confidence": 0.7,
                },
            )

    return platform


# Example usage
if __name__ == "__main__":
    print("=== Social Trading Platform Demo ===")

    # Generate demo platform
    platform = generate_demo_social_trading_data()

    print(f"\nPlatform Summary:")
    print(f"Total Traders: {len(platform.traders)}")
    print(f"Total Posts: {len(platform.posts)}")
    print(
        f"Total Copy Configs: {sum(len(configs) for configs in platform.copy_configs.values())}"
    )

    # Show trader leaderboard
    print(f"\n=== Trader Leaderboard ===")
    leaderboard = platform.get_trader_leaderboard(limit=5)
    for i, trader in enumerate(leaderboard, 1):
        print(f"\n🏆 #{i} {trader.display_name}")
        print(f"   Annual Return: {trader.annual_return*100:.1f}%")
        print(f"   Sharpe Ratio: {trader.sharpe_ratio:.2f}")
        print(f"   Win Rate: {trader.win_rate*100:.1f}%")
        print(f"   Tier: {trader.tier.value.title()}")
        print(
            f"   Followers: {trader.total_followers} | Copiers: {trader.total_copiers}"
        )

    # Show social feed
    print(f"\n=== Social Feed ===")
    feed = platform.get_social_feed("user_1", limit=3)
    for post in feed:
        print(f"\n📱 {post.trader_username}: {post.title}")
        print(f"   {post.content[:100]}...")
        print(f"   💙 {post.likes} | 💬 {post.comments} | 🔄 {post.shares}")
        if post.trade_symbol:
            print(
                f"   🎯 {post.trade_symbol} {post.trade_direction} | Confidence: {post.confidence*100:.0f}%"
            )

    # Show copy trading performance
    print(f"\n=== Copy Trading Performance ===")
    performance = platform.get_copy_trading_performance("user_1")
    print(f"Total Profit: ₹{performance['total_profit']:,.2f}")
    print(f"Total Trades Copied: {performance['total_trades']}")
    print(f"Active Copies: {performance['active_copies']}")
    print(f"Avg Profit per Trade: ₹{performance['avg_profit_per_trade']:,.2f}")

    # Show trader earnings
    print(f"\n=== Top Trader Earnings ===")
    top_trader_id = leaderboard[0].trader_id
    earnings = platform.calculate_trader_earnings(
        top_trader_id, datetime.now() - timedelta(days=30), datetime.now()
    )
    print(f"Trader: {earnings['trader_name']}")
    print(f"Monthly Earnings: ₹{earnings['total_earnings']:,.2f}")
    print(f"Followers Profit: ₹{earnings['total_followers_profit']:,.2f}")
    print(f"Fee Rate: {earnings['fee_rate']*100:.0f}%")
