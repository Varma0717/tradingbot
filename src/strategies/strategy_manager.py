"""
Universal Strategy Manager for CryptoPilot

This module manages ONE universal Grid DCA strategy that works with any balance.
No complex micro strategies - just ONE strategy that adapts automatically.
"""

from .universal_strategy import StrategyManager as UniversalStrategyManager

# Expose the universal strategy manager
StrategyManager = UniversalStrategyManager
