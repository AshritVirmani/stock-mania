"""
Enhanced Donchian Strategy with Regime Filtering and Pattern Exits

This module provides an enhanced Donchian breakout strategy that includes:
1. Regime filtering (avoid trading in Red Light regimes)
2. Pattern-based early exits (exit if similar historical days show poor performance)
"""

import os
import pandas as pd
import numpy as np
from donchian_strategy import donchian_breakout


def identify_trending_regimes(regime_data_path):
    """
    Identifies which regimes are trending (good for trading).
    
    Args:
        regime_data_path (str): Path to data_with_regimes.csv
    
    Returns:
        list: List of regime IDs that are trending (good for trading)
    """
    if not os.path.exists(regime_data_path):
        return []
    
    try:
        df = pd.read_csv(regime_data_path, index_col=0, parse_dates=True)
        
        # Find close column
        close_col = None
        for col in ['Close', 'close', 'CLOSE']:
            if col in df.columns:
                close_col = col
                break
        
        if close_col is None:
            return []
        
        # Calculate returns by regime
        df['returns'] = df[close_col].pct_change()
        regime_stats = df.groupby('regime')['returns'].mean()
        
        # Trending regimes are those with positive average returns
        trending = regime_stats[regime_stats > 0].index.tolist()
        return [int(r) for r in trending]
    except Exception:
        return []


def donchian_enhanced(data, lookback, regime_data_path=None, use_pattern_exit=False,
                     pattern_matcher=None, df_normalized=None, df_full=None,
                     allow_bearish=True, pattern_exit_threshold=-2.0,
                     num_similar_days=10, filter_red_light=True):
    """
    Enhanced Donchian breakout strategy with regime filtering and pattern exits.
    
    Args:
        data (pd.DataFrame): OHLCV data
        lookback (int): Donchian lookback period
        regime_data_path (str, optional): Path to regime data CSV
        use_pattern_exit (bool): Whether to use pattern-based exits
        pattern_matcher: Pattern matcher instance (from find_similar_days)
        df_normalized: Normalized indicator data for pattern matching
        df_full: Full OHLCV data for pattern matching
        allow_bearish (bool): Whether to allow short positions
        pattern_exit_threshold (float): Exit if similar days averaged return < threshold
        num_similar_days (int): Number of similar days to check
        filter_red_light (bool): Whether to filter out Red Light regimes
    
    Returns:
        pd.Series: Trading signals (1 = Long, -1 = Short, 0 = Flat)
    """
    # Start with base Donchian signals
    signals = donchian_breakout(data, lookback)
    
    # Apply regime filtering if enabled
    if filter_red_light and regime_data_path and os.path.exists(regime_data_path):
        try:
            regime_df = pd.read_csv(regime_data_path, index_col=0, parse_dates=True)
            
            # Align regime data with signal data
            # Get the regime for each date in data
            for date in data.index:
                if date in regime_df.index:
                    current_regime = regime_df.loc[date, 'regime']
                    
                    # Auto-detect red light regime (worst performing)
                    if 'Close' in regime_df.columns or 'close' in regime_df.columns:
                        close_col = 'Close' if 'Close' in regime_df.columns else 'close'
                        regime_returns = regime_df.groupby('regime')[close_col].pct_change().mean()
                        
                        if len(regime_returns) > 0:
                            red_light_regime = regime_returns.idxmin()
                            
                            # If we're in red light regime, set signal to 0 (flat)
                            if current_regime == red_light_regime:
                                signals.loc[date] = 0
        except Exception as e:
            # If regime filtering fails, continue without it
            pass
    
    # Apply pattern-based exits if enabled
    if use_pattern_exit and pattern_matcher is not None and df_normalized is not None and df_full is not None:
        try:
            # Get close column name
            close_col = None
            for col in ['close', 'Close', 'CLOSE']:
                if col in df_full.columns:
                    close_col = col
                    break
            
            if close_col:
                # For each day with a signal, check similar historical days
                for date in data.index:
                    if signals.loc[date] != 0:  # Only check if we have a position
                        # Get current day's normalized features
                        if date in df_normalized.index:
                            current_features = df_normalized.loc[date].values.reshape(1, -1)
                            
                            # Find similar days
                            distances, indices = pattern_matcher.kneighbors(current_features, n_neighbors=num_similar_days)
                            similar_indices = indices[0]
                            
                            # Check future returns of similar days
                            similar_returns = []
                            for idx in similar_indices:
                                # Get the date corresponding to this index
                                if idx < len(df_normalized):
                                    similar_date = df_normalized.index[idx]
                                    
                                    # Find this date in df_full and get next day's return
                                    if similar_date in df_full.index:
                                        similar_loc = df_full.index.get_loc(similar_date)
                                        if similar_loc < len(df_full) - 1:
                                            next_date = df_full.index[similar_loc + 1]
                                            future_return = (df_full.loc[next_date, close_col] / 
                                                           df_full.loc[similar_date, close_col] - 1) * 100
                                            similar_returns.append(future_return)
                            
                            # If average return is below threshold, exit
                            if similar_returns and np.mean(similar_returns) < pattern_exit_threshold:
                                signals.loc[date] = 0
        except Exception as e:
            # If pattern exit fails, continue without it
            pass
    
    # If bearish not allowed, convert shorts to flat
    if not allow_bearish:
        signals[signals == -1] = 0
    
    return signals

