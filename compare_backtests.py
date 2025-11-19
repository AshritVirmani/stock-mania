"""
Compare Standard vs Enhanced Donchian Backtests
"""

import os
import sys
import pandas as pd

def compare_backtests(stock_symbol):
    """Compare standard and enhanced Donchian backtest results."""
    base_dir = f"analysis_results/{stock_symbol}"
    
    # Load summaries
    standard_summary = pd.read_csv(f"{base_dir}/donchian_mcpt_summary.csv")
    enhanced_summary = pd.read_csv(f"{base_dir}/donchian_enhanced_mcpt_summary.csv")
    
    # Load readable results
    standard_results = pd.read_csv(f"{base_dir}/donchian_walkforward_results_readable_summary.csv")
    enhanced_results = pd.read_csv(f"{base_dir}/donchian_enhanced_walkforward_results_readable_summary.csv")
    
    print("\n" + "="*80)
    print("📊 STANDARD vs ENHANCED DONCHIAN STRATEGY COMPARISON")
    print("="*80)
    
    print("\n🔵 STANDARD DONCHIAN (No Filters)")
    print(f"   Total Log Return:        {float(standard_summary['Total Log Return']):.4f} ({float(standard_summary['Total Log Return'])*100:.1f}%)")
    print(f"   Annualized Return:       {float(standard_summary['Annualized Log Return']):.4f} ({float(standard_summary['Annualized Log Return'])*100:.1f}%)")
    print(f"   Average P-Value:          {float(standard_summary['Average P-Value']):.4f}")
    print(f"   Significant Periods:      {len(standard_results[standard_results['is_significant']==True])} / {len(standard_results)}")
    print(f"   Average Return/Period:    {standard_results['actual_returns'].mean():.4f}")
    print(f"   Best Period Return:       {standard_results['actual_returns'].max():.4f}")
    print(f"   Worst Period Return:       {standard_results['actual_returns'].min():.4f}")
    
    print("\n🟢 ENHANCED DONCHIAN (Regime Filtered + Pattern Exits)")
    print(f"   Total Log Return:        {float(enhanced_summary['Total Log Return']):.4f} ({float(enhanced_summary['Total Log Return'])*100:.1f}%)")
    print(f"   Annualized Return:       {float(enhanced_summary['Annualized Log Return']):.4f} ({float(enhanced_summary['Annualized Log Return'])*100:.1f}%)")
    print(f"   Average P-Value:          {float(enhanced_summary['Average P-Value']):.4f}")
    print(f"   Significant Periods:      {len(enhanced_results[enhanced_results['is_significant']==True])} / {len(enhanced_results)}")
    print(f"   Average Return/Period:    {enhanced_results['actual_returns'].mean():.4f}")
    print(f"   Best Period Return:       {enhanced_results['actual_returns'].max():.4f}")
    print(f"   Worst Period Return:       {enhanced_results['actual_returns'].min():.4f}")
    
    print("\n📈 COMPARISON")
    print("="*80)
    
    std_total = float(standard_summary['Total Log Return'])
    enh_total = float(enhanced_summary['Total Log Return'])
    diff = enh_total - std_total
    diff_pct = (diff / std_total) * 100 if std_total != 0 else 0
    
    print(f"   Total Return Difference:  {diff:+.4f} ({diff_pct:+.1f}%)")
    if diff > 0:
        print("   ✅ Enhanced strategy performed BETTER")
    else:
        print("   ⚠️  Standard strategy performed BETTER")
    
    std_ann = float(standard_summary['Annualized Log Return'])
    enh_ann = float(enhanced_summary['Annualized Log Return'])
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
            f"{float(standard_summary['Average P-Value']):.4f}",
            f"{len(standard_results[standard_results['is_significant']==True])}/{len(standard_results)}",
            f"{std_zeros}/{len(standard_results)}",
            f"{standard_results['actual_returns'].max():.4f}"
        ],
        'Enhanced': [
            f"{enh_total:.4f}",
            f"{enh_ann:.4f}",
            f"{float(enhanced_summary['Average P-Value']):.4f}",
            f"{len(enhanced_results[enhanced_results['is_significant']==True])}/{len(enhanced_results)}",
            f"{enh_zeros}/{len(enhanced_results)}",
            f"{enhanced_results['actual_returns'].max():.4f}"
        ],
        'Difference': [
            f"{diff:+.4f}",
            f"{ann_diff:+.4f}",
            f"{float(enhanced_summary['Average P-Value']) - float(standard_summary['Average P-Value']):+.4f}",
            f"{len(enhanced_results[enhanced_results['is_significant']==True]) - len(standard_results[standard_results['is_significant']==True]):+d}",
            f"{enh_zeros - std_zeros:+d}",
            f"{enhanced_results['actual_returns'].max() - standard_results['actual_returns'].max():+.4f}"
        ]
    })
    
    output_file = f"{base_dir}/backtest_comparison.csv"
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

