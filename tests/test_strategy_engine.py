import pytest
from app.strategies.top_strategies import MovingAverageCrossover

def test_strategy_initialization():
    """
    GIVEN a strategy class
    WHEN it is initialized
    THEN its parameters and risk controls should be set correctly
    """
    params = {'max_daily_trades': 20}
    strategy = MovingAverageCrossover(params=params)
    
    assert strategy.params['max_daily_trades'] == 20
    assert strategy.risk_controls['max_daily_trades'] == 20
    # Default value
    assert strategy.risk_controls['global_stop_loss_pct'] == 0.10

def test_base_strategy_signal_generation():
    """
    GIVEN the BaseStrategy class
    WHEN generate_signals is called
    THEN it should raise NotImplementedError
    """
    from app.strategies.top_strategies import BaseStrategy
    strategy = BaseStrategy()
    with pytest.raises(NotImplementedError):
        strategy.generate_signals({})