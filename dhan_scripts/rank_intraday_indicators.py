"""
Rank and Visualize Intraday TA Indicator Accuracy

Creates rankings, visualizations, and summary reports for indicator accuracy analysis.
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def rank_indicators(results_df, top_n=20):
    """
    Rank indicators by multiple metrics and create summary.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with accuracy results
        top_n (int): Number of top indicators to highlight
    
    Returns:
        pandas.DataFrame: Ranked indicators with composite score
    """
    if results_df is None or results_df.empty:
        logger.warning("No results to rank.")
        return pd.DataFrame()
    
    logger.info(f"📊 Ranking {len(results_df)} indicators...")
    
    # Create composite score (weighted average of metrics)
    # Normalize metrics to 0-1 scale
    df = results_df.copy()
    
    # Normalize accuracy (already 0-1)
    df['norm_accuracy'] = df['accuracy']
    
    # Normalize precision, recall, F1 (already 0-1)
    df['norm_precision'] = df['precision']
    df['norm_recall'] = df['recall']
    df['norm_f1'] = df['f1_score']
    
    # Normalize signal count (log scale to reduce impact of very high counts)
    df['norm_signals'] = np.log1p(df['total_signals']) / np.log1p(df['total_signals'].max())
    
    # Composite score: weighted average
    # Weights: accuracy 40%, F1 30%, precision 15%, recall 10%, signals 5%
    df['composite_score'] = (
        df['norm_accuracy'] * 0.40 +
        df['norm_f1'] * 0.30 +
        df['norm_precision'] * 0.15 +
        df['norm_recall'] * 0.10 +
        df['norm_signals'] * 0.05
    )
    
    # Sort by composite score
    df = df.sort_values('composite_score', ascending=False)
    
    # Add rank
    df['rank'] = range(1, len(df) + 1)
    
    logger.info(f"✅ Top indicator: {df.iloc[0]['indicator']} (score: {df.iloc[0]['composite_score']:.4f})")
    
    return df


def create_top_indicators_chart(results_df, output_file, top_n=20):
    """
    Create bar chart of top N indicators by accuracy.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with accuracy results
        output_file (str): Path to save chart
        top_n (int): Number of top indicators to show
    """
    if results_df is None or results_df.empty:
        logger.warning("No data for chart.")
        return
    
    logger.info(f"📈 Creating top {top_n} indicators chart...")
    
    # Get top N
    top_df = results_df.head(top_n).copy()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Create bar chart
    y_pos = np.arange(len(top_df))
    bars = ax.barh(y_pos, top_df['accuracy'], color='steelblue', alpha=0.7)
    
    # Customize
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_df['indicator'], fontsize=9)
    ax.set_xlabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Top {top_n} Most Accurate TA Indicators (1-minute Intraday)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(0, 1.0)
    
    # Add accuracy values on bars
    for i, (idx, row) in enumerate(top_df.iterrows()):
        accuracy_pct = row['accuracy'] * 100
        ax.text(row['accuracy'] + 0.01, i, f'{accuracy_pct:.1f}%', 
                va='center', fontsize=8)
    
    # Add grid
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.axvline(x=0.5, color='red', linestyle='--', alpha=0.5, label='Random (50%)')
    ax.legend()
    
    # Invert y-axis to show best at top
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"💾 Saved chart to {output_file}")


def create_signal_quality_scatter(results_df, output_file):
    """
    Create scatter plot of accuracy vs signal count.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with accuracy results
        output_file (str): Path to save chart
    """
    if results_df is None or results_df.empty:
        logger.warning("No data for scatter plot.")
        return
    
    logger.info("📈 Creating signal quality scatter plot...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create scatter plot
    scatter = ax.scatter(results_df['total_signals'], results_df['accuracy'], 
                        s=100, alpha=0.6, c=results_df['f1_score'], 
                        cmap='viridis', edgecolors='black', linewidth=0.5)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('F1 Score', fontsize=10)
    
    # Customize
    ax.set_xlabel('Total Signals Generated', fontsize=12, fontweight='bold')
    ax.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
    ax.set_title('Indicator Signal Quality: Accuracy vs Signal Count', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Random (50%)')
    ax.legend()
    
    # Add top indicators labels
    top_5 = results_df.head(5)
    for idx, row in top_5.iterrows():
        ax.annotate(row['indicator'].split('_')[-1], 
                   (row['total_signals'], row['accuracy']),
                   fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"💾 Saved scatter plot to {output_file}")


def create_accuracy_distribution(results_df, output_file):
    """
    Create histogram of accuracy distribution.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with accuracy results
        output_file (str): Path to save chart
    """
    if results_df is None or results_df.empty:
        logger.warning("No data for distribution plot.")
        return
    
    logger.info("📈 Creating accuracy distribution histogram...")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create histogram
    ax.hist(results_df['accuracy'], bins=30, color='steelblue', alpha=0.7, edgecolor='black')
    
    # Add statistics
    mean_acc = results_df['accuracy'].mean()
    median_acc = results_df['accuracy'].median()
    
    ax.axvline(mean_acc, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_acc:.3f}')
    ax.axvline(median_acc, color='green', linestyle='--', linewidth=2, label=f'Median: {median_acc:.3f}')
    ax.axvline(0.5, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Random (50%)')
    
    # Customize
    ax.set_xlabel('Accuracy', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Indicators', fontsize=12, fontweight='bold')
    ax.set_title('Distribution of Indicator Accuracy Scores', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"💾 Saved distribution plot to {output_file}")


def create_summary_report(results_df, symbol, interval, output_dir):
    """
    Create summary JSON report with key statistics.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with accuracy results
        symbol (str): Stock symbol
        interval (str): Interval in minutes
        output_dir (str): Output directory path
    
    Returns:
        str: Path to saved JSON file
    """
    if results_df is None or results_df.empty:
        logger.warning("No results for summary.")
        return None
    
    logger.info("📝 Creating summary report...")
    
    # Calculate statistics
    summary = {
        'symbol': symbol,
        'interval': f'{interval}min',
        'total_indicators': len(results_df),
        'statistics': {
            'accuracy': {
                'mean': float(results_df['accuracy'].mean()),
                'median': float(results_df['accuracy'].median()),
                'std': float(results_df['accuracy'].std()),
                'min': float(results_df['accuracy'].min()),
                'max': float(results_df['accuracy'].max())
            },
            'precision': {
                'mean': float(results_df['precision'].mean()),
                'median': float(results_df['precision'].median())
            },
            'recall': {
                'mean': float(results_df['recall'].mean()),
                'median': float(results_df['recall'].median())
            },
            'f1_score': {
                'mean': float(results_df['f1_score'].mean()),
                'median': float(results_df['f1_score'].median())
            },
            'total_signals': {
                'mean': float(results_df['total_signals'].mean()),
                'median': float(results_df['total_signals'].median()),
                'sum': int(results_df['total_signals'].sum())
            }
        },
        'top_10_indicators': results_df.head(10)[['indicator', 'accuracy', 'precision', 'recall', 'f1_score', 'total_signals']].to_dict('records'),
        'indicators_above_random': int((results_df['accuracy'] > 0.5).sum()),
        'indicators_below_random': int((results_df['accuracy'] < 0.5).sum())
    }
    
    # Save JSON
    os.makedirs(output_dir, exist_ok=True)
    json_file = os.path.join(output_dir, 'accuracy_summary.json')
    with open(json_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"💾 Saved summary to {json_file}")
    return json_file


def save_ranking(results_df, symbol, interval, output_dir):
    """
    Save ranked indicators to CSV.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with ranked results
        symbol (str): Stock symbol
        interval (str): Interval in minutes
        output_dir (str): Output directory path
    
    Returns:
        str: Path to saved CSV file
    """
    if results_df is None or results_df.empty:
        logger.warning("No results to save.")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"top_indicators_ranking.csv")
    
    # Select relevant columns for ranking
    ranking_cols = ['rank', 'indicator', 'composite_score', 'accuracy', 'precision', 
                    'recall', 'f1_score', 'total_signals', 'buy_signals', 'sell_signals']
    available_cols = [col for col in ranking_cols if col in results_df.columns]
    
    results_df[available_cols].to_csv(filename, index=False)
    logger.info(f"💾 Saved ranking to {filename}")
    return filename


def generate_all_visualizations(results_df, symbol, interval, output_dir):
    """
    Generate all visualizations and reports.
    
    Args:
        results_df (pandas.DataFrame): DataFrame with accuracy results
        symbol (str): Stock symbol
        interval (str): Interval in minutes
        output_dir (str): Output directory path
    """
    if results_df is None or results_df.empty:
        logger.warning("No results to visualize.")
        return
    
    logger.info("🎨 Generating visualizations and reports...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Rank indicators
    ranked_df = rank_indicators(results_df)
    
    # Save ranking
    save_ranking(ranked_df, symbol, interval, output_dir)
    
    # Create visualizations
    vis_dir = os.path.join(output_dir, 'visualizations')
    os.makedirs(vis_dir, exist_ok=True)
    
    create_top_indicators_chart(ranked_df, os.path.join(vis_dir, 'top_indicators_chart.png'))
    create_signal_quality_scatter(ranked_df, os.path.join(vis_dir, 'signal_quality_scatter.png'))
    create_accuracy_distribution(ranked_df, os.path.join(vis_dir, 'accuracy_distribution.png'))
    
    # Create summary
    create_summary_report(ranked_df, symbol, interval, output_dir)
    
    logger.info("✅ All visualizations and reports generated")


if __name__ == "__main__":
    # Test the function
    import argparse
    
    parser = argparse.ArgumentParser(description='Rank and visualize TA indicator accuracy')
    parser.add_argument('input_file', help='Path to input CSV file with accuracy results')
    parser.add_argument('--symbol', required=True, help='Stock symbol (e.g., HDFCBANK.NS)')
    parser.add_argument('--interval', default='1', help='Interval in minutes (default: 1)')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    logger.info(f"📂 Loading accuracy results from {args.input_file}...")
    results_df = pd.read_csv(args.input_file)
    logger.info(f"   Loaded {len(results_df)} indicator results")
    
    generate_all_visualizations(results_df, args.symbol, args.interval, args.output_dir)

