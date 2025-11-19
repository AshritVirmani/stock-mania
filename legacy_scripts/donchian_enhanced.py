"""
Enhanced Donchian Breakout Strategy

This module implements an improved Donchian strategy with:
1. Behavioral regime filtering (only trade in trending markets)
2. Pattern-matching exit logic (early exit based on similar historical days)
"""

import os
import pandas as pd
import numpy as np
from donchian_strategy import donchian_breakout
from find_similar_days import PatternMatcher, analyze_outcomes


def identify_trending_regimes(regime_data_path, use_red_light_detection=True):
    """
    Identifies which regimes are trending (bullish/bearish) vs choppy/sideways.
    Can also identify "Red Light" regimes (worst performers) to filter out.
    
    Args:
        regime_data_path: Path to data_with_regimes.csv
        use_red_light_detection: If True, identifies worst-performing regime as "Red Light"
    
    Returns:
        dict: {
            'bullish_regimes': [list of regime numbers with positive mean returns],
            'bearish_regimes': [list of regime numbers with negative mean returns],
            'choppy_regimes': [list of regime numbers with low absolute returns],
            'red_light_regimes': [list of worst-performing regimes to avoid],
            'regime_returns': {regime: mean_return},
            'regime_volatility': {regime: volatility}
        }
    """
    if not os.path.exists(regime_data_path):
        return None
    
    try:
        df = pd.read_csv(regime_data_path, index_col=0, parse_dates=True)
        df.index.name = 'Date'
        
        # Calculate daily returns
        df['daily_return'] = df['Close'].pct_change()
        
        # Group by regime and calculate mean returns and volatility
        regime_stats = df.groupby('regime')['daily_return'].agg(['mean', 'std'])
        regime_returns = regime_stats['mean']
        regime_volatility = regime_stats['std']
        
        # Identify regimes
        # Bullish: positive mean return
        # Bearish: negative mean return (but still trending, so we can short)
        # Choppy: low absolute return (we want to avoid these)
        
        bullish_regimes = regime_returns[regime_returns > 0.001].index.tolist()  # > 0.1% daily
        bearish_regimes = regime_returns[regime_returns < -0.001].index.tolist()  # < -0.1% daily
        choppy_regimes = regime_returns[abs(regime_returns) <= 0.001].index.tolist()  # Low absolute return
        
        # Identify Red Light regimes (worst performers)
        red_light_regimes = []
        if use_red_light_detection:
            # Find regimes with worst risk-adjusted returns (low return, high volatility)
            # Calculate a "risk score" = -return / volatility (higher is worse)
            risk_scores = {}
            for regime in regime_returns.index:
                ret = regime_returns[regime]
                vol = regime_volatility[regime]
                if vol > 0:
                    # Negative return + high volatility = bad
                    risk_scores[regime] = -ret / vol if ret < 0 else ret / vol
                else:
                    risk_scores[regime] = 0
            
            # Red Light = worst risk score (negative returns or very low returns with high volatility)
            # Also include regimes with negative returns
            worst_regimes = [r for r in regime_returns.index if regime_returns[r] < 0]
            
            # If no negative return regimes, use lowest return regime
            if not worst_regimes:
                worst_regime = regime_returns.idxmin()
                worst_regimes = [worst_regime]
            
            red_light_regimes = worst_regimes
        
        return {
            'bullish_regimes': bullish_regimes,
            'bearish_regimes': bearish_regimes,
            'choppy_regimes': choppy_regimes,
            'red_light_regimes': red_light_regimes,
            'regime_returns': regime_returns.to_dict(),
            'regime_volatility': regime_volatility.to_dict()
        }
    except Exception as e:
        print(f"⚠️  Error identifying regimes: {e}")
        return None


def donchian_with_regime_filter(ohlc, lookback, regime_data_path, allow_bearish=True, filter_red_light=True):
    """
    Donchian breakout strategy with regime filtering.
    
    Only generates signals when market is in trending regimes (bullish or bearish),
    avoiding choppy/sideways markets and "Red Light" regimes.
    
    Args:
        ohlc: DataFrame with OHLCV data
        lookback: Donchian lookback period
        regime_data_path: Path to data_with_regimes.csv file
        allow_bearish: If True, allows short signals in bearish regimes
        filter_red_light: If True, blocks all trades in Red Light (worst-performing) regimes
    
    Returns:
        pd.Series: Trading signals (1, -1, 0)
    """
    # Get base Donchian signals
    signals = donchian_breakout(ohlc, lookback)
    
    # Load regime data
    regime_info = identify_trending_regimes(regime_data_path, use_red_light_detection=filter_red_light)
    if regime_info is None:
        print("⚠️  Could not load regime data. Using unfiltered signals.")
        return signals
    
    # Load regime data for filtering
    try:
        regime_df = pd.read_csv(regime_data_path, index_col=0, parse_dates=True)
        regime_df.index.name = 'Date'
        
        # Align regimes with signals
        signals_with_regime = signals.to_frame('signal').join(regime_df[['regime']], how='left')
        
        # Filter signals based on regime
        filtered_signals = signals.copy()
        
        # Combine choppy and red light regimes
        regimes_to_avoid = set(regime_info['choppy_regimes'])
        if filter_red_light and 'red_light_regimes' in regime_info:
            regimes_to_avoid.update(regime_info['red_light_regimes'])
            if regime_info['red_light_regimes']:
                print(f"🚫 Filtering Red Light regimes: {regime_info['red_light_regimes']}")
        
        for date in signals.index:
            if date in signals_with_regime.index:
                regime = signals_with_regime.loc[date, 'regime']
                signal = signals.loc[date]
                
                if pd.notna(regime):
                    regime = int(regime)
                    
                    # Block all signals in Red Light or choppy regimes
                    if regime in regimes_to_avoid:
                        filtered_signals.loc[date] = 0  # Block all trades
                        continue
                    
                    # Only allow BUY signals in bullish regimes
                    if signal == 1 and regime not in regime_info['bullish_regimes']:
                        filtered_signals.loc[date] = 0  # Block the buy signal
                    
                    # Only allow SELL signals in bearish regimes (if allowed)
                    if signal == -1:
                        if not allow_bearish or regime not in regime_info['bearish_regimes']:
                            filtered_signals.loc[date] = 0  # Block the sell signal
        
        # Forward fill to maintain positions
        filtered_signals.ffill(inplace=True)
        filtered_signals.fillna(0, inplace=True)
        
        return filtered_signals
        
    except Exception as e:
        print(f"⚠️  Error applying regime filter: {e}")
        return signals


