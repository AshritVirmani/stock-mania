"""
Final Dashboard Generator - Portfolio Manager's Monitor

This script acts as the Portfolio Manager's Monitor. It pulls the specific "PhD Grade" 
artifacts we created in the previous steps (Validation, Regimes, Whales, Forecasts) and 
fuses them into a single, unified Headquarters dashboard.

The "Alpha Deck" - A unified view of all quantitative research for a ticker.

Usage:
    python3 13_generate_final_dashboard.py TICKER.NS
    python3 13_generate_final_dashboard.py RELIANCE.NS
"""

import os
import sys
import pandas as pd
import base64
from datetime import datetime

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root (go up two levels from scripts/legacy/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# Base directory for analysis results
BASE_DIR = os.path.join(PROJECT_ROOT, "analysis_results")


def get_paths(symbol):
    """Returns a dictionary of required paths (absolute paths for file operations, relative for HTML)."""
    # Base directory for this symbol
    base_dir = os.path.join(PROJECT_ROOT, "analysis_results", symbol)
    
    # Absolute paths for file operations
    paths_abs = {
        "base": base_dir,
        "reports": os.path.join(base_dir, "reports"),
        "analysis": os.path.join(base_dir, "analysis"),
        "valuation": os.path.join(base_dir, "valuation"),
        "backtests_standard": os.path.join(base_dir, "backtests", "standard"),
        "backtests_enhanced": os.path.join(base_dir, "backtests", "enhanced")
    }
    
    # File paths (absolute for os.path.exists checks)
    paths_abs["valuation_output"] = os.path.join(paths_abs["valuation"], "valuation_output.txt")
    paths_abs["strategy_comparison"] = os.path.join(paths_abs["reports"], "strategy_comparison.png")
    paths_abs["filter_impact"] = os.path.join(paths_abs["reports"], "filter_impact_equity_curve.png")
    paths_abs["backtest_comparison_csv"] = os.path.join(paths_abs["reports"], "backtest_comparison.csv")
    paths_abs["whale_pro_chart"] = os.path.join(paths_abs["analysis"], "whale_entry_map_pro.png")
    paths_abs["whale_calendar"] = os.path.join(paths_abs["analysis"], "complete_whale_calendar.html")
    paths_abs["market_regimes"] = os.path.join(paths_abs["analysis"], "market_regimes_plot.png")
    paths_abs["future_projection"] = os.path.join(paths_abs["analysis"], f"{symbol}_future_projection_spaghetti.png")
    paths_abs["actual_vs_permuted"] = os.path.join(paths_abs["backtests_standard"], "actual_vs_permuted.png")
    paths_abs["p_value_dist"] = os.path.join(paths_abs["analysis"], "p_value_distribution.png")
    paths_abs["correlation_clustered"] = os.path.join(paths_abs["analysis"], "correlation_heatmap_clustered.png")
    paths_abs["correlation_filtered"] = os.path.join(paths_abs["analysis"], "correlation_heatmap.png")
    
    # Relative paths for HTML (relative to the HTML file location, which is in analysis_results/SYMBOL/)
    # The HTML file is at: analysis_results/SYMBOL/SYMBOL_Alpha_Deck.html
    # So relative paths should be from that location
    paths_rel = {
        "base": ".",  # Same directory as HTML file
        "reports": "reports",
        "analysis": "analysis",
        "valuation": "valuation",
        "backtests_standard": os.path.join("backtests", "standard"),
        "backtests_enhanced": os.path.join("backtests", "enhanced")
    }
    paths_rel["whale_calendar"] = os.path.join("analysis", "complete_whale_calendar.html")
    
    # Return both absolute (for file ops) and relative (for HTML) paths
    return {"abs": paths_abs, "rel": paths_rel}


def get_image_b64(path):
    """Encodes image to base64 for embedding."""
    if os.path.exists(path):
        try:
            with open(path, "rb") as img:
                return base64.b64encode(img.read()).decode('utf-8')
        except Exception as e:
            print(f"⚠️  Could not load image {path}: {e}")
            return None
    return None


def get_img_tag(b64_data, alt_text="Visual artifact not found."):
    """Generate HTML img tag with base64 data or warning message."""
    if b64_data:
        return f'<div class="img-wrapper"><img src="data:image/png;base64,{b64_data}" class="img-fluid" alt="{alt_text}"></div>'
    else:
        return f'<div class="alert alert-warning p-3 text-center">{alt_text}</div>'


def generate_dashboard(symbol):
    """Generate the final Alpha Deck dashboard."""
    print(f"🏛️  Assembling Hedge Fund Dashboard for {symbol}...")
    
    paths = get_paths(symbol)
    paths_abs = paths["abs"]  # Absolute paths for file operations
    paths_rel = paths["rel"]  # Relative paths for HTML
    
    # 1. Load Assets (The Visual Proof)
    print("   Gathering visual assets...")
    assets = {
        "strategy_comparison": get_image_b64(paths_abs["strategy_comparison"]),
        "filter_impact": get_image_b64(paths_abs["filter_impact"]),
        "whale_pro_chart": get_image_b64(paths_abs["whale_pro_chart"]),
        "market_regimes": get_image_b64(paths_abs["market_regimes"]),
        "future_projection": get_image_b64(paths_abs["future_projection"]),
        "actual_vs_permuted": get_image_b64(paths_abs["actual_vs_permuted"]),
        "p_value_dist": get_image_b64(paths_abs["p_value_dist"]),
        "correlation_clustered": get_image_b64(paths_abs["correlation_clustered"]),
        "correlation_filtered": get_image_b64(paths_abs["correlation_filtered"]),
    }

    # Try alternative paths for forecast
    if not assets['future_projection']:
        # Try without symbol prefix
        alt_path = os.path.join(paths_abs['analysis'], "future_projection_spaghetti.png")
        assets['future_projection'] = get_image_b64(alt_path)
        if assets['future_projection']:
            print(f"   ✅ Found future projection (alternative path): {alt_path}")
    
    # Check if future projection exists
    if assets['future_projection']:
        print(f"   ✅ Found future projection: {paths_abs['future_projection']}")
    else:
        print(f"   ⚠️  Future projection not found: {paths_abs['future_projection']}")
        print(f"      Also tried: {os.path.join(paths_abs['analysis'], 'future_projection_spaghetti.png')}")
    
    # Check if whale calendar exists
    whale_calendar_exists = os.path.exists(paths_abs["whale_calendar"])
    if whale_calendar_exists:
        print(f"   ✅ Found whale calendar: {paths_abs['whale_calendar']}")
    else:
        print(f"   ⚠️  Whale calendar not found: {paths_abs['whale_calendar']}")
    
    # Check if whale chart exists
    if assets['whale_pro_chart']:
        print(f"   ✅ Found whale chart: {paths_abs['whale_pro_chart']}")
    else:
        print(f"   ⚠️  Whale chart not found: {paths_abs['whale_pro_chart']}")
    
    # --- Read Performance Data ---
    try:
        comparison_df = pd.read_csv(paths_abs["backtest_comparison_csv"])
        perf_audit_html = comparison_df.to_html(classes="table table-sm table-hover table-bordered", index=False)
    except Exception:
        perf_audit_html = '<div class="alert alert-warning">No backtest data found. Run <code>10_compare_backtests.py</code> first.</div>'

    # --- Read Valuation Data ---
    try:
        with open(paths_abs["valuation_output"], "r") as f:
            valuation_text = f.read()
    except Exception:
        valuation_text = "Valuation analysis not found."


    print("   Assembling HTML dashboard...")
    
    # --- HTML Structure ---
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Alpha Deck: {symbol}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f0f2f5; font-family: 'Inter', 'Segoe UI', sans-serif; padding-bottom: 50px; }}
            .header-section {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px 0; margin-bottom: 30px; }}
            .card {{ border: none; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 25px; overflow: hidden; }}
            .card-header {{ background-color: white; border-bottom: 1px solid #eee; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #555; padding: 15px 20px; }}
            .card-body {{ padding: 20px; }}
            .img-wrapper {{ border: 1px solid #eee; border-radius: 8px; padding: 5px; background: white; }}
            .metric-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #2a5298; }}
            .status-pill {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
            .pill-green {{ background: #d1e7dd; color: #0f5132; }}
            .pill-red {{ background: #f8d7da; color: #842029; }}
            .section-title {{ font-weight: 800; color: #2c3e50; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
            iframe {{ border: 1px solid #ddd; border-radius: 8px; }}
            .correlation-image {{ width: 100%; height: auto; max-width: 100%; object-fit: contain; border-radius: 4px; }}
        </style>
    </head>
    <body>

        <div class="header-section">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h6 class="text-uppercase opacity-75" style="letter-spacing: 1px;">Quantitative Research Report</h6>
                        <h1 class="display-5 fw-bold">{symbol}</h1>
                        <p class="mb-0 opacity-75">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Strategy: Enhanced Regime Filtering</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <span class="status-pill pill-green">Hedge Fund Grade</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="container">
            
            <div class="row">
                <div class="col-12">
                    <h3 class="section-title">1. Strategy Validation</h3>
                </div>
                <div class="col-lg-8">
                    <div class="card h-100">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            Cumulative Alpha (Equity Curve)
                            <small class="text-muted">Blind (Grey) vs. Filtered (Green)</small>
                        </div>
                        <div class="card-body">
                            {get_img_tag(assets['filter_impact'])}
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card h-100">
                        <div class="card-header">Performance Audit</div>
                        <div class="card-body">
                            {perf_audit_html}
                            <div class="mt-3 small text-muted">
                                <strong>Interpretation:</strong> The 'Enhanced' column represents the strategy with Regime Filtering active. A positive difference indicates the Regime Filter successfully avoided losses.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-12">
                    <h3 class="section-title">2. Institutional Radar (Whale Hunter)</h3>
                </div>
                <div class="col-lg-12">
                    <div class="card">
                        <div class="card-header">The Crime Scene (Entries & Traps)</div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Bloomberg-Style Deep Dive</h5>
                                    <p class="text-muted small">Professional candlestick chart with whale signals overlaid. Shows exact entry points with price action context.</p>
                                    {get_img_tag(assets['whale_pro_chart'])}
                                    <p class="small text-muted mt-2"><strong>Green Triangle (^):</strong> Ignition - Breakout with volume | <strong>Blue Circle (o):</strong> Stealth - Accumulation | <strong>Red Triangle (v):</strong> Trap - Selling into strength</p>
                                </div>
                                <div class="col-md-6">
                                    <h5>Activity Calendar</h5>
                                    <p class="text-muted small">Master Strategy Calendar showing whale signals with regime-aware filtering.</p>
                                    {f'<div class="img-wrapper"><iframe src="{paths_rel["whale_calendar"]}" style="width: 100%; height: 400px; border: 1px solid #ddd; border-radius: 4px;"></iframe><p class="text-muted small mt-2"><a href="{paths_rel["whale_calendar"]}" target="_blank">Open calendar in new tab</a></p></div>' if whale_calendar_exists else '<div class="alert alert-warning">Whale calendar not found. Run <code>12_whale_calendar.py</code> to generate.</div>'}
                                </div>
                            </div>
                            <div class="row mt-4">
                                <div class="col-12">
                                    <div class="metric-box">
                                        <h5>How to read this:</h5>
                                        <ul class="mb-0 ps-3">
                                            <li><strong>🚀 Green Triangle (Ignition):</strong> Breakouts with Volume - Buy Signal</li>
                                            <li><strong>🕵️ Blue Circle (Stealth):</strong> Accumulation in ranges - Accumulate</li>
                                            <li><strong>🪤 Red Triangle (Trap):</strong> Selling into strength - Sell Signal</li>
                                            <li><strong>⭐ Gold Star:</strong> High conviction (Regime 1 Rally + Whale signal)</li>
                                            <li><strong>⛔ Blocked:</strong> Regime 3 Crash detected - Bull Trap avoided</li>
                                            <li><strong>Action:</strong> Use the Deep Dive chart to see exact entry points. Use the Calendar to see when to look. If recent days show Green/Blue markers with Gold Star, probability of trend continuation is High.</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-12">
                    <h3 class="section-title">3. Intrinsic Value Analysis</h3>
                </div>
                <div class="col-lg-12">
                    <div class="card">
                        <div class="card-header">Valuation Summary</div>
                        <div class="card-body">
                            <pre class="bg-light p-3 rounded" style="white-space: pre-wrap; word-wrap: break-word;"><code>{valuation_text}</code></pre>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-12">
                    <h3 class="section-title">4. Market Context & Forecasting</h3>
                </div>
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header">Market Regimes (The Season)</div>
                        <div class="card-body">
                            {get_img_tag(assets['market_regimes'])}
                            <p class="mt-2 small text-muted">Colors represent the current 'mood' of the stock. Avoid trading during the 'Crash' regime (usually lowest return color).</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header">Future Projection (Similarity)</div>
                        <div class="card-body">
                            {get_img_tag(assets['future_projection'])}
                            <p class="mt-2 small text-muted">The 'Spaghetti Plot' projects the next 10 days based on the 10 most historically similar patterns to today.</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                         <div class="card-header">4. Statistical Significance (Null Hypothesis)</div>
                         <div class="card-body text-center">
                            {get_img_tag(assets['actual_vs_permuted'])}
                            <p class="small text-muted mt-2">If the Red Line is above the Grey Cloud, the strategy is statistically superior to luck.</p>
                         </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-12">
                    <h3 class="section-title">5. Indicator Correlation Analysis</h3>
                </div>
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header">Clustered View (Redundancy Detection)</div>
                        <div class="card-body">
                            {get_img_tag(assets['correlation_clustered'])}
                            <p class="mt-2 small text-muted">Hierarchical clustering groups similar indicators together. Indicators in the same cluster are highly correlated and may be redundant.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header">Filtered View (Significant Only)</div>
                        <div class="card-body">
                            {get_img_tag(assets['correlation_filtered'])}
                            <p class="mt-2 small text-muted">Shows only significant correlations (|r| ≥ 0.7). Red = negative correlation, Blue = positive correlation.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="text-center text-muted mt-5">
                <small>Generated by Quantitative Analysis Pipeline | {datetime.now().year}</small>
            </div>

        </div>

    </body>
    </html>
    """
    
    output_path = os.path.join(paths_abs['base'], f"{symbol}_Alpha_Deck.html")
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard Generated: {output_path}")
    return output_path


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 13_generate_final_dashboard.py <SYMBOL>")
        print("\nExample:")
        print("  python3 13_generate_final_dashboard.py RELIANCE.NS")
        print("  python3 13_generate_final_dashboard.py VOLTAS.NS")
        return
    
    symbol = sys.argv[1].strip().upper()
    
    # Ensure .NS suffix for Indian stocks
    if not symbol.endswith('.NS'):
        print(f"⚠️  Adding .NS suffix for Indian stock")
        symbol = symbol + '.NS'
    
    generate_dashboard(symbol)


if __name__ == "__main__":
    main()

