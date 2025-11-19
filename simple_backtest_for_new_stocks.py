"""
Simple Backtest for New Stocks (Insufficient Data for Walk-Forward)

For stocks with less than 3 years of data, use this simpler backtest
that doesn't require walk-forward analysis.
"""

import os
import sys
import pandas as pd
import numpy as np
from donchian_strategy import donchian_breakout, optimize_donchian
from walkforward_mcpt import load_stock_data, monte_carlo_permutation_test
from donchian_simple_summary import calculate_simple_metrics

BASE_OUTPUT_DIR = "analysis_results"
MCPT_ITERATIONS = 1000


def get_ticker_output_dir(stock_symbol):
    """Get ticker-specific output directory."""
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def simple_backtest(file_path, min_data_days=100):
    """
    Simple backtest for stocks with insufficient data for walk-forward.
    
    Uses:
    - First 70% of data for optimization
    - Last 30% of data for testing
    - Single MCPT test
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    stock_symbol = os.path.basename(file_path).replace('_analysis.csv', '').replace('.csv', '')
    output_dir = get_ticker_output_dir(stock_symbol)
    
    print(f"🔄 Loading data for {stock_symbol}...")
    ohlc_data = load_stock_data(file_path)
    if ohlc_data is None:
        return None
    
    print(f"✅ Data loaded: {len(ohlc_data)} days")
    
    if len(ohlc_data) < min_data_days:
        print(f"❌ Insufficient data: Need at least {min_data_days} days, have {len(ohlc_data)}")
        return None
    
    # Split data: 70% training, 30% testing
    split_idx = int(len(ohlc_data) * 0.7)
    train_data = ohlc_data.iloc[:split_idx]
    test_data = ohlc_data.iloc[split_idx:]
    
    print(f"\n📊 Data Split:")
    print(f"   Training: {len(train_data)} days ({train_data.index.min()} to {train_data.index.max()})")
    print(f"   Testing: {len(test_data)} days ({test_data.index.min()} to {test_data.index.max()})")
    
    # Optimize on training data
    print(f"\n🔍 Optimizing Donchian lookback period on training data...")
    best_lookback, best_pf = optimize_donchian(train_data)
    print(f"   ✅ Best lookback: {best_lookback} days (Profit Factor: {best_pf:.2f})")
    
    # Generate signals on test data
    print(f"\n📈 Generating signals on test data...")
    signals = donchian_breakout(test_data, best_lookback)
    log_returns = np.log(test_data['close']).diff()
    
    # Align signals and returns
    aligned_signals = signals.iloc[:-1].reset_index(drop=True)
    aligned_returns = log_returns.iloc[1:].reset_index(drop=True)
    min_len = min(len(aligned_signals), len(aligned_returns))
    aligned_signals = aligned_signals.iloc[:min_len]
    aligned_returns = aligned_returns.iloc[:min_len]
    
    valid_mask = ~(aligned_returns.isna() | aligned_signals.isna())
    aligned_signals = aligned_signals[valid_mask]
    aligned_returns = aligned_returns[valid_mask]
    
    if len(aligned_signals) == 0:
        print("❌ No valid signals after alignment")
        return None
    
    # MCPT
    print(f"\n🎲 Running Monte Carlo Permutation Test ({MCPT_ITERATIONS} iterations)...")
    actual_ret, permuted_rets, p_value = monte_carlo_permutation_test(
        aligned_signals, aligned_returns, MCPT_ITERATIONS
    )
    
    # Calculate metrics
    print(f"\n📊 Results:")
    print(f"   Actual Strategy Return (log): {actual_ret:.4f}")
    print(f"   P-Value: {p_value:.4f}")
    print(f"   {'✅ Statistically Significant' if p_value < 0.05 else '⚠️  Not Statistically Significant'}")
    
    # Simple summary
    results_df = pd.DataFrame([{
        'test_start': test_data.index.min(),
        'test_end': test_data.index.max(),
        'best_lookback': best_lookback,
        'actual_returns': actual_ret,
        'p_value': p_value,
        'permuted_returns_mean': np.mean(permuted_rets),
        'permuted_returns_std': np.std(permuted_rets),
    }])
    
    # Print simple summary
    from donchian_simple_summary import print_simple_summary
    output_file = os.path.join(output_dir, "donchian_simple_backtest_results.csv")
    results_df.to_csv(output_file, index=False)
    print_simple_summary(output_file, initial_capital=100000)
    
    # Save summary
    summary = {
        'Stock': stock_symbol,
        'Strategy': 'Simple Donchian (70/30 split)',
        'Total Log Return': f"{actual_ret:.4f}",
        'P-Value': f"{p_value:.4f}",
        'Best Lookback': best_lookback,
        'Training Days': len(train_data),
        'Testing Days': len(test_data),
        'Note': 'Simple backtest (insufficient data for walk-forward)'
    }
    
    summary_df = pd.DataFrame([summary])
    summary_path = os.path.join(output_dir, "donchian_simple_backtest_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"💾 Summary saved to: {summary_path}")
    
    return results_df


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 simple_backtest_for_new_stocks.py <analysis_file>")
        print("\nExample:")
        print("  python3 simple_backtest_for_new_stocks.py output/SWIGGY.NS_analysis.csv")
        print("\nThis is for stocks with insufficient data for walk-forward analysis.")
        print("Uses 70/30 train/test split instead.")
        return
    
    file_path = sys.argv[1]
    simple_backtest(file_path)


if __name__ == "__main__":
    main()

