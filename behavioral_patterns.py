"""
Behavioral Pattern Analyzer

This script uses clustering algorithms to identify distinct market regimes or
behavioral patterns from technical indicator data.

-   Loads and cleans indicator data.
-   Applies K-Means clustering to group days into different "regimes."
-   Analyzes the characteristics of each regime (e.g., average returns, volatility).
-   Visualizes the distribution of regimes over time.
-   Saves the clustered data with regime labels for further analysis.
"""

import os
import sys
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np

# Directory for output plots and data
BASE_OUTPUT_DIR = "analysis_results"
DEFAULT_STOCK_FILE = "output/RELIANCE.NS_analysis.csv"
N_CLUSTERS = 5  # Default number of clusters/regimes to identify


def get_ticker_output_dir(stock_symbol):
    """Get ticker-specific output directory."""
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def load_analysis_data(file_path):
    """Loads and preprocesses stock analysis data."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return None
    
    try:
        print(f"🔄 Loading data from {file_path}...")
        # Consistent data loading: read, rename date col, set as index
        df = pd.read_csv(file_path, header=0, skiprows=[1, 2])
        first_col = df.columns[0]
        df = df.rename(columns={first_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        print(f"✅ Data loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None


def get_indicator_columns(df):
    """Filters the DataFrame to get only indicator columns."""
    indicator_prefixes = ['volume_', 'volatility_', 'trend_', 'momentum_', 'others_']
    indicator_cols = [col for col in df.columns if any(col.startswith(prefix) for prefix in indicator_prefixes)]
    return df[indicator_cols]


def normalize_indicators(df_indicators):
    """
    Normalizes indicator data to a 0-1 scale after handling infs and NaNs.
    Returns the cleaned, normalized DataFrame and the columns used.
    """
    print("Normalizing indicator data for clustering...")
    
    # Replace infinite values and drop columns that are entirely NaN
    df_cleaned = df_indicators.replace([np.inf, -np.inf], np.nan).dropna(axis=1, how='all')
    
    # Drop any rows that still have NaNs after column-wise check (necessary if the NaNs are scattered)
    df_cleaned = df_cleaned.dropna(axis=0, how='any')
    
    if df_cleaned.empty:
        raise ValueError("Dataset is empty after cleaning NaN/Inf values. Cannot perform clustering.")
    
    scaler = MinMaxScaler()
    normalized_data = scaler.fit_transform(df_cleaned)
    
    normalized_df = pd.DataFrame(normalized_data, index=df_cleaned.index, columns=df_cleaned.columns)
    return normalized_df


def perform_clustering(df_normalized, n_clusters):
    """
    Performs K-Means clustering on the normalized indicator data.
    """
    print(f"Performing K-Means clustering to find {n_clusters} regimes...")
    # Suppress the K-Means warning about a high number of iterations if convergence is fast
    
    try:
        # Use a consistent random state for reproducibility
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        clusters = kmeans.fit_predict(df_normalized)
    except Exception as e:
        print(f"❌ K-Means clustering failed: {e}")
        return pd.DataFrame()
        
    df_clustered = pd.DataFrame(clusters, index=df_normalized.index, columns=['regime'])
    print("✅ Clustering complete.")
    return df_clustered


def analyze_regimes(df_full, df_clustered):
    """
    Analyzes the characteristics of each identified regime based on returns and volatility.
    """
    print("Analyzing regime characteristics...")
    
    # 1. Calculate daily returns on the full dataset
    df_full['daily_return'] = df_full['Close'].pct_change()
    
    # 2. Join regime labels with the full dataset on the index (Date)
    # This automatically handles alignment, keeping only dates present in both.
    df_analysis = df_full.join(df_clustered['regime'])
    
    # Ensure we only analyze periods that were successfully clustered
    df_analysis = df_analysis.dropna(subset=['regime'])
    df_analysis['regime'] = df_analysis['regime'].astype(int)  # Convert regime to integer type
    
    # Group by regime and calculate core summary statistics
    regime_analysis = df_analysis.groupby('regime')['daily_return'].agg(['mean', 'std', 'count'])
    regime_analysis.columns = ['Mean Daily Return', 'Std Dev (Volatility)', 'Days in Regime']
    
    # Calculate percentage of days in each regime
    regime_analysis['% of Total Days'] = (regime_analysis['Days in Regime'] / len(df_analysis) * 100).round(2)
    
    # Add average ATR (volatility measure) if the column exists in the original data
    if 'volatility_atr' in df_full.columns:
        avg_atr = df_analysis.groupby('regime')['volatility_atr'].mean().round(4)
        regime_analysis['Average ATR'] = avg_atr
    
    # Format return columns for readability
    regime_analysis['Mean Daily Return'] = (regime_analysis['Mean Daily Return'] * 100).round(4).astype(str) + '%'
    regime_analysis['Std Dev (Volatility)'] = (regime_analysis['Std Dev (Volatility)'] * 100).round(4).astype(str) + '%'
    
    return regime_analysis.sort_values(by='Days in Regime', ascending=False)


def plot_regimes_over_time(df_full, df_clustered, stock_symbol):
    """
    Creates a plot showing the price and the identified market regimes over time.
    """
    print("Generating plot of regimes over time...")
    
    # Join regime labels with the original Close price data
    df_plot = df_full[['Close']].join(df_clustered['regime'])
    df_plot = df_plot.dropna(subset=['regime'])
    
    fig, ax = plt.subplots(figsize=(18, 8))
    
    # Plot closing price
    ax.plot(df_plot.index, df_plot['Close'], color='gray', alpha=0.5, label='Close Price')
    
    # Create a scatter plot for the regimes, colored by regime
    # Ensure 'regime' is an integer for proper coloring
    scatter = ax.scatter(df_plot.index, df_plot['Close'], 
                         c=df_plot['regime'].astype(int), 
                         cmap='viridis', s=15, alpha=0.8,
                         label='Market Regime')
    
    # Formatting
    ax.set_title(f'Market Regimes Identified by Clustering for {stock_symbol} (K={df_plot["regime"].nunique()})', fontsize=16)
    ax.set_ylabel('Close Price (₹)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Improve date formatting on x-axis (show monthly or yearly tick marks dynamically)
    years = mdates.YearLocator()
    years_fmt = mdates.DateFormatter('\n%Y')
    months = mdates.MonthLocator()
    
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(years_fmt)
    ax.xaxis.set_minor_locator(months)
    fig.autofmt_xdate(rotation=0, ha='center')
    
    # Add a legend for the regimes
    legend_elements = scatter.legend_elements()
    ax.legend(handles=legend_elements[0], labels=[f"Regime {i}" for i in sorted(df_plot['regime'].unique())], title="Regimes")
    
    plt.tight_layout()
    
    # Save the plot in ticker-specific directory
    ticker_dir = get_ticker_output_dir(stock_symbol)
    output_path = os.path.join(ticker_dir, "market_regimes_plot.png")
    fig.savefig(output_path, dpi=300)
    print(f"💾 Regime plot saved to {output_path}")
    plt.close(fig)


def main():
    """Main function to run the behavioral pattern analysis."""
    # --- Argument Parsing ---
    file_path = DEFAULT_STOCK_FILE
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        file_path = sys.argv[1]
    else:
        file_arg = [arg for arg in sys.argv if arg.startswith('--file=')]
        if file_arg:
            file_path = file_arg[0].split('=')[1]
        
    print(f"Analyzing file: {file_path}")
    n_clusters_arg = [arg for arg in sys.argv if arg.startswith('--clusters=')]
    n_clusters = int(n_clusters_arg[0].split('=')[1]) if n_clusters_arg else N_CLUSTERS
    
    stock_symbol = os.path.basename(file_path).replace('_analysis.csv', '').replace('.csv', '')
    if not stock_symbol:
        print("❌ Error: Could not determine stock symbol from file path.")
        return

    # --- Main Workflow ---
    df_full = load_analysis_data(file_path)
    if df_full is None:
        return
        
    df_indicators = get_indicator_columns(df_full)
    
    try:
        df_normalized = normalize_indicators(df_indicators)
    except ValueError as e:
        print(f"❌ Normalization failed: {e}")
        return
        
    df_clustered = perform_clustering(df_normalized, n_clusters)
    if df_clustered.empty:
        return
    
    # Add regime labels back to the full dataset for saving
    df_full_with_regimes = df_full.join(df_clustered)
    
    # Analyze the regimes
    regime_summary = analyze_regimes(df_full, df_clustered)
    
    print("\n" + "="*80)
    print(f"📈 REGIME ANALYSIS SUMMARY ({stock_symbol}, K={n_clusters})")
    print("="*80)
    print(regime_summary.to_string())
    print("="*80)
    
    # Plot the results
    plot_regimes_over_time(df_full, df_clustered, stock_symbol)
    
    # Save the full dataset with regime labels in ticker-specific directory
    ticker_dir = get_ticker_output_dir(stock_symbol)
    output_path_csv = os.path.join(ticker_dir, "data_with_regimes.csv")
    df_full_with_regimes.to_csv(output_path_csv)
    print(f"\n💾 Full data with regime labels saved to {output_path_csv}")
    print(f"📁 All results saved in: {ticker_dir}/")


if __name__ == "__main__":
    # If run standalone, it will attempt to find the default file
    if os.path.exists("output"):
        main()
    else:
        print("⚠️ Missing 'output' directory. Please run a data generation script first or use --file argument.")
