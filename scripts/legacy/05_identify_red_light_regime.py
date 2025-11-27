"""
Identify Red Light Regime (Hedge Fund Grade)

This tool analyzes regime characteristics to identify the "Red Light" regime
that should be avoided to reduce Maximum Drawdown.

Features:
- Equity curves visualization (regime personality test)
- Auto-labeling of regimes with human-readable names
- Sharpe Ratio (professional standard) instead of custom risk scores
- Professional metrics (CAGR, Win Rate, Annualized Volatility)
- Robust data loading with dynamic header detection

Version: 2.0 (Hedge Fund Grade)
- Uses Sharpe Ratio for risk-adjusted return analysis
- Visual equity curves to see regime "personality"
- Human-readable regime labels (e.g., "CRASH / BEAR", "STEADY BULL")
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def load_regime_data(file_path):
    """
    Robust data loader with dynamic header detection.
    
    Args:
        file_path (str): Path to data_with_regimes.csv file.
    
    Returns:
        pandas.DataFrame: Loaded data with regime labels, or None if error.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return None
    
    try:
        # Sniff for yfinance/complex headers
        with open(file_path, 'r') as f:
            _ = f.readline()
            header_check = f.readline()
        
        skip = [1, 2] if ("Ticker" in header_check or "Price" in header_check) else []
        
        df = pd.read_csv(file_path, index_col=0, parse_dates=True, skiprows=skip)
        df.index.name = 'Date'
        
        # Calculate Returns if missing
        if 'daily_return' not in df.columns and 'Close' in df.columns:
            df['daily_return'] = df['Close'].pct_change()
        
        return df.dropna()
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None


def analyze_regime_performance(df):
    """
    Calculates professional metrics (Sharpe, CAGR, Win Rate) for each regime.
    
    Args:
        df (pandas.DataFrame): DataFrame with 'regime' and 'daily_return' columns.
    
    Returns:
        pandas.DataFrame: Statistics for each regime.
    """
    stats = []
    
    # Get unique regime IDs
    regime_ids = sorted(df['regime'].unique())
    
    for r_id in regime_ids:
        # Filter for ONLY days in this regime
        mask = df['regime'] == r_id
        sub_df = df[mask]
        
        days = len(sub_df)
        if days < 10:
            continue  # Skip tiny noise clusters
        
        # Annualized Metrics
        mean_daily_ret = sub_df['daily_return'].mean()
        daily_vol = sub_df['daily_return'].std()
        
        # 252 trading days in a year
        cagr = (1 + mean_daily_ret) ** 252 - 1
        ann_vol = daily_vol * np.sqrt(252)
        
        # Sharpe Ratio (assuming 0% risk free for simplicity)
        sharpe = (cagr / ann_vol) if ann_vol > 0 else 0
        
        # Win Rate
        win_rate = (sub_df['daily_return'] > 0).mean()
        
        stats.append({
            'Regime ID': int(r_id),
            'Days': days,
            'Win Rate': win_rate,
            'Ann. Return (CAGR)': cagr,
            'Ann. Volatility': ann_vol,
            'Sharpe Ratio': sharpe
        })
    
    return pd.DataFrame(stats).set_index('Regime ID')


def auto_label_regimes(stats_df):
    """
    Hedge Fund Logic: Auto-assigns human readable names based on stats.
    
    Args:
        stats_df (pandas.DataFrame): DataFrame with regime statistics.
    
    Returns:
        pandas.DataFrame: DataFrame with added 'Market Condition' column.
    """
    labels = {}
    
    for r_id, row in stats_df.iterrows():
        ret = row['Ann. Return (CAGR)']
        vol = row['Ann. Volatility']
        
        # Logic Tree for Naming
        if ret < -0.10:
            if vol > 0.30:
                label = "CRASH / BEAR"
            else:
                label = "SLOW BLEED"
        elif ret < 0.05:
            if vol > 0.25:
                label = "CHOPPY / SIDEWAYS"
            else:
                label = "STAGNANT"
        else:
            if vol < 0.15:
                label = "STEADY BULL"
            elif vol > 0.30:
                label = "VOLATILE BULL"
            else:
                label = "RALLY"
        
        labels[r_id] = label
    
    stats_df['Market Condition'] = stats_df.index.map(labels)
    return stats_df


