"""
Analyze Intraday Price Patterns

Analyzes 1-minute intraday data to identify momentum, breakouts, reversals,
and other price action patterns.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sns.set_style("whitegrid")

def analyze_price_patterns(df, symbol, output_dir):
    """
    Analyze price movement patterns.
    
    Args:
        df (pandas.DataFrame): DataFrame with OHLCV data
        symbol (str): Stock symbol
        output_dir (str): Output directory
        
    Returns:
        dict: Results summary
    """
    logger.info("📈 Analyzing price patterns...")
    os.makedirs(output_dir, exist_ok=True)
    
    df = df.copy()
    if 'returns' not in df.columns:
        df['returns'] = df['Close'].pct_change()
        
    # 1. Momentum Patterns
    # 3 consecutive up/down candles
    df['direction'] = np.sign(df['returns'])
    df['streak'] = df['direction'].groupby((df['direction'] != df['direction'].shift()).cumsum()).cumcount() + 1
    
    # Analyze what happens after streak of 3
    streak_3_up = df[(df['direction'] == 1) & (df['streak'] == 3)].index
    streak_3_down = df[(df['direction'] == -1) & (df['streak'] == 3)].index
    
    momentum_results = []
    for name, indices in [('3 Up', streak_3_up), ('3 Down', streak_3_down)]:
        outcomes = []
        for idx in indices:
            try:
                loc = df.index.get_loc(idx)
                if loc + 1 < len(df):
                    next_ret = df['returns'].iloc[loc+1]
                    outcomes.append(next_ret)
            except: pass
        
        if outcomes:
            win_rate = (np.array(outcomes) > 0).mean() if 'Up' in name else (np.array(outcomes) < 0).mean()
            momentum_results.append({
                'pattern': name,
                'count': len(outcomes),
                'continuation_rate': win_rate,
                'avg_next_return': np.mean(outcomes)
            })
            
    mom_df = pd.DataFrame(momentum_results)
    mom_file = os.path.join(output_dir, 'momentum_analysis.csv')
    mom_df.to_csv(mom_file)
    
    # 2. Reversal Patterns (Pin bars / Hammers)
    # Simple definition: Long wick, small body
    # Hammer (Bullish): Lower wick > 2x body, Upper wick small
    df['body'] = (df['Close'] - df['Open']).abs()
    df['upper_wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['lower_wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    
    # Avoid division by zero
    df['body'] = df['body'].replace(0, 0.01) # minimal size
    
    hammers = df[
        (df['lower_wick'] > 2 * df['body']) & 
        (df['upper_wick'] < df['body'])
    ].copy()
    
    shooting_stars = df[
        (df['upper_wick'] > 2 * df['body']) & 
        (df['lower_wick'] < df['body'])
    ].copy()
    
    reversal_results = []
    
    # Analyze Hammers
    hammer_outcomes = []
    for idx in hammers.index:
        try:
            loc = df.index.get_loc(idx)
            if loc + 5 < len(df):
                # Return over next 5 mins
                ret_5 = (df['Close'].iloc[loc+5] / df['Close'].iloc[loc]) - 1
                hammer_outcomes.append(ret_5)
        except: pass
        
    if hammer_outcomes:
        reversal_results.append({
            'pattern': 'Hammer',
            'count': len(hammer_outcomes),
            'bullish_accuracy': (np.array(hammer_outcomes) > 0).mean(),
            'avg_5min_return': np.mean(hammer_outcomes)
        })
        
    # Analyze Shooting Stars
    star_outcomes = []
    for idx in shooting_stars.index:
        try:
            loc = df.index.get_loc(idx)
            if loc + 5 < len(df):
                ret_5 = (df['Close'].iloc[loc+5] / df['Close'].iloc[loc]) - 1
                star_outcomes.append(ret_5)
        except: pass
        
    if star_outcomes:
        reversal_results.append({
            'pattern': 'Shooting Star',
            'count': len(star_outcomes),
            'bearish_accuracy': (np.array(star_outcomes) < 0).mean(),
            'avg_5min_return': np.mean(star_outcomes)
        })
        
    rev_df = pd.DataFrame(reversal_results)
    rev_file = os.path.join(output_dir, 'reversal_patterns.csv')
    rev_df.to_csv(rev_file)
    
    # Visualization: Pattern Success Rates
    if not rev_df.empty:
        plt.figure(figsize=(8, 6))
        sns.barplot(data=rev_df, x='pattern', y='bullish_accuracy' if 'bullish_accuracy' in rev_df.columns else 'avg_5min_return') 
        # Note: This visualization is simple, real implementation would handle different metrics better
        plt.title(f'{symbol} - Reversal Pattern Performance', fontsize=14)
        plt.ylabel('Success Rate / Return')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'reversal_performance.png'))
        plt.close()
    
    logger.info("✅ Price pattern analysis complete.")
    
    return {
        'momentum_file': mom_file,
        'reversal_file': rev_file,
        'plots': [os.path.join(output_dir, 'reversal_performance.png')] if not rev_df.empty else []
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Input CSV file')
    parser.add_argument('--symbol', required=True, help='Stock symbol')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    args = parser.parse_args()
    
    df = pd.read_csv(args.input_file, index_col=0, parse_dates=True)
    analyze_price_patterns(df, args.symbol, args.output_dir)
