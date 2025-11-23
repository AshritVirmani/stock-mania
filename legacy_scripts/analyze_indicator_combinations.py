"""
Analyze Indicator Combinations

Tests combinations of technical indicators to find optimal pairings for
intraday trading signals.
"""

import os
import pandas as pd
import numpy as np
import itertools
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_score

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_signals(df, indicator):
    """Generate basic buy signals (1) for an indicator."""
    # This relies on the previously implemented logic or simple rules
    # For simplicity here, we assume we have a way to get signals
    # Ideally, we reuse logic from analyze_intraday_ta_accuracy.py
    # But to keep standalone, we'll implement simple heuristics or load pre-calculated signals
    # Here we'll implement a few common ones for demonstration
    
    vals = df[indicator]
    signals = pd.Series(0, index=df.index)
    
    if 'rsi' in indicator:
        signals[vals < 30] = 1
    elif 'bbl' in indicator: # Bollinger Lower
        if 'Close' in df.columns:
            signals[df['Close'] < vals] = 1
    elif 'macd' in indicator and 'signal' not in indicator and 'diff' not in indicator:
        # MACD Line > Signal
        # Simplified: MACD > 0
        signals[vals > 0] = 1
    elif 'mfi' in indicator:
        signals[vals < 20] = 1
        
    return signals

def analyze_combinations(df, symbol, output_dir):
    """
    Analyze indicator combinations.
    
    Args:
        df (pandas.DataFrame): DataFrame with indicators
        symbol (str): Stock symbol
        output_dir (str): Output directory
        
    Returns:
        dict: Results summary
    """
    logger.info("🔗 Analyzing indicator combinations...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate future return direction (target)
    if 'target' not in df.columns:
        df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
    # Select a subset of distinct indicators to avoid combinatorial explosion
    # Pick top performing ones from previous analysis or key categories
    key_indicators = [
        'momentum_rsi', 'volatility_bbl', 'trend_macd', 
        'volume_mfi', 'trend_adx', 'momentum_stoch'
    ]
    
    # Filter available columns
    available_indicators = [col for col in key_indicators if col in df.columns]
    
    if len(available_indicators) < 2:
        logger.warning("Not enough indicators for combination analysis.")
        return {}
        
    # Generate signals for each
    signal_df = pd.DataFrame(index=df.index)
    for ind in available_indicators:
        signal_df[ind] = generate_signals(df, ind)
        
    # Test Pairs
    pair_results = []
    
    for pair in itertools.combinations(available_indicators, 2):
        # AND Logic: Both must signal Buy
        combined_signal = (signal_df[pair[0]] == 1) & (signal_df[pair[1]] == 1)
        
        if combined_signal.sum() > 0:
            # Calculate precision
            target_subset = df['target'][combined_signal]
            accuracy = target_subset.mean()
            
            pair_results.append({
                'indicator_1': pair[0],
                'indicator_2': pair[1],
                'signals': combined_signal.sum(),
                'accuracy': accuracy
            })
            
    pair_df = pd.DataFrame(pair_results)
    if not pair_df.empty:
        pair_df = pair_df.sort_values('accuracy', ascending=False)
        pair_file = os.path.join(output_dir, 'top_pairs.csv')
        pair_df.to_csv(pair_file)
        
        # Visualization: Top Pairs
        plt.figure(figsize=(10, 6))
        top_5 = pair_df.head(5)
        names = top_5.apply(lambda x: f"{x['indicator_1'].split('_')[-1]} + {x['indicator_2'].split('_')[-1]}", axis=1)
        sns.barplot(x=top_5['accuracy'], y=names, palette='viridis')
        plt.title(f'{symbol} - Top Indicator Pair Accuracy', fontsize=14)
        plt.xlim(0, 1)
        plt.axvline(0.5, color='red', linestyle='--')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'pair_accuracy.png'))
        plt.close()
    else:
        pair_file = None
        
    logger.info("✅ Indicator combination analysis complete.")
    
    return {
        'pairs_file': pair_file,
        'plots': [os.path.join(output_dir, 'pair_accuracy.png')] if not pair_df.empty else []
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Input CSV file')
    parser.add_argument('--symbol', required=True, help='Stock symbol')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    args = parser.parse_args()
    
    df = pd.read_csv(args.input_file, index_col=0, parse_dates=True)
    analyze_combinations(df, args.symbol, args.output_dir)
