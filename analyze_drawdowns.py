"""
Analyze Drawdowns and Identify Dangerous Market Regimes

This tool helps identify which market regimes are associated with drawdowns,
so you can filter them out to reduce Maximum Drawdown (MDD).
"""

import os
import sys
import pandas as pd
import numpy as np
from behavioral_patterns import load_analysis_data, get_indicator_columns


def analyze_drawdown_periods(results_file, regime_file, threshold_percentile=25):
    """
    Analyze which market regimes are associated with drawdown periods.
    
    Args:
        results_file: Path to walk-forward results CSV
        regime_file: Path to data_with_regimes.csv
        threshold_percentile: Percentile threshold for identifying "bad" periods (default 25 = bottom 25%)
    
    Returns:
        dict with analysis results
    """
    print("🔄 Loading data...")
    
    # Load walk-forward results
    results_df = pd.read_csv(results_file)
    results_df['test_start'] = pd.to_datetime(results_df['test_start'])
    results_df['test_end'] = pd.to_datetime(results_df['test_end'])
    
    # Load regime data
    regime_df = pd.read_csv(regime_file, index_col=0, parse_dates=True)
    regime_df.index.name = 'Date'
    
    # Calculate period returns (convert log to simple)
    results_df['simple_return'] = np.exp(results_df['actual_returns']) - 1
    
    # Identify worst periods (bottom threshold_percentile)
    threshold = np.percentile(results_df['simple_return'], threshold_percentile)
    worst_periods = results_df[results_df['simple_return'] <= threshold].copy()
    
    print(f"\n📊 Analysis Results:")
    print(f"   Total periods: {len(results_df)}")
    print(f"   Worst periods (bottom {threshold_percentile}%): {len(worst_periods)}")
    print(f"   Threshold return: {threshold*100:.2f}%")
    
    # For each worst period, identify the regime
    regime_counts = {}
    regime_details = []
    
    for idx, period in worst_periods.iterrows():
        # Get dates in this test period
        period_dates = pd.date_range(period['test_start'], period['test_end'], freq='D')
        
        # Get regimes for these dates
        period_regimes = regime_df.loc[regime_df.index.isin(period_dates), 'regime']
        
        if len(period_regimes) > 0:
            # Count regime occurrences
            regime_dist = period_regimes.value_counts()
            dominant_regime = regime_dist.index[0]  # Most common regime
            
            regime_counts[dominant_regime] = regime_counts.get(dominant_regime, 0) + 1
            
            regime_details.append({
                'period_start': period['test_start'],
                'period_end': period['test_end'],
                'return': period['simple_return'] * 100,
                'dominant_regime': dominant_regime,
                'regime_distribution': regime_dist.to_dict()
            })
    
    print(f"\n📉 Regime Analysis for Worst Periods:")
    print(f"   Regime distribution:")
    for regime, count in sorted(regime_counts.items()):
        pct = (count / len(worst_periods)) * 100
        print(f"      Regime {regime}: {count} periods ({pct:.1f}%)")
    
    # Identify dangerous regimes (appear in >50% of worst periods)
    dangerous_regimes = [r for r, c in regime_counts.items() if (c / len(worst_periods)) > 0.5]
    
    print(f"\n⚠️  Dangerous Regimes (appear in >50% of worst periods):")
    if dangerous_regimes:
        for regime in dangerous_regimes:
            print(f"      Regime {regime}: AVOID trading in this regime")
    else:
        print(f"      No single regime dominates worst periods")
        print(f"      Consider using top 2-3 most common regimes")
    
    return {
        'worst_periods': worst_periods,
        'regime_counts': regime_counts,
        'dangerous_regimes': dangerous_regimes,
        'regime_details': regime_details,
        'threshold': threshold
    }


