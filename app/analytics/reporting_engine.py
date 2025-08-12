"""
Advanced Analytics and Reporting Dashboard for Trade Mantra
Comprehensive performance analytics, tax reporting, and business intelligence
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta, date
import json
import uuid
import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
import calendar


class ReportType(Enum):
    """Types of reports available"""

    PERFORMANCE = "performance"
    TAX = "tax"
    RISK = "risk"
    TRADING_SUMMARY = "trading_summary"
    STRATEGY_ANALYSIS = "strategy_analysis"
    COMPLIANCE = "compliance"
    PORTFOLIO_ATTRIBUTION = "portfolio_attribution"


class TimeFrame(Enum):
    """Time frames for analysis"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class TaxEvent(Enum):
    """Types of tax events"""

    SHORT_TERM_CAPITAL_GAIN = "short_term_capital_gain"
    LONG_TERM_CAPITAL_GAIN = "long_term_capital_gain"
    SHORT_TERM_CAPITAL_LOSS = "short_term_capital_loss"
    LONG_TERM_CAPITAL_LOSS = "long_term_capital_loss"
    DIVIDEND_INCOME = "dividend_income"
    INTEREST_INCOME = "interest_income"
    BROKERAGE_FEES = "brokerage_fees"
    STT = "securities_transaction_tax"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""

    # Return metrics
    total_return: float
    annualized_return: float
    excess_return: float  # vs benchmark

    # Risk metrics
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    var_95: float

    # Trading metrics
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float

    # Consistency metrics
    monthly_win_rate: float
    consecutive_wins: int
    consecutive_losses: int

    # Benchmark comparison
    beta: float
    alpha: float
    correlation: float
    tracking_error: float
    information_ratio: float


@dataclass
class TaxReport:
    """Tax calculation report"""

    financial_year: str
    user_id: str

    # Capital gains
    short_term_gains: float
    long_term_gains: float
    short_term_losses: float
    long_term_losses: float
    net_capital_gains: float

    # Other income
    dividend_income: float
    interest_income: float

    # Deductions
    brokerage_fees: float
    stt_paid: float
    other_charges: float

    # Tax calculations
    taxable_income: float
    tax_liability: float
    advance_tax_paid: float
    tds_deducted: float

    # Detailed transactions
    detailed_transactions: List[Dict]

    generated_at: datetime


@dataclass
class StrategyPerformance:
    """Strategy-specific performance analysis"""

    strategy_id: str
    strategy_name: str

    # Performance
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Returns
    total_return: float
    avg_return_per_trade: float
    best_trade: float
    worst_trade: float

    # Risk
    max_drawdown: float
    volatility: float
    sharpe_ratio: float

    # Trading patterns
    avg_holding_period: float
    preferred_symbols: List[str]
    sector_allocation: Dict[str, float]

    # Time analysis
    performance_by_month: Dict[str, float]
    performance_by_day: Dict[str, float]
    performance_by_hour: Dict[str, float]