def get_pattern_exit_signal(current_date, ohlc, pattern_matcher, df_normalized, lookahead_days=5, threshold=-2.0, num_similar_days=10):
    """
    Uses pattern matching to determine if we should exit early.
    
    When in a trade, checks if similar historical patterns led to poor performance.
    If average 5-day return of similar days is below threshold, exit immediately.
    
    Args:
        current_date: Current trading date
        ohlc: Full OHLCV data (with lowercase column names)
        pattern_matcher: PatternMatcher instance
        df_normalized: Normalized indicator data
        lookahead_days: Number of days ahead to check (default 5)
        threshold: Exit if average return of similar days is below this threshold (default -2.0%)
        num_similar_days: Number of similar days to check (default 10)
    
    Returns:
        bool: True if should exit early, False otherwise
    """
    try:
        # Ensure ohlc has 'Close' column (analyze_outcomes expects it)
        ohlc_for_analysis = ohlc.copy()
        if 'close' in ohlc_for_analysis.columns and 'Close' not in ohlc_for_analysis.columns:
            ohlc_for_analysis['Close'] = ohlc_for_analysis['close']
        
        # Find similar days
        similar_days = pattern_matcher.find_similar_days(df_normalized, current_date.strftime('%Y-%m-%d'))
        
        if similar_days is None or len(similar_days) == 0:
            return False
        
        # Get top N most similar days (default 10, as per user request)
        top_similar = similar_days.head(num_similar_days)
        
        # Analyze outcomes for these similar days
        _, outcomes_df = analyze_outcomes(ohlc_for_analysis, top_similar, current_date, N=num_similar_days)
        
        if outcomes_df.empty:
            return False
        
        # Calculate average 5-day return of similar days
        avg_5d_return = outcomes_df['Return_+5d_%'].mean()
        
        # Exit early if similar historical days had poor average returns (below threshold)
        # Default threshold is -2.0% (more conservative than -1.0%)
        if pd.notna(avg_5d_return) and avg_5d_return < threshold:
            return True
        
        return False
        
    except Exception as e:
        # If pattern matching fails, don't exit early
        return False


def donchian_enhanced(ohlc, lookback, regime_data_path=None, use_pattern_exit=False, 
                     pattern_matcher=None, df_normalized=None, df_full=None, allow_bearish=True,
                     pattern_exit_threshold=-2.0, num_similar_days=10, filter_red_light=True):
    """
    Enhanced Donchian strategy with regime filtering and pattern-matching exits.
    
    Args:
        ohlc: DataFrame with OHLCV data (test period only)
        lookback: Donchian lookback period
        regime_data_path: Path to data_with_regimes.csv (for regime filtering)
        use_pattern_exit: If True, uses pattern matching for early exits
        pattern_matcher: PatternMatcher instance (required if use_pattern_exit=True)
        df_normalized: Normalized indicator data (required if use_pattern_exit=True)
        df_full: Full OHLCV data for pattern matching (required if use_pattern_exit=True)
        allow_bearish: If True, allows short signals in bearish regimes
        pattern_exit_threshold: Exit if similar days averaged below this return % (default -2.0%)
        num_similar_days: Number of similar days to check (default 10)
        filter_red_light: If True, filters out Red Light (worst-performing) regimes
    
    Returns:
        pd.Series: Enhanced trading signals
    """
    # Step 1: Get base Donchian signals (with or without regime filter)
    if regime_data_path and os.path.exists(regime_data_path):
        signals = donchian_with_regime_filter(ohlc, lookback, regime_data_path, allow_bearish, filter_red_light)
    else:
        signals = donchian_breakout(ohlc, lookback)
    
    # Step 2: Apply pattern-matching exit logic
    if use_pattern_exit and pattern_matcher is not None and df_normalized is not None and df_full is not None:
        enhanced_signals = signals.copy()
        current_position = 0  # 0 = no position, 1 = long, -1 = short
        
        for date in signals.index:
            signal = signals.loc[date]
            
            # Check if we should exit early based on pattern matching
            if current_position != 0:  # We have a position
                should_exit = get_pattern_exit_signal(
                    date, df_full, pattern_matcher, df_normalized,
                    threshold=pattern_exit_threshold,
                    num_similar_days=num_similar_days
                )
                
                if should_exit:
                    enhanced_signals.loc[date] = 0  # Exit position
                    current_position = 0
                    continue
            
            # Update position based on signal
            if signal == 1:
                current_position = 1  # Long
            elif signal == -1:
                current_position = -1  # Short
            # signal == 0 means hold current position
        
        return enhanced_signals
    
    return signals

