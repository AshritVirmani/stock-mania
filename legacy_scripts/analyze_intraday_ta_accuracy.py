"""
Analyze Technical Analysis Indicator Accuracy for Intraday Data

For each indicator, generates buy/sell signals and measures accuracy in predicting
next candle direction.
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from sklearn.metrics import precision_score, recall_score, f1_score

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_actual_direction(df):
    """
    Calculate actual next candle direction (1 = up, 0 = down).
    
    Args:
        df (pandas.DataFrame): DataFrame with Close prices
    
    Returns:
        pandas.Series: Series with 1 for up, 0 for down, NaN for last row
    """
    # Shift close price to get next candle's close
    next_close = df['Close'].shift(-1)
    current_close = df['Close']
    
    # Direction: 1 if next close > current close, 0 otherwise
    direction = (next_close > current_close).astype(float)
    
    # Last row will be NaN (no next candle)
    return direction


def generate_momentum_signals(df, indicator_name):
    """
    Generate buy/sell signals for momentum indicators.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicator values
        indicator_name (str): Name of the indicator column
    
    Returns:
        pandas.Series: Series with 1 for buy, -1 for sell, 0 for neutral
    """
    if indicator_name not in df.columns:
        return pd.Series(0, index=df.index)
    
    values = df[indicator_name].copy()
    signals = pd.Series(0, index=df.index)
    
    if 'rsi' in indicator_name.lower():
        # RSI: Buy when < 30 (oversold), Sell when > 70 (overbought)
        signals[values < 30] = 1  # Buy
        signals[values > 70] = -1  # Sell
    
    elif 'stoch' in indicator_name.lower():
        if 'signal' in indicator_name.lower():
            # Stochastic Signal: Buy when %D < 20, Sell when > 80
            signals[values < 20] = 1
            signals[values > 80] = -1
        else:
            # Stochastic %K: Buy when < 20, Sell when > 80
            signals[values < 20] = 1
            signals[values > 80] = -1
    
    elif 'wr' in indicator_name.lower() or 'williams' in indicator_name.lower():
        # Williams %R: Buy when < -80 (oversold), Sell when > -20 (overbought)
        signals[values < -80] = 1
        signals[values > -20] = -1
    
    elif 'mfi' in indicator_name.lower():
        # Money Flow Index: Buy when < 20, Sell when > 80
        signals[values < 20] = 1
        signals[values > 80] = -1
    
    elif 'roc' in indicator_name.lower():
        # Rate of Change: Buy when positive and increasing, Sell when negative and decreasing
        roc_diff = values.diff()
        signals[(values > 0) & (roc_diff > 0)] = 1
        signals[(values < 0) & (roc_diff < 0)] = -1
    
    elif 'uo' in indicator_name.lower() or 'ultimate' in indicator_name.lower():
        # Ultimate Oscillator: Buy when < 30, Sell when > 70
        signals[values < 30] = 1
        signals[values > 70] = -1
    
    elif 'tsi' in indicator_name.lower():
        # True Strength Index: Buy when crosses above 0, Sell when crosses below
        tsi_prev = values.shift(1)
        signals[(values > 0) & (tsi_prev <= 0)] = 1  # Cross above zero
        signals[(values < 0) & (tsi_prev >= 0)] = -1  # Cross below zero
    
    elif 'ao' in indicator_name.lower() or 'awesome' in indicator_name.lower():
        # Awesome Oscillator: Buy when positive and increasing, Sell when negative
        ao_diff = values.diff()
        signals[(values > 0) & (ao_diff > 0)] = 1
        signals[(values < 0) & (ao_diff < 0)] = -1
    
    return signals


def generate_trend_signals(df, indicator_name):
    """
    Generate buy/sell signals for trend indicators.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicator values
        indicator_name (str): Name of the indicator column
    
    Returns:
        pandas.Series: Series with 1 for buy, -1 for sell, 0 for neutral
    """
    if indicator_name not in df.columns:
        return pd.Series(0, index=df.index)
    
    values = df[indicator_name].copy()
    signals = pd.Series(0, index=df.index)
    
    if 'macd' in indicator_name.lower():
        if 'signal' in indicator_name.lower():
            # MACD Signal: Compare MACD with Signal
            macd = df.get('trend_macd', pd.Series(0, index=df.index))
            signals[macd > values] = 1  # MACD above signal = buy
            signals[macd < values] = -1  # MACD below signal = sell
        elif 'diff' in indicator_name.lower() or 'hist' in indicator_name.lower():
            # MACD Histogram: Buy when positive, Sell when negative
            signals[values > 0] = 1
            signals[values < 0] = -1
        else:
            # MACD Line: Buy when crosses above signal
            macd_signal = df.get('trend_macd_signal', pd.Series(0, index=df.index))
            macd_prev = values.shift(1)
            signal_prev = macd_signal.shift(1)
            signals[(values > macd_signal) & (macd_prev <= signal_prev)] = 1
            signals[(values < macd_signal) & (macd_prev >= signal_prev)] = -1
    
    elif 'sma' in indicator_name.lower() or 'ema' in indicator_name.lower():
        if 'fast' in indicator_name.lower():
            # Fast MA: Buy when fast > slow, Sell when fast < slow
            slow_col = indicator_name.replace('fast', 'slow')
            if slow_col in df.columns:
                slow_ma = df[slow_col]
                signals[values > slow_ma] = 1
                signals[values < slow_ma] = -1
        elif 'slow' in indicator_name.lower():
            # Slow MA: Already handled in fast
            pass
        else:
            # Single MA: Buy when price > MA, Sell when price < MA
            if 'Close' in df.columns:
                signals[df['Close'] > values] = 1
                signals[df['Close'] < values] = -1
    
    elif 'adx' in indicator_name.lower():
        # ADX: Buy when ADX > 25 (strong trend) and +DI > -DI
        if 'pos' in indicator_name.lower():
            adx_neg = df.get('trend_adx_neg', pd.Series(0, index=df.index))
            adx = df.get('trend_adx', pd.Series(0, index=df.index))
            signals[(adx > 25) & (values > adx_neg)] = 1
        elif 'neg' in indicator_name.lower():
            adx_pos = df.get('trend_adx_pos', pd.Series(0, index=df.index))
            adx = df.get('trend_adx', pd.Series(0, index=df.index))
            signals[(adx > 25) & (adx_pos < values)] = -1
        else:
            # ADX itself: Just indicates trend strength, use with +DI/-DI
            pass
    
    elif 'cci' in indicator_name.lower():
        # Commodity Channel Index: Buy when < -100, Sell when > 100
        signals[values < -100] = 1
        signals[values > 100] = -1
    
    elif 'psar' in indicator_name.lower():
        if 'up' in indicator_name.lower() and 'indicator' in indicator_name.lower():
            # PSAR Up Indicator: Buy when 1
            signals[values == 1] = 1
        elif 'down' in indicator_name.lower() and 'indicator' in indicator_name.lower():
            # PSAR Down Indicator: Sell when 1
            signals[values == 1] = -1
    
    elif 'aroon' in indicator_name.lower():
        if 'up' in indicator_name.lower():
            # Aroon Up: Buy when > 70
            aroon_down = df.get('trend_aroon_down', pd.Series(0, index=df.index))
            signals[(values > 70) & (values > aroon_down)] = 1
        elif 'down' in indicator_name.lower():
            # Aroon Down: Sell when > 70
            aroon_up = df.get('trend_aroon_up', pd.Series(0, index=df.index))
            signals[(values > 70) & (values > aroon_up)] = -1
    
    elif 'trix' in indicator_name.lower():
        # TRIX: Buy when crosses above 0, Sell when crosses below
        trix_prev = values.shift(1)
        signals[(values > 0) & (trix_prev <= 0)] = 1
        signals[(values < 0) & (trix_prev >= 0)] = -1
    
    return signals


def generate_volatility_signals(df, indicator_name):
    """
    Generate buy/sell signals for volatility indicators.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicator values
        indicator_name (str): Name of the indicator column
    
    Returns:
        pandas.Series: Series with 1 for buy, -1 for sell, 0 for neutral
    """
    if indicator_name not in df.columns:
        return pd.Series(0, index=df.index)
    
    values = df[indicator_name].copy()
    signals = pd.Series(0, index=df.index)
    
    if 'bb' in indicator_name.lower() or 'bollinger' in indicator_name.lower():
        if 'bbh' in indicator_name.lower() or 'high' in indicator_name.lower():
            # Bollinger Upper Band: Sell when price touches
            if 'Close' in df.columns:
                signals[df['Close'] >= values] = -1
        elif 'bbl' in indicator_name.lower() or 'low' in indicator_name.lower():
            # Bollinger Lower Band: Buy when price touches
            if 'Close' in df.columns:
                signals[df['Close'] <= values] = 1
        elif 'bbp' in indicator_name.lower() or 'percent' in indicator_name.lower():
            # Bollinger %B: Buy when < 0, Sell when > 1
            signals[values < 0] = 1
            signals[values > 1] = -1
        elif 'bbli' in indicator_name.lower():
            # BB Low Indicator: Buy when 1
            signals[values == 1] = 1
        elif 'bbhi' in indicator_name.lower():
            # BB High Indicator: Sell when 1
            signals[values == 1] = -1
    
    elif 'kc' in indicator_name.lower() or 'keltner' in indicator_name.lower():
        if 'kch' in indicator_name.lower() or 'high' in indicator_name.lower():
            # Keltner Upper: Sell when price touches
            if 'Close' in df.columns:
                signals[df['Close'] >= values] = -1
        elif 'kcl' in indicator_name.lower() or 'low' in indicator_name.lower():
            # Keltner Lower: Buy when price touches
            if 'Close' in df.columns:
                signals[df['Close'] <= values] = 1
        elif 'kcli' in indicator_name.lower():
            signals[values == 1] = 1
        elif 'kchi' in indicator_name.lower():
            signals[values == 1] = -1
    
    elif 'dc' in indicator_name.lower() or 'donchian' in indicator_name.lower():
        if 'dch' in indicator_name.lower() or 'high' in indicator_name.lower():
            # Donchian High: Sell when price breaks above
            if 'Close' in df.columns:
                signals[df['Close'] > values] = -1
        elif 'dcl' in indicator_name.lower() or 'low' in indicator_name.lower():
            # Donchian Low: Buy when price breaks below
            if 'Close' in df.columns:
                signals[df['Close'] < values] = 1
    
    return signals


def generate_volume_signals(df, indicator_name):
    """
    Generate buy/sell signals for volume indicators.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicator values
        indicator_name (str): Name of the indicator column
    
    Returns:
        pandas.Series: Series with 1 for buy, -1 for sell, 0 for neutral
    """
    if indicator_name not in df.columns:
        return pd.Series(0, index=df.index)
    
    values = df[indicator_name].copy()
    signals = pd.Series(0, index=df.index)
    
    if 'obv' in indicator_name.lower():
        # On-Balance Volume: Buy when increasing, Sell when decreasing
        obv_diff = values.diff()
        signals[obv_diff > 0] = 1
        signals[obv_diff < 0] = -1
    
    elif 'cmf' in indicator_name.lower():
        # Chaikin Money Flow: Buy when > 0.1, Sell when < -0.1
        signals[values > 0.1] = 1
        signals[values < -0.1] = -1
    
    elif 'adi' in indicator_name.lower():
        # Accumulation/Distribution: Buy when increasing, Sell when decreasing
        adi_diff = values.diff()
        signals[adi_diff > 0] = 1
        signals[adi_diff < 0] = -1
    
    elif 'vpt' in indicator_name.lower():
        # Volume Price Trend: Buy when increasing, Sell when decreasing
        vpt_diff = values.diff()
        signals[vpt_diff > 0] = 1
        signals[vpt_diff < 0] = -1
    
    elif 'fi' in indicator_name.lower() or 'force' in indicator_name.lower():
        # Force Index: Buy when positive, Sell when negative
        signals[values > 0] = 1
        signals[values < 0] = -1
    
    elif 'em' in indicator_name.lower() or 'ease' in indicator_name.lower():
        # Ease of Movement: Buy when positive, Sell when negative
        signals[values > 0] = 1
        signals[values < 0] = -1
    
    return signals


def generate_signals(df, indicator_name):
    """
    Generate buy/sell signals for any indicator.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicator values
        indicator_name (str): Name of the indicator column
    
    Returns:
        pandas.Series: Series with 1 for buy, -1 for sell, 0 for neutral
    """
    # Skip OHLCV columns and return columns
    skip_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'others_dr', 'others_dlr', 'others_cr',
                  'Date', 'Returns', 'Body_Size', 'Upper_Wick', 'Lower_Wick', 'Candle_Range',
                  'Avg_Range', 'Vol_Mean', 'Vol_Std', 'Vol_Z', 'Parkinson_Var']
    if indicator_name in skip_cols:
        return pd.Series(0, index=df.index)
    
    indicator_lower = indicator_name.lower()
    
    # Momentum indicators
    momentum_indicators = ['rsi', 'stoch', 'williams', 'wr', 'mfi', 'roc', 'uo', 'ultimate', 
                          'tsi', 'ao', 'awesome', 'ppo', 'pvo', 'kama']
    if any(mom in indicator_lower for mom in momentum_indicators):
        return generate_momentum_signals(df, indicator_name)
    
    # Trend indicators
    trend_indicators = ['macd', 'sma', 'ema', 'adx', 'aroon', 'cci', 'dpo', 'ichimoku', 
                       'kst', 'mass', 'psar', 'trix', 'vortex', 'stc', 'ema_5m', 'trend_5m']
    if any(trend in indicator_lower for trend in trend_indicators):
        return generate_trend_signals(df, indicator_name)
    
    # Volatility indicators
    volatility_indicators = ['atr', 'bb', 'bollinger', 'kc', 'keltner', 'dc', 'donchian',
                            'ui', 'synthetic_iv', 'rsi_5m', 'atr_15m', 'rsi_15m']
    if any(vol in indicator_lower for vol in volatility_indicators):
        return generate_volatility_signals(df, indicator_name)
    
    # Volume indicators
    volume_indicators = ['volume', 'obv', 'cmf', 'fi', 'eom', 'vwap', 'dist_vwap', 
                        'smart_money_flow', 'sentiment_skew', 'vol_lag', 'return_lag']
    if any(vol in indicator_lower for vol in volume_indicators):
        return generate_volume_signals(df, indicator_name)
    
    # Default: no signal
    return pd.Series(0, index=df.index)


def calculate_accuracy_metrics(predictions, actual_directions):
    """
    Calculate accuracy metrics for predictions.
    
    Args:
        predictions (pandas.Series): Predicted directions (1 for buy, -1 for sell, 0 for neutral)
        actual_directions (pandas.Series): Actual directions (1 for up, 0 for down)
    
    Returns:
        dict: Dictionary with accuracy metrics
    """
    # Convert predictions to binary (1 = up, 0 = down)
    # Buy signals (1) predict up (1), Sell signals (-1) predict down (0)
    pred_binary = predictions.copy()
    pred_binary[predictions == 1] = 1  # Buy = up
    pred_binary[predictions == -1] = 0  # Sell = down
    pred_binary[predictions == 0] = np.nan  # Neutral = no prediction
    
    # Filter out NaN values (neutral predictions)
    mask = ~(pred_binary.isna() | actual_directions.isna())
    if mask.sum() == 0:
        return {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'correct_predictions': 0
        }
    
    pred_filtered = pred_binary[mask]
    actual_filtered = actual_directions[mask]
    
    # Calculate metrics
    correct = (pred_filtered == actual_filtered).sum()
    total = len(pred_filtered)
    accuracy = correct / total if total > 0 else 0.0
    
    # Precision, Recall, F1 (for buy signals predicting up)
    try:
        precision = precision_score(actual_filtered, pred_filtered, zero_division=0)
        recall = recall_score(actual_filtered, pred_filtered, zero_division=0)
        f1 = f1_score(actual_filtered, pred_filtered, zero_division=0)
    except:
        precision = 0.0
        recall = 0.0
        f1 = 0.0
    
    # Count signals
    buy_signals = (predictions == 1).sum()
    sell_signals = (predictions == -1).sum()
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'total_signals': total,
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'correct_predictions': correct
    }


def analyze_indicator_accuracy(df, indicator_name):
    """
    Analyze accuracy of a single indicator.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicators and prices
        indicator_name (str): Name of the indicator column
    
    Returns:
        dict: Dictionary with accuracy metrics for the indicator
    """
    # Calculate actual next candle direction
    actual_directions = calculate_actual_direction(df)
    
    # Generate signals
    signals = generate_signals(df, indicator_name)
    
    # Calculate accuracy metrics
    metrics = calculate_accuracy_metrics(signals, actual_directions)
    metrics['indicator'] = indicator_name
    
    return metrics


def analyze_all_indicators(df):
    """
    Analyze accuracy of all indicators in the dataframe.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicators and prices
    
    Returns:
        pandas.DataFrame: DataFrame with accuracy metrics for each indicator
    """
    logger.info("🔍 Analyzing indicator accuracy...")
    
    # Clean data: drop rows where key indicators are NaN
    # Keep rows where at least some indicators have values
    df_clean = df.copy()
    original_len = len(df_clean)
    
    # Drop rows where all key indicators are NaN
    key_indicators = ['RSI', 'MACD', 'ATR', 'VWAP']
    available_key = [col for col in key_indicators if col in df_clean.columns]
    if available_key:
        df_clean = df_clean.dropna(subset=available_key[:1])  # Drop if first key indicator is NaN
    
    dropped = original_len - len(df_clean)
    if dropped > 0:
        logger.info(f"   Dropped {dropped} rows with missing key indicators (startup period)")
    
    # Get all indicator columns (exclude OHLCV and return columns)
    skip_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'others_dr', 'others_dlr', 'others_cr',
                  'Date', 'Returns', 'Body_Size', 'Upper_Wick', 'Lower_Wick', 'Candle_Range',
                  'Avg_Range', 'Vol_Mean', 'Vol_Std', 'Vol_Z', 'Parkinson_Var', 'Log_HL']
    indicator_cols = [col for col in df_clean.columns if col not in skip_cols]
    
    logger.info(f"   Analyzing {len(indicator_cols)} indicators on {len(df_clean)} rows...")
    
    results = []
    for i, indicator in enumerate(indicator_cols, 1):
        if i % 10 == 0:
            logger.info(f"   Progress: {i}/{len(indicator_cols)} indicators analyzed...")
        
        try:
            metrics = analyze_indicator_accuracy(df_clean, indicator)
            results.append(metrics)
        except Exception as e:
            logger.warning(f"   Error analyzing {indicator}: {e}")
            continue
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by accuracy (descending), but prioritize indicators with signals
    if not results_df.empty:
        # Sort by total_signals first (descending), then by accuracy
        results_df = results_df.sort_values(['total_signals', 'accuracy'], ascending=[False, False])
    
    logger.info(f"✅ Analyzed {len(results_df)} indicators")
    
    return results_df


def save_accuracy_results(results_df, symbol, interval, output_dir):
    """
    Save accuracy results to CSV file.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with accuracy results
        symbol (str): Stock symbol
        interval (str): Interval in minutes
        output_dir (str): Output directory path
    
    Returns:
        str: Path to saved file, or None if fails
    """
    if results_df is None or results_df.empty:
        logger.warning("No results to save.")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"indicator_accuracy_{interval}min.csv")
    results_df.to_csv(filename, index=False)
    logger.info(f"💾 Saved accuracy results to {filename}")
    return filename


if __name__ == "__main__":
    # Test the function
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze TA indicator accuracy for intraday data')
    parser.add_argument('input_file', help='Path to input CSV file with indicators')
    parser.add_argument('--symbol', required=True, help='Stock symbol (e.g., HDFCBANK.NS)')
    parser.add_argument('--interval', default='1', help='Interval in minutes (default: 1)')
    parser.add_argument('--output-dir', help='Output directory (optional)')
    
    args = parser.parse_args()
    
    logger.info(f"📂 Loading data from {args.input_file}...")
    df = pd.read_csv(args.input_file, index_col=0, parse_dates=True)
    logger.info(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
    
    results_df = analyze_all_indicators(df)
    
    if not results_df.empty:
        print(f"\n✅ Top 10 Most Accurate Indicators:")
        print(results_df.head(10)[['indicator', 'accuracy', 'precision', 'recall', 'f1_score', 'total_signals']].to_string())
        
        if args.output_dir:
            save_accuracy_results(results_df, args.symbol, args.interval, args.output_dir)

