"""
Donchian Channel Breakout Strategy

This module provides the core Donchian breakout strategy functions:
1. optimize_donchian: Finds optimal lookback period
2. donchian_breakout: Generates trading signals based on Donchian channels
"""

import pandas as pd
import numpy as np


def donchian_breakout(data, lookback=20):
    """
    Generates Donchian Channel breakout signals.
    
    Strategy:
    - Long (1): When price breaks above the highest high of the last N days
    - Short (-1): When price breaks below the lowest low of the last N days
    - Flat (0): Otherwise (hold current position or stay flat)
    
    Args:
        data (pd.DataFrame): OHLCV data with columns ['high', 'low', 'close']
        lookback (int): Number of periods for Donchian channel calculation
    
    Returns:
        pd.Series: Trading signals (1 = Long, -1 = Short, 0 = Flat)
    """
    # Calculate Donchian channels
    high_band = data['high'].rolling(window=lookback, min_periods=1).max().shift(1)
    low_band = data['low'].rolling(window=lookback, min_periods=1).min().shift(1)
    
    # Initialize signals
    signals = pd.Series(0, index=data.index)
    
    # Long signal: Price breaks above high band
    signals[data['close'] > high_band] = 1
    
    # Short signal: Price breaks below low band
    signals[data['close'] < low_band] = -1
    
    # Forward fill to maintain position until opposite signal
    # This creates a trend-following system
    current_position = 0
    for i in range(len(signals)):
        if signals.iloc[i] != 0:
            current_position = signals.iloc[i]
        else:
            signals.iloc[i] = current_position
    
    return signals


def optimize_donchian(data, lookback_range=(10, 50), min_periods=100):
    """
    Optimizes the Donchian lookback period by testing different values
    and selecting the one with the best profit factor.
    
    Args:
        data (pd.DataFrame): OHLCV data with columns ['high', 'low', 'close']
        lookback_range (tuple): (min, max) range of lookback periods to test
        min_periods (int): Minimum number of periods required for optimization
    
    Returns:
        tuple: (best_lookback, best_profit_factor)
    """
    if len(data) < min_periods:
        # Return default if insufficient data
        return 20, 0.0
    
    min_lookback, max_lookback = lookback_range
    best_lookback = min_lookback
    best_profit_factor = 0.0
    
    # Calculate returns for profit factor calculation
    returns = np.log(data['close'] / data['close'].shift(1))
    
    for lookback in range(min_lookback, max_lookback + 1):
        signals = donchian_breakout(data, lookback)
        
        # Align signals with returns (signal on day T affects return on day T+1)
        aligned_signals = signals.shift(1)
        strategy_returns = aligned_signals * returns
        
        # Calculate profit factor
        positive_returns = strategy_returns[strategy_returns > 0].sum()
        negative_returns = abs(strategy_returns[strategy_returns < 0].sum())
        
        if negative_returns > 0:
            profit_factor = positive_returns / negative_returns
        else:
            profit_factor = positive_returns if positive_returns > 0 else 0
        
        if profit_factor > best_profit_factor:
            best_profit_factor = profit_factor
            best_lookback = lookback
    
    return best_lookback, best_profit_factor