class PerformanceAnalyzer:
    """Advanced performance analytics engine"""

    def __init__(self):
        self.benchmark_data = self._load_benchmark_data()

    def calculate_performance_metrics(
        self,
        returns: List[float],
        benchmark_returns: List[float] = None,
        trades: List[Dict] = None,
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not returns:
            return self._empty_performance_metrics()

        returns_array = np.array(returns)

        # Basic return metrics
        total_return = np.prod(1 + returns_array) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1

        # Benchmark comparison
        excess_return = 0
        beta = 1.0
        alpha = 0
        correlation = 0
        tracking_error = 0
        information_ratio = 0

        if benchmark_returns and len(benchmark_returns) == len(returns):
            benchmark_array = np.array(benchmark_returns)
            excess_returns = returns_array - benchmark_array
            excess_return = np.mean(excess_returns)

            # Beta calculation
            covariance = np.cov(returns_array, benchmark_array)[0, 1]
            benchmark_variance = np.var(benchmark_array)
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 1.0

            # Alpha calculation
            alpha = annualized_return - (beta * np.mean(benchmark_array) * 252)

            # Correlation
            correlation = np.corrcoef(returns_array, benchmark_array)[0, 1]

            # Tracking error
            tracking_error = np.std(excess_returns) * np.sqrt(252)

            # Information ratio
            information_ratio = (
                excess_return / tracking_error if tracking_error != 0 else 0
            )

        # Risk metrics
        volatility = np.std(returns_array) * np.sqrt(252)

        # Sharpe ratio (assuming risk-free rate of 6%)
        risk_free_rate = 0.06
        sharpe_ratio = (
            (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
        )

        # Sortino ratio
        downside_returns = returns_array[returns_array < 0]
        downside_deviation = (
            np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
        )
        sortino_ratio = (
            (annualized_return - risk_free_rate) / downside_deviation
            if downside_deviation != 0
            else 0
        )

        # Maximum drawdown
        cumulative = np.cumprod(1 + returns_array)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)

        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Value at Risk (95%)
        var_95 = np.percentile(returns_array, 5)

        # Trading metrics (if trades provided)
        win_rate = 0
        profit_factor = 0
        avg_win = 0
        avg_loss = 0
        largest_win = 0
        largest_loss = 0
        monthly_win_rate = 0
        consecutive_wins = 0
        consecutive_losses = 0

        if trades:
            profits = [t["pnl"] for t in trades if t["pnl"] > 0]
            losses = [t["pnl"] for t in trades if t["pnl"] < 0]

            win_rate = len(profits) / len(trades) if trades else 0

            if profits and losses:
                avg_win = np.mean(profits)
                avg_loss = np.mean(losses)
                profit_factor = sum(profits) / abs(sum(losses))
                largest_win = max(profits)
                largest_loss = min(losses)

            # Calculate consecutive wins/losses
            consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(
                trades
            )

            # Monthly win rate
            monthly_win_rate = self._calculate_monthly_win_rate(trades)

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            excess_return=excess_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            monthly_win_rate=monthly_win_rate,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            beta=beta,
            alpha=alpha,
            correlation=correlation,
            tracking_error=tracking_error,
            information_ratio=information_ratio,
        )

    def analyze_strategy_performance(
        self, strategy_id: str, trades: List[Dict]
    ) -> StrategyPerformance:
        """Analyze performance of a specific strategy"""
        if not trades:
            return self._empty_strategy_performance(strategy_id, "Unknown Strategy")

        strategy_name = trades[0].get("strategy_name", f"Strategy {strategy_id}")

        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t["pnl"] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Return metrics
        total_pnl = sum(t["pnl"] for t in trades)
        avg_return_per_trade = total_pnl / total_trades if total_trades > 0 else 0
        best_trade = max(t["pnl"] for t in trades) if trades else 0
        worst_trade = min(t["pnl"] for t in trades) if trades else 0

        # Calculate total return percentage
        initial_capital = trades[0].get("initial_capital", 100000)  # Default 1L
        total_return = total_pnl / initial_capital if initial_capital > 0 else 0

        # Risk metrics
        returns = [t["pnl"] / initial_capital for t in trades]
        max_drawdown = self._calculate_strategy_drawdown(trades, initial_capital)
        volatility = np.std(returns) * np.sqrt(252) if returns else 0
        sharpe_ratio = (total_return - 0.06) / volatility if volatility != 0 else 0

        # Trading patterns
        holding_periods = [
            (t["exit_time"] - t["entry_time"]).total_seconds() / 3600  # hours
            for t in trades
            if "exit_time" in t and "entry_time" in t
        ]
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0

        # Symbol analysis
        symbol_counts = {}
        for trade in trades:
            symbol = trade.get("symbol", "Unknown")
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

        preferred_symbols = sorted(
            symbol_counts.keys(), key=lambda x: symbol_counts[x], reverse=True
        )[:5]

        # Sector allocation (mock data)
        sector_allocation = self._calculate_sector_allocation(trades)

        # Time-based performance
        performance_by_month = self._analyze_monthly_performance(trades)
        performance_by_day = self._analyze_daily_performance(trades)
        performance_by_hour = self._analyze_hourly_performance(trades)

        return StrategyPerformance(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            avg_return_per_trade=avg_return_per_trade,
            best_trade=best_trade,
            worst_trade=worst_trade,
            max_drawdown=max_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            avg_holding_period=avg_holding_period,
            preferred_symbols=preferred_symbols,
            sector_allocation=sector_allocation,
            performance_by_month=performance_by_month,
            performance_by_day=performance_by_day,
            performance_by_hour=performance_by_hour,
        )

    def _calculate_consecutive_trades(self, trades: List[Dict]) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses"""
        if not trades:
            return 0, 0

        max_wins = current_wins = 0
        max_losses = current_losses = 0

        for trade in trades:
            if trade["pnl"] > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    def _calculate_monthly_win_rate(self, trades: List[Dict]) -> float:
        """Calculate percentage of profitable months"""
        if not trades:
            return 0

        monthly_pnl = {}
        for trade in trades:
            trade_date = trade.get("date", datetime.now())
            month_key = f"{trade_date.year}-{trade_date.month:02d}"
            monthly_pnl[month_key] = monthly_pnl.get(month_key, 0) + trade["pnl"]

        profitable_months = len([pnl for pnl in monthly_pnl.values() if pnl > 0])
        total_months = len(monthly_pnl)

        return profitable_months / total_months if total_months > 0 else 0

    def _calculate_strategy_drawdown(
        self, trades: List[Dict], initial_capital: float
    ) -> float:
        """Calculate maximum drawdown for strategy"""
        if not trades:
            return 0

        cumulative_pnl = 0
        peak = initial_capital
        max_drawdown = 0

        for trade in trades:
            cumulative_pnl += trade["pnl"]
            current_value = initial_capital + cumulative_pnl

            if current_value > peak:
                peak = current_value

            drawdown = (peak - current_value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_sector_allocation(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate sector allocation (mock implementation)"""
        # Mock sector mapping
        sector_map = {
            "RELIANCE": "Oil & Gas",
            "TCS": "IT",
            "INFY": "IT",
            "HDFC": "Banking",
            "ICICI": "Banking",
            "WIPRO": "IT",
            "HUL": "FMCG",
            "ITC": "FMCG",
        }

        sector_counts = {}
        total_trades = len(trades)

        for trade in trades:
            symbol = trade.get("symbol", "Unknown")
            sector = sector_map.get(symbol, "Others")
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        return {sector: count / total_trades for sector, count in sector_counts.items()}

    def _analyze_monthly_performance(self, trades: List[Dict]) -> Dict[str, float]:
        """Analyze performance by month"""
        monthly_pnl = {}
        for trade in trades:
            trade_date = trade.get("date", datetime.now())
            month_name = calendar.month_name[trade_date.month]
            monthly_pnl[month_name] = monthly_pnl.get(month_name, 0) + trade["pnl"]

        return monthly_pnl

    def _analyze_daily_performance(self, trades: List[Dict]) -> Dict[str, float]:
        """Analyze performance by day of week"""
        daily_pnl = {}
        for trade in trades:
            trade_date = trade.get("date", datetime.now())
            day_name = calendar.day_name[trade_date.weekday()]
            daily_pnl[day_name] = daily_pnl.get(day_name, 0) + trade["pnl"]

        return daily_pnl

    def _analyze_hourly_performance(self, trades: List[Dict]) -> Dict[str, float]:
        """Analyze performance by hour of day"""
        hourly_pnl = {}
        for trade in trades:
            trade_date = trade.get("date", datetime.now())
            hour = f"{trade_date.hour:02d}:00"
            hourly_pnl[hour] = hourly_pnl.get(hour, 0) + trade["pnl"]

        return hourly_pnl

    def _load_benchmark_data(self) -> Dict:
        """Load benchmark data (mock implementation)"""
        # In production, this would load actual Nifty/Sensex data
        return {
            "NIFTY50": {"annual_return": 0.12, "volatility": 0.18, "sharpe_ratio": 0.67}
        }

    def _empty_performance_metrics(self) -> PerformanceMetrics:
        """Return empty performance metrics"""
        return PerformanceMetrics(
            total_return=0,
            annualized_return=0,
            excess_return=0,
            volatility=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            max_drawdown=0,
            var_95=0,
            win_rate=0,
            profit_factor=0,
            avg_win=0,
            avg_loss=0,
            largest_win=0,
            largest_loss=0,
            monthly_win_rate=0,
            consecutive_wins=0,
            consecutive_losses=0,
            beta=0,
            alpha=0,
            correlation=0,
            tracking_error=0,
            information_ratio=0,
        )

    def _empty_strategy_performance(
        self, strategy_id: str, strategy_name: str
    ) -> StrategyPerformance:
        """Return empty strategy performance"""
        return StrategyPerformance(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            total_return=0,
            avg_return_per_trade=0,
            best_trade=0,
            worst_trade=0,
            max_drawdown=0,
            volatility=0,
            sharpe_ratio=0,
            avg_holding_period=0,
            preferred_symbols=[],
            sector_allocation={},
            performance_by_month={},
            performance_by_day={},
            performance_by_hour={},
        )


