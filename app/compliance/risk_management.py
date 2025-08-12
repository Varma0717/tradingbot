"""
Advanced Risk Management and Compliance System for Trade Mantra
SEBI compliance, risk controls, and regulatory reporting
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
import warnings

warnings.filterwarnings("ignore")


class RiskLevel(Enum):
    """Risk levels for different strategies and users"""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ComplianceType(Enum):
    """Types of compliance checks"""

    SEBI_POSITION_LIMITS = "sebi_position_limits"
    CIRCUIT_BREAKER = "circuit_breaker"
    MARGIN_REQUIREMENTS = "margin_requirements"
    CONCENTRATION_RISK = "concentration_risk"
    WASH_TRADING = "wash_trading"
    INSIDER_TRADING = "insider_trading"
    KYC_VERIFICATION = "kyc_verification"


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKED = "blocked"


@dataclass
class RiskMetrics:
    """Portfolio risk metrics"""

    portfolio_value: float
    total_pnl: float
    daily_pnl: float
    weekly_pnl: float
    monthly_pnl: float

    # Risk measures
    value_at_risk_1d: float  # 1-day VaR at 95% confidence
    value_at_risk_5d: float  # 5-day VaR at 95% confidence
    expected_shortfall: float  # Expected loss beyond VaR
    maximum_drawdown: float
    current_drawdown: float

    # Concentration metrics
    max_position_weight: float
    sector_concentration: Dict[str, float]
    top_5_concentration: float

    # Volatility metrics
    portfolio_volatility: float
    beta: float
    correlation_to_market: float

    # Leverage and margin
    gross_exposure: float
    net_exposure: float
    leverage_ratio: float
    margin_utilization: float

    last_updated: datetime


@dataclass
class ComplianceAlert:
    """Compliance violation alert"""

    alert_id: str
    user_id: str
    alert_type: ComplianceType
    severity: AlertSeverity
    title: str
    description: str
    recommendation: str
    affected_positions: List[str]
    threshold_breached: Optional[float]
    current_value: Optional[float]
    auto_action_taken: Optional[str]

    created_at: datetime
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    is_resolved: bool


@dataclass
class RiskLimits:
    """Risk limits configuration"""

    max_portfolio_risk: float  # Maximum portfolio VaR as % of capital
    max_position_size: float  # Maximum single position as % of portfolio
    max_sector_concentration: float  # Maximum sector exposure
    max_leverage: float  # Maximum leverage ratio
    max_daily_loss: float  # Maximum daily loss limit
    max_drawdown: float  # Maximum portfolio drawdown

    # Trading limits
    max_orders_per_day: int
    max_order_value: float
    min_liquidity_requirement: float  # Minimum cash as % of portfolio

    # Concentration limits
    max_single_stock: float  # % of portfolio
    max_correlated_positions: float  # Maximum correlation between positions


class SEBIComplianceManager:
    """SEBI compliance and regulatory requirements"""

    # SEBI position limits (simplified)
    SEBI_POSITION_LIMITS = {
        "NIFTY50": {
            "market_wide_limit": 0.15,  # 15% of market-wide position limit
            "individual_limit": 0.05,  # 5% of individual stock
        },
        "MIDCAP": {"market_wide_limit": 0.10, "individual_limit": 0.03},
        "SMALLCAP": {"market_wide_limit": 0.05, "individual_limit": 0.02},
    }

    # Circuit breaker limits
    CIRCUIT_BREAKER_LIMITS = {
        "NIFTY50": {"lower": 0.10, "upper": 0.20},  # 10% and 20% limits
        "MIDCAP": {"lower": 0.15, "upper": 0.30},
        "SMALLCAP": {"lower": 0.20, "upper": 0.40},
    }

    def __init__(self):
        self.compliance_alerts: Dict[str, ComplianceAlert] = {}

    def check_position_limits(
        self, user_id: str, symbol: str, position_value: float, market_cap_category: str
    ) -> Optional[ComplianceAlert]:
        """Check SEBI position limits"""
        limits = self.SEBI_POSITION_LIMITS.get(
            market_cap_category, self.SEBI_POSITION_LIMITS["SMALLCAP"]
        )

        # Mock market data for demonstration
        market_wide_position = 100_000_000  # ₹10 Cr market-wide position
        individual_stock_mcap = 50_000_000_000  # ₹500 Cr market cap

        # Check individual limit
        individual_limit_value = individual_stock_mcap * limits["individual_limit"]

        if position_value > individual_limit_value:
            return self._create_compliance_alert(
                user_id=user_id,
                alert_type=ComplianceType.SEBI_POSITION_LIMITS,
                severity=AlertSeverity.BLOCKED,
                title="SEBI Position Limit Exceeded",
                description=f"Position in {symbol} exceeds SEBI individual limit",
                recommendation=f"Reduce position to ₹{individual_limit_value:,.0f}",
                threshold_breached=individual_limit_value,
                current_value=position_value,
                affected_positions=[symbol],
            )

        return None

    def check_circuit_breaker(
        self, symbol: str, price_change: float, market_cap_category: str
    ) -> Optional[str]:
        """Check if stock hit circuit breaker"""
        limits = self.CIRCUIT_BREAKER_LIMITS.get(
            market_cap_category, self.CIRCUIT_BREAKER_LIMITS["SMALLCAP"]
        )

        if abs(price_change) >= limits["upper"]:
            return "TRADING_HALTED"
        elif abs(price_change) >= limits["lower"]:
            return "CIRCUIT_BREAKER_WARNING"

        return None

    def check_wash_trading(
        self, user_trades: List[Dict], time_window: timedelta = timedelta(minutes=30)
    ) -> List[ComplianceAlert]:
        """Detect potential wash trading patterns"""
        alerts = []

        # Group trades by symbol and time
        symbol_trades = {}
        for trade in user_trades:
            symbol = trade["symbol"]
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(trade)

        for symbol, trades in symbol_trades.items():
            # Check for rapid buy-sell patterns
            for i in range(len(trades) - 1):
                current_trade = trades[i]
                next_trade = trades[i + 1]

                time_diff = next_trade["timestamp"] - current_trade["timestamp"]

                if (
                    time_diff <= time_window
                    and current_trade["side"] != next_trade["side"]
                    and abs(current_trade["quantity"] - next_trade["quantity"])
                    / current_trade["quantity"]
                    < 0.1
                ):  # Similar quantities

                    alert = self._create_compliance_alert(
                        user_id=current_trade["user_id"],
                        alert_type=ComplianceType.WASH_TRADING,
                        severity=AlertSeverity.WARNING,
                        title="Potential Wash Trading Pattern",
                        description=f"Rapid buy-sell pattern detected in {symbol}",
                        recommendation="Review trading pattern to ensure compliance",
                        affected_positions=[symbol],
                    )
                    alerts.append(alert)

        return alerts

    def _create_compliance_alert(self, **kwargs) -> ComplianceAlert:
        """Create a compliance alert"""
        alert_id = str(uuid.uuid4())

        alert = ComplianceAlert(
            alert_id=alert_id,
            created_at=datetime.now(),
            resolved_at=None,
            resolution_notes=None,
            is_resolved=False,
            **kwargs,
        )

        self.compliance_alerts[alert_id] = alert
        return alert


class RiskManager:
    """Advanced risk management system"""

    def __init__(self):
        self.risk_limits: Dict[str, RiskLimits] = {}
        self.risk_metrics: Dict[str, RiskMetrics] = {}
        self.compliance_manager = SEBIComplianceManager()

    def set_risk_limits(self, user_id: str, limits: RiskLimits):
        """Set risk limits for a user"""
        self.risk_limits[user_id] = limits

    def calculate_portfolio_risk(
        self, user_id: str, positions: List[Dict], market_data: Dict
    ) -> RiskMetrics:
        """Calculate comprehensive portfolio risk metrics"""
        if not positions:
            return self._create_empty_risk_metrics()

        portfolio_value = sum(pos["market_value"] for pos in positions)
        total_pnl = sum(pos["unrealized_pnl"] for pos in positions)

        # Calculate VaR using parametric method (simplified)
        portfolio_volatility = self._calculate_portfolio_volatility(
            positions, market_data
        )
        var_1d = portfolio_value * portfolio_volatility * 1.645  # 95% confidence, 1-day
        var_5d = var_1d * np.sqrt(5)  # Scale to 5 days

        # Expected Shortfall (CVaR)
        expected_shortfall = var_1d * 1.3  # Approximation

        # Concentration analysis
        position_weights = [pos["market_value"] / portfolio_value for pos in positions]
        max_position_weight = max(position_weights)

        # Sector concentration
        sector_exposure = {}
        for pos in positions:
            sector = pos.get("sector", "Unknown")
            sector_exposure[sector] = (
                sector_exposure.get(sector, 0) + pos["market_value"]
            )

        sector_concentration = {
            sector: value / portfolio_value for sector, value in sector_exposure.items()
        }

        # Top 5 concentration
        sorted_weights = sorted(position_weights, reverse=True)
        top_5_concentration = sum(sorted_weights[:5])

        # Drawdown calculation
        # This would typically use historical portfolio values
        max_drawdown = -0.15  # Mock value
        current_drawdown = min(0, total_pnl / portfolio_value)

        # Beta and correlation (mock values)
        beta = np.random.uniform(0.8, 1.2)
        correlation_to_market = np.random.uniform(0.6, 0.9)

        # Leverage metrics
        gross_exposure = sum(abs(pos["market_value"]) for pos in positions)
        net_exposure = sum(pos["market_value"] for pos in positions)
        leverage_ratio = gross_exposure / portfolio_value if portfolio_value > 0 else 0

        # Mock margin utilization
        margin_utilization = np.random.uniform(0.3, 0.8)

        risk_metrics = RiskMetrics(
            portfolio_value=portfolio_value,
            total_pnl=total_pnl,
            daily_pnl=total_pnl * 0.1,  # Mock daily P&L
            weekly_pnl=total_pnl * 0.3,  # Mock weekly P&L
            monthly_pnl=total_pnl,
            value_at_risk_1d=var_1d,
            value_at_risk_5d=var_5d,
            expected_shortfall=expected_shortfall,
            maximum_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            max_position_weight=max_position_weight,
            sector_concentration=sector_concentration,
            top_5_concentration=top_5_concentration,
            portfolio_volatility=portfolio_volatility,
            beta=beta,
            correlation_to_market=correlation_to_market,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            leverage_ratio=leverage_ratio,
            margin_utilization=margin_utilization,
            last_updated=datetime.now(),
        )

        self.risk_metrics[user_id] = risk_metrics
        return risk_metrics

    def _calculate_portfolio_volatility(
        self, positions: List[Dict], market_data: Dict
    ) -> float:
        """Calculate portfolio volatility"""
        # Simplified calculation - in production would use covariance matrix
        if not positions:
            return 0.0

        # Mock individual volatilities
        individual_vols = [np.random.uniform(0.15, 0.35) for _ in positions]
        weights = [pos["market_value"] for pos in positions]
        total_value = sum(weights)

        if total_value == 0:
            return 0.0

        weights = [w / total_value for w in weights]

        # Simplified portfolio volatility (assuming average correlation of 0.3)
        avg_correlation = 0.3
        portfolio_variance = sum(
            w**2 * vol**2 for w, vol in zip(weights, individual_vols)
        )

        # Add correlation effects
        for i in range(len(weights)):
            for j in range(i + 1, len(weights)):
                portfolio_variance += (
                    2
                    * weights[i]
                    * weights[j]
                    * individual_vols[i]
                    * individual_vols[j]
                    * avg_correlation
                )

        return np.sqrt(portfolio_variance)

    def check_risk_limits(self, user_id: str) -> List[ComplianceAlert]:
        """Check if user is violating risk limits"""
        alerts = []

        limits = self.risk_limits.get(user_id)
        metrics = self.risk_metrics.get(user_id)

        if not limits or not metrics:
            return alerts

        # Check portfolio VaR limit
        var_percentage = metrics.value_at_risk_1d / metrics.portfolio_value
        if var_percentage > limits.max_portfolio_risk:
            alert = ComplianceAlert(
                alert_id=str(uuid.uuid4()),
                user_id=user_id,
                alert_type=ComplianceType.CONCENTRATION_RISK,
                severity=AlertSeverity.WARNING,
                title="Portfolio Risk Limit Exceeded",
                description=f"Portfolio VaR ({var_percentage*100:.1f}%) exceeds limit ({limits.max_portfolio_risk*100:.1f}%)",
                recommendation="Reduce position sizes or hedge exposure",
                affected_positions=[],
                threshold_breached=limits.max_portfolio_risk,
                current_value=var_percentage,
                auto_action_taken=None,
                created_at=datetime.now(),
                resolved_at=None,
                resolution_notes=None,
                is_resolved=False,
            )
            alerts.append(alert)

        # Check position concentration
        if metrics.max_position_weight > limits.max_position_size:
            alert = ComplianceAlert(
                alert_id=str(uuid.uuid4()),
                user_id=user_id,
                alert_type=ComplianceType.CONCENTRATION_RISK,
                severity=AlertSeverity.WARNING,
                title="Position Concentration Limit Exceeded",
                description=f"Largest position ({metrics.max_position_weight*100:.1f}%) exceeds limit ({limits.max_position_size*100:.1f}%)",
                recommendation="Diversify portfolio or reduce position size",
                affected_positions=[],
                threshold_breached=limits.max_position_size,
                current_value=metrics.max_position_weight,
                auto_action_taken=None,
                created_at=datetime.now(),
                resolved_at=None,
                resolution_notes=None,
                is_resolved=False,
            )
            alerts.append(alert)

        # Check leverage
        if metrics.leverage_ratio > limits.max_leverage:
            alert = ComplianceAlert(
                alert_id=str(uuid.uuid4()),
                user_id=user_id,
                alert_type=ComplianceType.MARGIN_REQUIREMENTS,
                severity=AlertSeverity.CRITICAL,
                title="Leverage Limit Exceeded",
                description=f"Leverage ratio ({metrics.leverage_ratio:.2f}) exceeds limit ({limits.max_leverage:.2f})",
                recommendation="Close positions or add margin",
                affected_positions=[],
                threshold_breached=limits.max_leverage,
                current_value=metrics.leverage_ratio,
                auto_action_taken="MARGIN_CALL_INITIATED",
                created_at=datetime.now(),
                resolved_at=None,
                resolution_notes=None,
                is_resolved=False,
            )
            alerts.append(alert)

        # Check drawdown
        if abs(metrics.current_drawdown) > limits.max_drawdown:
            alert = ComplianceAlert(
                alert_id=str(uuid.uuid4()),
                user_id=user_id,
                alert_type=ComplianceType.CONCENTRATION_RISK,
                severity=AlertSeverity.CRITICAL,
                title="Maximum Drawdown Exceeded",
                description=f"Current drawdown ({abs(metrics.current_drawdown)*100:.1f}%) exceeds limit ({limits.max_drawdown*100:.1f}%)",
                recommendation="Consider reducing risk or stop trading",
                affected_positions=[],
                threshold_breached=limits.max_drawdown,
                current_value=abs(metrics.current_drawdown),
                auto_action_taken="RISK_REDUCTION_SUGGESTED",
                created_at=datetime.now(),
                resolved_at=None,
                resolution_notes=None,
                is_resolved=False,
            )
            alerts.append(alert)

        return alerts

    def calculate_position_sizing(self, user_id: str, trade_signal: Dict) -> Dict:
        """Calculate optimal position size based on risk management"""
        limits = self.risk_limits.get(user_id)
        metrics = self.risk_metrics.get(user_id)

        if not limits or not metrics:
            return {"recommended_size": 0, "reason": "No risk limits configured"}

        # Base position size from signal
        signal_confidence = trade_signal.get("confidence", 0.5)
        base_size = trade_signal.get("suggested_position_size", 10000)

        # Risk-adjusted sizing
        # 1. Portfolio heat adjustment
        max_position_value = metrics.portfolio_value * limits.max_position_size

        # 2. Volatility adjustment
        symbol_volatility = trade_signal.get("volatility", 0.25)
        vol_adjustment = min(1.0, 0.20 / symbol_volatility)  # Target 20% volatility

        # 3. Confidence adjustment
        confidence_adjustment = signal_confidence

        # 4. Current risk adjustment
        current_risk_ratio = metrics.value_at_risk_1d / (
            metrics.portfolio_value * limits.max_portfolio_risk
        )
        risk_adjustment = max(0.1, 1 - current_risk_ratio)

        # Calculate final position size
        recommended_size = min(
            base_size * vol_adjustment * confidence_adjustment * risk_adjustment,
            max_position_value,
        )

        return {
            "recommended_size": recommended_size,
            "max_position_value": max_position_value,
            "adjustments": {
                "volatility": vol_adjustment,
                "confidence": confidence_adjustment,
                "risk": risk_adjustment,
            },
            "reason": "Risk-adjusted position sizing applied",
        }

    def _create_empty_risk_metrics(self) -> RiskMetrics:
        """Create empty risk metrics for users with no positions"""
        return RiskMetrics(
            portfolio_value=0,
            total_pnl=0,
            daily_pnl=0,
            weekly_pnl=0,
            monthly_pnl=0,
            value_at_risk_1d=0,
            value_at_risk_5d=0,
            expected_shortfall=0,
            maximum_drawdown=0,
            current_drawdown=0,
            max_position_weight=0,
            sector_concentration={},
            top_5_concentration=0,
            portfolio_volatility=0,
            beta=0,
            correlation_to_market=0,
            gross_exposure=0,
            net_exposure=0,
            leverage_ratio=0,
            margin_utilization=0,
            last_updated=datetime.now(),
        )


class ComplianceReporter:
    """Generate compliance and regulatory reports"""

    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager

    def generate_risk_report(self, user_id: str) -> Dict:
        """Generate comprehensive risk report"""
        metrics = self.risk_manager.risk_metrics.get(user_id)
        limits = self.risk_manager.risk_limits.get(user_id)

        if not metrics:
            return {"error": "No risk metrics available"}

        report = {
            "user_id": user_id,
            "report_date": datetime.now().isoformat(),
            "portfolio_summary": {
                "total_value": metrics.portfolio_value,
                "total_pnl": metrics.total_pnl,
                "pnl_percentage": (
                    (metrics.total_pnl / metrics.portfolio_value * 100)
                    if metrics.portfolio_value > 0
                    else 0
                ),
            },
            "risk_metrics": {
                "value_at_risk_1d": metrics.value_at_risk_1d,
                "value_at_risk_percentage": (
                    (metrics.value_at_risk_1d / metrics.portfolio_value * 100)
                    if metrics.portfolio_value > 0
                    else 0
                ),
                "expected_shortfall": metrics.expected_shortfall,
                "maximum_drawdown": metrics.maximum_drawdown * 100,
                "current_drawdown": metrics.current_drawdown * 100,
                "portfolio_volatility": metrics.portfolio_volatility * 100,
            },
            "concentration_analysis": {
                "max_position_weight": metrics.max_position_weight * 100,
                "top_5_concentration": metrics.top_5_concentration * 100,
                "sector_breakdown": {
                    sector: weight * 100
                    for sector, weight in metrics.sector_concentration.items()
                },
            },
            "leverage_metrics": {
                "gross_exposure": metrics.gross_exposure,
                "net_exposure": metrics.net_exposure,
                "leverage_ratio": metrics.leverage_ratio,
                "margin_utilization": metrics.margin_utilization * 100,
            },
        }

        # Add limit compliance if limits are set
        if limits:
            report["limit_compliance"] = {
                "var_limit_utilization": (
                    (metrics.value_at_risk_1d / metrics.portfolio_value)
                    / limits.max_portfolio_risk
                    * 100
                    if metrics.portfolio_value > 0
                    else 0
                ),
                "position_limit_utilization": metrics.max_position_weight
                / limits.max_position_size
                * 100,
                "leverage_limit_utilization": metrics.leverage_ratio
                / limits.max_leverage
                * 100,
            }

        return report

    def generate_compliance_summary(
        self, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Generate compliance summary report"""
        all_alerts = list(
            self.risk_manager.compliance_manager.compliance_alerts.values()
        )

        # Filter alerts by date range
        period_alerts = [
            alert for alert in all_alerts if start_date <= alert.created_at <= end_date
        ]

        # Categorize alerts
        alert_summary = {}
        for alert_type in ComplianceType:
            alert_summary[alert_type.value] = {
                "total": len([a for a in period_alerts if a.alert_type == alert_type]),
                "critical": len(
                    [
                        a
                        for a in period_alerts
                        if a.alert_type == alert_type
                        and a.severity == AlertSeverity.CRITICAL
                    ]
                ),
                "resolved": len(
                    [
                        a
                        for a in period_alerts
                        if a.alert_type == alert_type and a.is_resolved
                    ]
                ),
            }

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_alerts": len(period_alerts),
            "critical_alerts": len(
                [a for a in period_alerts if a.severity == AlertSeverity.CRITICAL]
            ),
            "resolved_alerts": len([a for a in period_alerts if a.is_resolved]),
            "alert_breakdown": alert_summary,
            "top_violations": [
                {
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "description": alert.description,
                    "user_id": alert.user_id,
                }
                for alert in sorted(
                    period_alerts,
                    key=lambda x: (x.severity == AlertSeverity.CRITICAL, x.created_at),
                    reverse=True,
                )[:10]
            ],
        }


