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
TRAIN_PERIOD_DAYS = 365 * 2  # 2 years for training
TEST_PERIOD_DAYS = 365 // 2  # 6 months for testing
MCPT_ITERATIONS = 1000       # Number of Monte Carlo iterations (Higher = More Precision)

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
    """
    Plots the cumulative log returns over time.
    This represents the growth of $1 invested in the strategy (log scale).
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Ensure data is sorted by time
    results_df = results_df.sort_values('test_end')
    results_df['cumulative_returns'] = results_df['actual_returns'].cumsum()
    
    ax.plot(results_df['test_end'], results_df['cumulative_returns'], 
            marker='o', linestyle='-', linewidth=2, color='#1f77b4', label='Strategy Equity (Log)')
    
    ax.set_title('Walk-Forward Donchian Strategy Performance', fontsize=16, fontweight='bold')
    ax.set_xlabel('Test Period End Date', fontsize=12)
    ax.set_ylabel('Cumulative Log Returns', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

def plot_p_value_distribution(results_df, output_path):
    """
    Plots the distribution of p-values from the MCPT.
    A skew towards 0.0 indicates genuine edge. A flat distribution indicates randomness.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.histplot(results_df['p_value'], bins=10, kde=True, ax=ax, color='skyblue', edgecolor='black')
    
    ax.axvline(0.05, color='r', linestyle='--', linewidth=2, label='Significance (p=0.05)')
    ax.axvline(0.10, color='orange', linestyle='--', linewidth=2, label='Marginal (p=0.10)')
    
    ax.set_title('Robustness Check: Distribution of P-Values', fontsize=16, fontweight='bold')
    ax.set_xlabel('P-Value (Probability that Return is Luck)', fontsize=12)
    ax.set_ylabel('Frequency (Number of Periods)', fontsize=12)
    ax.legend()
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