def plot_regime_equity_curves(df, stats_df, stock_symbol, output_dir):
    """
    The 'Aha!' Chart - Regime Personality Test.
    
    Plots the cumulative return of each regime as if they were separate strategies.
    This visualizes "What if I only held the stock during Regime X?"
    
    Args:
        df (pandas.DataFrame): Full dataset with regime labels.
        stats_df (pandas.DataFrame): Regime statistics.
        stock_symbol (str): Stock symbol for title.
        output_dir (str): Directory to save the plot.
    
    Returns:
        int: Red Light regime ID (worst Sharpe Ratio).
    """
    print("Generating equity curves visualization...")
    
    plt.figure(figsize=(14, 8))
    
    # Identify the "Red Light" (Worst Sharpe)
    red_light_id = stats_df['Sharpe Ratio'].idxmin()
    
    for r_id in stats_df.index:
        # Get days belonging to this regime
        mask = df['regime'] == r_id
        
        # Create a synthetic equity curve
        # We extract the returns of these specific days and cumulate them
        regime_returns = df.loc[mask, 'daily_return']
        
        # We ignore the gaps in time to see the "Nature" of the regime
        cum_returns = (1 + regime_returns).cumprod()
        
        # Reset index to 0..N days to compare "Speed" of growth/decay
        cum_returns.index = range(len(cum_returns))
        
        label = f"Regime {r_id}: {stats_df.loc[r_id, 'Market Condition']}"
        
        # Style: Red Light is thick red, others are thin
        if r_id == red_light_id:
            plt.plot(cum_returns, label=label + " (AVOID)", color='red', linewidth=3, alpha=0.9)
        else:
            plt.plot(cum_returns, label=label, linewidth=1.5, alpha=0.6)
    
    plt.title(
        f"Regime Personality Test: {stock_symbol}\n"
        f"(Performance if you ONLY held during that specific regime)",
        fontsize=14,
        fontweight='bold'
    )
    plt.xlabel("Number of Days in Regime", fontsize=12)
    plt.ylabel("Growth of ₹1", fontsize=12)
    plt.legend(loc='best', fontsize=9)
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Save plot
    output_path = os.path.join(output_dir, f"{stock_symbol}_regime_equity_curves.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"💾 Equity curves plot saved to {output_path}")
    plt.close()
    
    return red_light_id


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Hedge Fund Grade Red Light Regime Identifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 05_identify_red_light_regime.py analysis_results/RELIANCE.NS/analysis/data_with_regimes.csv
  python3 05_identify_red_light_regime.py analysis_results/TCS.NS/analysis/data_with_regimes.csv
        """
    )
    parser.add_argument('file', help="Path to data_with_regimes.csv")
    
    args = parser.parse_args()
    
    # 1. Load
    df = load_regime_data(args.file)
    if df is None:
        return
    
    # Extract stock symbol from file path
    stock_symbol = os.path.basename(args.file).split('_')[0] if '_' in os.path.basename(args.file) else "STOCK"
    
    # Get output directory
    output_dir = os.path.dirname(args.file)
    if not output_dir or not os.path.isdir(output_dir):
        # Fallback to analysis_results structure
        output_dir = os.path.join("analysis_results", stock_symbol, "analysis")
        os.makedirs(output_dir, exist_ok=True)
    
    # 2. Analyze
    print(f"\n📊 Analyzing Regimes for {stock_symbol}...")
    print("="*100)
    stats_df = analyze_regime_performance(df)
    
    if stats_df.empty:
        print("❌ No valid regimes found for analysis.")
        return
    
    # 3. Label
    stats_df = auto_label_regimes(stats_df)
    
    # 4. Sort by Sharpe (Risk-Adjusted Return)
    stats_df = stats_df.sort_values('Sharpe Ratio', ascending=False)
    
    print("\n" + "="*100)
    print("🚦 REGIME CLASSIFICATION REPORT")
    print("="*100)
    
    # Formatting for display
    display_df = stats_df.copy()
    cols = ['Ann. Return (CAGR)', 'Ann. Volatility', 'Win Rate']
    for c in cols:
        display_df[c] = display_df[c].apply(lambda x: f"{x:.1%}")
    display_df['Sharpe Ratio'] = display_df['Sharpe Ratio'].apply(lambda x: f"{x:.2f}")
    
    print(display_df[['Market Condition', 'Sharpe Ratio', 'Ann. Return (CAGR)', 
                      'Ann. Volatility', 'Win Rate', 'Days']].to_string())
    print("="*100)
    
    # 5. Visualize and Identify Red Light
    red_light_id = plot_regime_equity_curves(df, stats_df, stock_symbol, output_dir)
    
    # 6. Red Light Alert
    red_label = stats_df.loc[red_light_id, 'Market Condition']
    red_sharpe = stats_df.loc[red_light_id, 'Sharpe Ratio']
    red_return = stats_df.loc[red_light_id, 'Ann. Return (CAGR)']
    red_vol = stats_df.loc[red_light_id, 'Ann. Volatility']
    red_days = stats_df.loc[red_light_id, 'Days']
    
    print(f"\n🚫 RED LIGHT ALERT: Regime {red_light_id} ({red_label})")
    print(f"   Why? Lowest Risk-Adjusted Return (Sharpe: {red_sharpe:.2f})")
    print(f"   Characteristics:")
    print(f"      - Annual Return: {red_return:.1%}")
    print(f"      - Annual Volatility: {red_vol:.1%}")
    print(f"      - Days in Regime: {red_days}")
    print(f"      - % of Total Days: {(red_days / len(df) * 100):.2f}%")
    
    print(f"\n💡 Strategy Enhancement:")
    print(f"   Add this filter to your Donchian strategy:")
    print(f"   ```python")
    print(f"   if current_regime == {red_light_id}:")
    print(f"       donchian_signal = 'DO_NOT_TRADE'  # Or 'EXIT_ALL'")
    print(f"   ```")
    print(f"   This will avoid trading during the worst-performing regime.")
    
    return {
        'red_light_regime': red_light_id,
        'regime_stats': stats_df,
        'label': red_label
    }


if __name__ == "__main__":
    main()