# Demo usage
def demo_risk_management_system():
    """Demonstrate the risk management system"""
    print("=== Advanced Risk Management System Demo ===")

    # Initialize system
    risk_manager = RiskManager()
    reporter = ComplianceReporter(risk_manager)

    # Set up risk limits for a user
    user_id = "user_123"
    limits = RiskLimits(
        max_portfolio_risk=0.02,  # 2% daily VaR
        max_position_size=0.10,  # 10% max position
        max_sector_concentration=0.30,  # 30% max sector
        max_leverage=2.0,  # 2x leverage
        max_daily_loss=0.05,  # 5% daily loss
        max_drawdown=0.15,  # 15% max drawdown
        max_orders_per_day=100,
        max_order_value=100000,
        min_liquidity_requirement=0.05,
        max_single_stock=0.08,
        max_correlated_positions=0.6,
    )

    risk_manager.set_risk_limits(user_id, limits)

    # Mock portfolio positions
    positions = [
        {
            "symbol": "RELIANCE",
            "quantity": 100,
            "market_value": 250000,
            "unrealized_pnl": 15000,
            "sector": "Oil & Gas",
        },
        {
            "symbol": "TCS",
            "quantity": 50,
            "market_value": 180000,
            "unrealized_pnl": -5000,
            "sector": "IT",
        },
        {
            "symbol": "HDFC",
            "quantity": 80,
            "market_value": 200000,
            "unrealized_pnl": 8000,
            "sector": "Banking",
        },
        {
            "symbol": "INFY",
            "quantity": 75,
            "market_value": 120000,
            "unrealized_pnl": 3000,
            "sector": "IT",
        },
    ]

    # Calculate risk metrics
    market_data = {}  # Mock market data
    risk_metrics = risk_manager.calculate_portfolio_risk(
        user_id, positions, market_data
    )

    print(f"\n=== Portfolio Risk Metrics ===")
    print(f"Portfolio Value: ₹{risk_metrics.portfolio_value:,.0f}")
    print(f"Total P&L: ₹{risk_metrics.total_pnl:,.0f}")
    print(
        f"1-Day VaR: ₹{risk_metrics.value_at_risk_1d:,.0f} ({risk_metrics.value_at_risk_1d/risk_metrics.portfolio_value*100:.1f}%)"
    )
    print(f"Expected Shortfall: ₹{risk_metrics.expected_shortfall:,.0f}")
    print(f"Max Position Weight: {risk_metrics.max_position_weight*100:.1f}%")
    print(f"Portfolio Volatility: {risk_metrics.portfolio_volatility*100:.1f}%")
    print(f"Leverage Ratio: {risk_metrics.leverage_ratio:.2f}")

    print(f"\nSector Concentration:")
    for sector, weight in risk_metrics.sector_concentration.items():
        print(f"  {sector}: {weight*100:.1f}%")

    # Check risk limit violations
    alerts = risk_manager.check_risk_limits(user_id)
    if alerts:
        print(f"\n=== Risk Limit Violations ===")
        for alert in alerts:
            print(f"🚨 {alert.severity.value.upper()}: {alert.title}")
            print(f"   {alert.description}")
            print(f"   Recommendation: {alert.recommendation}")
    else:
        print(f"\n✅ All risk limits within acceptable ranges")

    # Test position sizing
    trade_signal = {
        "symbol": "WIPRO",
        "confidence": 0.8,
        "suggested_position_size": 75000,
        "volatility": 0.28,
    }

    sizing = risk_manager.calculate_position_sizing(user_id, trade_signal)
    print(f"\n=== Position Sizing Recommendation ===")
    print(f"Suggested Position: ₹{trade_signal['suggested_position_size']:,.0f}")
    print(f"Risk-Adjusted Size: ₹{sizing['recommended_size']:,.0f}")
    print(f"Adjustments Applied:")
    print(f"  Volatility: {sizing['adjustments']['volatility']:.2f}")
    print(f"  Confidence: {sizing['adjustments']['confidence']:.2f}")
    print(f"  Risk: {sizing['adjustments']['risk']:.2f}")

    # Generate risk report
    risk_report = reporter.generate_risk_report(user_id)
    print(f"\n=== Risk Report Summary ===")
    print(f"Portfolio P&L: {risk_report['portfolio_summary']['pnl_percentage']:.1f}%")
    print(
        f"VaR Limit Utilization: {risk_report['limit_compliance']['var_limit_utilization']:.1f}%"
    )
    print(
        f"Position Limit Utilization: {risk_report['limit_compliance']['position_limit_utilization']:.1f}%"
    )
    print(
        f"Leverage Limit Utilization: {risk_report['limit_compliance']['leverage_limit_utilization']:.1f}%"
    )


if __name__ == "__main__":
    demo_risk_management_system()