def plot_actual_vs_permuted(results_df, output_path):
    """
    The 'Money Shot' Chart:
    - Red line: Actual strategy cumulative returns (Real Optimized)
    - Grey cloud: 100 random paths constructed from the permuted null distributions.
    
    Interpretation: If the Red line is above the Grey cloud, the strategy has significant Alpha.
    If it's inside the cloud, the strategy is indistinguishable from luck.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')
    
    # Sort and calculate actual cumulative
    results_df = results_df.sort_values('test_end').copy()
    results_df['cumulative_actual'] = results_df['actual_returns'].cumsum()
    
    # --- Plot Permuted "Null Hypothesis" Paths ---
    # We simulate 100 possible "luck" outcomes by sampling one permuted return 
    # from each period's null distribution.
    if 'permuted_returns' in results_df.columns and len(results_df) > 0:
        num_paths_to_plot = 100
        np.random.seed(42)  # Seed for consistent reporting
        
        for _ in range(num_paths_to_plot):
            cumulative_permuted = []
            current_sum = 0
            
            for _, row in results_df.iterrows():
                permuted_rets = row['permuted_returns']
                if isinstance(permuted_rets, list) and len(permuted_rets) > 0:
                    # Sample one "what-if" return from the null distribution of this period
                    sampled_return = np.random.choice(permuted_rets)
                    current_sum += sampled_return
                    cumulative_permuted.append(current_sum)
                else:
                    # Fallback if data missing
                    cumulative_permuted.append(current_sum)
            
            if len(cumulative_permuted) == len(results_df):
                ax.plot(results_df['test_end'], cumulative_permuted, 
                       color='grey', alpha=0.15, linewidth=1, zorder=1)
    
    # --- Plot Mean of Permutations (The Baseline) ---
    if 'permuted_returns_mean' in results_df.columns:
        results_df['cumulative_permuted_mean'] = results_df['permuted_returns_mean'].cumsum()
        ax.plot(results_df['test_end'], results_df['cumulative_permuted_mean'], 
               color='#555555', linewidth=2, linestyle='--', 
               label='Mean Random Performance', zorder=5)
    
    # --- Plot Actual Strategy (The Alpha) ---
    ax.plot(results_df['test_end'], results_df['cumulative_actual'], 
            color='#d62728', linewidth=3, label='Real Optimized Strategy', zorder=10)
    
    ax.set_title('Alpha Verification: Actual vs. Random Permutations', fontsize=16, fontweight='bold')
    ax.set_xlabel('Test Period End Date', fontsize=12)
    ax.set_ylabel('Cumulative Log Return', fontsize=12)
    
    # Create custom legend
    ax.legend(loc='upper left', frameon=True, framealpha=0.9, facecolor='white')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    
def generate_html_report(summary_df, results_df, stock_symbol, output_dir):
    """
    Generates a comprehensive HTML report integrating all charts and metrics.
    """
    env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
    
    # Simple inline template for robustness
    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Hedge Fund Grade Report: {{ stock_symbol }}</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0 auto; max-width: 1200px; padding: 20px; background-color: #f9f9f9; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .summary-table { border-collapse: collapse; width: 100%; font-size: 14px; }
            .summary-table th, .summary-table td { border: 1px solid #e0e0e0; padding: 12px; text-align: left; }
            .summary-table th { background-color: #f2f6fc; font-weight: 600; color: #2c3e50; }
            .plot-container { text-align: center; margin: 20px 0; }
            img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
            .caption { font-style: italic; color: #666; margin-top: 8px; }
            .metric-box { background-color: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Donchian Strategy Audit: {{ stock_symbol }}</h1>
        
        <div class="container">
            <h2>Executive Summary</h2>
        {{ summary_table }}
            <div class="metric-box">
                <strong>Methodology:</strong> Walk-Forward Optimization ({{ train_days }} day train / {{ test_days }} day test).
                <br>
                <strong>Validation:</strong> Monte Carlo Permutation Test ({{ mcpt_iter }} iterations per period).
            </div>
        </div>
        <div class="container">
            <h2>1. Alpha Verification (The "Money Plot")</h2>
            <div class="plot-container">
                <img src="actual_vs_permuted.png" alt="Actual vs Permuted">
                <div class="caption">Red line = Your Strategy. Grey lines = Random Luck. If Red is above Grey, you have Alpha.</div>
            </div>
        </div>
        <div class="container">
            <h2>2. Equity Curve</h2>
            <div class="plot-container">
        <img src="equity_curve.png" alt="Equity Curve">
                <div class="caption">Cumulative Log Returns over the entire test history.</div>
            </div>
        </div>
        <div class="container">
            <h2>3. Statistical Robustness</h2>
            <div class="plot-container">
                <img src="p_value_dist.png" alt="P-Value Distribution">
                <div class="caption">Distribution of P-Values. A left-skewed histogram (bars stacked near 0.0) indicates consistent statistical significance.</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = env.from_string(template_str)
    
    summary_table_html = summary_df.to_html(classes='summary-table', index=False)
    
    html_content = template.render(
        stock_symbol=stock_symbol,
        summary_table=summary_table_html,
        train_days=TRAIN_PERIOD_DAYS,
        test_days=TEST_PERIOD_DAYS,
        mcpt_iter=MCPT_ITERATIONS
    )
    
    report_path = os.path.join(output_dir, "report.html")
    with open(report_path, 'w') as f:
        f.write(html_content)
    print(f"📄 Professional HTML report generated at: {report_path}")

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
    print(f"   Train Window: {TRAIN_PERIOD_DAYS} days | Test Window: {TEST_PERIOD_DAYS} days")
    
    wf_analyzer = WalkForwardAnalysis(
        data=ohlc_data,
        train_period_days=TRAIN_PERIOD_DAYS,
        test_period_days=TEST_PERIOD_DAYS
    )
    results_df = wf_analyzer.run(mcpt_iterations=MCPT_ITERATIONS)

    if results_df.empty:
        print("❌ Walk-forward analysis produced no results. Check data length.")
        return

    # --- 4. Analyze Results ---
    print("\n📊 Calculating Performance Metrics...")
    
    # Calculate total annualized return
    total_log_return = results_df['actual_returns'].sum()
    total_days = (results_df['test_end'].max() - results_df['test_start'].min()).days
    annualized_return = (total_log_return / (total_days / 365.25)) if total_days > 0 else 0
    
    mean_p_value = results_df['p_value'].mean()
    significant_periods = sum(results_df['p_value'] < 0.05)
    total_periods = len(results_df)
    
    summary = {
        'Stock': stock_symbol,
        'Total Log Return': f"{total_log_return:.4f}",
        'Annualized Return': f"{annualized_return:.2%}",
        'Avg P-Value': f"{mean_p_value:.4f}",
        'Significant Periods (p<0.05)': f"{significant_periods}/{total_periods}",
        'MCPT Iterations': MCPT_ITERATIONS
    }
    
    summary_df = pd.DataFrame([summary])

    print("\n" + "="*80)
    print("📈 HEDGE FUND GRADE SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))
    print("="*80)

    # Save raw data
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
    
    # --- 5. Generate Visualizations ---
    print("\n🎨 Generating PhD-Grade Visualizations...")

    # 1. Equity Curve
    equity_curve_path = os.path.join(output_dir, "equity_curve.png")
    plot_equity_curve(results_df, equity_curve_path)
    print(f"📈 Equity curve plot saved to: {equity_curve_path}")

    # 2. P-Value Distribution (Robustness)
    p_value_dist_path = os.path.join(output_dir, "p_value_dist.png")
    plot_p_value_distribution(results_df, p_value_dist_path)
    print(f"📊 P-value distribution plot saved to: {p_value_dist_path}")
    
    # 3. Actual vs Permuted (Null Hypothesis Check) - CRITICAL STEP
    actual_vs_permuted_path = os.path.join(output_dir, "actual_vs_permuted.png")
    plot_actual_vs_permuted(results_df, actual_vs_permuted_path)
    print(f"🎯 Alpha verification plot saved to: {actual_vs_permuted_path}")
    
    print(f"\n✅ Charts saved to: {output_dir}")

    # --- 6. Generate HTML Report ---
    generate_html_report(summary_df, results_df, stock_symbol, output_dir)
    
    print(f"\n✅ Analysis complete for {stock_symbol}.")

if __name__ == "__main__":
    main()
