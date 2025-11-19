"""
Hedge Fund Grade Executive Report Generator

This script generates a comprehensive "PhD Grade" HTML report that integrates:
1. Strategy Validation (Blind vs Regime-Aware comparison)
2. Market Regime Identification (with Red Light detection)
3. Future Projection (Pattern Matching Spaghetti Plot)
4. Institutional Activity (Whale Calendar with regime filtering)
5. Statistical Significance (MCPT validation)
6. Backtest Comparison Metrics

All charts are embedded as base64 images for a self-contained report.
Whale calendar is embedded as an iframe for interactive viewing.
No external dependencies required - just reads previously generated files.
"""

import os
import sys
import pandas as pd
import base64
from datetime import datetime

# --- Configuration ---
BASE_ANALYSIS_DIR = "analysis_results"
DEFAULT_STOCK_SYMBOL = "RELIANCE.NS"


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory for correlation, regimes, similarity."""
    analysis_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "analysis")
    return analysis_dir


def get_reports_dir(stock_symbol):
    """Get reports subdirectory for final reports."""
    reports_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir


def get_backtests_dir(stock_symbol, strategy="standard"):
    """Get backtests subdirectory for strategy results."""
    backtests_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "backtests", strategy)
    return backtests_dir


def get_image_as_base64(path):
    """Encodes an image file into a base64 string for embedding in HTML."""
    if not os.path.exists(path):
        return None
    try:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️  Could not load image {path}: {e}")
        return None


def create_html_table(df, classes="table table-bordered table-hover table-sm"):
    """Converts a pandas DataFrame to an HTML table with nice styling."""
    if df is None or df.empty:
        return "<p><em>No data available.</em></p>"
    return df.to_html(classes=classes, border=0, index=False, escape=False)


def generate_hedge_fund_report(stock_symbol):
    """
    Generates a Hedge Fund Grade Executive Report integrating all advanced analyses.
    """
    print(f"📄 Generating Executive Report for {stock_symbol}...")
    
    # --- 1. Gather Assets (Images) ---
    print("Step 1: Gathering analysis assets...")
    
    base_dir = get_ticker_analysis_dir(stock_symbol)
    analysis_dir = get_analysis_dir(stock_symbol)
    reports_dir = get_reports_dir(stock_symbol)
    backtests_standard_dir = get_backtests_dir(stock_symbol, "standard")
    
    # Collect all "PhD Grade" charts
    assets = {
        'regime_map': get_image_as_base64(os.path.join(analysis_dir, "market_regimes_plot.png")),
        'equity_curve_filter': get_image_as_base64(os.path.join(reports_dir, "filter_impact_equity_curve.png")),
        'spaghetti': get_image_as_base64(os.path.join(analysis_dir, f"{stock_symbol}_future_projection_spaghetti.png")),
        'mcpt_validation': get_image_as_base64(os.path.join(backtests_standard_dir, "actual_vs_permuted.png")),
        'equity_curve_standard': get_image_as_base64(os.path.join(backtests_standard_dir, "equity_curve.png")),
        'p_value_dist': get_image_as_base64(os.path.join(backtests_standard_dir, "p_value_dist.png")),
        'strategy_comparison': get_image_as_base64(os.path.join(get_backtests_dir(stock_symbol, "enhanced"), "strategy_comparison.png")),
        'whale_entry_map': get_image_as_base64(os.path.join(analysis_dir, "whale_entry_map.png")),
    }
    
    # Check for whale calendar HTML
    whale_calendar_path = os.path.join(analysis_dir, "complete_whale_calendar.html")
    whale_calendar_exists = os.path.exists(whale_calendar_path)
    
    # --- 2. Gather Data (Stats) ---
    print("Step 2: Loading performance metrics...")
    
    # Backtest comparison
    comparison_path = os.path.join(reports_dir, "backtest_comparison.csv")
    comparison_df = None
    if os.path.exists(comparison_path):
        comparison_df = pd.read_csv(comparison_path)
    
    # Standard strategy summary
    standard_summary_path = os.path.join(backtests_standard_dir, "summary.csv")
    standard_summary = None
    if os.path.exists(standard_summary_path):
        standard_summary = pd.read_csv(standard_summary_path)
    
    # Enhanced strategy summary
    enhanced_summary_path = os.path.join(get_backtests_dir(stock_symbol, "enhanced"), "summary.csv")
    enhanced_summary = None
    if os.path.exists(enhanced_summary_path):
        enhanced_summary = pd.read_csv(enhanced_summary_path)
    
    # Regime data for summary stats
    regime_data_path = os.path.join(analysis_dir, "data_with_regimes.csv")
    regime_data = None
    if os.path.exists(regime_data_path):
        regime_data = pd.read_csv(regime_data_path, index_col=0, parse_dates=True)
        regime_data.index.name = 'Date'
        
    # Similarity data
    similar_days_df = None
    latest_date = None
    if regime_data is not None:
        latest_date = regime_data.index.max().strftime('%Y-%m-%d')
        # Try multiple paths for similarity data
        similar_paths = [
            os.path.join(analysis_dir, "similar_days_latest.csv"),
            os.path.join(analysis_dir, f"similar_days_euclidean_{latest_date}.csv"),
            os.path.join(base_dir, f"similar_days_euclidean_{latest_date}.csv"),
        ]
        for path in similar_paths:
            if os.path.exists(path):
                similar_days_df = pd.read_csv(path)
                break

    # --- 3. Build HTML Report ---
    print("Step 3: Assembling HTML report...")
    
    # Format comparison table HTML
    stats_html = create_html_table(comparison_df) if comparison_df is not None else "<p><em>No backtest comparison data found. Run '10_compare_backtests.py' first.</em></p>"
    
    # Format standard summary
    standard_html = create_html_table(standard_summary) if standard_summary is not None else "<p><em>Standard strategy summary not available.</em></p>"
    
    # Format enhanced summary
    enhanced_html = create_html_table(enhanced_summary) if enhanced_summary is not None else "<p><em>Enhanced strategy summary not available.</em></p>"
    
    # Format similarity table
    similarity_html = create_html_table(similar_days_df.head(10)) if similar_days_df is not None else f"<p><em>Similarity analysis for {latest_date} not found.</em></p>"
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Build HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quant Strategy Audit: {stock_symbol}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f4f6f9; padding: 20px; font-family: 'Segoe UI', Roboto, sans-serif; }}
            .card {{ margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: none; }}
            .card-header {{ background-color: #2c3e50; color: white; font-weight: 600; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
            .metric-value.negative {{ color: #e74c3c; }}
            .metric-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
            img {{ max-width: 100%; height: auto; border-radius: 4px; margin: 10px 0; }}
            .status-badge {{ padding: 5px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
            .status-green {{ background-color: #d4edda; color: #155724; }}
            .status-red {{ background-color: #f8d7da; color: #721c24; }}
            .table td.negative {{ color: #e74c3c; font-weight: bold; }}
            iframe {{ border: 1px solid #ddd; border-radius: 4px; }}
            .alert-box {{ padding: 15px; margin: 10px 0; border-radius: 4px; }}
            .alert-warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
            .plot-container {{ text-align: center; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row mb-4">
                <div class="col-12 text-center">
                    <h1 class="display-4">{stock_symbol} Strategy Audit</h1>
                    <p class="lead text-muted">Hedge Fund Grade Analysis Report</p>
                    <p class="text-muted small">Generated: {timestamp}</p>
                </div>
            </div>

            <!-- Section 1: Strategy Validation -->
            <div class="card">
                <div class="card-header">1. Strategy Validation (Regime Filtering Impact)</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-7">
                            <h5>Equity Curve Impact</h5>
                            <p class="text-muted small">Comparison of Blind Trend Following vs. Regime-Aware Strategy. Green line shows the value-add of avoiding dangerous regimes.</p>
                            {f'<div class="plot-container"><img src="data:image/png;base64,{assets["equity_curve_filter"]}" class="img-fluid"></div>' if assets['equity_curve_filter'] else '<div class="alert-box alert-warning">Chart not found. Run <code>10_compare_backtests.py</code> to generate.</div>'}
                        </div>
                        <div class="col-md-5">
                            <h5>Performance Metrics Comparison</h5>
                            {stats_html}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section 2: Market Regime Identification -->
            <div class="card">
                <div class="card-header">2. Market Regime Identification</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-12">
                            <p>The algorithm clusters market behavior into distinct 'Seasons'. The 'Red Light' regime (worst-performing) should be avoided to reduce drawdowns.</p>
                            {f'<div class="plot-container"><img src="data:image/png;base64,{assets["regime_map"]}" class="img-fluid"></div>' if assets['regime_map'] else '<div class="alert-box alert-warning">Regime map not found. Run <code>04_behavioral_patterns.py</code> to generate.</div>'}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section 3: Future Projection -->
            <div class="card">
                <div class="card-header">3. Future Projection (Pattern Matching)</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-12">
                            <h5>The "Spaghetti" Forecast</h5>
                            <p class="text-muted small">Projected path based on the top 10 most similar historical setups (Price Action + Mathematical Context). Black line = Current context. Colored lines = Historical analogs. Shows expected move and win rate.</p>
                            {f'<div class="plot-container"><img src="data:image/png;base64,{assets["spaghetti"]}" class="img-fluid"></div>' if assets['spaghetti'] else '<div class="alert-box alert-warning">Projection not found. Run <code>06_find_similar_days.py</code> to generate.</div>'}
                            {f'<div class="mt-3"><h6>Top Similar Days (Latest: {latest_date})</h6>{similarity_html}</div>' if similar_days_df is not None else ''}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section 4: Institutional Activity (Whale Calendar) -->
            <div class="card">
                <div class="card-header">4. Institutional Activity (Whale Signals)</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-12">
                            <h5>Master Strategy Calendar</h5>
                            <p class="text-muted small">Combines whale buy signals (volume, spread, CLV analysis) with regime-aware filtering. <strong>Green boxes with gold star (⭐)</strong> = High conviction (Regime 1 Rally + Whale signal). <strong>Green boxes with ⛔</strong> = Blocked (Regime 3 Crash detected - Bull Trap avoided).</p>
                            {f'<div class="plot-container"><iframe src="../analysis/complete_whale_calendar.html" style="width: 100%; height: 800px; border: 1px solid #ddd; border-radius: 4px;"></iframe><p class="text-muted small mt-2"><a href="../analysis/complete_whale_calendar.html" target="_blank">Open calendar in new tab</a></p></div>' if whale_calendar_exists else '<div class="alert-box alert-warning">Whale calendar not found. Run <code>12_whale_calendar.py</code> to generate.</div>'}
                        </div>
                    </div>
                    {f'<div class="row mt-3"><div class="col-12"><h5>Whale Entry Map</h5><p class="text-muted small">Detailed visualization of institutional entry points and volume patterns.</p><div class="plot-container"><img src="data:image/png;base64,{assets["whale_entry_map"]}" class="img-fluid"></div></div></div>' if assets['whale_entry_map'] else ''}
                </div>
            </div>

            <!-- Section 5: Statistical Significance -->
            <div class="card">
                <div class="card-header">5. Statistical Significance (MCPT Validation)</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h5>Alpha Verification</h5>
                            <p class="text-muted small">Does the strategy have real Alpha, or is it luck? Red line = Actual strategy. Grey cloud = Random permutations. If Red is above Grey, you have Alpha.</p>
                            {f'<div class="plot-container"><img src="data:image/png;base64,{assets["mcpt_validation"]}" class="img-fluid"></div>' if assets['mcpt_validation'] else '<div class="alert-box alert-warning">Validation chart not found. Run <code>07b_donchian_mcpt_backtest.py</code> to generate.</div>'}
                        </div>
                        <div class="col-md-6">
                            <h5>P-Value Distribution</h5>
                            <p class="text-muted small">Distribution of P-Values across walk-forward periods. A left-skewed histogram (bars stacked near 0.0) indicates consistent statistical significance.</p>
                            {f'<div class="plot-container"><img src="data:image/png;base64,{assets["p_value_dist"]}" class="img-fluid"></div>' if assets['p_value_dist'] else '<div class="alert-box alert-warning">P-value distribution not found.</div>'}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section 6: Strategy Summaries -->
            <div class="card">
                <div class="card-header">6. Strategy Performance Summaries</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h5>Standard Donchian Strategy</h5>
                            {standard_html}
                            {f'<div class="plot-container"><img src="data:image/png;base64,{assets["equity_curve_standard"]}" class="img-fluid"></div>' if assets['equity_curve_standard'] else ''}
                        </div>
                        <div class="col-md-6">
                            <h5>Enhanced Donchian Strategy</h5>
                            {enhanced_html}
                            {f'<div class="plot-container"><img src="data:image/png;base64,{assets["strategy_comparison"]}" class="img-fluid"></div>' if assets['strategy_comparison'] else ''}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer text-center text-muted mt-4 mb-4">
                <small>Generated by Hedge Fund Scalper Engine | {timestamp}</small>
            </div>
        </div>
    </body>
    </html>
    """

    # --- 4. Save the HTML report ---
    print("Step 4: Saving HTML report...")
    output_path = os.path.join(reports_dir, "comprehensive_report.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Report generation complete!")
    print(f"📁 View the report at: {output_path}")
    print(f"📁 All results organized in: {base_dir}/")
    
    return output_path


def main():
    """Main function to run the report generator."""
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1]
    else:
        stock_symbol = DEFAULT_STOCK_SYMBOL
        print(f"⚠️  No stock symbol provided. Using default: {stock_symbol}")
    
    # Note: We don't auto-generate missing files (removed os.system call)
    # The report generator should just report what exists
    # Users should run the analysis scripts separately if needed
    
    generate_hedge_fund_report(stock_symbol)

if __name__ == "__main__":
    main()
