"""
Enhanced Dashboard Data Generator
Creates realistic trading data for demonstration purposes
"""

import random
import datetime
from flask import jsonify


class DashboardDataGenerator:
    """
    Generates realistic trading data for dashboard demonstration
    """

    def __init__(self):
        self.base_portfolio_value = 50000  # Starting portfolio value
        self.daily_volatility = 0.02  # 2% daily volatility
        self.profit_bias = 0.003  # 0.3% positive bias for profitable trading

        # Mock positions
        self.positions = [
            {
                "symbol": "AAPL",
                "quantity": 25,
                "avg_price": 175.50,
                "current_price": 178.20,
                "pnl": 67.50,
                "pnl_percent": 1.54,
                "side": "LONG",
            },
            {
                "symbol": "TSLA",
                "quantity": 10,
                "avg_price": 245.80,
                "current_price": 251.30,
                "pnl": 55.00,
                "pnl_percent": 2.24,
                "side": "LONG",
            },
            {
                "symbol": "MSFT",
                "quantity": 15,
                "avg_price": 385.20,
                "current_price": 389.50,
                "pnl": 64.50,
                "pnl_percent": 1.12,
                "side": "LONG",
            },
            {
                "symbol": "NVDA",
                "quantity": 8,
                "avg_price": 420.00,
                "current_price": 432.80,
                "pnl": 102.40,
                "pnl_percent": 3.05,
                "side": "LONG",
            },
        ]

        # Mock recent trades
        self.recent_trades = [
            {
                "id": "TRD_001",
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 25,
                "price": 175.50,
                "timestamp": "2025-08-12 10:15:30",
                "strategy": "Grid Trading",
                "pnl": 67.50,
                "status": "FILLED",
            },
            {
                "id": "TRD_002",
                "symbol": "TSLA",
                "side": "BUY",
                "quantity": 10,
                "price": 245.80,
                "timestamp": "2025-08-12 11:22:15",
                "strategy": "Mean Reversion",
                "pnl": 55.00,
                "status": "FILLED",
            },
            {
                "id": "TRD_003",
                "symbol": "MSFT",
                "side": "BUY",
                "quantity": 15,
                "price": 385.20,
                "timestamp": "2025-08-12 12:45:20",
                "strategy": "Momentum",
                "pnl": 64.50,
                "status": "FILLED",
            },
            {
                "id": "TRD_004",
                "symbol": "NVDA",
                "side": "BUY",
                "quantity": 8,
                "price": 420.00,
                "timestamp": "2025-08-12 14:30:45",
                "strategy": "Breakout",
                "pnl": 102.40,
                "status": "FILLED",
            },
        ]

    def generate_portfolio_summary(self):
        """Generate realistic portfolio summary data"""

        # Calculate total portfolio value
        total_value = sum(
            pos["quantity"] * pos["current_price"] for pos in self.positions
        )
        total_cost = sum(pos["quantity"] * pos["avg_price"] for pos in self.positions)
        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost) * 100 if total_cost > 0 else 0

        # Generate daily P&L with some randomness
        daily_pnl = random.uniform(-500, 800)  # Biased towards profit
        daily_pnl_percent = (daily_pnl / total_value) * 100 if total_value > 0 else 0

        # Portfolio change (simulated)
        portfolio_change = random.uniform(-200, 600)
        portfolio_change_percent = (
            (portfolio_change / total_value) * 100 if total_value > 0 else 0
        )

        return {
            "success": True,
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round(total_pnl_percent, 2),
            "daily_pnl": round(daily_pnl, 2),
            "daily_pnl_percent": round(daily_pnl_percent, 2),
            "portfolio_change": round(portfolio_change, 2),
            "portfolio_change_percent": round(portfolio_change_percent, 2),
            "positions_count": len(self.positions),
            "cash_available": round(self.base_portfolio_value - total_cost, 2),
            "total_invested": round(total_cost, 2),
        }

    def generate_bot_status(self):
        """Generate bot status data"""
        return {
            "success": True,
            "stock_bot": {
                "running": True,
                "strategy": "Multi-Strategy Enhanced",
                "uptime": "2h 45m",
                "trades_today": 12,
                "profit_today": 350.75,
                "win_rate": 78.5,
            },
            "crypto_bot": {
                "running": True,
                "strategy": "Crypto Momentum + Mean Reversion",
                "uptime": "3h 12m",
                "trades_today": 18,
                "profit_today": 425.30,
                "win_rate": 82.3,
            },
            "grid_bot": {
                "running": False,
                "available": True,
                "estimated_daily_return": "2-5%",
                "description": "Pionex-style Grid Trading for consistent profits",
            },
            "overall_status": {
                "total_trades_today": 30,
                "total_profit_today": 776.05,
                "average_win_rate": 80.4,
                "active_strategies": 5,
            },
        }

    def generate_recent_activity(self):
        """Generate recent trading activity"""

        # Add some time variation to recent trades
        now = datetime.datetime.now()
        activities = []

        for i, trade in enumerate(self.recent_trades):
            time_offset = datetime.timedelta(
                hours=random.randint(1, 8), minutes=random.randint(0, 59)
            )
            trade_time = now - time_offset

            activities.append(
                {
                    "id": trade["id"],
                    "type": "TRADE",
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "quantity": trade["quantity"],
                    "price": trade["price"],
                    "timestamp": trade_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "strategy": trade["strategy"],
                    "pnl": trade["pnl"],
                    "status": trade["status"],
                    "description": f"{trade['side']} {trade['quantity']} {trade['symbol']} @ ${trade['price']}",
                }
            )

        # Add some system activities
        activities.extend(
            [
                {
                    "id": "SYS_001",
                    "type": "SYSTEM",
                    "description": "Stock bot started successfully",
                    "timestamp": (now - datetime.timedelta(hours=3)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "status": "SUCCESS",
                },
                {
                    "id": "SYS_002",
                    "type": "SYSTEM",
                    "description": "Crypto bot strategy optimized",
                    "timestamp": (now - datetime.timedelta(hours=2)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "status": "SUCCESS",
                },
            ]
        )

        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "success": True,
            "activities": activities[:20],  # Return last 20 activities
        }

    def generate_ai_signals(self):
        """Generate AI trading signals"""

        signals = [
            {
                "symbol": "AAPL",
                "signal": "BUY",
                "confidence": 85.2,
                "target_price": 185.00,
                "current_price": 178.20,
                "potential_return": 3.81,
                "timeframe": "1-3 days",
                "strategy": "Momentum + Volume Analysis",
            },
            {
                "symbol": "MSFT",
                "signal": "HOLD",
                "confidence": 72.8,
                "target_price": 395.00,
                "current_price": 389.50,
                "potential_return": 1.41,
                "timeframe": "3-5 days",
                "strategy": "Technical Analysis",
            },
            {
                "symbol": "NVDA",
                "signal": "STRONG_BUY",
                "confidence": 92.1,
                "target_price": 450.00,
                "current_price": 432.80,
                "potential_return": 3.97,
                "timeframe": "1-2 days",
                "strategy": "AI Sentiment + Technical",
            },
            {
                "symbol": "TSLA",
                "signal": "BUY",
                "confidence": 78.5,
                "target_price": 265.00,
                "current_price": 251.30,
                "potential_return": 5.45,
                "timeframe": "2-4 days",
                "strategy": "Mean Reversion + News Analysis",
            },
        ]

        return {
            "success": True,
            "signals": signals,
            "market_sentiment": "BULLISH",
            "confidence_score": 83.7,
            "recommendation": "INCREASE_POSITIONS",
        }


# Global instance
dashboard_generator = DashboardDataGenerator()
