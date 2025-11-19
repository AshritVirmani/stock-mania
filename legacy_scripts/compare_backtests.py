"""
Compare Standard vs Enhanced Donchian Backtests
"""

import os
import sys
import pandas as pd

def get_reports_dir(stock_symbol):
    """Get reports subdirectory for final reports."""
    reports_dir = os.path.join("analysis_results", stock_symbol, "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir


def compare_backtests(stock_symbol):
    """Compare standard and enhanced Donchian backtest results."""
    base_dir = f"analysis_results/{stock_symbol}"
    
    # Load summaries from new structure
    standard_summary_path = f"{base_dir}/backtests/standard/summary.csv"
    enhanced_summary_path = f"{base_dir}/backtests/enhanced/summary.csv"
    
    # Fallback to old paths for backward compatibility
    if not os.path.exists(standard_summary_path):
        standard_summary_path = f"{base_dir}/donchian_mcpt_summary.csv"
    if not os.path.exists(enhanced_summary_path):
        enhanced_summary_path = f"{base_dir}/donchian_enhanced_mcpt_summary.csv"
    
    standard_summary = pd.read_csv(standard_summary_path)
    enhanced_summary = pd.read_csv(enhanced_summary_path)
    
    # Load results from new structure
    standard_results_path = f"{base_dir}/backtests/standard/results.csv"
    enhanced_results_path = f"{base_dir}/backtests/enhanced/results.csv"
    
    # Fallback to old paths for backward compatibility
    if not os.path.exists(standard_results_path):
        standard_results_path = f"{base_dir}/donchian_walkforward_results.csv"
    if not os.path.exists(enhanced_results_path):
        enhanced_results_path = f"{base_dir}/donchian_enhanced_walkforward_results.csv"
    
    standard_results = pd.read_csv(standard_results_path)
    enhanced_results = pd.read_csv(enhanced_results_path)
    
    # Calculate is_significant if not present
    if 'is_significant' not in standard_results.columns and 'p_value' in standard_results.columns:
        standard_results['is_significant'] = standard_results['p_value'] < 0.05
    if 'actual_returns' not in standard_results.columns and 'log_return' in standard_results.columns:
        standard_results['actual_returns'] = standard_results['log_return']
    
    if 'is_significant' not in enhanced_results.columns and 'p_value' in enhanced_results.columns:
        enhanced_results['is_significant'] = enhanced_results['p_value'] < 0.05
    if 'actual_returns' not in enhanced_results.columns and 'log_return' in enhanced_results.columns:
        enhanced_results['actual_returns'] = enhanced_results['log_return']
    
    print("\n" + "="*80)
    print("📊 STANDARD vs ENHANCED DONCHIAN STRATEGY COMPARISON")
    print("="*80)
    
    print("\n🔵 STANDARD DONCHIAN (No Filters)")
    std_total_ret = float(standard_summary['Total Log Return'].iloc[0])
    std_ann_ret = float(standard_summary['Annualized Log Return'].iloc[0])
    std_pval = float(standard_summary['Average P-Value'].iloc[0])
    print(f"   Total Log Return:        {std_total_ret:.4f} ({std_total_ret*100:.1f}%)")
    print(f"   Annualized Return:       {std_ann_ret:.4f} ({std_ann_ret*100:.1f}%)")
    print(f"   Average P-Value:          {std_pval:.4f}")
    # Calculate significant periods from p_value
    if 'is_significant' not in standard_results.columns:
        standard_results['is_significant'] = standard_results['p_value'] < 0.05
    print(f"   Significant Periods:      {len(standard_results[standard_results['is_significant']==True])} / {len(standard_results)}")
    print(f"   Average Return/Period:    {standard_results['actual_returns'].mean():.4f}")
    print(f"   Best Period Return:       {standard_results['actual_returns'].max():.4f}")
    print(f"   Worst Period Return:       {standard_results['actual_returns'].min():.4f}")
    
    print("\n🟢 ENHANCED DONCHIAN (Regime Filtered + Pattern Exits)")
    enh_total_ret = float(enhanced_summary['Total Log Return'].iloc[0])
    enh_ann_ret = float(enhanced_summary['Annualized Log Return'].iloc[0])
    enh_pval = float(enhanced_summary['Average P-Value'].iloc[0])
    print(f"   Total Log Return:        {enh_total_ret:.4f} ({enh_total_ret*100:.1f}%)")
    print(f"   Annualized Return:       {enh_ann_ret:.4f} ({enh_ann_ret*100:.1f}%)")
    print(f"   Average P-Value:          {enh_pval:.4f}")
    # Calculate significant periods from p_value
    if 'is_significant' not in enhanced_results.columns:
        enhanced_results['is_significant'] = enhanced_results['p_value'] < 0.05
    print(f"   Significant Periods:      {len(enhanced_results[enhanced_results['is_significant']==True])} / {len(enhanced_results)}")
    print(f"   Average Return/Period:    {enhanced_results['actual_returns'].mean():.4f}")
    print(f"   Best Period Return:       {enhanced_results['actual_returns'].max():.4f}")
    print(f"   Worst Period Return:       {enhanced_results['actual_returns'].min():.4f}")
    
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
    
    # Count zero return periods (filtered out trades)
    std_zeros = len(standard_results[standard_results['actual_returns'] == 0.0])
    enh_zeros = len(enhanced_results[enhanced_results['actual_returns'] == 0.0])
    
    print(f"\n   Zero Return Periods:")
    print(f"      Standard:  {std_zeros} / {len(standard_results)}")
    print(f"      Enhanced:  {enh_zeros} / {len(enhanced_results)}")
    print(f"      Difference: {enh_zeros - std_zeros:+d} periods")
    
    if enh_zeros > std_zeros:
        print("   ⚠️  Enhanced strategy filtered out more trades (more conservative)")
    
    print("\n" + "="*80)
    
    # Save comparison
    comparison = pd.DataFrame({
        'Metric': ['Total Log Return', 'Annualized Return', 'Average P-Value', 
                   'Significant Periods', 'Zero Return Periods', 'Best Period Return'],
        'Standard': [
            f"{std_total:.4f}",
            f"{std_ann:.4f}",
            f"{std_pval:.4f}",
            f"{len(standard_results[standard_results['is_significant']==True])}/{len(standard_results)}",
            f"{std_zeros}/{len(standard_results)}",
            f"{standard_results['actual_returns'].max():.4f}"
        ],
        'Enhanced': [
            f"{enh_total:.4f}",
            f"{enh_ann:.4f}",
            f"{enh_pval:.4f}",
            f"{len(enhanced_results[enhanced_results['is_significant']==True])}/{len(enhanced_results)}",
            f"{enh_zeros}/{len(enhanced_results)}",
            f"{enhanced_results['actual_returns'].max():.4f}"
        ],
        'Difference': [
            f"{diff:+.4f}",
            f"{ann_diff:+.4f}",
            f"{enh_pval - std_pval:+.4f}",
            f"{len(enhanced_results[enhanced_results['is_significant']==True]) - len(standard_results[standard_results['is_significant']==True]):+d}",
            f"{enh_zeros - std_zeros:+d}",
            f"{enhanced_results['actual_returns'].max() - standard_results['actual_returns'].max():+.4f}"
        ]
    })
    
    reports_dir = get_reports_dir(stock_symbol)
    output_file = os.path.join(reports_dir, "backtest_comparison.csv")
    comparison.to_csv(output_file, index=False)
    print(f"\n💾 Comparison saved to: {output_file}")
    
    return comparison


def main():
    """Main function."""
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1]
    else:
        stock_symbol = "GODREJPROP.NS"
    
    compare_backtests(stock_symbol)


if __name__ == "__main__":
    main()

