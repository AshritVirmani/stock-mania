"""
Read and Summarize Donchian Backtest Results

This script reads the walk-forward results CSV and creates a more readable summary.
"""

import os
import sys
import pandas as pd
import numpy as np

def create_readable_summary(results_file):
    """Create a readable summary from the walk-forward results."""
    if not os.path.exists(results_file):
        print(f"❌ File not found: {results_file}")
        return
    
    print(f"🔄 Reading results from: {results_file}")
    
    # Read the CSV
    df = pd.read_csv(results_file)
    
    # Extract key columns (skip permuted_returns for now)
    summary_cols = ['train_start', 'train_end', 'test_start', 'test_end', 
                   'best_lookback', 'actual_returns', 'p_value', 
                   'permuted_returns_mean', 'permuted_returns_std']
    
    # Create summary dataframe
    summary_df = df[summary_cols].copy()
    
    # Format dates
    for col in ['train_start', 'train_end', 'test_start', 'test_end']:
        if col in summary_df.columns:
            summary_df[col] = pd.to_datetime(summary_df[col]).dt.strftime('%Y-%m-%d')
    
    # Format numbers
    summary_df['actual_returns'] = summary_df['actual_returns'].round(4)
    summary_df['p_value'] = summary_df['p_value'].round(4)
    summary_df['permuted_returns_mean'] = summary_df['permuted_returns_mean'].round(4)
    summary_df['permuted_returns_std'] = summary_df['permuted_returns_std'].round(4)
    
    # Add performance metrics
    summary_df['cumulative_return'] = summary_df['actual_returns'].cumsum()
    summary_df['is_significant'] = summary_df['p_value'] < 0.05
    
    # Save readable summary
    output_file = results_file.replace('.csv', '_readable_summary.csv')
    summary_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Readable summary saved to: {output_file}")
    
    # Print statistics
    print("\n" + "="*80)
    print("📊 SUMMARY STATISTICS")
    print("="*80)
    print(f"Total Walk-Forward Periods: {len(summary_df)}")
    print(f"Total Cumulative Return: {summary_df['cumulative_return'].iloc[-1]:.4f}")
    print(f"Average Return per Period: {summary_df['actual_returns'].mean():.4f}")
    print(f"Std Dev of Returns: {summary_df['actual_returns'].std():.4f}")
    print(f"Best Period Return: {summary_df['actual_returns'].max():.4f}")
    print(f"Worst Period Return: {summary_df['actual_returns'].min():.4f}")
    print(f"Average P-Value: {summary_df['p_value'].mean():.4f}")
    print(f"Significant Periods (p < 0.05): {summary_df['is_significant'].sum()} / {len(summary_df)}")
    print(f"Average Lookback Period: {summary_df['best_lookback'].mean():.1f}")
    print("="*80)
    
    # Show top and bottom periods
    print("\n📈 TOP 5 BEST PERIODS:")
    print(summary_df.nlargest(5, 'actual_returns')[['test_start', 'test_end', 'actual_returns', 'p_value', 'best_lookback']].to_string(index=False))
    
    print("\n📉 TOP 5 WORST PERIODS:")
    print(summary_df.nsmallest(5, 'actual_returns')[['test_start', 'test_end', 'actual_returns', 'p_value', 'best_lookback']].to_string(index=False))
    
    return summary_df


def main():
    """Main function."""
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
    else:
        # Default to enhanced results
        results_file = "analysis_results/GODREJPROP.NS/donchian_enhanced_walkforward_results.csv"
        if not os.path.exists(results_file):
            print("Usage: python3 read_results_summary.py <results_file.csv>")
            print(f"Example: python3 read_results_summary.py {results_file}")
            return
    
    create_readable_summary(results_file)


if __name__ == "__main__":
    main()

