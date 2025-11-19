"""
Comprehensive Analysis Report Generator

This script automates the generation of a detailed HTML analysis report for a
given stock, combining insights from correlation, similarity, and behavioral
pattern analyses.

-   Loads all previously generated analysis data and plots.
-   Assembles the data into a structured HTML report using Plotly figures
    and pandas DataFrames.
-   Includes sections for:
    -   Correlation analysis (heatmap and highly correlated pairs).
    -   Behavioral analysis (regime summary and plot).
    -   Similarity analysis (example of similar days to the latest trading day).
-   Saves the report as a single, self-contained HTML file.
"""

import os
import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64

# --- Configuration ---
BASE_ANALYSIS_DIR = "analysis_results"
DEFAULT_STOCK_SYMBOL = "RELIANCE.NS"


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_image_as_base64(path):
    """Encodes an image file into a base64 string for embedding in HTML."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_html_table(df):
    """Converts a pandas DataFrame to an HTML table with nice styling."""
    return df.to_html(classes=["table", "table-striped", "table-hover", "table-sm"], border=0, float_format="%.4f")


def generate_report(stock_symbol):
    """
    Generates a comprehensive HTML report for the given stock symbol.
    """
    print(f"--- Generating Comprehensive Analysis Report for {stock_symbol} ---")
    
    # --- 1. Load all necessary data ---
    print("Step 1: Loading analysis data...")
    
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    
    # Correlation data
    corr_matrix_path = os.path.join(ticker_dir, "correlation_matrix.csv")
    corr_matrix = pd.read_csv(corr_matrix_path, index_col=0) if os.path.exists(corr_matrix_path) else None
    
    # Try new filename first, fallback to old for backward compatibility
    corr_heatmap_path = os.path.join(ticker_dir, "correlation_heatmap_full.png")
    if not os.path.exists(corr_heatmap_path):
        corr_heatmap_path = os.path.join(ticker_dir, "correlation_heatmap.png")
    corr_heatmap_b64 = get_image_as_base64(corr_heatmap_path)
    
    # Behavioral/Regime data
    regime_data_path = os.path.join(ticker_dir, "data_with_regimes.csv")
    # Use index_col=0 because the date column is the first column and may be unnamed
    regime_data = pd.read_csv(regime_data_path, index_col=0, parse_dates=True) if os.path.exists(regime_data_path) else None
    if regime_data is not None:
        regime_data.index.name = 'Date'
        
    regime_plot_path = os.path.join(ticker_dir, "market_regimes_plot.png")
    regime_plot_b64 = get_image_as_base64(regime_plot_path)

    # Find the latest date to use for similarity analysis
    latest_date = regime_data.index.max().strftime('%Y-%m-%d') if regime_data is not None else None
    
    # Similarity data - look for any similar_days file
    similar_days_df = None
    if latest_date:
        similar_days_path = os.path.join(ticker_dir, f"similar_days_{latest_date}.csv")
        if os.path.exists(similar_days_path):
            similar_days_df = pd.read_csv(similar_days_path)
        else:
            # Try to find any similar_days file
            import glob
            similar_files = glob.glob(os.path.join(ticker_dir, "similar_days_*.csv"))
            if similar_files:
                similar_days_df = pd.read_csv(similar_files[-1])  # Use most recent

    # --- 2. Assemble HTML content ---
    print("Step 2: Assembling HTML content...")
    
    html = f"""
    <html>
    <head>
        <title>Comprehensive Analysis for {stock_symbol}</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1, h2, h3 {{ color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
            .section {{ margin-top: 40px; }}
            .plot-container {{ text-align: center; margin-top: 20px; }}
            .table-sm th, .table-sm td {{ padding: .4rem; }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <h1 class="text-center">Comprehensive Analysis Report for {stock_symbol}</h1>
    """

    # --- Section: Correlation Analysis ---
    html += "<div class='section'><h2>1. Correlation Analysis</h2>"
    if corr_heatmap_b64:
        html += "<h3>Correlation Heatmap</h3>"
        html += f"<p>This heatmap visualizes the correlation between all {len(corr_matrix)} technical indicators. Red indicates a strong positive correlation, blue indicates a strong negative correlation, and white indicates no correlation.</p>"
        html += f"<div class='plot-container'><img src='data:image/png;base64,{corr_heatmap_b64}' class='img-fluid'></div>"
    else:
        html += "<p>Correlation heatmap not found.</p>"
    html += "</div>"
    
    # --- Section: Behavioral Pattern Analysis ---
    html += "<div class='section'><h2>2. Behavioral Pattern (Market Regime) Analysis</h2>"
    if regime_plot_b64 and regime_data is not None:
        html += "<h3>Market Regimes Over Time</h3>"
        html += "<p>The plot below shows the stock's closing price, with each point colored according to the market regime identified by K-Means clustering. This helps visualize when different market behaviors occurred.</p>"
        html += f"<div class='plot-container'><img src='data:image/png;base64,{regime_plot_b64}' class='img-fluid'></div>"
        
        # Regime Summary Table
        regime_summary = regime_data.groupby('regime')['Close'].pct_change().groupby(regime_data['regime']).agg(['mean', 'std', 'count'])
        regime_summary.columns = ['Mean Daily Return', 'Std Dev (Volatility)', 'Days in Regime']
        regime_summary['% of Total Days'] = (regime_summary['Days in Regime'] / len(regime_data) * 100).round(2)
        
        html += "<h3>Regime Characteristics Summary</h3>"
        html += "<p>The table summarizes the statistical properties of each identified regime, highlighting differences in average returns and volatility.</p>"
        html += create_html_table(regime_summary.sort_values('Mean Daily Return', ascending=False))
    else:
        html += "<p>Behavioral analysis data or plot not found.</p>"
    html += "</div>"

    # --- Section: Similarity Analysis ---
    html += "<div class='section'><h2>3. Similarity Analysis</h2>"
    if similar_days_df is not None:
        html += f"<h3>Days Similar to the Latest Trading Day ({latest_date})</h3>"
        html += f"<p>This table shows the top 10 historical trading days with the most similar technical indicator patterns to the market conditions on {latest_date}. The subsequent returns columns show how the market performed after those similar days.</p>"
        html += create_html_table(similar_days_df)
    else:
        html += f"<p>Similarity analysis data for the latest day ({latest_date}) not found. Please run <code>find_similar_days.py {latest_date} output/{stock_symbol}_analysis.csv</code> to generate it.</p>"
    html += "</div>"

    html += """
        </div>
    </body>
    </html>
    """

    # --- 3. Save the HTML report ---
    print("Step 3: Saving the HTML report...")
    output_path = os.path.join(ticker_dir, "comprehensive_report.html")
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"\n🎉 Report generation complete!")
    print(f"📁 View the report at: {output_path}")
    print(f"📁 All results organized in: {ticker_dir}/")


def main():
    """Main function to run the report generator."""
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1]
    else:
        stock_symbol = DEFAULT_STOCK_SYMBOL
        print(f"No stock symbol provided. Using default: {stock_symbol}")
    
    # Before generating the report, ensure the similarity file for the latest day exists.
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    regime_data_path = os.path.join(ticker_dir, "data_with_regimes.csv")
    if os.path.exists(regime_data_path):
        # Load the data and get the last date from the index
        # Use index_col=0 as the date column might be unnamed in the CSV
        regime_df = pd.read_csv(regime_data_path, index_col=0, parse_dates=True)
        regime_df.index.name = 'Date'
        latest_date = regime_df.index.max().strftime('%Y-%m-%d')
        
        similar_days_path = os.path.join(ticker_dir, f"similar_days_{latest_date}.csv")
        if not os.path.exists(similar_days_path):
            print(f"⚠️ Similarity file for latest date ({latest_date}) not found. Generating it now...")
            # Use the full file path for the analysis file
            analysis_file_path = f"output/{stock_symbol}_analysis.csv"
            os.system(f"python3 find_similar_days.py {latest_date} {analysis_file_path}")
    
    generate_report(stock_symbol)

if __name__ == "__main__":
    main()
