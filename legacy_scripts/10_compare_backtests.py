"""
Compare Standard vs Enhanced Donchian Backtests (Hedge Fund Grade)

Enhanced with:
1. Bayesian Regime Risk Analysis (Conditional Probability of Loss)
2. Comparative Equity Curves (Original vs Filtered)
3. Risk Ratio Calculation to identify truly dangerous regimes
4. Filtering simulation to quantify value-add
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# --- Configuration ---
BASE_OUTPUT_DIR = "analysis_results"

def get_ticker_output_dir(stock_symbol):
    """Get ticker-specific output directory."""
    return os.path.join(BASE_OUTPUT_DIR, stock_symbol)

def get_reports_dir(stock_symbol):
    """Get reports subdirectory for final reports."""
    reports_dir = os.path.join(get_ticker_output_dir(stock_symbol), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory for regime data."""
    analysis_dir = os.path.join(get_ticker_output_dir(stock_symbol), "analysis")
    return analysis_dir


def analyze_regime_performance(results_df, regime_df):
    """
    Hedge Fund Grade: Calculates Conditional Probability of Loss per Regime.
    P(Loss | Regime) vs P(Loss | Random)
    
    Returns:
        list: Dangerous regime IDs identified
    """
    print("\n📊 PROBABILISTIC REGIME AUDIT")
    print("="*80)
    
    # Ensure regime index is datetime
    if not isinstance(regime_df.index, pd.DatetimeIndex):
        regime_df.index = pd.to_datetime(regime_df.index)
    
    # 1. Map each test period to its Dominant Regime
    results_df = results_df.copy()
    results_df['dominant_regime'] = np.nan
    
    for idx, row in results_df.iterrows():
        start_date = pd.to_datetime(row['test_start'])
        end_date = pd.to_datetime(row['test_end'])
        
        # Filter regime data for this specific date range
        mask = (regime_df.index >= start_date) & (regime_df.index <= end_date)
        period_regimes = regime_df.loc[mask, 'regime']
        
        if not period_regimes.empty:
            # Find most frequent regime (mode)
            try:
                mode_res = period_regimes.mode()
                if not mode_res.empty:
                    results_df.at[idx, 'dominant_regime'] = mode_res.iloc[0]
            except Exception:
                pass
    
    # Drop periods where we couldn't find a regime
    valid_results = results_df.dropna(subset=['dominant_regime']).copy()
    
    if len(valid_results) == 0:
        print("⚠️  Could not map any periods to regimes. Skipping regime analysis.")
        return []
    
    # 2. Calculate Stats per Regime
    grouped = valid_results.groupby('dominant_regime')
    
    regime_stats = pd.DataFrame({
        'Count': grouped['actual_returns'].count(),
        'Avg_Log_Return': grouped['actual_returns'].mean(),
        'Prob_of_Loss': grouped['actual_returns'].apply(lambda x: (x < 0).mean())
    })
    
    # Calculate Baseline Probability of Loss (across all periods)
    baseline_loss_prob = (valid_results['actual_returns'] < 0).mean()
    
    print(f"{'Regime':<8} | {'Count':<6} | {'Avg Return':<12} | {'Prob Loss':<10} | {'Risk Ratio':<12}")
    print("-" * 80)
    
    dangerous_regimes = []
    
    for regime in regime_stats.index:
        count = int(regime_stats.loc[regime, 'Count'])
        avg_ret = regime_stats.loc[regime, 'Avg_Log_Return']
        prob_loss = regime_stats.loc[regime, 'Prob_of_Loss']
        
        # Risk Ratio > 1.0 means this regime is riskier than average
        risk_ratio = prob_loss / baseline_loss_prob if baseline_loss_prob > 0 else 0
        
        print(f"{int(regime):<8} | {count:<6} | {avg_ret:<12.4f} | {prob_loss:<10.1%} | {risk_ratio:<12.2f}")
        
        # Definition of "Dangerous":
        # 1. Negative Expectancy (Avg Return < 0) OR
        # 2. High Probability of Loss (> 60% and Risk Ratio > 1.2)
        if avg_ret < 0 or (prob_loss > 0.60 and risk_ratio > 1.2):
            dangerous_regimes.append(int(regime))
    
    print("-" * 80)
    print(f"Global Baseline Loss Probability: {baseline_loss_prob:.1%}")
    if dangerous_regimes:
        print(f"⚠️  Identified Dangerous Regimes: {dangerous_regimes}")
    else:
        print("✅ No dangerously negative regimes found. Strategy is robust across all conditions.")
    
    return dangerous_regimes