def compare_mdd_with_filtering(results_file, regime_file, regimes_to_filter):
    """
    Simulate MDD reduction by filtering out dangerous regimes.
    
    Args:
        results_file: Path to walk-forward results CSV
        regime_file: Path to data_with_regimes.csv
        regimes_to_filter: List of regime numbers to filter out
    
    Returns:
        dict with MDD comparison
    """
    print(f"\n🔄 Simulating MDD reduction by filtering regimes: {regimes_to_filter}...")
    
    # Load results
    results_df = pd.read_csv(results_file)
    results_df['test_start'] = pd.to_datetime(results_df['test_start'])
    
    # Load regime data
    regime_df = pd.read_csv(regime_file, index_col=0, parse_dates=True)
    regime_df.index.name = 'Date'
    
    # Calculate portfolio progression
    initial_capital = 100000
    portfolio_value = float(initial_capital)
    portfolio_values = [portfolio_value]
    
    # Original (no filtering)
    for ret in results_df['actual_returns']:
        portfolio_value = portfolio_value * np.exp(ret)
        portfolio_values.append(portfolio_value)
    
    original_mdd = ((pd.Series(portfolio_values) / pd.Series(portfolio_values).expanding().max()) - 1).min() * 100
    original_total_return = ((portfolio_values[-1] - initial_capital) / initial_capital) * 100
    
    # Filtered (exclude dangerous regimes)
    portfolio_value_filtered = float(initial_capital)
    portfolio_values_filtered = [portfolio_value_filtered]
    
    for idx, period in results_df.iterrows():
        # Check if period should be filtered
        period_dates = pd.date_range(period['test_start'], period['test_end'], freq='D')
        period_regimes = regime_df.loc[regime_df.index.isin(period_dates), 'regime']
        
        if len(period_regimes) > 0:
            dominant_regime = period_regimes.value_counts().index[0]
            
            # If dominant regime is in filter list, skip this period (0% return)
            if dominant_regime in regimes_to_filter:
                # Don't compound (stay flat)
                portfolio_value_filtered = portfolio_value_filtered
            else:
                # Normal return
                portfolio_value_filtered = portfolio_value_filtered * np.exp(period['actual_returns'])
        else:
            # No regime data, use normal return
            portfolio_value_filtered = portfolio_value_filtered * np.exp(period['actual_returns'])
        
        portfolio_values_filtered.append(portfolio_value_filtered)
    
    filtered_mdd = ((pd.Series(portfolio_values_filtered) / pd.Series(portfolio_values_filtered).expanding().max()) - 1).min() * 100
    filtered_total_return = ((portfolio_values_filtered[-1] - initial_capital) / initial_capital) * 100
    
    # MDD reduction: negative MDD values, so reduction = original - filtered (both negative, so this is positive if improved)
    # Example: -20% to -10% = -20 - (-10) = -10, but we want to show as improvement
    mdd_improvement = abs(original_mdd) - abs(filtered_mdd)  # Positive if MDD reduced
    
    print(f"\n📊 MDD Comparison:")
    print(f"   Original Strategy:")
    print(f"      Total Return: {original_total_return:.2f}%")
    print(f"      Maximum Drawdown: {original_mdd:.2f}%")
    print(f"\n   Filtered Strategy (excluding regimes {regimes_to_filter}):")
    print(f"      Total Return: {filtered_total_return:.2f}%")
    print(f"      Maximum Drawdown: {filtered_mdd:.2f}%")
    print(f"\n   Improvement:")
    print(f"      MDD Reduction: {mdd_improvement:.2f}% (from {abs(original_mdd):.2f}% to {abs(filtered_mdd):.2f}%)")
    print(f"      Return Change: {filtered_total_return - original_total_return:+.2f}%")
    
    return {
        'original_mdd': original_mdd,
        'original_return': original_total_return,
        'filtered_mdd': filtered_mdd,
        'filtered_return': filtered_total_return,
        'mdd_improvement': mdd_improvement,  # Positive if MDD reduced
        'return_change': filtered_total_return - original_total_return
    }


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python3 analyze_drawdowns.py <results_file> <regime_file> [threshold_percentile]")
        print("\nExample:")
        print("  python3 analyze_drawdowns.py analysis_results/GODREJPROP.NS/donchian_walkforward_results.csv \\")
        print("                                analysis_results/GODREJPROP.NS/data_with_regimes.csv")
        return
    
    results_file = sys.argv[1]
    regime_file = sys.argv[2]
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return
    
    if not os.path.exists(regime_file):
        print(f"❌ Regime file not found: {regime_file}")
        print("   Run behavioral_patterns.py first to generate regime data")
        return
    
    # Analyze drawdowns
    analysis = analyze_drawdown_periods(results_file, regime_file, threshold)
    
    # If dangerous regimes identified, simulate filtering
    if analysis['dangerous_regimes']:
        print(f"\n🧪 Testing MDD Reduction by Filtering Dangerous Regimes...")
        comparison = compare_mdd_with_filtering(
            results_file, 
            regime_file, 
            analysis['dangerous_regimes']
        )
        
        print(f"\n💡 Recommendation:")
        if comparison['mdd_improvement'] > 0:
            if comparison['return_change'] >= 0:
                # MDD reduced AND returns improved - perfect!
                print(f"   ✅ EXCELLENT: Filtering regimes {analysis['dangerous_regimes']} reduces MDD by {comparison['mdd_improvement']:.2f}%")
                print(f"      AND improves returns by {comparison['return_change']:.2f}%!")
                print(f"   → DEFINITELY use Enhanced Donchian with regime filtering enabled")
            elif abs(comparison['return_change']) < comparison['mdd_improvement'] * 0.5:
                # MDD reduced significantly, small return drop
                print(f"   ✅ GOOD: Filtering regimes {analysis['dangerous_regimes']} reduces MDD by {comparison['mdd_improvement']:.2f}%")
                print(f"      with only {abs(comparison['return_change']):.2f}% reduction in returns")
                print(f"   → Use Enhanced Donchian with regime filtering enabled")
            else:
                # MDD reduced but returns dropped significantly
                print(f"   ⚠️  Filtering reduces MDD by {comparison['mdd_improvement']:.2f}%")
                print(f"      but also reduces returns by {abs(comparison['return_change']):.2f}%")
                print(f"   → Consider using pattern-based early exits instead, or fine-tune regime thresholds")
        else:
            print(f"   ⚠️  Filtering doesn't significantly reduce MDD")
            print(f"   → Consider using pattern-based early exits instead")
    else:
        print(f"\n💡 Recommendation:")
        print(f"   No single regime dominates worst periods")
        print(f"   → Consider using pattern-based early exits (Option 2)")
        print(f"   → Or filter top 2-3 most common regimes from worst periods")


if __name__ == "__main__":
    main()

