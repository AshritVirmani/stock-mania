import pandas as pd
import numpy as np

def donchian_breakout(ohlc: pd.DataFrame, lookback: int):
    """
    Calculates Donchian channel breakout signals.

    Args:
        ohlc (pd.DataFrame): DataFrame with at least a 'Close' column.
        lookback (int): The lookback period for the Donchian channel.

    Returns:
        pd.Series: A series of trading signals (1 for buy, -1 for sell, 0 for hold).
    """
    # Ensure 'close' is lowercase for consistency with mcpt repo
    df = ohlc.copy()
    if 'Close' in df.columns and 'close' not in df.columns:
        df.rename(columns={'Close': 'close'}, inplace=True)

    # Calculate upper and lower Donchian channels, shifting to prevent look-ahead bias
    upper = df['close'].rolling(lookback - 1).max().shift(1)
    lower = df['close'].rolling(lookback - 1).min().shift(1)

    # Generate signals
    signal = pd.Series(np.zeros(len(df)), index=df.index)
    signal[df['close'] > upper] = 1
    signal[df['close'] < lower] = -1

    # Forward-fill signals to hold positions
    signal.ffill(inplace=True)
    return signal

def optimize_donchian(ohlc: pd.DataFrame):
    """
    Optimizes the Donchian channel lookback period by maximizing the profit factor.

    Args:
        ohlc (pd.DataFrame): DataFrame with at least a 'Close' column.

    Returns:
        tuple: A tuple containing the best lookback period and the best profit factor.
    """
    best_pf = -np.inf
    best_lookback = -1

    # Ensure 'close' is lowercase
    df = ohlc.copy()
    if 'Close' in df.columns and 'close' not in df.columns:
        df.rename(columns={'Close': 'close'}, inplace=True)

    # Calculate log returns for performance evaluation
    # IMPORTANT: Align signals and returns correctly to avoid lookahead bias
    # Signal on day T should capture return from day T to T+1
    log_returns = np.log(df['close']).diff()

    # Iterate through a range of lookback periods to find the best one
    for lookback in range(12, 170): # As seen in the provided image
        signal = donchian_breakout(df, lookback)
        
        # Calculate returns based on the signal
        # Signal on day T captures return from day T to T+1
        # So we use signal[:-1] * log_returns[1:]
        aligned_signals = signal.iloc[:-1].reset_index(drop=True)
        aligned_returns = log_returns.iloc[1:].reset_index(drop=True)
        min_len = min(len(aligned_signals), len(aligned_returns))
        
        # Take only the valid length
        aligned_signals = aligned_signals.iloc[:min_len]
        aligned_returns = aligned_returns.iloc[:min_len]
        
        # Drop NaN values
        valid_mask = ~(aligned_returns.isna() | aligned_signals.isna())
        aligned_signals = aligned_signals[valid_mask]
        aligned_returns = aligned_returns[valid_mask]
        
        if len(aligned_signals) == 0:
            sig_rets = pd.Series([], dtype=float)
        else:
            sig_rets = aligned_signals * aligned_returns
        
        # Calculate Profit Factor
        wins = sig_rets[sig_rets > 0].sum()
        losses = sig_rets[sig_rets < 0].abs().sum()

        if losses == 0:
            pf = np.inf # Avoid division by zero if there are no losses
        else:
            pf = wins / losses
        
        if pf > best_pf:
            best_pf = pf
            best_lookback = lookback
            
    return best_lookback, best_pf