class TaxCalculator:
    """Advanced tax calculation and reporting"""

    # Indian tax rates for AY 2024-25
    TAX_SLABS = [
        (250000, 0.0),  # Up to 2.5L - 0%
        (500000, 0.05),  # 2.5L to 5L - 5%
        (750000, 0.10),  # 5L to 7.5L - 10%
        (1000000, 0.15),  # 7.5L to 10L - 15%
        (1250000, 0.20),  # 10L to 12.5L - 20%
        (1500000, 0.25),  # 12.5L to 15L - 25%
        (float("inf"), 0.30),  # Above 15L - 30%
    ]

    # Capital gains tax rates
    STCG_RATE = 0.15  # Short-term capital gains - 15%
    LTCG_RATE = 0.10  # Long-term capital gains - 10% (above 1L exemption)
    LTCG_EXEMPTION = 100000  # ₹1 lakh exemption for LTCG

    def __init__(self):
        self.stt_rates = {
            "equity_delivery": 0.00025,  # 0.025% on sell side
            "equity_intraday": 0.000025,  # 0.0025% on both sides
            "equity_futures": 0.0001,  # 0.01% on sell side
            "equity_options": 0.0001,  # 0.01% on sell side
        }

    def calculate_tax_report(
        self, user_id: str, transactions: List[Dict], financial_year: str
    ) -> TaxReport:
        """Calculate comprehensive tax report"""

        # Separate transactions by type
        capital_gains_txns = []
        dividend_txns = []
        interest_txns = []
        fee_txns = []

        for txn in transactions:
            txn_type = txn.get("type", "trade")
            if txn_type in ["buy", "sell"]:
                capital_gains_txns.append(txn)
            elif txn_type == "dividend":
                dividend_txns.append(txn)
            elif txn_type == "interest":
                interest_txns.append(txn)
            elif txn_type in ["brokerage", "stt", "fees"]:
                fee_txns.append(txn)

        # Calculate capital gains
        capital_gains = self._calculate_capital_gains(capital_gains_txns)

        # Calculate other income
        dividend_income = sum(txn.get("amount", 0) for txn in dividend_txns)
        interest_income = sum(txn.get("amount", 0) for txn in interest_txns)

        # Calculate deductions
        brokerage_fees = sum(
            txn.get("amount", 0) for txn in fee_txns if txn.get("type") == "brokerage"
        )
        stt_paid = sum(
            txn.get("amount", 0) for txn in fee_txns if txn.get("type") == "stt"
        )
        other_charges = sum(
            txn.get("amount", 0)
            for txn in fee_txns
            if txn.get("type") not in ["brokerage", "stt"]
        )

        # Net capital gains
        net_capital_gains = (
            capital_gains["short_term_gains"]
            + capital_gains["long_term_gains"]
            - capital_gains["short_term_losses"]
            - capital_gains["long_term_losses"]
        )

        # Taxable income (simplified)
        taxable_capital_gains = max(0, net_capital_gains)
        taxable_ltcg = max(0, capital_gains["long_term_gains"] - self.LTCG_EXEMPTION)
        taxable_stcg = max(0, capital_gains["short_term_gains"])

        # Tax calculations
        stcg_tax = taxable_stcg * self.STCG_RATE
        ltcg_tax = taxable_ltcg * self.LTCG_RATE
        total_tax_liability = stcg_tax + ltcg_tax

        # Generate detailed transaction list
        detailed_transactions = self._generate_detailed_tax_transactions(
            capital_gains_txns, financial_year
        )

        return TaxReport(
            financial_year=financial_year,
            user_id=user_id,
            short_term_gains=capital_gains["short_term_gains"],
            long_term_gains=capital_gains["long_term_gains"],
            short_term_losses=capital_gains["short_term_losses"],
            long_term_losses=capital_gains["long_term_losses"],
            net_capital_gains=net_capital_gains,
            dividend_income=dividend_income,
            interest_income=interest_income,
            brokerage_fees=brokerage_fees,
            stt_paid=stt_paid,
            other_charges=other_charges,
            taxable_income=taxable_capital_gains,
            tax_liability=total_tax_liability,
            advance_tax_paid=0,  # To be filled by user
            tds_deducted=0,  # To be filled by user
            detailed_transactions=detailed_transactions,
            generated_at=datetime.now(),
        )

    def _calculate_capital_gains(self, transactions: List[Dict]) -> Dict[str, float]:
        """Calculate capital gains using FIFO method"""
        holdings = {}  # symbol -> list of (quantity, price, date)
        gains = {
            "short_term_gains": 0,
            "long_term_gains": 0,
            "short_term_losses": 0,
            "long_term_losses": 0,
        }

        for txn in sorted(transactions, key=lambda x: x.get("date", datetime.now())):
            symbol = txn["symbol"]
            quantity = txn["quantity"]
            price = txn["price"]
            txn_date = txn.get("date", datetime.now())

            if symbol not in holdings:
                holdings[symbol] = []

            if txn["side"] == "buy":
                holdings[symbol].append((quantity, price, txn_date))

            elif txn["side"] == "sell":
                remaining_to_sell = quantity

                while remaining_to_sell > 0 and holdings[symbol]:
                    buy_qty, buy_price, buy_date = holdings[symbol][0]

                    # Determine if short-term or long-term
                    holding_period = (txn_date - buy_date).days
                    is_long_term = holding_period > 365

                    # Calculate quantity to sell from this lot
                    sell_qty = min(remaining_to_sell, buy_qty)

                    # Calculate gain/loss
                    gain_loss = sell_qty * (price - buy_price)

                    # Categorize gain/loss
                    if gain_loss > 0:
                        if is_long_term:
                            gains["long_term_gains"] += gain_loss
                        else:
                            gains["short_term_gains"] += gain_loss
                    else:
                        if is_long_term:
                            gains["long_term_losses"] += abs(gain_loss)
                        else:
                            gains["short_term_losses"] += abs(gain_loss)

                    # Update holdings
                    if sell_qty == buy_qty:
                        holdings[symbol].pop(0)
                    else:
                        holdings[symbol][0] = (buy_qty - sell_qty, buy_price, buy_date)

                    remaining_to_sell -= sell_qty

        return gains

    def _generate_detailed_tax_transactions(
        self, transactions: List[Dict], financial_year: str
    ) -> List[Dict]:
        """Generate detailed transaction list for tax filing"""
        detailed = []

        for txn in transactions:
            detailed.append(
                {
                    "date": txn.get("date", datetime.now()).strftime("%Y-%m-%d"),
                    "symbol": txn["symbol"],
                    "transaction_type": txn["side"].upper(),
                    "quantity": txn["quantity"],
                    "price": txn["price"],
                    "value": txn["quantity"] * txn["price"],
                    "brokerage": txn.get("brokerage", 0),
                    "stt": txn.get("stt", 0),
                    "total_charges": txn.get("total_charges", 0),
                }
            )

        return detailed


