"""
Interactive Indicator Visualization Dashboard

This script creates an interactive HTML dashboard using Plotly to visualize
the relationships between different technical indicators and market regimes.

-   Scans for available stock analysis files.
-   Allows the user to select a stock and two indicators for comparison.
-   Generates an interactive scatter plot where points are colored by market regime.
-   Saves the dashboard as a self-contained HTML file.
"""

import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Directories
INPUT_DIR = "output"
BASE_ANALYSIS_DIR = "analysis_results"


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def find_analysis_files():
    """Finds all available stock analysis CSV files."""
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Error: Input directory '{INPUT_DIR}' not found.")
        return []
    
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('_analysis.csv')]
    return sorted(files)


def load_data_with_regimes(stock_symbol):
    """
    Loads the analysis data and merges it with the regime labels.
    
    Args:
        stock_symbol (str): The stock symbol (e.g., 'RELIANCE.NS').

    Returns:
        pandas.DataFrame: A DataFrame with indicators and regime labels, or None.
    """
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    regime_file = os.path.join(ticker_dir, "data_with_regimes.csv")
    if not os.path.exists(regime_file):
        print(f"❌ Error: Regime file not found at '{regime_file}'")
        print("   Please run 'python3 behavioral_patterns.py' first.")
        return None
        
    print(f"🔄 Loading data with regimes from '{regime_file}'...")
    try:
        df = pd.read_csv(regime_file, index_col='Date', parse_dates=True)
        print("✅ Data loaded successfully.")
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None


def get_indicator_choices(df):
    """Returns a list of indicator columns for user selection."""
    indicator_prefixes = ['volume_', 'volatility_', 'trend_', 'momentum_', 'others_']
    return sorted([col for col in df.columns if any(col.startswith(prefix) for prefix in indicator_prefixes)])


def user_selection_menu(choices, title):
    """Generic menu for user selection."""
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50)
    for i, choice in enumerate(choices, 1):
        print(f"  {i:2}. {choice}")
    print("="*50)
    
    while True:
        try:
            selection = int(input(f"Select a number (1-{len(choices)}): "))
            if 1 <= selection <= len(choices):
                return choices[selection - 1]
            else:
                print("❌ Invalid selection. Please try again.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")


def create_interactive_dashboard(df, stock_symbol, indicator_x, indicator_y):
    """
    Generates and saves an interactive scatter plot dashboard.
    """
    print(f"🎨 Generating dashboard for {indicator_x} vs {indicator_y}...")
    
    fig = px.scatter(
        df,
        x=indicator_x,
        y=indicator_y,
        color='regime',
        color_continuous_scale=px.colors.sequential.Viridis,
        hover_name=df.index.strftime('%Y-%m-%d'),
        hover_data={'regime': True, 'Close': ':.2f'},
        title=f'{stock_symbol}: {indicator_x} vs. {indicator_y} (Colored by Market Regime)'
    )
    
    fig.update_layout(
        xaxis_title=indicator_x,
        yaxis_title=indicator_y,
        legend_title_text='Market Regime',
        title_font_size=20,
        title_x=0.5,
        template='plotly_white'
    )
    
    fig.update_traces(marker=dict(size=5, opacity=0.7))
    
    # Save the dashboard in ticker-specific directory
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    dashboard_dir = os.path.join(ticker_dir, "dashboards")
    if not os.path.exists(dashboard_dir):
        os.makedirs(dashboard_dir)
        
    filename = f"{indicator_x}_vs_{indicator_y}.html"
    output_path = os.path.join(dashboard_dir, filename)
    
    fig.write_html(output_path, full_html=True, include_plotlyjs='cdn')
    print(f"\n✅ Interactive dashboard saved to: {output_path}")
    print(f"📁 All results organized in: {ticker_dir}/")


def main():
    """Main function to run the dashboard generator."""
    # 1. Select Stock
    available_stocks = [f.replace('_analysis.csv', '') for f in find_analysis_files()]
    if not available_stocks:
        print("No analysis files found. Please run the analysis script first.")
        return
    
    stock_symbol = user_selection_menu(available_stocks, "Select a Stock")
    
    # 2. Load Data
    df = load_data_with_regimes(stock_symbol)
    if df is None:
        return
        
    # 3. Select Indicators
    indicator_choices = get_indicator_choices(df)
    indicator_x = user_selection_menu(indicator_choices, f"Select Indicator for X-axis")
    indicator_y = user_selection_menu(indicator_choices, f"Select Indicator for Y-axis")
    
    # 4. Create Dashboard
    create_interactive_dashboard(df, stock_symbol, indicator_x, indicator_y)


if __name__ == "__main__":
    main()