def plot_comparative_equity_curves(original_curve, filtered_curve, output_path, stock_symbol):
    """
    Visualizes the value add of the filter.
    Shows Original (Blind) vs Filtered (Regime-Aware) equity curves.
    """
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        plt.style.use('bmh')  # Fallback style
    
    fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')
    
    ax.plot(original_curve.index, original_curve.values, 
            label='Original Strategy (Blind)', color='gray', alpha=0.7, 
            linestyle='--', linewidth=2)
    ax.plot(filtered_curve.index, filtered_curve.values, 
            label='Regime-Filtered Strategy', color='#2ca02c', linewidth=3)
    
    ax.set_title(f'Impact of Regime Filtering on Equity Curve: {stock_symbol}', 
                 fontsize=16, fontweight='bold')
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.legend(loc='upper left', frameon=True, framealpha=0.9, facecolor='white')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add summary text box
    if len(original_curve) > 0 and len(filtered_curve) > 0:
        final_orig = original_curve.iloc[-1]
        final_filt = filtered_curve.iloc[-1]
        
        improvement = ((final_filt - final_orig) / final_orig) * 100
        
        ax.text(0.02, 0.95, f'Net Profit Improvement: {improvement:+.1f}%', 
                transform=ax.transAxes, fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", alpha=0.8))
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def simulate_filtering(results_df, regime_df, regimes_to_filter, output_dir, stock_symbol):
    """
    Simulates equity curves with and without the dangerous regimes.
    Shows the impact of filtering on portfolio performance.
    """
    if not regimes_to_filter:
        return
    
    print(f"\n🧪 SIMULATION: Filtering Regimes {regimes_to_filter}")
    
    initial_capital = 100000.0
    
    # Ensure dates are datetime and sort
    results_df = results_df.copy()
    results_df['test_start'] = pd.to_datetime(results_df['test_start'])
    results_df['test_end'] = pd.to_datetime(results_df['test_end'])
    results_df = results_df.sort_values('test_end')
    
    # Ensure regime index is datetime
    if not isinstance(regime_df.index, pd.DatetimeIndex):
        regime_df.index = pd.to_datetime(regime_df.index)
    
    dates = pd.to_datetime(results_df['test_end'])
    
    # 1. Original Equity Curve (No Filtering)
    orig_values = [initial_capital]
    curr_orig = initial_capital
    
    # 2. Filtered Equity Curve (Filter Dangerous Regimes)
    filt_values = [initial_capital]
    curr_filt = initial_capital
    
    filtered_count = 0
    
    for idx, row in results_df.iterrows():
        ret = row['actual_returns']  # Log return
        simple_ret = np.exp(ret) - 1  # Convert to simple return
        
        # Original: Always take the trade
        curr_orig = curr_orig * (1 + simple_ret)
        orig_values.append(curr_orig)
        
        # Filtered: Check Regime for this period
        mask = (regime_df.index >= row['test_start']) & (regime_df.index <= row['test_end'])
        period_regimes = regime_df.loc[mask, 'regime']
        
        dominant_regime = None
        if not period_regimes.empty:
            # Use mode to find dominant regime
            try:
                mode_res = period_regimes.mode()
                if not mode_res.empty:
                    dominant_regime = int(mode_res.iloc[0])
            except:
                pass
        
        if dominant_regime is not None and dominant_regime in regimes_to_filter:
            # Filtered: Go to Cash (0% return, no change)
            curr_filt = curr_filt
            filtered_count += 1
        else:
            # Normal Trade
            curr_filt = curr_filt * (1 + simple_ret)
        
        filt_values.append(curr_filt)
    
    # Plotting preparation
    plot_dates = [dates.min() - pd.Timedelta(days=1)] + dates.tolist()
    if len(plot_dates) != len(orig_values):
        # Handle potential length mismatch if dates aren't unique or other issues
        # Fallback to range index if needed
        plot_dates = range(len(orig_values))
    
    orig_series = pd.Series(orig_values, index=plot_dates)
    filt_series = pd.Series(filt_values, index=plot_dates)
    
    # Stats
    orig_total_ret = (curr_orig - initial_capital) / initial_capital
    filt_total_ret = (curr_filt - initial_capital) / initial_capital
    
    # Calculate MDD (Approximate based on period closes)
    orig_mdd = (orig_series / orig_series.cummax() - 1).min()
    filt_mdd = (filt_series / filt_series.cummax() - 1).min()
    
    print(f"\n📊 FILTER RESULTS:")
    print(f"   Periods Filtered: {filtered_count} / {len(results_df)} ({filtered_count/len(results_df)*100:.1f}%)")
    print(f"   Original Return:  {orig_total_ret:.2%}")
    print(f"   Filtered Return:  {filt_total_ret:.2%}")
    print(f"   Value Added:      {(filt_total_ret - orig_total_ret):.2%}")
    print(f"   Original MDD:     {orig_mdd:.2%}")
    print(f"   Filtered MDD:      {filt_mdd:.2%}")
    print(f"   MDD Improvement:   {(filt_mdd - orig_mdd):.2%}")
    
    output_path = os.path.join(output_dir, "filter_impact_equity_curve.png")
    plot_comparative_equity_curves(orig_series, filt_series, output_path, stock_symbol)
    print(f"\n💾 Comparative equity curve saved to: {output_path}")


def compare_backtests(stock_symbol, analyze_regimes=True):
    """
    Compare standard and enhanced Donchian backtest results.
    
    Args:
        stock_symbol: Stock symbol to analyze
        analyze_regimes: If True, perform Bayesian regime risk analysis
    """
    base_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    
    # 1. Paths to CSVs (Support both old and new structure)
    paths = {
        'std_sum': [
            os.path.join(base_dir, "backtests", "standard", "summary.csv"),
            os.path.join(base_dir, "donchian_mcpt_summary.csv")
        ],
        'enh_sum': [
            os.path.join(base_dir, "backtests", "enhanced", "summary.csv"),
            os.path.join(base_dir, "donchian_enhanced_mcpt_summary.csv")
        ],
        'std_res': [
            os.path.join(base_dir, "backtests", "standard", "results.csv"),
            os.path.join(base_dir, "donchian_walkforward_results.csv")
        ],
        'enh_res': [
            os.path.join(base_dir, "backtests", "enhanced", "results.csv"),
            os.path.join(base_dir, "donchian_enhanced_walkforward_results.csv")
        ]
    }
    
    files = {}
    for key, path_list in paths.items():
        for p in path_list:
            if os.path.exists(p):
                files[key] = p
                break
    
    # Check if we found enough files to compare
    if 'std_res' not in files:
        print(f"❌ Could not find Standard Strategy results for {stock_symbol}")
        return
    
    # Load Data
    try:
        std_results = pd.read_csv(files['std_res'])
        
        # If Enhanced doesn't exist, we can still run Regime Analysis on Standard
        has_enhanced = 'enh_res' in files
        if has_enhanced:
            enh_results = pd.read_csv(files['enh_res'])
            std_summary = pd.read_csv(files['std_sum']) if 'std_sum' in files else None
            enh_summary = pd.read_csv(files['enh_sum']) if 'enh_sum' in files else None
        
        # Calculate is_significant if not present
        if 'is_significant' not in std_results.columns and 'p_value' in std_results.columns:
            std_results['is_significant'] = std_results['p_value'] < 0.05
        if 'actual_returns' not in std_results.columns and 'log_return' in std_results.columns:
            std_results['actual_returns'] = std_results['log_return']
        
        if has_enhanced:
            if 'is_significant' not in enh_results.columns and 'p_value' in enh_results.columns:
                enh_results['is_significant'] = enh_results['p_value'] < 0.05
            if 'actual_returns' not in enh_results.columns and 'log_return' in enh_results.columns:
                enh_results['actual_returns'] = enh_results['log_return']
    except Exception as e:
        print(f"❌ Error loading backtest data: {e}")
        return
    
    print("\n" + "="*80)
    print(f"📊 STRATEGY AUDIT: {stock_symbol}")
    print("="*80)
    
    # Only show comparison if both strategies exist
    if has_enhanced and std_summary is not None and enh_summary is not None:
        print("\n🔵 STANDARD DONCHIAN (No Filters)")
        # Handle different column name variations
        std_total_ret = float(std_summary['Total Log Return'].iloc[0])
        # Try different column name variations
        ann_ret_col = None
        for col in ['Annualized Return', 'Annualized Log Return']:
            if col in std_summary.columns:
                ann_ret_col = col
                break
        if ann_ret_col:
            std_ann_ret_str = std_summary[ann_ret_col].iloc[0]
            # Remove % sign if present and convert to float
            std_ann_ret = float(str(std_ann_ret_str).replace('%', '')) / 100 if '%' in str(std_ann_ret_str) else float(std_ann_ret_str)
        else:
            std_ann_ret = 0.0
        
        # Try different p-value column names
        pval_col = None
        for col in ['Average P-Value', 'Avg P-Value']:
            if col in std_summary.columns:
                pval_col = col
                break
        std_pval = float(std_summary[pval_col].iloc[0]) if pval_col else 0.0
        print(f"   Total Log Return:        {std_total_ret:.4f} ({std_total_ret*100:.1f}%)")
        print(f"   Annualized Return:       {std_ann_ret:.4f} ({std_ann_ret*100:.1f}%)")
        print(f"   Average P-Value:          {std_pval:.4f}")
        if 'is_significant' not in std_results.columns:
            std_results['is_significant'] = std_results['p_value'] < 0.05
        print(f"   Significant Periods:      {len(std_results[std_results['is_significant']==True])} / {len(std_results)}")
        print(f"   Average Return/Period:    {std_results['actual_returns'].mean():.4f}")
        print(f"   Best Period Return:       {std_results['actual_returns'].max():.4f}")
        print(f"   Worst Period Return:       {std_results['actual_returns'].min():.4f}")
        
        print("\n🟢 ENHANCED DONCHIAN (Regime Filtered + Pattern Exits)")
        enh_total_ret = float(enh_summary['Total Log Return'].iloc[0])
        # Handle different column name variations
        ann_ret_col = None
        for col in ['Annualized Return', 'Annualized Log Return']:
            if col in enh_summary.columns:
                ann_ret_col = col
                break
        if ann_ret_col:
            enh_ann_ret_str = enh_summary[ann_ret_col].iloc[0]
            # Remove % sign if present and convert to float
            enh_ann_ret = float(str(enh_ann_ret_str).replace('%', '')) / 100 if '%' in str(enh_ann_ret_str) else float(enh_ann_ret_str)
        else:
            enh_ann_ret = 0.0
        
        # Try different p-value column names
        pval_col = None
        for col in ['Average P-Value', 'Avg P-Value']:
            if col in enh_summary.columns:
                pval_col = col
                break
        enh_pval = float(enh_summary[pval_col].iloc[0]) if pval_col else 0.0
        print(f"   Total Log Return:        {enh_total_ret:.4f} ({enh_total_ret*100:.1f}%)")
        print(f"   Annualized Return:       {enh_ann_ret:.4f} ({enh_ann_ret*100:.1f}%)")
        print(f"   Average P-Value:          {enh_pval:.4f}")
        if 'is_significant' not in enh_results.columns:
            enh_results['is_significant'] = enh_results['p_value'] < 0.05
        print(f"   Significant Periods:      {len(enh_results[enh_results['is_significant']==True])} / {len(enh_results)}")
        print(f"   Average Return/Period:    {enh_results['actual_returns'].mean():.4f}")
        print(f"   Best Period Return:       {enh_results['actual_returns'].max():.4f}")
        print(f"   Worst Period Return:       {enh_results['actual_returns'].min():.4f}")
    
        print("\n📈 COMPARISON")
        print("="*80)
        
        std_total = std_total_ret
        enh_total = enh_total_ret
        diff = enh_total - std_total
        diff_pct = (diff / std_total) * 100 if std_total != 0 else 0
        
        print(f"   Total Return Difference:  {diff:+.4f} ({diff_pct:+.1f}%)")
        if diff > 0:
            print("   ✅ Enhanced strategy performed BETTER")
        else:
            print("   ⚠️  Standard strategy performed BETTER")
        
        std_ann = std_ann_ret
        enh_ann = enh_ann_ret
        ann_diff = enh_ann - std_ann
        ann_diff_pct = (ann_diff / std_ann) * 100 if std_ann != 0 else 0
        
        print(f"   Annualized Return Diff:  {ann_diff:+.4f} ({ann_diff_pct:+.1f}%)")
        
        # Count zero return periods
        std_zeros = len(std_results[std_results['actual_returns'] == 0.0])
        enh_zeros = len(enh_results[enh_results['actual_returns'] == 0.0])
        
        print(f"\n   Zero Return Periods:")
        print(f"      Standard:  {std_zeros} / {len(std_results)}")
        print(f"      Enhanced:  {enh_zeros} / {len(enh_results)}")
        print(f"      Difference: {enh_zeros - std_zeros:+d} periods")
        
        if enh_zeros > std_zeros:
            print("   ⚠️  Enhanced strategy filtered out more trades (more conservative)")
        
        print("\n" + "="*80)
        
        # Save comparison
        # Calculate significant periods
        std_sig = len(std_results[std_results['is_significant']==True]) if 'is_significant' in std_results.columns else 0
        enh_sig = len(enh_results[enh_results['is_significant']==True]) if 'is_significant' in enh_results.columns else 0
        
        comparison = pd.DataFrame({
            'Metric': ['Total Log Return', 'Annualized Return', 'Average P-Value', 
                       'Significant Periods', 'Zero Return Periods', 'Best Period Return'],
            'Standard': [
                f"{std_total:.4f}",
                f"{std_ann:.4f}",
                f"{std_pval:.4f}",
                f"{std_sig}/{len(std_results)}",
                f"{std_zeros}/{len(std_results)}",
                f"{std_results['actual_returns'].max():.4f}"
            ],
            'Enhanced': [
                f"{enh_total:.4f}",
                f"{enh_ann:.4f}",
                f"{enh_pval:.4f}",
                f"{enh_sig}/{len(enh_results)}",
                f"{enh_zeros}/{len(enh_results)}",
                f"{enh_results['actual_returns'].max():.4f}"
            ],
            'Difference': [
                f"{diff:+.4f}",
                f"{ann_diff:+.4f}",
                f"{enh_pval - std_pval:+.4f}",
                f"{enh_sig - std_sig:+d}",
                f"{enh_zeros - std_zeros:+d}",
                f"{enh_results['actual_returns'].max() - std_results['actual_returns'].max():+.4f}"
            ]
        })
        
        reports_dir = get_reports_dir(stock_symbol)
        output_file = os.path.join(reports_dir, "backtest_comparison.csv")
        comparison.to_csv(output_file, index=False)
        print(f"\n💾 Comparison saved to: {output_file}")
    else:
        print(f"\n⚠️  Enhanced strategy results not found. Running regime analysis on standard strategy only.")
        comparison = None
    
    # Initialize comparison if not set
    if 'comparison' not in locals():
        comparison = None

    # --- REGIME RISK ANALYSIS ---
    if analyze_regimes:
        regime_path = os.path.join(get_analysis_dir(stock_symbol), "data_with_regimes.csv")
        if os.path.exists(regime_path):
            print("\n🔬 HEDGE FUND GRADE: BAYESIAN REGIME RISK ANALYSIS")
            regime_df = pd.read_csv(regime_path, index_col=0, parse_dates=True)
            
            # Use Standard results as baseline for audit
            dangerous = analyze_regime_performance(std_results.copy(), regime_df)
            
            if dangerous:
                simulate_filtering(std_results.copy(), regime_df, dangerous, get_reports_dir(stock_symbol), stock_symbol)
        else:
            print("⚠️  Regime data not found. Skipping regime analysis.")
    
    return comparison


def main():
    """Main function."""
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1]
    else:
        # Default for testing
        stock_symbol = "RELIANCE.NS"
        print(f"⚠️  No symbol provided. Using default: {stock_symbol}")
    
    compare_backtests(stock_symbol)


if __name__ == "__main__":
    main()

