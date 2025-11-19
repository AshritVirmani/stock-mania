import os
import sys
import pandas as pd
import numpy as np
from walkforward_mcpt import WalkForwardAnalysis, load_stock_data
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Environment, FileSystemLoader

# --- Configuration ---
BASE_OUTPUT_DIR = "analysis_results"
DEFAULT_STOCK_FILE = "output/RELIANCE.NS_analysis.csv"
TRAIN_PERIOD_DAYS = 365 * 2 # 2 years for training
TEST_PERIOD_DAYS = 365 // 2 # 6 months for testing
MCPT_ITERATIONS = 1000 # Number of Monte Carlo iterations

def get_ticker_output_dir(stock_symbol):
    """Creates and returns the output directory for a given stock ticker."""
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_backtests_dir(stock_symbol, strategy="standard"):
    """Get backtests subdirectory for strategy results."""
    backtests_dir = os.path.join(get_ticker_output_dir(stock_symbol), "backtests", strategy)
    if not os.path.exists(backtests_dir):
        os.makedirs(backtests_dir)
    return backtests_dir

def plot_equity_curve(results_df, output_path):
    """Plots the cumulative log returns over time."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 7))
    
    results_df['cumulative_returns'] = results_df['actual_returns'].cumsum()
    
    ax.plot(results_df['test_end'], results_df['cumulative_returns'], 
            marker='o', linestyle='-', label='Donchian Strategy Equity Curve')
    
    ax.set_title('Walk-Forward Donchian Strategy Performance', fontsize=16)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Log Returns', fontsize=12)
    ax.legend()
    ax.grid(True)
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

def plot_p_value_distribution(results_df, output_path):
    """Plots the distribution of p-values from the MCPT."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.histplot(results_df['p_value'], bins=20, kde=True, ax=ax, color='skyblue')
    
    ax.axvline(0.05, color='r', linestyle='--', label='p=0.05 (Significance Level)')
    ax.axvline(0.10, color='orange', linestyle='--', label='p=0.10')
    
    ax.set_title('Distribution of MCPT P-Values across Walk-Forward Periods', fontsize=14)
    ax.set_xlabel('P-Value', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.legend()
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

def plot_actual_vs_permuted(results_df, output_path):
    """
    Creates a visualization similar to the YouTube graph showing:
    - Red line: Actual strategy cumulative returns
    - Grey lines: Permuted strategy cumulative returns distribution
    
    Note: Each period has independent permutations, so we create random paths
    by randomly sampling from each period's permuted returns distribution.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')
    ax.set_facecolor('white')
    
    # Calculate cumulative returns over time
    results_df = results_df.sort_values('test_end').copy()
    results_df['cumulative_actual'] = results_df['actual_returns'].cumsum()
    
    # Plot actual strategy (red line - like "Real Optimized")
    ax.plot(results_df['test_end'], results_df['cumulative_actual'], 
            color='red', linewidth=2.5, label='Real Optimized Strategy', zorder=10)
    
    # Plot permuted strategies (grey lines - like "Permutation Optimized")
    # Each period has independent permutations, so we create random paths
    # by randomly sampling one permuted return from each period
    if 'permuted_returns' in results_df.columns and len(results_df) > 0:
        num_permutations_to_plot = 100  # Plot more paths for better distribution visualization
        np.random.seed(42)  # For reproducibility
        
        for path_idx in range(num_permutations_to_plot):
            cumulative_permuted = []
            cum_sum = 0
            for _, row in results_df.iterrows():
                permuted_rets = row['permuted_returns']
                if isinstance(permuted_rets, list) and len(permuted_rets) > 0:
                    # Randomly sample one permuted return from this period's distribution
                    sampled_return = np.random.choice(permuted_rets)
                    cum_sum += sampled_return
                    cumulative_permuted.append(cum_sum)
                else:
                    cumulative_permuted.append(cum_sum)
            
            if len(cumulative_permuted) == len(results_df):
                ax.plot(results_df['test_end'], cumulative_permuted, 
                       color='grey', alpha=0.2, linewidth=0.5, zorder=1)
    
    # Add a line showing the mean of permuted strategies
    if 'permuted_returns_mean' in results_df.columns:
        results_df['cumulative_permuted_mean'] = results_df['permuted_returns_mean'].cumsum()
        ax.plot(results_df['test_end'], results_df['cumulative_permuted_mean'], 
               color='darkgrey', linewidth=1.5, linestyle='--', 
               label='Permutation Optimized (Mean)', zorder=5)
    
    # Add confidence bands (percentiles of permuted distribution)
    if 'permuted_returns' in results_df.columns and len(results_df) > 0:
        # Calculate percentiles across all periods
        percentiles_5 = []
        percentiles_95 = []
        cum_sum_5 = 0
        cum_sum_95 = 0
        for _, row in results_df.iterrows():
            permuted_rets = row['permuted_returns']
            if isinstance(permuted_rets, list) and len(permuted_rets) > 0:
                cum_sum_5 += np.percentile(permuted_rets, 5)
                cum_sum_95 += np.percentile(permuted_rets, 95)
            percentiles_5.append(cum_sum_5)
            percentiles_95.append(cum_sum_95)
        
        if len(percentiles_5) == len(results_df):
            ax.fill_between(results_df['test_end'], percentiles_5, percentiles_95,
                           color='lightgrey', alpha=0.3, label='95% Confidence Band', zorder=2)
    
    ax.set_title('Real Optimized vs Permutation Optimized Strategies\n(Monte Carlo Permutation Test)', 
                 fontsize=16, fontweight='bold', color='black')
    ax.set_xlabel('Date', fontsize=12, color='black')
    ax.set_ylabel('Cumulative Log Return', fontsize=12, color='black')
    ax.tick_params(colors='black')
    ax.legend(loc='upper left', facecolor='white', edgecolor='black')
    ax.grid(True, alpha=0.3, color='grey')
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200, facecolor='white', edgecolor='none')
    plt.close(fig)
    
def generate_html_report(summary_df, results_df, stock_symbol, output_dir):
    """Generates a comprehensive HTML report with summary and plots."""
    env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
    template = env.from_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Donchian MCPT Report: {{ stock_symbol }}</title>
        <style>
            body { font-family: sans-serif; margin: 2em; }
            h1, h2 { color: #333; }
            .summary-table { border-collapse: collapse; width: 100%; }
            .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 8px; }
            .summary-table th { background-color: #f2f2f2; text-align: left; }
            img { max-width: 100%; height: auto; margin-top: 1em; }
        </style>
    </head>
    <body>
        <h1>Donchian Strategy Walk-Forward MCPT Report: {{ stock_symbol }}</h1>
        <h2>Summary</h2>
        {{ summary_table }}
        <h2>Walk-Forward Performance</h2>
        <img src="equity_curve.png" alt="Equity Curve">
        <p><em>This chart shows the cumulative log returns over time for the Donchian strategy.</em></p>
    </body>
    </html>
    """)
    
    summary_table_html = summary_df.to_html(classes='summary-table', index=False)
    
    html_content = template.render(
        stock_symbol=stock_symbol,
        summary_table=summary_table_html
    )
    
    report_path = os.path.join(output_dir, "report.html")
    with open(report_path, 'w') as f:
        f.write(html_content)
    print(f"📄 HTML report generated at: {report_path}")