class ReportGenerator:
    """Generate various types of reports"""

    def __init__(self):
        self.performance_analyzer = PerformanceAnalyzer()
        self.tax_calculator = TaxCalculator()

    def generate_performance_report(
        self,
        user_id: str,
        portfolio_data: Dict,
        time_frame: TimeFrame = TimeFrame.MONTHLY,
    ) -> Dict:
        """Generate comprehensive performance report"""

        # Extract data
        trades = portfolio_data.get("trades", [])
        positions = portfolio_data.get("positions", [])
        returns = portfolio_data.get("daily_returns", [])

        # Calculate performance metrics
        performance = self.performance_analyzer.calculate_performance_metrics(
            returns, trades=trades
        )

        # Strategy breakdown
        strategy_performance = {}
        strategies = {}
        for trade in trades:
            strategy_id = trade.get("strategy_id", "manual")
            if strategy_id not in strategies:
                strategies[strategy_id] = []
            strategies[strategy_id].append(trade)

        for strategy_id, strategy_trades in strategies.items():
            strategy_performance[strategy_id] = (
                self.performance_analyzer.analyze_strategy_performance(
                    strategy_id, strategy_trades
                )
            )

        # Portfolio attribution
        portfolio_attribution = self._calculate_portfolio_attribution(positions)

        return {
            "user_id": user_id,
            "report_type": ReportType.PERFORMANCE.value,
            "time_frame": time_frame.value,
            "generated_at": datetime.now().isoformat(),
            "overall_performance": {
                "total_return": performance.total_return * 100,
                "annualized_return": performance.annualized_return * 100,
                "volatility": performance.volatility * 100,
                "sharpe_ratio": performance.sharpe_ratio,
                "max_drawdown": performance.max_drawdown * 100,
                "win_rate": performance.win_rate * 100,
                "profit_factor": performance.profit_factor,
            },
            "risk_metrics": {
                "var_95": performance.var_95 * 100,
                "sortino_ratio": performance.sortino_ratio,
                "calmar_ratio": performance.calmar_ratio,
                "beta": performance.beta,
                "alpha": performance.alpha * 100,
                "correlation": performance.correlation,
            },
            "trading_statistics": {
                "total_trades": len(trades),
                "winning_trades": int(len(trades) * performance.win_rate),
                "avg_win": performance.avg_win,
                "avg_loss": performance.avg_loss,
                "largest_win": performance.largest_win,
                "largest_loss": performance.largest_loss,
                "consecutive_wins": performance.consecutive_wins,
                "consecutive_losses": performance.consecutive_losses,
            },
            "strategy_breakdown": {
                strategy_id: {
                    "name": perf.strategy_name,
                    "total_return": perf.total_return * 100,
                    "win_rate": perf.win_rate * 100,
                    "sharpe_ratio": perf.sharpe_ratio,
                    "total_trades": perf.total_trades,
                    "avg_holding_period": perf.avg_holding_period,
                }
                for strategy_id, perf in strategy_performance.items()
            },
            "portfolio_attribution": portfolio_attribution,
        }

    def generate_tax_report(
        self, user_id: str, transactions: List[Dict], financial_year: str
    ) -> Dict:
        """Generate tax report"""
        tax_report = self.tax_calculator.calculate_tax_report(
            user_id, transactions, financial_year
        )

        return {
            "user_id": user_id,
            "report_type": ReportType.TAX.value,
            "financial_year": financial_year,
            "generated_at": tax_report.generated_at.isoformat(),
            "capital_gains_summary": {
                "short_term_gains": tax_report.short_term_gains,
                "long_term_gains": tax_report.long_term_gains,
                "short_term_losses": tax_report.short_term_losses,
                "long_term_losses": tax_report.long_term_losses,
                "net_capital_gains": tax_report.net_capital_gains,
            },
            "other_income": {
                "dividend_income": tax_report.dividend_income,
                "interest_income": tax_report.interest_income,
            },
            "deductions": {
                "brokerage_fees": tax_report.brokerage_fees,
                "stt_paid": tax_report.stt_paid,
                "other_charges": tax_report.other_charges,
            },
            "tax_calculation": {
                "taxable_income": tax_report.taxable_income,
                "tax_liability": tax_report.tax_liability,
                "advance_tax_paid": tax_report.advance_tax_paid,
                "tds_deducted": tax_report.tds_deducted,
                "net_tax_due": tax_report.tax_liability
                - tax_report.advance_tax_paid
                - tax_report.tds_deducted,
            },
            "detailed_transactions": tax_report.detailed_transactions[
                :100
            ],  # Limit for response size
        }

    def _calculate_portfolio_attribution(self, positions: List[Dict]) -> Dict:
        """Calculate portfolio attribution by sector and asset class"""
        if not positions:
            return {"sectors": {}, "asset_classes": {}}

        total_value = sum(pos.get("market_value", 0) for pos in positions)

        # Sector attribution
        sector_attribution = {}
        asset_class_attribution = {}

        for position in positions:
            market_value = position.get("market_value", 0)
            weight = market_value / total_value if total_value > 0 else 0

            # Sector
            sector = position.get("sector", "Others")
            if sector not in sector_attribution:
                sector_attribution[sector] = {"weight": 0, "return": 0, "value": 0}

            sector_attribution[sector]["weight"] += weight
            sector_attribution[sector]["value"] += market_value
            sector_attribution[sector]["return"] += position.get("return", 0) * weight

            # Asset class
            asset_class = position.get("asset_class", "Equity")
            if asset_class not in asset_class_attribution:
                asset_class_attribution[asset_class] = {
                    "weight": 0,
                    "return": 0,
                    "value": 0,
                }

            asset_class_attribution[asset_class]["weight"] += weight
            asset_class_attribution[asset_class]["value"] += market_value
            asset_class_attribution[asset_class]["return"] += (
                position.get("return", 0) * weight
            )

        return {
            "sectors": {
                sector: {
                    "weight_percent": data["weight"] * 100,
                    "value": data["value"],
                    "contribution_to_return": data["return"] * 100,
                }
                for sector, data in sector_attribution.items()
            },
            "asset_classes": {
                asset_class: {
                    "weight_percent": data["weight"] * 100,
                    "value": data["value"],
                    "contribution_to_return": data["return"] * 100,
                }
                for asset_class, data in asset_class_attribution.items()
            },
        }


