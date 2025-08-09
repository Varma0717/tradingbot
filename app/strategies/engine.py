from flask import current_app
from ..models import Strategy, User
from .top_strategies import STRATEGY_MAP

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
        current_app.logger.warning(f"Strategy {strategy_id} for user {user.id} skipped due to inactive subscription.")
        return

    strategy_class = STRATEGY_MAP.get(strategy_model.name)
    if not strategy_class:
        current_app.logger.error(f"Strategy class for '{strategy_model.name}' not found.")
        return

    strategy_instance = strategy_class(params=strategy_model.parameters)
    
    # TODO: Fetch real-time market data for the strategy's symbols
    # market_data = exchange_adapter.get_market_data(...)
    market_data = {} # Placeholder

    signals = strategy_instance.generate_signals(market_data)
    
    # TODO: Process signals and place orders
    # for signal in signals:
    #     if signal['action'] == 'BUY':
    #         place_order(...)
    #     elif signal['action'] == 'SELL':
    #         place_order(...)
    
    current_app.logger.info(f"Ran strategy '{strategy_model.name}' for user {user.username}. Signals: {signals}")


def run_all_strategies(app):
    """
    A function to be called by the scheduler to run all active strategies.
    """
    with app.app_context():
        active_strategies = Strategy.query.filter_by(is_active=True).all()
        current_app.logger.info(f"Scheduler running for {len(active_strategies)} active strategies.")
        for strategy in active_strategies:
            try:
                run_strategy(strategy.id)
            except Exception as e:
                current_app.logger.exception(f"Error running strategy {strategy.id}: {e}")