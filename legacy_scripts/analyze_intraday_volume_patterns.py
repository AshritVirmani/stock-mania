"""
Analyze Intraday Volume Patterns

Analyzes 1-minute intraday data to identify volume spikes, volume-price relationships,
and volume clustering.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from scipy import stats

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sns.set_style("whitegrid")

def analyze_volume_patterns(df, symbol, output_dir):
    """
    Analyze volume-based patterns.
    
    Args:
        df (pandas.DataFrame): DataFrame with OHLCV data
        symbol (str): Stock symbol
        output_dir (str): Output directory
        
    Returns:
        dict: Results summary
    """
    logger.info("🔊 Analyzing volume patterns...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure calculations
    if 'returns' not in df.columns:
        df['returns'] = df['Close'].pct_change()
        
    # 1. Volume Spikes Analysis
    # Define spike: Volume > Mean + 2*StdDev (rolling window to account for time-of-day)
    # Better: Ratio to rolling average (e.g., 20-period)
    df['vol_ma'] = df['Volume'].rolling(window=20).mean()
    df['vol_ratio'] = df['Volume'] / df['vol_ma']
    
    # Spike threshold: 3x average
    spike_threshold = 3.0
    spikes = df[df['vol_ratio'] > spike_threshold].copy()
    
    # Analyze returns after spikes
    # Look at next 1, 5, 15 mins
    spike_outcomes = []
    for idx in spikes.index:
        try:
            loc = df.index.get_loc(idx)
            if loc + 15 < len(df):
                forward_ret_1 = (df['Close'].iloc[loc+1] / df['Close'].iloc[loc]) - 1
                forward_ret_5 = (df['Close'].iloc[loc+5] / df['Close'].iloc[loc]) - 1
                forward_ret_15 = (df['Close'].iloc[loc+15] / df['Close'].iloc[loc]) - 1
                
                spike_outcomes.append({
                    'timestamp': idx,
                    'volume': df['Volume'].iloc[loc],
                    'ratio': df['vol_ratio'].iloc[loc],
                    'price_change_at_spike': df['returns'].iloc[loc],
                    'ret_1min': forward_ret_1,
                    'ret_5min': forward_ret_5,
                    'ret_15min': forward_ret_15
                })
        except Exception:
            continue
            
    spikes_df = pd.DataFrame(spike_outcomes)
    spikes_file = os.path.join(output_dir, 'volume_spikes.csv')
    spikes_df.to_csv(spikes_file)
    
    # 2. Volume-Price Correlation
    # Rolling correlation between volume and absolute returns (volatility)
    df['abs_returns'] = df['returns'].abs()
    rolling_corr = df['Volume'].rolling(60).corr(df['abs_returns'])
    
    corr_file = os.path.join(output_dir, 'volume_price_correlation.csv')
    rolling_corr.describe().to_csv(corr_file)
    
    # Visualization: Volume Ratio vs Returns
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=spikes_df, x='price_change_at_spike', y='ratio', alpha=0.6)
    plt.title(f'{symbol} - Volume Spikes: Volume Ratio vs Price Change', fontsize=14)
    plt.xlabel('Price Change at Spike')
    plt.ylabel('Volume Ratio (x Moving Avg)')
    plt.axvline(0, color='black', linestyle='--')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'volume_spike_scatter.png'))
    plt.close()
    
    # 3. Volume Breakouts
    # High volume + High price move
    # Top decile of volume AND top decile of abs returns
    vol_thresh = df['Volume'].quantile(0.9)
    ret_thresh = df['abs_returns'].quantile(0.9)
    
    breakouts = df[(df['Volume'] > vol_thresh) & (df['abs_returns'] > ret_thresh)].copy()
    # Directional analysis
    breakouts['direction'] = np.where(breakouts['returns'] > 0, 'Up', 'Down')
    
    breakout_file = os.path.join(output_dir, 'volume_breakouts.csv')
    breakouts.to_csv(breakout_file)
    
    # Visualization: Breakout Distribution
    plt.figure(figsize=(8, 6))
    sns.countplot(data=breakouts, x='direction', palette='Set2')
    plt.title(f'{symbol} - Volume Breakout Direction Distribution', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'volume_breakout_dist.png'))
    plt.close()
    
    logger.info("✅ Volume pattern analysis complete.")
    
    return {
        'spikes_file': spikes_file,
        'breakout_file': breakout_file,
        'plots': [
            os.path.join(output_dir, 'volume_spike_scatter.png'),
            os.path.join(output_dir, 'volume_breakout_dist.png')
        ]
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Input CSV file')
    parser.add_argument('--symbol', required=True, help='Stock symbol')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    args = parser.parse_args()
    
    df = pd.read_csv(args.input_file, index_col=0, parse_dates=True)
    analyze_volume_patterns(df, args.symbol, args.output_dir)
