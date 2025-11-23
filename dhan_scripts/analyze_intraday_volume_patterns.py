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
    if len(spikes_df) > 0:
        # Convert price_change_at_spike to percentage
        spikes_df['price_change_pct'] = spikes_df['price_change_at_spike'] * 100
        spikes_df['ret_5min_pct'] = spikes_df['ret_5min'] * 100
        
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(spikes_df['price_change_pct'], spikes_df['ratio'], 
                            c=spikes_df['ret_5min_pct'], s=100, alpha=0.6, 
                            cmap='RdYlGn', edgecolors='black', linewidth=0.5)
        plt.colorbar(scatter, label='5-min Forward Return (%)')
        plt.title(f'{symbol} - Volume Spikes: Volume Ratio vs Price Change\n(Color indicates 5-min forward return)', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Price Change at Spike (%)', fontweight='bold', fontsize=12)
        plt.ylabel('Volume Ratio (x Moving Avg)', fontweight='bold', fontsize=12)
        plt.axvline(0, color='black', linestyle='--', alpha=0.5, linewidth=1.5)
        plt.axhline(spike_threshold, color='red', linestyle='--', alpha=0.5, 
                   linewidth=1.5, label=f'Spike Threshold ({spike_threshold}x)')
        plt.legend(loc='upper right', fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = f'Total Spikes: {len(spikes_df)}\n'
        stats_text += f'Avg 5-min Return: {spikes_df["ret_5min_pct"].mean():.3f}%\n'
        stats_text += f'Positive Returns: {(spikes_df["ret_5min_pct"] > 0).sum()} ({(spikes_df["ret_5min_pct"] > 0).sum()/len(spikes_df)*100:.1f}%)'
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=10)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'volume_spike_scatter.png'), dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"   ✅ Saved volume spike scatter with {len(spikes_df)} spikes")
    else:
        logger.warning("   ⚠️  No volume spikes found - scatter plot not generated")
        # Create placeholder
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'No Volume Spikes Detected\n(Threshold may be too high or insufficient data)', 
                ha='center', va='center', fontsize=14, transform=plt.gca().transAxes)
        plt.title(f'{symbol} - Volume Spike Scatter', fontsize=14)
        plt.xlabel('Price Change at Spike (%)')
        plt.ylabel('Volume Ratio (x Moving Avg)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'volume_spike_scatter.png'), dpi=150)
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
    if len(breakouts) > 0:
        plt.figure(figsize=(10, 6))
        direction_counts = breakouts['direction'].value_counts()
        colors = ['green' if d == 'Up' else 'red' for d in direction_counts.index]
        bars = plt.bar(direction_counts.index, direction_counts.values, color=colors, alpha=0.7, edgecolor='black')
        plt.title(f'{symbol} - Volume Breakout Direction Distribution\n(Total: {len(breakouts)} breakouts)', fontsize=14)
        plt.xlabel('Direction')
        plt.ylabel('Count')
        plt.grid(True, alpha=0.3, axis='y')
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}\n({height/len(breakouts)*100:.1f}%)',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'volume_breakout_dist.png'), dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"   ✅ Saved volume breakout distribution with {len(breakouts)} breakouts")
    else:
        logger.warning("   ⚠️  No volume breakouts found. Skipping distribution plot.")
        # Create empty placeholder
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No Volume Breakouts Detected\n(Requires top 10% volume AND top 10% price movement)', 
                ha='center', va='center', fontsize=14, transform=plt.gca().transAxes)
        plt.title(f'{symbol} - Volume Breakout Distribution', fontsize=14)
        plt.xlabel('Direction')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'volume_breakout_dist.png'), dpi=150)
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
