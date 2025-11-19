"""
Identify Red Light Regime (Worst-Performing Market State)

This tool analyzes regime characteristics to identify the "Red Light" regime
that should be avoided to reduce Maximum Drawdown.
"""

import os
import sys
import pandas as pd
import numpy as np


def identify_red_light_regime(regime_file):
    """
    Identifies the Red Light regime (worst performer) based on:
    - Low or negative returns
    - High volatility
    - High risk score
    
    Returns:
        dict with Red Light regime info
    """
    if not os.path.exists(regime_file):
        print(f"❌ Regime file not found: {regime_file}")
        return None
    
    print("🔄 Analyzing regime characteristics...")
    
    df = pd.read_csv(regime_file, index_col=0, parse_dates=True)
    df.index.name = 'Date'
    
    # Calculate daily returns
    df['daily_return'] = df['Close'].pct_change()
    
    # Group by regime
    regime_stats = df.groupby('regime')['daily_return'].agg(['mean', 'std', 'count'])
    regime_stats.columns = ['Mean Return', 'Volatility', 'Days Count']
    
    # Calculate percentage metrics
    regime_stats['Mean Return %'] = (regime_stats['Mean Return'] * 100).round(4)
    regime_stats['Volatility %'] = (regime_stats['Volatility'] * 100).round(4)
    
    # Calculate risk score (higher = worse)
    # Risk score = -return / volatility (for negative returns)
    # Or return / volatility (for positive returns, lower is better)
    regime_stats['Risk Score'] = 0.0
    for regime in regime_stats.index:
        ret = regime_stats.loc[regime, 'Mean Return']
        vol = regime_stats.loc[regime, 'Volatility']
        if vol > 0:
            if ret < 0:
                regime_stats.loc[regime, 'Risk Score'] = -ret / vol  # Higher is worse
            else:
                regime_stats.loc[regime, 'Risk Score'] = ret / vol  # Lower is better (inverted)
    
    print("\n" + "="*80)
    print("📊 REGIME CHARACTERISTICS ANALYSIS")
    print("="*80)
    print(regime_stats.sort_values('Mean Return').to_string())
    print("="*80)
    
    # Identify Red Light regime
    # Criteria: Worst return OR highest risk score
    worst_return_regime = regime_stats['Mean Return'].idxmin()
    worst_return = regime_stats.loc[worst_return_regime, 'Mean Return %']
    
    highest_risk_regime = regime_stats['Risk Score'].idxmax()
    highest_risk_score = regime_stats.loc[highest_risk_regime, 'Risk Score']
    
    # Red Light = regime with worst return (most negative or least positive)
    red_light_regime = worst_return_regime
    
    print(f"\n🚫 RED LIGHT REGIME IDENTIFIED:")
    print(f"   Regime {red_light_regime}:")
    print(f"      Mean Return: {worst_return:.4f}%")
    print(f"      Volatility: {regime_stats.loc[red_light_regime, 'Volatility %']:.4f}%")
    print(f"      Risk Score: {regime_stats.loc[red_light_regime, 'Risk Score']:.4f}")
    print(f"      Days in Regime: {regime_stats.loc[red_light_regime, 'Days Count']}")
    print(f"      % of Total Days: {(regime_stats.loc[red_light_regime, 'Days Count'] / len(df) * 100):.2f}%")
    
    print(f"\n💡 Strategy Enhancement:")
    print(f"   Add this filter to your Donchian strategy:")
    print(f"   IF (Donchian_Signal == BUY/SELL) AND (Current_Regime != {red_light_regime}):")
    print(f"       Execute Trade")
    print(f"   ELSE:")
    print(f"       Stay in Cash")
    
    return {
        'red_light_regime': red_light_regime,
        'regime_stats': regime_stats,
        'worst_return': worst_return,
        'volatility': regime_stats.loc[red_light_regime, 'Volatility %']
    }


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 identify_red_light_regime.py <regime_file>")
        print("\nExample:")
        print("  python3 identify_red_light_regime.py analysis_results/GODREJPROP.NS/data_with_regimes.csv")
        return
    
    regime_file = sys.argv[1]
    identify_red_light_regime(regime_file)


if __name__ == "__main__":
    main()