def main():
    """
    Main function to run the Donchian Walk-Forward MCPT backtest.
    """
    # --- 1. Argument Parsing ---
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print(f"⚠️ No file path provided. Using default: {DEFAULT_STOCK_FILE}")
        file_path = DEFAULT_STOCK_FILE

    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        print("Please run 'python3 analyze_indian_stocks.py' first.")
        return

    stock_symbol = os.path.basename(file_path).replace('_analysis.csv', '')
    output_dir = get_backtests_dir(stock_symbol, "standard")

    # --- 2. Load Data ---
    print(f"🔄 Loading data for {stock_symbol}...")
    ohlc_data = load_stock_data(file_path)
    if ohlc_data is None:
        return
    print(f"✅ Data loaded successfully. Shape: {ohlc_data.shape}")

    # --- 3. Run Walk-Forward Analysis ---
    print("\n🚀 Starting Walk-Forward Analysis with MCPT...")
    wf_analyzer = WalkForwardAnalysis(
        data=ohlc_data,
        train_period_days=TRAIN_PERIOD_DAYS,
        test_period_days=TEST_PERIOD_DAYS
    )
    results_df = wf_analyzer.run(mcpt_iterations=MCPT_ITERATIONS)

    if results_df.empty:
        print("❌ Walk-forward analysis produced no results. Check data length and period settings.")
        return

    # --- 4. Analyze and Save Results ---
    print("\n📊 Analyzing results...")
    
    # Overall Performance
    total_log_return = results_df['actual_returns'].sum()
    total_p_value = results_df['p_value'].mean()
    
    summary = {
        'Stock': stock_symbol,
        'Total Log Return': total_log_return,
        'Annualized Log Return': (total_log_return / ((results_df['test_end'].max() - results_df['test_start'].min()).days / 365.25)),
        'Average P-Value': total_p_value,
        'Num Walk-Forward Periods': len(results_df),
        'Train Period Days': TRAIN_PERIOD_DAYS,
        'Test Period Days': TEST_PERIOD_DAYS,
        'MCPT Iterations': MCPT_ITERATIONS
    }
    
    summary_df = pd.DataFrame([summary])

    print("\n" + "="*80)
    print("📈 DONCHIAN STRATEGY - WALK-FORWARD MCPT SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))
    print("="*80)
    print(f"Interpretation: A low 'Average P-Value' (e.g., < 0.10) suggests the strategy's positive returns are statistically significant and not likely due to random chance.")

    # Save results
    walkforward_results_path = os.path.join(output_dir, "results.csv")
    summary_path = os.path.join(output_dir, "summary.csv")
    
    results_df.to_csv(walkforward_results_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    
    print(f"\n💾 Detailed walk-forward results saved to: {walkforward_results_path}")
    print(f"💾 Summary results saved to: {summary_path}")
    
    # --- 4b. Print Simple Summary (Easy to Read Format) ---
    try:
        from donchian_simple_summary import print_simple_summary
        print_simple_summary(walkforward_results_path, initial_capital=100000)
    except Exception as e:
        print(f"⚠️  Could not generate simple summary: {e}")
    
    print(f"\n✅ Analysis complete for {stock_symbol}.")

    # --- 5. Generate Visualizations and Report ---
    print("\n🎨 Generating visualizations...")
    # Keep only essential visualization (equity curve)
    equity_curve_path = os.path.join(output_dir, "equity_curve.png")
    plot_equity_curve(results_df, equity_curve_path)
    print(f"📈 Equity curve plot saved to: {equity_curve_path}")

    generate_html_report(summary_df, results_df, stock_symbol, output_dir)

if __name__ == "__main__":
    main()
