"""
Analyze Intraday Time-Based Patterns

Analyzes 1-minute intraday data to identify time-based patterns in returns,
volatility, and volume across hours of day, days of week, and trading sessions.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def analyze_time_patterns(df, symbol, output_dir):
    """
    Analyze time-based patterns in the data.
    
    Args:
        df (pandas.DataFrame): DataFrame with OHLCV data and indicators, indexed by datetime
        symbol (str): Stock symbol
        output_dir (str): Output directory for results
    
    Returns:
        dict: Dictionary with analysis results and file paths
    """
    logger.info("⏳ Analyzing time-based patterns...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Add time features
    df = df.copy()
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['day_of_week'] = df.index.dayofweek
    df['day_name'] = df.index.day_name()
    df['time_decimal'] = df['hour'] + df['minute'] / 60.0
    
    # Calculate returns and volatility if not present
    if 'returns' not in df.columns:
        df['returns'] = df['Close'].pct_change()
    
    if 'log_returns' not in df.columns:
        df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
    if 'volatility' not in df.columns:
        # Simple high-low range as volatility proxy for 1-min data
        df['volatility'] = (df['High'] - df['Low']) / df['Open']
    
    # 1. Hourly Analysis
    hourly_stats = df.groupby('hour').agg({
        'returns': ['mean', 'std', 'count'],
        'volatility': 'mean',
        'Volume': 'mean'
    })
    hourly_stats.columns = ['_'.join(col).strip() for col in hourly_stats.columns.values]
    hourly_stats['sharpe_proxy'] = hourly_stats['returns_mean'] / hourly_stats['returns_std'] * np.sqrt(60) # Annualized-ish
    
    # Convert returns to percentage (basis points) for better visualization
    hourly_stats['returns_mean_pct'] = hourly_stats['returns_mean'] * 100  # Convert to percentage
    hourly_stats['returns_std_pct'] = hourly_stats['returns_std'] * 100
    
    # Calculate cumulative return per hour (assuming ~60 minutes per hour)
    hourly_stats['cumulative_return_pct'] = hourly_stats['returns_mean'] * hourly_stats['returns_count'] * 100
    
    # Also save percentage versions for readability
    hourly_stats_display = hourly_stats.copy()
    hourly_stats_display['returns_mean_pct'] = hourly_stats_display['returns_mean'] * 100
    hourly_stats_display['returns_std_pct'] = hourly_stats_display['returns_std'] * 100
    hourly_stats_display['volatility_mean_pct'] = hourly_stats_display['volatility_mean'] * 100
    
    hourly_file = os.path.join(output_dir, 'hourly_analysis.csv')
    hourly_stats_display.to_csv(hourly_file)
    
    # Visualization: Hourly Patterns
    # Filter to trading hours only (9-15)
    trading_hours = hourly_stats[(hourly_stats.index >= 9) & (hourly_stats.index <= 15)].copy()
    
    if len(trading_hours) > 0:
        fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
        
        # Create hour labels with IST time
        hour_labels = [f"{int(h)}:00\n({h}:00-{h+1}:00 IST)" for h in trading_hours.index]
        
        # Returns (in percentage) - show cumulative return per hour for better visibility
        colors = ['green' if x > 0 else 'red' for x in trading_hours['cumulative_return_pct']]
        bars = axes[0].bar(range(len(trading_hours)), trading_hours['cumulative_return_pct'], 
                          color=colors, alpha=0.7, edgecolor='black')
        axes[0].set_title(f'{symbol} - Cumulative Returns by Hour (%)', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Cumulative Return per Hour (%)', fontweight='bold')
        axes[0].set_xticks(range(len(trading_hours)))
        axes[0].set_xticklabels([f"{int(h)}:00" for h in trading_hours.index], rotation=0)
        axes[0].axhline(0, color='black', linewidth=1.5)
        axes[0].grid(True, alpha=0.3, axis='y')
        # Add value labels on bars
        for i, (idx, row) in enumerate(trading_hours.iterrows()):
            height = row['cumulative_return_pct']
            axes[0].text(i, height, f'{height:.2f}%', 
                        ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')
        
        # Volatility (convert to percentage)
        trading_hours['volatility_mean_pct'] = trading_hours['volatility_mean'] * 100
        axes[1].plot(range(len(trading_hours)), trading_hours['volatility_mean_pct'], 
                    marker='o', linewidth=2, markersize=8, color='purple', label='Volatility')
        axes[1].fill_between(range(len(trading_hours)), trading_hours['volatility_mean_pct'], 
                            alpha=0.3, color='purple')
        axes[1].set_title(f'{symbol} - Average Volatility by Hour', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Average Range (%)', fontweight='bold')
        axes[1].set_xticks(range(len(trading_hours)))
        axes[1].set_xticklabels([f"{int(h)}:00" for h in trading_hours.index], rotation=0)
        axes[1].grid(True, alpha=0.3)
        # Add value labels
        for i, (idx, row) in enumerate(trading_hours.iterrows()):
            axes[1].text(i, row['volatility_mean_pct'], f'{row["volatility_mean_pct"]:.3f}%', 
                        ha='center', va='bottom', fontsize=8)
        
        # Volume
        bars2 = axes[2].bar(range(len(trading_hours)), trading_hours['Volume_mean'], 
                           color='steelblue', alpha=0.7, edgecolor='black')
        axes[2].set_title(f'{symbol} - Average Volume by Hour', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('Average Volume', fontweight='bold')
        axes[2].set_xlabel('Hour of Day (IST)', fontweight='bold')
        axes[2].set_xticks(range(len(trading_hours)))
        axes[2].set_xticklabels([f"{int(h)}:00\n({h}:00-{h+1}:00)" for h in trading_hours.index], rotation=0, fontsize=9)
        axes[2].grid(True, alpha=0.3, axis='y')
        # Add value labels
        for i, (idx, row) in enumerate(trading_hours.iterrows()):
            height = row['Volume_mean']
            axes[2].text(i, height, f'{int(height):,}', 
                        ha='center', va='bottom', fontsize=8, rotation=90)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'hourly_patterns.png'), dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"   ✅ Saved hourly patterns chart with {len(trading_hours)} trading hours")
    else:
        logger.warning("   ⚠️  No trading hours data (9-15) for hourly patterns chart")
        # Create placeholder
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No Trading Hours Data Available\n(Market hours: 9:15 AM - 3:30 PM IST)', 
               ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title(f'{symbol} - Hourly Patterns', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'hourly_patterns.png'), dpi=150)
        plt.close()
    
    # 2. Day of Week Analysis
    # 0=Monday, 4=Friday (assuming trading days)
    day_stats = df.groupby('day_of_week').agg({
        'returns': ['mean', 'std', 'count'],
        'volatility': 'mean',
        'Volume': 'mean'
    })
    day_stats.columns = ['_'.join(col).strip() for col in day_stats.columns.values]
    # Convert to percentage
    day_stats['returns_mean_pct'] = day_stats['returns_mean'] * 100
    day_stats['volatility_mean_pct'] = day_stats['volatility_mean'] * 100
    # Map index to day names
    day_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
    day_stats.index = day_stats.index.map(day_map)
    
    # Save with percentage columns
    day_stats_display = day_stats.copy()
    day_stats_display['returns_mean_pct'] = day_stats_display['returns_mean'] * 100
    day_stats_display['volatility_mean_pct'] = day_stats_display['volatility_mean'] * 100
    
    day_file = os.path.join(output_dir, 'day_of_week_analysis.csv')
    day_stats_display.to_csv(day_file)
    
    # Visualization: Day of Week
    if len(day_stats) > 0:
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        # Returns (in percentage)
        colors = ['green' if x > 0 else 'red' for x in day_stats['returns_mean_pct']]
        bars1 = axes[0].bar(day_stats.index, day_stats['returns_mean_pct'], color=colors, alpha=0.7, edgecolor='black')
        axes[0].set_title(f'{symbol} - Average Returns by Day of Week (%)', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Average Return (%)')
        axes[0].axhline(0, color='black', linewidth=1.5)
        axes[0].grid(True, alpha=0.3, axis='y')
        # Add value labels
        for bar, val in zip(bars1, day_stats['returns_mean_pct']):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.3f}%', ha='center', va='bottom' if height > 0 else 'top', 
                        fontsize=11, fontweight='bold')
        
        # Volatility (in percentage)
        bars2 = axes[1].bar(day_stats.index, day_stats['volatility_mean_pct'], 
                           color='purple', alpha=0.7, edgecolor='black')
        axes[1].set_title(f'{symbol} - Average Volatility by Day of Week (%)', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Average Volatility (%)')
        axes[1].grid(True, alpha=0.3, axis='y')
        # Add value labels
        for bar, val in zip(bars2, day_stats['volatility_mean_pct']):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.3f}%', ha='center', va='bottom', 
                        fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'day_of_week_patterns.png'), dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"   ✅ Saved day of week patterns with {len(day_stats)} days")
    else:
        logger.warning("   ⚠️  No day of week data. Creating placeholder.")
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'Insufficient Data for Day of Week Analysis\n(Need data across multiple days)', 
                ha='center', va='center', fontsize=14, transform=plt.gca().transAxes)
        plt.title(f'{symbol} - Day of Week Patterns', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'day_of_week_patterns.png'), dpi=150)
        plt.close()
    
    # 3. Session Analysis (Indian Market Specific)
    # Opening: 9:15 - 10:15
    # Mid-day: 10:15 - 14:30
    # Closing: 14:30 - 15:30
    
    def get_session(row):
        t = row['time_decimal']
        if 9.25 <= t < 10.25:
            return 'Opening'
        elif 10.25 <= t < 14.5:
            return 'Mid-day'
        elif 14.5 <= t <= 15.5:
            return 'Closing'
        else:
            return 'Other'
            
    df['session'] = df.apply(get_session, axis=1)
    session_stats = df[df['session'] != 'Other'].groupby('session').agg({
        'returns': ['mean', 'std'],
        'volatility': 'mean',
        'Volume': 'mean'
    })
    session_stats.columns = ['_'.join(col).strip() for col in session_stats.columns.values]
    # Reorder
    session_order = ['Opening', 'Mid-day', 'Closing']
    session_stats = session_stats.reindex(session_order)
    
    session_file = os.path.join(output_dir, 'session_analysis.csv')
    session_stats.to_csv(session_file)
    
    # Visualization: Heatmap of Returns (Hour vs Day)
    # Pivot data for heatmap - convert to percentage
    pivot_returns = df.groupby(['day_name', 'hour'])['returns'].mean().unstack() * 100  # Convert to percentage
    # Reorder days
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    pivot_returns = pivot_returns.reindex([d for d in days_order if d in pivot_returns.index])
    
    if len(pivot_returns) > 0 and len(pivot_returns.columns) > 0:
        plt.figure(figsize=(14, 8))
        sns.heatmap(pivot_returns, cmap='RdYlGn', center=0, annot=True, fmt='.2f', 
                   cbar_kws={'label': 'Average Return (%)'}, linewidths=0.5, linecolor='gray')
        plt.title(f'{symbol} - Returns Heatmap: Day of Week vs Hour of Day\n' +
                 'Green = Positive Returns, Red = Negative Returns\n' +
                 'Shows which hour-day combinations are most profitable', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Hour of Day (IST)', fontsize=12, fontweight='bold')
        plt.ylabel('Day of Week', fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'time_heatmap.png'), dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"   ✅ Saved time heatmap with {len(pivot_returns)} days and {len(pivot_returns.columns)} hours")
    else:
        logger.warning("   ⚠️  Insufficient data for time heatmap. Creating placeholder.")
        plt.figure(figsize=(12, 6))
        plt.text(0.5, 0.5, 'Insufficient Data for Time Heatmap\n(Need data across multiple days and hours)', 
                ha='center', va='center', fontsize=14, transform=plt.gca().transAxes)
        plt.title(f'{symbol} - Returns Heatmap (Day vs Hour)', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'time_heatmap.png'), dpi=150)
        plt.close()
    
    # 4. Minute-level Granularity (Intraday Seasonality)
    # Group by minute of day (e.g., 9:15, 9:16, ...)
    minute_stats = df.groupby(['hour', 'minute']).agg({
        'returns': 'mean',
        'volatility': 'mean',
        'Volume': 'mean'
    }).reset_index()
    minute_stats['time_str'] = minute_stats.apply(lambda x: f"{int(x['hour']):02d}:{int(x['minute']):02d}", axis=1)
    
    # Plot cumulative intraday return (average day) - convert to percentage
    minute_stats['cum_return'] = ((1 + minute_stats['returns']).cumprod() - 1) * 100  # Convert to percentage
    
    plt.figure(figsize=(14, 6))
    plt.plot(range(len(minute_stats)), minute_stats['cum_return'], linewidth=2)
    # Set xticks sparsely
    xticks = range(0, len(minute_stats), 30) # Every 30 mins
    if len(minute_stats) > 0:
        plt.xticks(xticks, [minute_stats.iloc[i]['time_str'] for i in xticks if i < len(minute_stats)], rotation=45)
    plt.title(f'{symbol} - Average Cumulative Intraday Return Path (%)', fontsize=14)
    plt.ylabel('Cumulative Return (%)')
    plt.xlabel('Time of Day')
    plt.grid(True, alpha=0.3)
    plt.axhline(0, color='black', linestyle='--', linewidth=1)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'average_intraday_path.png'))
    plt.close()

    # Generate summary insights
    logger.info("\n📊 Key Time-Based Insights:")
    best_hour = hourly_stats['cumulative_return_pct'].idxmax()
    worst_hour = hourly_stats['cumulative_return_pct'].idxmin()
    logger.info(f"   Best Hour: {best_hour} ({hourly_stats.loc[best_hour, 'cumulative_return_pct']:.3f}% cumulative)")
    logger.info(f"   Worst Hour: {worst_hour} ({hourly_stats.loc[worst_hour, 'cumulative_return_pct']:.3f}% cumulative)")
    
    if not day_stats.empty:
        best_day = day_stats['returns_mean_pct'].idxmax()
        logger.info(f"   Best Day: {best_day} ({day_stats.loc[best_day, 'returns_mean_pct']:.3f}% avg return)")
    
    logger.info("✅ Time-based analysis complete.")
    
    return {
        'hourly_stats': hourly_file,
        'day_stats': day_file,
        'session_stats': session_file,
        'plots': [
            os.path.join(output_dir, 'hourly_patterns.png'),
            os.path.join(output_dir, 'day_of_week_patterns.png'),
            os.path.join(output_dir, 'time_heatmap.png'),
            os.path.join(output_dir, 'average_intraday_path.png')
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
    analyze_time_patterns(df, args.symbol, args.output_dir)
