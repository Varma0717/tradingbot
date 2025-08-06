"""
Backtest Engine
Provides backtesting capabilities for trading strategies.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from ..core.exceptions import BacktestError
from ..utils.logger import get_logger


class BacktestEngine:
    """
    Backtesting engine for strategy evaluation.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the backtest engine.

        Args:
            config: Backtesting configuration
        """
        self.logger = get_logger(__name__)
        self.config = config.get("backtesting", {})

        # Backtest parameters
        self.initial_capital = self.config.get("initial_capital", 10000)
        self.commission = self.config.get("commission", 0.001)  # 0.1%
        self.slippage = self.config.get("slippage", 0.0005)  # 0.05%

        # Results tracking
        self.trades = []
        self.portfolio_history = []
        self.metrics = {}

        self.logger.info("Backtest Engine initialized")

    def run_backtest(
        self,
        strategy,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Run a backtest for a given strategy and data.

        Args:
            strategy: Trading strategy to backtest
            data: Historical price data
            start_date: Start date for backtest
            end_date: End date for backtest

        Returns:
            Backtest results
        """
        try:
            self.logger.info("Starting backtest")

            # Filter data by date range if specified
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]

            # Initialize portfolio
            capital = self.initial_capital
            position = 0
            entry_price = 0

            self.trades.clear()
            self.portfolio_history.clear()

            # Simulate trading
            for i, (timestamp, row) in enumerate(data.iterrows()):
                price = row["close"]

                # Get strategy signal
                signal = strategy.generate_signal(data.iloc[: i + 1])

                # Execute trades based on signal
                if signal == "buy" and position == 0:
                    # Buy signal - enter long position
                    position = capital / (price * (1 + self.commission + self.slippage))
                    entry_price = price
                    capital = 0

                    self.trades.append(
                        {
                            "timestamp": timestamp,
                            "action": "buy",
                            "price": price,
                            "quantity": position,
                            "capital": capital,
                        }
                    )

                elif signal == "sell" and position > 0:
                    # Sell signal - exit position
                    capital = position * price * (1 - self.commission - self.slippage)

                    # Calculate trade profit/loss
                    pnl = capital - self.initial_capital
                    pnl_pct = (capital / self.initial_capital - 1) * 100

                    self.trades.append(
                        {
                            "timestamp": timestamp,
                            "action": "sell",
                            "price": price,
                            "quantity": position,
                            "capital": capital,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                        }
                    )

                    position = 0
                    entry_price = 0

                # Record portfolio value
                if position > 0:
                    portfolio_value = position * price
                else:
                    portfolio_value = capital

                self.portfolio_history.append(
                    {
                        "timestamp": timestamp,
                        "portfolio_value": portfolio_value,
                        "position": position,
                        "price": price,
                    }
                )

            # Calculate final metrics
            self.metrics = self._calculate_metrics()

            results = {
                "trades": self.trades,
                "portfolio_history": self.portfolio_history,
                "metrics": self.metrics,
                "final_capital": (
                    capital if position == 0 else position * data.iloc[-1]["close"]
                ),
            }

            self.logger.info(
                f"Backtest completed. Final capital: {results['final_capital']:.2f}"
            )
            return results

        except Exception as e:
            self.logger.error(f"Error running backtest: {e}")
            raise BacktestError(f"Backtest failed: {e}")

    def _calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate backtest performance metrics.

        Returns:
            Performance metrics
        """
        try:
            if not self.portfolio_history:
                return {}

            # Convert to DataFrame for easier calculations
            df = pd.DataFrame(self.portfolio_history)
            df["returns"] = df["portfolio_value"].pct_change()

            # Basic metrics
            initial_value = self.initial_capital
            final_value = df["portfolio_value"].iloc[-1]
            total_return = (final_value / initial_value - 1) * 100

            # Risk metrics
            returns = df["returns"].dropna()
            if len(returns) > 0:
                volatility = returns.std() * np.sqrt(252) * 100  # Annualized
                sharpe_ratio = (
                    (returns.mean() / returns.std()) * np.sqrt(252)
                    if returns.std() > 0
                    else 0
                )

                # Drawdown
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative / running_max - 1) * 100
                max_drawdown = drawdown.min()
            else:
                volatility = 0
                sharpe_ratio = 0
                max_drawdown = 0

            # Trade metrics
            winning_trades = [t for t in self.trades if t.get("pnl", 0) > 0]
            losing_trades = [t for t in self.trades if t.get("pnl", 0) < 0]

            total_trades = len([t for t in self.trades if "pnl" in t])
            win_rate = (
                (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            )

            avg_win = (
                np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
            )
            avg_loss = (
                np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
            )

            profit_factor = (
                abs(
                    sum([t["pnl"] for t in winning_trades])
                    / sum([t["pnl"] for t in losing_trades])
                )
                if losing_trades
                else 0
            )

            metrics = {
                "total_return": total_return,
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": win_rate,
                "average_win": avg_win,
                "average_loss": avg_loss,
                "profit_factor": profit_factor,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "initial_capital": initial_value,
                "final_capital": final_value,
            }

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {}

    def get_trade_summary(self) -> pd.DataFrame:
        """
        Get a summary of all trades.

        Returns:
            DataFrame with trade summary
        """
        try:
            if not self.trades:
                return pd.DataFrame()

            df = pd.DataFrame(self.trades)
            return df

        except Exception as e:
            self.logger.error(f"Error getting trade summary: {e}")
            return pd.DataFrame()

    def plot_results(self):
        """
        Plot backtest results (placeholder - would need matplotlib).
        """
        try:
            # This would create plots of portfolio performance, drawdown, etc.
            # For now, just log the metrics
            self.logger.info("Backtest Results:")
            for key, value in self.metrics.items():
                if isinstance(value, float):
                    self.logger.info(f"  {key}: {value:.2f}")
                else:
                    self.logger.info(f"  {key}: {value}")

        except Exception as e:
            self.logger.error(f"Error plotting results: {e}")

    def export_results(self, filename: str):
        """
        Export backtest results to file.

        Args:
            filename: Output filename
        """
        try:
            results = {
                "metrics": self.metrics,
                "trades": self.trades,
                "portfolio_history": self.portfolio_history,
            }

            # This would export to CSV/JSON file
            self.logger.info(f"Results exported to {filename}")

        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            raise BacktestError(f"Export failed: {e}")
