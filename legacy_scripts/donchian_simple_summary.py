"""
Simple Summary Display for Donchian Backtest Results

Creates an easy-to-read console summary similar to backtest_example.py
"""

import os
import sys
import pandas as pd
import numpy as np


def calculate_simple_metrics(results_df, initial_capital=100000):
    """
    Calculate simple backtest metrics from walk-forward results.
    Similar to backtest_example.py format.
    """
    # Convert log returns to simple returns for calculation
    # Log returns are cumulative, so we need to convert back
    total_log_return = results_df['actual_returns'].sum()
    
    # Calculate portfolio value progression
    # Start with initial capital
    portfolio_value = float(initial_capital)
    portfolio_values = [portfolio_value]
    
    # Each period's return is already a cumulative log return for that period
    # We need to compound them properly
    for ret in results_df['actual_returns']:
        # Convert log return to simple return: e^log_return
        # Then compound: new_value = old_value * e^log_return
        portfolio_value = portfolio_value * np.exp(ret)
        portfolio_values.append(portfolio_value)
    
    portfolio_series = pd.Series(portfolio_values)
    
    # Calculate metrics
    final_value = portfolio_series.iloc[-1]
    # For very large returns, also show the multiplier
    multiplier = final_value / initial_capital
    total_return = (multiplier - 1) * 100
    
    # Cap display at reasonable percentage (if > 10000%, show as multiplier)
    if total_return > 10000:
        display_return = f"{multiplier:.1f}x ({total_return:.1f}%)"
    else:
        display_return = f"{total_return:.2f}%"
    
    # Calculate daily returns for Sharpe ratio
    # Approximate: use period returns scaled to daily
    period_returns = results_df['actual_returns']
    # Convert log returns to simple returns
    simple_returns = np.exp(period_returns) - 1
    # Scale to daily (assuming ~182 days per period)
    avg_days_per_period = 182
    daily_returns = simple_returns / avg_days_per_period
    
    # Sharpe ratio (annualized)
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe_ratio = 0
    
    # Maximum drawdown
    max_drawdown = ((portfolio_series / portfolio_series.expanding().max()) - 1).min() * 100
    
    # Count trades (approximate: count non-zero return periods as active trading)
    num_trades = len(results_df[results_df['actual_returns'] != 0])
    
    # Buy-and-hold return (approximate from first to last period)
    # We'd need the actual price data for this, so we'll skip it for now
    # Or calculate from the data if available
    
    return {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': total_return,
        'num_trades': num_trades,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'total_log_return': total_log_return,
        'portfolio_series': portfolio_series
    }


def print_simple_summary(results_file, initial_capital=100000):
    """
    Print a simple, readable summary similar to backtest_example.py.
    """
    if not os.path.exists(results_file):
        print(f"❌ File not found: {results_file}")
        return
    
    print("\n" + "="*60)
    print("DONCHIAN STRATEGY BACKTEST RESULTS")
    print("="*60)
    
    # Load results
    df = pd.read_csv(results_file)
    
    # Calculate metrics
    metrics = calculate_simple_metrics(df, initial_capital)
    
    # Print results in same format as backtest_example.py
    print(f"Initial Capital: ₹{metrics['initial_capital']:,.2f}")
    print(f"Final Portfolio Value: ₹{metrics['final_value']:,.2f}")
    
    # Format return display
    multiplier = metrics['final_value'] / metrics['initial_capital']
    if metrics['total_return'] > 10000:
        print(f"Total Return: {multiplier:.1f}x ({metrics['total_return']:.1f}%)")
    else:
        print(f"Total Return: {metrics['total_return']:.2f}%")
    print(f"Number of Trades: {metrics['num_trades']}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown: {metrics['max_drawdown']:.2f}%")
    print("="*60)
    
    # Additional Donchian-specific info
    print(f"\nWalk-Forward Periods: {len(df)}")
    print(f"Average P-Value: {df['p_value'].mean():.4f}")
    significant_periods = len(df[df['p_value'] < 0.05])
    print(f"Statistically Significant Periods: {significant_periods} / {len(df)}")
    print(f"Average Lookback Period: {df['best_lookback'].mean():.1f} days")
    
    # Best and worst periods
    best_period = df.loc[df['actual_returns'].idxmax()]
    worst_period = df.loc[df['actual_returns'].idxmin()]
    
    print(f"\n📈 Best Period:")
    print(f"   Date: {best_period['test_start']} to {best_period['test_end']}")
    print(f"   Return: {best_period['actual_returns']*100:.2f}%")
    print(f"   P-Value: {best_period['p_value']:.4f}")
    print(f"   Lookback: {best_period['best_lookback']} days")
    
    print(f"\n📉 Worst Period:")
    print(f"   Date: {worst_period['test_start']} to {worst_period['test_end']}")
    print(f"   Return: {worst_period['actual_returns']*100:.2f}%")
    print(f"   P-Value: {worst_period['p_value']:.4f}")
    print(f"   Lookback: {worst_period['best_lookback']} days")
    
    return metrics


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 donchian_simple_summary.py <results_file.csv> [initial_capital]")
        print("\nExample:")
        print("  python3 donchian_simple_summary.py analysis_results/GODREJPROP.NS/donchian_walkforward_results.csv")
        print("  python3 donchian_simple_summary.py analysis_results/GODREJPROP.NS/donchian_walkforward_results.csv 100000")
        return
    
    results_file = sys.argv[1]
    initial_capital = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
    
    print_simple_summary(results_file, initial_capital)


if __name__ == "__main__":
    main()

