"""
Analyze Algo Trading Patterns

Identifies potential algorithmic/quantitative trading activity by analyzing:
1. Iceberg pattern timing
2. Unusual volume/price spikes
3. Time-based clustering of anomalies
4. Potential algo entry/exit patterns
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

def analyze_algo_patterns(df, symbol, output_dir, iceberg_file=None):
    """
    Analyze potential algo trading patterns.
    
    Args:
        df (pandas.DataFrame): DataFrame with OHLCV data
        symbol (str): Stock symbol
        output_dir (str): Output directory
        iceberg_file (str): Optional path to iceberg patterns CSV
        
    Returns:
        dict: Results summary
    """
    logger.info("🤖 Analyzing algo trading patterns...")
    os.makedirs(output_dir, exist_ok=True)
    
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Ensure required columns
    if 'returns' not in df.columns:
        df['returns'] = df['Close'].pct_change()
    df['abs_returns'] = df['returns'].abs()
    
    # Add time features
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['day_of_week'] = df.index.dayofweek
    df['day_name'] = df.index.day_name()
    df['time_str'] = df.index.strftime('%H:%M')
    
    results = {}
    
    # 1. Iceberg Pattern Timing Analysis
    if iceberg_file and os.path.exists(iceberg_file):
        logger.info("   📊 Analyzing iceberg pattern timing...")
        try:
            iceberg_df = pd.read_csv(iceberg_file, index_col=0, parse_dates=True)
            
            if len(iceberg_df) > 0:
                # Extract timing information
                iceberg_timing = []
                for idx in iceberg_df.index:
                    iceberg_timing.append({
                        'timestamp': idx,
                        'hour': idx.hour if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx).hour,
                        'minute': idx.minute if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx).minute,
                        'day_of_week': idx.dayofweek if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx).dayofweek,
                        'day_name': idx.strftime('%A') if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx).strftime('%A'),
                        'time_str': idx.strftime('%H:%M') if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx).strftime('%H:%M')
                    })
                
                iceberg_timing_df = pd.DataFrame(iceberg_timing)
                
                # Hourly distribution
                hourly_iceberg = iceberg_timing_df.groupby('hour').size().reset_index(name='count')
                hourly_iceberg['percentage'] = (hourly_iceberg['count'] / len(iceberg_timing_df) * 100).round(2)
                
                # Day of week distribution
                day_iceberg = iceberg_timing_df.groupby('day_name').size().reset_index(name='count')
                day_iceberg['percentage'] = (day_iceberg['count'] / len(iceberg_timing_df) * 100).round(2)
                
                # Time window analysis (15-min buckets)
                iceberg_timing_df['time_bucket'] = iceberg_timing_df['hour'].astype(str) + ':' + \
                    (iceberg_timing_df['minute'] // 15 * 15).astype(str).str.zfill(2)
                time_bucket_iceberg = iceberg_timing_df.groupby('time_bucket').size().reset_index(name='count')
                time_bucket_iceberg = time_bucket_iceberg.sort_values('count', ascending=False)
                
                # Save results
                hourly_iceberg_file = os.path.join(output_dir, 'iceberg_hourly_distribution.csv')
                hourly_iceberg.to_csv(hourly_iceberg_file, index=False)
                
                day_iceberg_file = os.path.join(output_dir, 'iceberg_day_distribution.csv')
                day_iceberg.to_csv(day_iceberg_file, index=False)
                
                time_bucket_file = os.path.join(output_dir, 'iceberg_time_buckets.csv')
                time_bucket_iceberg.to_csv(time_bucket_file, index=False)
                
                # Visualization: Iceberg timing
                fig, axes = plt.subplots(2, 2, figsize=(16, 12))
                
                # Hourly distribution
                axes[0, 0].bar(hourly_iceberg['hour'], hourly_iceberg['count'], color='steelblue', alpha=0.7, edgecolor='black')
                axes[0, 0].set_title(f'{symbol} - Iceberg Patterns by Hour\n(Total: {len(iceberg_timing_df)} patterns)', 
                                   fontsize=14, fontweight='bold')
                axes[0, 0].set_xlabel('Hour of Day (IST)', fontweight='bold')
                axes[0, 0].set_ylabel('Count', fontweight='bold')
                axes[0, 0].grid(True, alpha=0.3, axis='y')
                for i, (h, c) in enumerate(zip(hourly_iceberg['hour'], hourly_iceberg['count'])):
                    axes[0, 0].text(h, c, f'{c}\n({hourly_iceberg.iloc[i]["percentage"]:.1f}%)', 
                                   ha='center', va='bottom', fontsize=9, fontweight='bold')
                
                # Day of week distribution
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                day_iceberg_ordered = day_iceberg.set_index('day_name').reindex([d for d in day_order if d in day_iceberg['day_name'].values])
                axes[0, 1].bar(range(len(day_iceberg_ordered)), day_iceberg_ordered['count'], 
                              color='coral', alpha=0.7, edgecolor='black')
                axes[0, 1].set_xticks(range(len(day_iceberg_ordered)))
                axes[0, 1].set_xticklabels(day_iceberg_ordered.index, rotation=45, ha='right')
                axes[0, 1].set_title(f'Iceberg Patterns by Day of Week', fontsize=14, fontweight='bold')
                axes[0, 1].set_ylabel('Count', fontweight='bold')
                axes[0, 1].grid(True, alpha=0.3, axis='y')
                for i, (idx, row) in enumerate(day_iceberg_ordered.iterrows()):
                    axes[0, 1].text(i, row['count'], f'{int(row["count"])}\n({row["percentage"]:.1f}%)', 
                                   ha='center', va='bottom', fontsize=9, fontweight='bold')
                
                # Time bucket heatmap (top 10)
                top_buckets = time_bucket_iceberg.head(10)
                axes[1, 0].barh(range(len(top_buckets)), top_buckets['count'], color='green', alpha=0.7, edgecolor='black')
                axes[1, 0].set_yticks(range(len(top_buckets)))
                axes[1, 0].set_yticklabels(top_buckets['time_bucket'])
                axes[1, 0].set_title('Top 10 Time Windows for Iceberg Patterns', fontsize=14, fontweight='bold')
                axes[1, 0].set_xlabel('Count', fontweight='bold')
                axes[1, 0].grid(True, alpha=0.3, axis='x')
                for i, (idx, row) in enumerate(top_buckets.iterrows()):
                    axes[1, 0].text(row['count'], i, f' {int(row["count"])}', 
                                   va='center', fontsize=10, fontweight='bold')
                
                # Cumulative distribution over time
                iceberg_timing_df_sorted = iceberg_timing_df.sort_values('timestamp')
                iceberg_timing_df_sorted['cumulative'] = range(1, len(iceberg_timing_df_sorted) + 1)
                axes[1, 1].plot(iceberg_timing_df_sorted['timestamp'], iceberg_timing_df_sorted['cumulative'], 
                               marker='o', markersize=3, linewidth=2, color='red')
                axes[1, 1].set_title('Cumulative Iceberg Patterns Over Time', fontsize=14, fontweight='bold')
                axes[1, 1].set_xlabel('Date', fontweight='bold')
                axes[1, 1].set_ylabel('Cumulative Count', fontweight='bold')
                axes[1, 1].grid(True, alpha=0.3)
                axes[1, 1].tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'iceberg_timing_analysis.png'), dpi=150, bbox_inches='tight')
                plt.close()
                
                results['iceberg_timing'] = {
                    'total_patterns': len(iceberg_timing_df),
                    'peak_hour': hourly_iceberg.loc[hourly_iceberg['count'].idxmax(), 'hour'],
                    'peak_day': day_iceberg.loc[day_iceberg['count'].idxmax(), 'day_name'],
                    'top_time_bucket': time_bucket_iceberg.iloc[0]['time_bucket'] if len(time_bucket_iceberg) > 0 else None
                }
                logger.info(f"   ✅ Analyzed {len(iceberg_timing_df)} iceberg patterns")
        except Exception as e:
            logger.warning(f"   ⚠️  Error analyzing iceberg timing: {e}")
    
    # 2. Unusual Volume/Price Anomalies
    logger.info("   📊 Detecting unusual volume/price anomalies...")
    
    # Calculate rolling statistics
    df['vol_ma_20'] = df['Volume'].rolling(window=20).mean()
    df['vol_std_20'] = df['Volume'].rolling(window=20).std()
    df['price_ma_20'] = df['Close'].rolling(window=20).mean()
    df['price_std_20'] = df['Close'].rolling(window=20).std()
    
    # Define anomalies: > 3 standard deviations
    df['vol_zscore'] = (df['Volume'] - df['vol_ma_20']) / df['vol_std_20']
    df['price_zscore'] = (df['abs_returns'] - df['abs_returns'].rolling(20).mean()) / df['abs_returns'].rolling(20).std()
    
    # Anomalies
    vol_anomalies = df[df['vol_zscore'] > 3].copy()
    price_anomalies = df[df['price_zscore'] > 3].copy()
    combined_anomalies = df[(df['vol_zscore'] > 2.5) & (df['price_zscore'] > 2.5)].copy()
    
    # Add timing info to anomalies
    if len(vol_anomalies) > 0:
        vol_anomalies['hour'] = vol_anomalies.index.hour
        vol_anomalies['day_name'] = vol_anomalies.index.day_name()
        vol_anomalies['time_str'] = vol_anomalies.index.strftime('%H:%M')
        
        # Hourly distribution of volume anomalies
        vol_anomaly_hourly = vol_anomalies.groupby('hour').size().reset_index(name='count')
        vol_anomaly_hourly['percentage'] = (vol_anomaly_hourly['count'] / len(vol_anomalies) * 100).round(2)
        
        vol_anomalies_file = os.path.join(output_dir, 'volume_anomalies.csv')
        vol_anomalies[['Open', 'High', 'Low', 'Close', 'Volume', 'vol_zscore', 'returns', 'time_str']].to_csv(vol_anomalies_file)
        
        vol_anomaly_hourly_file = os.path.join(output_dir, 'volume_anomaly_hourly.csv')
        vol_anomaly_hourly.to_csv(vol_anomaly_hourly_file, index=False)
        
        logger.info(f"   ✅ Found {len(vol_anomalies)} volume anomalies")
    
    if len(price_anomalies) > 0:
        price_anomalies['hour'] = price_anomalies.index.hour
        price_anomalies['day_name'] = price_anomalies.index.day_name()
        price_anomalies['time_str'] = price_anomalies.index.strftime('%H:%M')
        
        price_anomalies_file = os.path.join(output_dir, 'price_anomalies.csv')
        price_anomalies[['Open', 'High', 'Low', 'Close', 'Volume', 'price_zscore', 'returns', 'time_str']].to_csv(price_anomalies_file)
        
        logger.info(f"   ✅ Found {len(price_anomalies)} price anomalies")
    
    if len(combined_anomalies) > 0:
        combined_anomalies['hour'] = combined_anomalies.index.hour
        combined_anomalies['day_name'] = combined_anomalies.index.day_name()
        combined_anomalies['time_str'] = combined_anomalies.index.strftime('%H:%M')
        
        combined_anomalies_file = os.path.join(output_dir, 'combined_anomalies.csv')
        combined_anomalies[['Open', 'High', 'Low', 'Close', 'Volume', 'vol_zscore', 'price_zscore', 'returns', 'time_str']].to_csv(combined_anomalies_file)
        
        # Time distribution of combined anomalies
        combined_hourly = combined_anomalies.groupby('hour').size().reset_index(name='count')
        combined_hourly['percentage'] = (combined_hourly['count'] / len(combined_anomalies) * 100).round(2)
        
        combined_hourly_file = os.path.join(output_dir, 'combined_anomaly_hourly.csv')
        combined_hourly.to_csv(combined_hourly_file, index=False)
        
        logger.info(f"   ✅ Found {len(combined_anomalies)} combined anomalies (high vol + high price move)")
    
    # 3. Visualization: Anomaly Timing
    if len(vol_anomalies) > 0 or len(price_anomalies) > 0 or len(combined_anomalies) > 0:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Volume anomalies by hour
        if len(vol_anomalies) > 0:
            axes[0, 0].bar(vol_anomaly_hourly['hour'], vol_anomaly_hourly['count'], 
                          color='orange', alpha=0.7, edgecolor='black')
            axes[0, 0].set_title(f'{symbol} - Volume Anomalies by Hour\n(>3σ from 20-period mean, Total: {len(vol_anomalies)})', 
                                 fontsize=14, fontweight='bold')
            axes[0, 0].set_xlabel('Hour of Day (IST)', fontweight='bold')
            axes[0, 0].set_ylabel('Count', fontweight='bold')
            axes[0, 0].grid(True, alpha=0.3, axis='y')
            for i, (h, c) in enumerate(zip(vol_anomaly_hourly['hour'], vol_anomaly_hourly['count'])):
                axes[0, 0].text(h, c, f'{c}\n({vol_anomaly_hourly.iloc[i]["percentage"]:.1f}%)', 
                               ha='center', va='bottom', fontsize=9, fontweight='bold')
        else:
            axes[0, 0].text(0.5, 0.5, 'No Volume Anomalies Detected', ha='center', va='center', 
                           transform=axes[0, 0].transAxes, fontsize=14)
            axes[0, 0].set_title('Volume Anomalies by Hour', fontsize=14)
        
        # Combined anomalies by hour
        if len(combined_anomalies) > 0:
            axes[0, 1].bar(combined_hourly['hour'], combined_hourly['count'], 
                           color='red', alpha=0.7, edgecolor='black')
            axes[0, 1].set_title(f'Combined Anomalies by Hour\n(High Vol + High Price Move, Total: {len(combined_anomalies)})', 
                                fontsize=14, fontweight='bold')
            axes[0, 1].set_xlabel('Hour of Day (IST)', fontweight='bold')
            axes[0, 1].set_ylabel('Count', fontweight='bold')
            axes[0, 1].grid(True, alpha=0.3, axis='y')
            for i, (h, c) in enumerate(zip(combined_hourly['hour'], combined_hourly['count'])):
                axes[0, 1].text(h, c, f'{c}\n({combined_hourly.iloc[i]["percentage"]:.1f}%)', 
                               ha='center', va='bottom', fontsize=9, fontweight='bold')
        else:
            axes[0, 1].text(0.5, 0.5, 'No Combined Anomalies Detected', ha='center', va='center', 
                           transform=axes[0, 1].transAxes, fontsize=14)
            axes[0, 1].set_title('Combined Anomalies by Hour', fontsize=14)
        
        # Top anomaly times (15-min buckets)
        if len(combined_anomalies) > 0:
            combined_anomalies['time_bucket'] = combined_anomalies['hour'].astype(str) + ':' + \
                (combined_anomalies['minute'] // 15 * 15).astype(str).str.zfill(2)
            time_bucket_combined = combined_anomalies.groupby('time_bucket').size().reset_index(name='count')
            time_bucket_combined = time_bucket_combined.sort_values('count', ascending=False).head(10)
            
            axes[1, 0].barh(range(len(time_bucket_combined)), time_bucket_combined['count'], 
                           color='darkred', alpha=0.7, edgecolor='black')
            axes[1, 0].set_yticks(range(len(time_bucket_combined)))
            axes[1, 0].set_yticklabels(time_bucket_combined['time_bucket'])
            axes[1, 0].set_title('Top 10 Time Windows for Combined Anomalies\n(Potential Algo Trading Windows)', 
                                fontsize=14, fontweight='bold')
            axes[1, 0].set_xlabel('Count', fontweight='bold')
            axes[1, 0].grid(True, alpha=0.3, axis='x')
            for i, (idx, row) in enumerate(time_bucket_combined.iterrows()):
                axes[1, 0].text(row['count'], i, f' {int(row["count"])}', 
                               va='center', fontsize=10, fontweight='bold')
        else:
            axes[1, 0].text(0.5, 0.5, 'No Data Available', ha='center', va='center', 
                           transform=axes[1, 0].transAxes, fontsize=14)
            axes[1, 0].set_title('Top Anomaly Time Windows', fontsize=14)
        
        # Summary statistics
        summary_text = f"""
        ANOMALY SUMMARY
        ================
        Volume Anomalies: {len(vol_anomalies)}
        Price Anomalies: {len(price_anomalies)}
        Combined Anomalies: {len(combined_anomalies)}
        
        POTENTIAL ALGO TRADING INDICATORS:
        - Combined anomalies suggest coordinated algo activity
        - Clustering in specific time windows indicates systematic trading
        - High volume + high price moves = potential large algo orders
        """
        axes[1, 1].text(0.1, 0.5, summary_text, transform=axes[1, 1].transAxes, 
                        fontsize=12, verticalalignment='center', family='monospace',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        axes[1, 1].axis('off')
        axes[1, 1].set_title('Analysis Summary', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'algo_trading_patterns.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        results['anomalies'] = {
            'volume_anomalies': len(vol_anomalies),
            'price_anomalies': len(price_anomalies),
            'combined_anomalies': len(combined_anomalies),
            'peak_anomaly_hour': combined_hourly.loc[combined_hourly['count'].idxmax(), 'hour'] if len(combined_anomalies) > 0 else None
        }
    
    logger.info("✅ Algo trading pattern analysis complete.")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Input CSV file')
    parser.add_argument('--symbol', required=True, help='Stock symbol')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--iceberg-file', help='Path to iceberg patterns CSV')
    args = parser.parse_args()
    
    df = pd.read_csv(args.input_file, index_col=0, parse_dates=True)
    analyze_algo_patterns(df, args.symbol, args.output_dir, args.iceberg_file)

