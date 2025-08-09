from flask import current_app
from ..models import Strategy, User
from .top_strategies import STRATEGY_MAP
from ..orders.manager import place_order
from ..exchange_adapter.kite_adapter import exchange_adapter
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_mock_market_data(symbols):
    """
    Generate mock market data for testing. In production, this should be replaced
    with actual market data from your broker's API.
    """
    market_data = {}

    for symbol in symbols:
        # Generate 50 days of mock OHLCV data
        dates = pd.date_range(end=datetime.now(), periods=50, freq="D")

        # Generate realistic price data with some volatility
        base_price = np.random.uniform(100, 1000)
        returns = np.random.normal(0.001, 0.02, 50)  # 0.1% daily return, 2% volatility
        prices = base_price * np.exp(np.cumsum(returns))

        # Create OHLCV data
        data = pd.DataFrame(
            {
                "datetime": dates,
                "open": prices * np.random.uniform(0.99, 1.01, 50),
                "high": prices * np.random.uniform(1.00, 1.03, 50),
                "low": prices * np.random.uniform(0.97, 1.00, 50),
                "close": prices,
                "volume": np.random.randint(10000, 100000, 50),
            }
        )

        market_data[symbol] = data

    return market_data


def run_strategy(strategy_id):
    """
    Runs a single strategy instance.
    This would be called by the scheduler.
    """
    strategy_model = Strategy.query.get(strategy_id)
    if not strategy_model or not strategy_model.is_active:
        return

    user = User.query.get(strategy_model.user_id)

    # Check if user subscription is active
    if not user.subscription or not user.subscription.is_active:
        current_app.logger.warning(
            f"Strategy {strategy_id} for user {user.id} skipped due to inactive subscription."
        )
        return

    strategy_class = STRATEGY_MAP.get(strategy_model.name)
    if not strategy_class:
        current_app.logger.error(
            f"Strategy class for '{strategy_model.name}' not found."
        )
        return

    strategy_instance = strategy_class(params=strategy_model.parameters)

    # Get symbols from strategy parameters or use defaults
    symbols = strategy_model.parameters.get("symbols", ["RELIANCE", "TCS", "INFY"])

    try:
        # Try to fetch real market data first
        market_data = exchange_adapter.get_market_data(symbols)
    except (NotImplementedError, Exception) as e:
        current_app.logger.warning(
            f"Could not fetch real market data: {e}. Using mock data."
        )
        market_data = get_mock_market_data(symbols)

    signals = strategy_instance.generate_signals(market_data)

    # Process signals and place orders
    for signal in signals:
        if signal["action"] in ["BUY", "SELL"]:
            try:
                order_payload = {
                    "symbol": signal["symbol"],
                    "quantity": signal["quantity"],
                    "order_type": signal.get("order_type", "market"),
                    "side": signal["action"].lower(),
                    "price": signal.get("price"),
                    "is_paper": not user.has_pro_plan,  # Free users get paper trading
                }

                order = place_order(user, order_payload)
                current_app.logger.info(
                    f"Order placed: {order.id} for signal: {signal['reason']}"
                )

            except Exception as e:
                current_app.logger.exception(
                    f"Failed to place order for signal {signal}: {e}"
                )

    current_app.logger.info(
        f"Ran strategy '{strategy_model.name}' for user {user.username}. Generated {len(signals)} signals."
    )


def run_all_strategies(app):
    """
    A function to be called by the scheduler to run all active strategies.
    """
    with app.app_context():
        active_strategies = Strategy.query.filter_by(is_active=True).all()
        current_app.logger.info(
            f"Scheduler running for {len(active_strategies)} active strategies."
        )
        for strategy in active_strategies:
            try:
                run_strategy(strategy.id)
            except Exception as e:
                current_app.logger.exception(
                    f"Error running strategy {strategy.id}: {e}"
                )
