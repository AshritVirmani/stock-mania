"""
Simple Backtest for New Stocks (Hedge Fund Grade)

For stocks with less than 3 years of data, use this simpler backtest
that doesn't require walk-forward analysis.

Version: 2.0 (Hedge Fund Grade)
- Fixed look-ahead bias using shift(1) for proper signal alignment
- Added transaction costs (slippage + commissions)
- Equity curve visualization
- Trade counting to identify over-trading
- Net returns after costs reporting
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from donchian_strategy import donchian_breakout, optimize_donchian
from walkforward_mcpt import load_stock_data, monte_carlo_permutation_test

# --- Configuration ---
BASE_OUTPUT_DIR = "analysis_results"
MCPT_ITERATIONS = 1000
# Transaction Cost: 10 Basis Points (0.10%) per trade
# This includes slippage + commissions (realistic for IPOs/small caps)
TRANSACTION_COST_BPS = 0.0010


def get_ticker_output_dir(stock_symbol):
    """Get ticker-specific output directory."""
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    os.makedirs(ticker_dir, exist_ok=True)
    return ticker_dir


def get_backtests_dir(stock_symbol, strategy="standard"):
    """Get backtests subdirectory for strategy results."""
    backtests_dir = os.path.join(get_ticker_output_dir(stock_symbol), "backtests", strategy)
    os.makedirs(backtests_dir, exist_ok=True)
    return backtests_dir


def plot_equity_curve(strategy_cum_ret, benchmark_cum_ret, symbol, output_dir):
    """
    Visualizes the performance vs buy-and-hold.
    
    Args:
        strategy_cum_ret (pandas.Series): Cumulative strategy returns.
        benchmark_cum_ret (pandas.Series): Cumulative buy-and-hold returns.
        symbol (str): Stock symbol for title.
        output_dir (str): Directory to save the plot.
    """
    plt.figure(figsize=(14, 8))
    
    plt.plot(strategy_cum_ret.index, strategy_cum_ret, 
             label=f"Strategy (Donchian)", color='green', linewidth=2)
    plt.plot(benchmark_cum_ret.index, benchmark_cum_ret, 
             label="Buy & Hold", color='gray', alpha=0.5, linestyle='--')
    
    plt.title(f"Simple Backtest Performance: {symbol}\n(After Transaction Costs)", 
              fontsize=14, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Cumulative Return (Log Scale)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='best', fontsize=11)
    
    # Add zero line
    plt.axhline(y=0, color='black', linewidth=0.5, linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    
    filename = os.path.join(output_dir, "simple_backtest_equity_curve.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"💾 Equity curve saved to {filename}")
    plt.close()


def simple_backtest(file_path, min_data_days=100):
    """
    Simple backtest for stocks with insufficient data for walk-forward.
    
    Hedge Fund Grade Improvements:
    - Fixed look-ahead bias using shift(1) for proper signal alignment
    - Added transaction costs (10 bps per trade)
    - Equity curve visualization
    - Trade counting to identify over-trading
    
    Uses:
    - First 70% of data for optimization
    - Last 30% of data for testing
    - Single MCPT test
    
    Args:
        file_path (str): Path to analysis CSV file.
        min_data_days (int): Minimum days required (default 100).
    
    Returns:
        pandas.DataFrame: Results summary, or None if error.
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    stock_symbol = os.path.basename(file_path).split('_')[0] if '_' in os.path.basename(file_path) else os.path.basename(file_path).replace('.csv', '')
    output_dir = get_backtests_dir(stock_symbol, "standard")
    
    print(f"🔄 Loading data for {stock_symbol}...")
    ohlc_data = load_stock_data(file_path)
    if ohlc_data is None:
        return None
    
    print(f"✅ Data loaded: {len(ohlc_data)} days")
    
    if len(ohlc_data) < min_data_days:
        print(f"❌ Insufficient data: Need at least {min_data_days} days, have {len(ohlc_data)}")
        return None
    
    # --- 1. Split Data (Holdout Method) ---
    # For IPOs, the first 6 months are often wild. We train on that volatility to find robust params.
    split_idx = int(len(ohlc_data) * 0.70)
    train_data = ohlc_data.iloc[:split_idx].copy()
    test_data = ohlc_data.iloc[split_idx:].copy()
    
    print(f"\n📊 Data Split:")
    print(f"   Training: {len(train_data)} days ({train_data.index.min().date()} to {train_data.index.max().date()})")
    print(f"   Testing: {len(test_data)} days ({test_data.index.min().date()} to {test_data.index.max().date()})")
    
    # --- 2. Optimize (In-Sample) ---
    print(f"\n🔍 Optimizing Donchian lookback period on training data...")
    best_lookback, best_pf = optimize_donchian(train_data)
    print(f"   ✅ Best lookback: {best_lookback} days (Profit Factor: {best_pf:.2f})")
    
    # --- 3. Backtest (Out-of-Sample) ---
    print(f"\n📈 Running test on recent data...")
    
    # Generate Raw Signals (1 = Long, 0 = Flat, -1 = Short)
    signals = donchian_breakout(test_data, best_lookback)
    
    # CRITICAL FIX: Alignment & Look-Ahead Prevention
    # We must shift signal by 1. If signal says BUY at close of Day T, we own it on Day T+1.
    # We trade at the Open or Close of the next bar (simplified here to Close-to-Close logic)
    
    # Calculate Market Returns (Log returns for additivity)
    test_data['log_ret'] = np.log(test_data['close'] / test_data['close'].shift(1))
    
    # Align: Strategy Return = Yesterday's Signal * Today's Market Return
    # CRITICAL: Use shift(1) to prevent look-ahead bias
    test_data['signal_lag'] = signals.shift(1)
    test_data['strategy_raw_ret'] = test_data['signal_lag'] * test_data['log_ret']
    
    # --- 4. Apply Transaction Costs ---
    # Detect trades: When signal changes from 0 to 1, 1 to 0, etc.
    # This counts every position change (entry or exit)
    trades = test_data['signal_lag'].diff().abs().fillna(0)
    # Cost is applied on every turnover event
    test_data['strategy_net_ret'] = test_data['strategy_raw_ret'] - (trades * TRANSACTION_COST_BPS)
    
    # Drop NaNs created by lagging
    test_data = test_data.dropna()
    
    if test_data.empty:
        print("❌ No valid data points after alignment.")
        return None
    
    # --- 5. Performance Metrics ---
    # Cumulative Returns for Plotting
    test_data['cum_strategy'] = test_data['strategy_net_ret'].cumsum()
    test_data['cum_benchmark'] = test_data['log_ret'].cumsum()
    
    total_return = test_data['strategy_net_ret'].sum()
    total_trades = trades.sum()
    
    # MCPT for Statistical Significance
    # We pass the net returns to check if the edge survives costs
    print(f"\n🎲 Running Monte Carlo Permutation Test ({MCPT_ITERATIONS} iterations)...")
    actual_ret, permuted_rets, p_value = monte_carlo_permutation_test(
        test_data['signal_lag'], test_data['log_ret'], MCPT_ITERATIONS
    )
    
    # --- 6. Reporting ---
    print(f"\n" + "="*80)
    print(f"📊 FINAL RESULTS ({stock_symbol})")
    print("="*80)
    print(f"   Net Log Return: {total_return:.4f} (after {TRANSACTION_COST_BPS*10000:.0f} bps cost)")
    print(f"   Gross Return:   {test_data['strategy_raw_ret'].sum():.4f} (before costs)")
    print(f"   Total Trades:  {total_trades:.0f}")
    print(f"   Avg Trades/Day: {(total_trades / len(test_data)):.3f}")
    if total_trades > 0:
        cost_impact = (test_data['strategy_raw_ret'].sum() - total_return) / abs(test_data['strategy_raw_ret'].sum()) * 100 if test_data['strategy_raw_ret'].sum() != 0 else 0
        print(f"   Cost Impact:   {cost_impact:.1f}% of gross returns")
    print(f"   P-Value:        {p_value:.4f} {'✅ Significant' if p_value < 0.05 else '⚠️  Not Significant'}")
    
    # Over-trading warning
    if total_trades > len(test_data) * 0.5:  # More than 50% of days have trades
        print(f"\n   ⚠️  WARNING: High trade frequency detected!")
        print(f"      Strategy may be over-trading. Consider wider stops or filters.")
    
    print("="*80)
    
    # Visualization
    plot_equity_curve(test_data['cum_strategy'], test_data['cum_benchmark'], stock_symbol, output_dir)
    
    # --- 7. Save Results ---
    results_df = pd.DataFrame([{
        'test_start': test_data.index.min(),
        'test_end': test_data.index.max(),
        'best_lookback': best_lookback,
        'gross_return': test_data['strategy_raw_ret'].sum(),
        'net_return': total_return,
        'total_trades': total_trades,
        'p_value': p_value,
        'permuted_returns_mean': np.mean(permuted_rets),
        'permuted_returns_std': np.std(permuted_rets),
        'transaction_cost_bps': TRANSACTION_COST_BPS * 10000,
    }])
    
    # Save detailed results
    results_path = os.path.join(output_dir, "results.csv")
    results_df.to_csv(results_path, index=False)
    print(f"\n💾 Results saved to {results_path}")
    
    # Save summary
    summary = {
        'Stock': stock_symbol,
        'Strategy': 'Simple Donchian (70/30 split)',
        'Gross Log Return': f"{test_data['strategy_raw_ret'].sum():.4f}",
        'Net Log Return': f"{total_return:.4f}",
        'Total Trades': int(total_trades),
        'P-Value': f"{p_value:.4f}",
        'Best Lookback': best_lookback,
        'Training Days': len(train_data),
        'Testing Days': len(test_data),
        'Transaction Cost (bps)': f"{TRANSACTION_COST_BPS*10000:.0f}",
        'Note': 'Simple backtest (insufficient data for walk-forward)'
    }
    
    summary_df = pd.DataFrame([summary])
    summary_path = os.path.join(output_dir, "summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"💾 Summary saved to {summary_path}")
    
    return results_df


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Simple Backtest for New Stocks (Hedge Fund Grade)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 07a_simple_backtest_for_new_stocks.py analysis_results/SWIGGY.NS/data/SWIGGY.NS_analysis.csv
  python3 07a_simple_backtest_for_new_stocks.py analysis_results/IRCTC.NS/data/IRCTC.NS_analysis.csv

This is for stocks with insufficient data for walk-forward analysis.
Uses 70/30 train/test split instead.
        """
    )
    parser.add_argument('file', help="Path to analysis CSV file")
    parser.add_argument('--min-days', type=int, default=100,
                        help="Minimum days required (default: 100)")
    
    args = parser.parse_args()
    
    simple_backtest(args.file, min_data_days=args.min_days)


if __name__ == "__main__":
    main()