# Demo usage
def demo_analytics_system():
    """Demonstrate the analytics and reporting system"""
    print("=== Advanced Analytics System Demo ===")

    # Initialize system
    report_generator = ReportGenerator()

    # Mock portfolio data
    mock_trades = [
        {
            "symbol": "RELIANCE",
            "side": "buy",
            "quantity": 100,
            "price": 2400,
            "pnl": 15000,
            "strategy_id": "momentum_1",
            "strategy_name": "Momentum Strategy",
            "date": datetime.now() - timedelta(days=30),
            "entry_time": datetime.now() - timedelta(days=30),
            "exit_time": datetime.now() - timedelta(days=25),
            "initial_capital": 100000,
        },
        {
            "symbol": "TCS",
            "side": "buy",
            "quantity": 50,
            "price": 3600,
            "pnl": -5000,
            "strategy_id": "mean_reversion_1",
            "strategy_name": "Mean Reversion",
            "date": datetime.now() - timedelta(days=20),
            "entry_time": datetime.now() - timedelta(days=20),
            "exit_time": datetime.now() - timedelta(days=18),
            "initial_capital": 100000,
        },
        {
            "symbol": "HDFC",
            "side": "buy",
            "quantity": 80,
            "price": 2500,
            "pnl": 8000,
            "strategy_id": "momentum_1",
            "strategy_name": "Momentum Strategy",
            "date": datetime.now() - timedelta(days=15),
            "entry_time": datetime.now() - timedelta(days=15),
            "exit_time": datetime.now() - timedelta(days=10),
            "initial_capital": 100000,
        },
    ]

    mock_positions = [
        {
            "symbol": "RELIANCE",
            "market_value": 250000,
            "return": 0.06,
            "sector": "Oil & Gas",
            "asset_class": "Equity",
        },
        {
            "symbol": "TCS",
            "market_value": 180000,
            "return": -0.03,
            "sector": "IT",
            "asset_class": "Equity",
        },
        {
            "symbol": "HDFC",
            "market_value": 200000,
            "return": 0.04,
            "sector": "Banking",
            "asset_class": "Equity",
        },
    ]

    mock_returns = [
        0.02,
        -0.01,
        0.015,
        0.005,
        -0.008,
        0.012,
        0.001,
        -0.005,
        0.018,
        -0.003,
        0.007,
        0.011,
        -0.002,
        0.009,
        0.004,
        -0.006,
        0.013,
        0.008,
        -0.004,
        0.016,
        0.003,
        -0.001,
        0.010,
        0.002,
        -0.007,
        0.014,
        0.006,
        -0.003,
        0.008,
        0.012,
    ]

    portfolio_data = {
        "trades": mock_trades,
        "positions": mock_positions,
        "daily_returns": mock_returns,
    }

    # Generate performance report
    performance_report = report_generator.generate_performance_report(
        "user_123", portfolio_data
    )

    print(f"\n=== Performance Report Summary ===")
    print(
        f"Total Return: {performance_report['overall_performance']['total_return']:.1f}%"
    )
    print(
        f"Annualized Return: {performance_report['overall_performance']['annualized_return']:.1f}%"
    )
    print(
        f"Sharpe Ratio: {performance_report['overall_performance']['sharpe_ratio']:.2f}"
    )
    print(
        f"Max Drawdown: {performance_report['overall_performance']['max_drawdown']:.1f}%"
    )
    print(f"Win Rate: {performance_report['overall_performance']['win_rate']:.1f}%")

    print(f"\n=== Strategy Breakdown ===")
    for strategy_id, strategy_data in performance_report["strategy_breakdown"].items():
        print(f"{strategy_data['name']}:")
        print(f"  Return: {strategy_data['total_return']:.1f}%")
        print(f"  Win Rate: {strategy_data['win_rate']:.1f}%")
        print(f"  Total Trades: {strategy_data['total_trades']}")

    print(f"\n=== Portfolio Attribution ===")
    for sector, data in performance_report["portfolio_attribution"]["sectors"].items():
        print(f"{sector}: {data['weight_percent']:.1f}% (₹{data['value']:,.0f})")

    # Generate tax report
    mock_transactions = [
        {
            "symbol": "RELIANCE",
            "side": "buy",
            "quantity": 100,
            "price": 2400,
            "date": datetime(2023, 4, 15),
            "type": "buy",
        },
        {
            "symbol": "RELIANCE",
            "side": "sell",
            "quantity": 100,
            "price": 2550,
            "date": datetime(2024, 1, 15),
            "type": "sell",
        },
        {
            "symbol": "TCS",
            "side": "buy",
            "quantity": 50,
            "price": 3600,
            "date": datetime(2023, 6, 10),
            "type": "buy",
        },
        {
            "symbol": "TCS",
            "side": "sell",
            "quantity": 50,
            "price": 3500,
            "date": datetime(2023, 8, 20),
            "type": "sell",
        },
    ]

    tax_report = report_generator.generate_tax_report(
        "user_123", mock_transactions, "FY2023-24"
    )

    print(f"\n=== Tax Report Summary (FY2023-24) ===")
    print(
        f"Short-term Gains: ₹{tax_report['capital_gains_summary']['short_term_gains']:,.0f}"
    )
    print(
        f"Long-term Gains: ₹{tax_report['capital_gains_summary']['long_term_gains']:,.0f}"
    )
    print(
        f"Net Capital Gains: ₹{tax_report['capital_gains_summary']['net_capital_gains']:,.0f}"
    )
    print(f"Tax Liability: ₹{tax_report['tax_calculation']['tax_liability']:,.0f}")


if __name__ == "__main__":
    demo_analytics_system()
