"""
Behavioral Pattern Analyzer (Hedge Fund Grade)

This script uses clustering algorithms to identify distinct market regimes or
behavioral patterns from technical indicator data.

-   Loads and cleans indicator data with robust header detection.
-   Applies PCA for dimensionality reduction and noise removal.
-   Uses StandardScaler (Z-Score) to handle outliers better than MinMax.
-   Applies K-Means clustering to group days into different "regimes."
-   Analyzes the characteristics of each regime (returns, volatility).
-   Calculates transition matrix for regime switching probabilities.
-   Visualizes the distribution of regimes over time with continuous coloring.
-   Saves the clustered data with regime labels for further analysis.

Version: 2.0 (Hedge Fund Grade)
- PCA for dimensionality reduction and collinearity removal
- StandardScaler (Z-Score) instead of MinMaxScaler for outlier robustness
- Transition matrix for Markov Chain analysis
- Annualized metrics for human-readable interpretation
- Continuous line coloring visualization
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Directory for output plots and data
BASE_OUTPUT_DIR = "analysis_results"
RANDOM_STATE = 42  # For reproducibility


def get_ticker_output_dir(stock_symbol):
    """Get ticker-specific output directory."""
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    os.makedirs(ticker_dir, exist_ok=True)
    return ticker_dir


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory for correlation, regimes, similarity."""
    analysis_dir = os.path.join(get_ticker_output_dir(stock_symbol), "analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    return analysis_dir


def load_analysis_data(file_path):
    """
    Robust data loader with dynamic header detection.
    
    Hedge Fund Grade: Sniffs header format instead of hardcoding skiprows.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return None
    
    try:
        print(f"🔄 Loading data from {file_path}...")
        
        # Sniff header to handle yfinance MultiIndex vs Standard CSV
        skip_rows = []
        try:
            with open(file_path, 'r') as f:
                _ = f.readline()
                second_line = f.readline()
            
            if "Ticker" in second_line or "Price" in second_line:
                skip_rows = [1, 2]
                print(f"   Detected multi-row header format, skipping rows {skip_rows}")
        except Exception as e:
            print(f"   ⚠️  Could not detect header format, using default: {e}")
        
        df = pd.read_csv(file_path, skiprows=skip_rows, parse_dates=True, index_col=0)
        df.index.name = 'Date'
        
        # Quick clean: remove rows with infinite values immediately
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        
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


def preprocess_features(df_indicators):
    """
    Hedge Fund Standard Preprocessing:
    1. Standardize (Z-Score) to handle outliers better than MinMax.
    2. PCA to reduce dimensionality and remove collinearity (noise).
    
    Financial data has fat tails (black swans). MinMaxScaler gets crushed by outliers
    (e.g., one day of 100% volatility makes normal days look like 0).
    StandardScaler (Z-Score) is more robust.
    
    Args:
        df_indicators (pandas.DataFrame): DataFrame with indicator columns.
    
    Returns:
        tuple: (df_pca, pca_model, scaler) - PCA-reduced DataFrame and models for inverse transform if needed.
    """
    print("Preprocessing: Standardizing and applying PCA...")
    
    # Replace infinite values and drop columns that are entirely NaN
    df_cleaned = df_indicators.replace([np.inf, -np.inf], np.nan).dropna(axis=1, how='all')
    
    # Drop any rows that still have NaNs
    df_cleaned = df_cleaned.dropna(axis=0, how='any')
    
    if df_cleaned.empty:
        raise ValueError("Dataset is empty after cleaning NaN/Inf values. Cannot perform clustering.")
    
    # 1. StandardScaler (Z-Score Normalization) - more robust to outliers
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_cleaned)
    
    # 2. PCA (Dimensionality Reduction)
    # We keep 95% of the variance, discarding the 5% pure noise
    pca = PCA(n_components=0.95, random_state=RANDOM_STATE)
    pca_data = pca.fit_transform(scaled_data)
    
    print(f"   ℹ️  PCA reduced features from {df_cleaned.shape[1]} to {pca_data.shape[1]} components.")
    print(f"   ℹ️  Explained variance: {pca.explained_variance_ratio_.sum()*100:.2f}%")
    
    # Return DataFrame for easier handling
    pca_df = pd.DataFrame(pca_data, index=df_cleaned.index)
    return pca_df, pca, scaler


def perform_clustering(df_pca, n_clusters):
    """
    Performs K-Means clustering on the PCA-reduced data.
    
    Args:
        df_pca (pandas.DataFrame): PCA-reduced indicator data.
        n_clusters (int): Number of regimes to identify.
    
    Returns:
        pandas.DataFrame: DataFrame with regime labels.
    """
    print(f"Performing K-Means clustering (k={n_clusters})...")
    
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
        clusters = kmeans.fit_predict(df_pca)
        
        df_clustered = pd.DataFrame(clusters, index=df_pca.index, columns=['regime'])
        print("✅ Clustering complete.")
        return df_clustered
    except Exception as e:
        print(f"❌ K-Means clustering failed: {e}")
        return pd.DataFrame()


def interpret_regimes(df_full, df_clustered):
    """
    Describe regimes using human-readable metrics (Returns, Volatility).
    
    Annualizes metrics for better human interpretation.
    
    Args:
        df_full (pandas.DataFrame): Full dataset with price data.
        df_clustered (pandas.DataFrame): DataFrame with regime labels.
    
    Returns:
        pandas.DataFrame: Summary statistics for each regime.
    """
    print("Analyzing regime characteristics...")
    
    df_analysis = df_full[['Close']].copy()
    df_analysis['Returns'] = df_analysis['Close'].pct_change()
    
    # Add Volatility (if available in original, else calculate rolling std)
    if 'volatility_atr' in df_full.columns:
        df_analysis['Volatility'] = df_full['volatility_atr']
    else:
        df_analysis['Volatility'] = df_analysis['Returns'].rolling(14).std()
    
    df_analysis = df_analysis.join(df_clustered).dropna()
    df_analysis['regime'] = df_analysis['regime'].astype(int)
    
    # Group by Regime
    summary = df_analysis.groupby('regime').agg({
        'Returns': ['mean', 'std'],
        'Volatility': 'mean',
        'Close': 'count'  # To count days
    })
    
    # Flatten columns
    summary.columns = ['Avg Daily Return', 'Return Std Dev', 'Avg Volatility', 'Days']
    
    # Annualize Returns/Vol for readability
    summary['Ann. Return'] = summary['Avg Daily Return'] * 252
    summary['Ann. Volatility'] = summary['Return Std Dev'] * (252**0.5)
    summary['% of Time'] = (summary['Days'] / summary['Days'].sum() * 100).round(2)
    
    # Add regime labels based on characteristics
    summary['Label'] = summary.apply(lambda row: 
        'High Volatility / Bearish' if row['Ann. Return'] < -0.10 and row['Ann. Volatility'] > 0.30 else
        'Low Volatility / Bullish' if row['Ann. Return'] > 0.10 and row['Ann. Volatility'] < 0.20 else
        'Moderate / Neutral' if -0.05 < row['Ann. Return'] < 0.05 else
        'High Volatility / Bullish' if row['Ann. Return'] > 0.10 else
        'Low Volatility / Bearish', axis=1)
    
    return summary.sort_values('Ann. Return', ascending=False)


def calculate_transition_matrix(df_clustered):
    """
    Calculates the probability of moving from Regime A to Regime B.
    
    Essential for Markov Chain analysis of markets. Shows market "memory" and stability.
    High diagonal values indicate stable regimes. Low diagonal values indicate unstable regimes.
    
    Args:
        df_clustered (pandas.DataFrame): DataFrame with regime labels.
    
    Returns:
        pandas.DataFrame: Transition probability matrix.
    """
    print("Calculating transition matrix...")
    
    df = df_clustered.copy()
    df['next_regime'] = df['regime'].shift(-1)
    df = df.dropna()
    
    # Create transition matrix (normalized by row to get probabilities)
    transitions = pd.crosstab(df['regime'], df['next_regime'], normalize='index')
    
    return transitions


def plot_regimes_map(df_full, df_clustered, stock_symbol):
    """
    Visualizes the Price vs Regimes with continuous line coloring.
    
    Creates a "snake chart" where the price line changes color as the regime changes.
    Also includes a strip chart (barcode) showing regime timeline.
    
    Args:
        df_full (pandas.DataFrame): Full dataset with price data.
        df_clustered (pandas.DataFrame): DataFrame with regime labels.
        stock_symbol (str): Stock symbol for title.
    """
    print("Generating plot of regimes over time...")
    
    df_plot = df_full[['Close']].join(df_clustered).dropna()
    df_plot['regime'] = df_plot['regime'].astype(int)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12), 
                                    gridspec_kw={'height_ratios': [3, 1]}, 
                                    sharex=True)
    
    # Upper Plot: Price colored by Regime (continuous line)
    # Create segments to color the line continuously
    points = np.array([mdates.date2num(df_plot.index), df_plot['Close']]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # Create a continuous line collection
    norm = plt.Normalize(df_plot['regime'].min(), df_plot['regime'].max())
    lc = LineCollection(segments, cmap='viridis', norm=norm)
    
    # Set the values used for colormapping
    lc.set_array(df_plot['regime'].values)
    lc.set_linewidth(2)
    line = ax1.add_collection(lc)
    
    ax1.autoscale_view()
    ax1.set_title(f'{stock_symbol}: Market Regimes (PCA + K-Means, k={df_plot["regime"].nunique()})', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price (₹)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Add Colorbar legend
    cbar = fig.colorbar(line, ax=ax1, label='Regime ID')
    cbar.set_ticks(np.unique(df_plot['regime']))
    
    # Lower Plot: Regime Strip Chart (Barcode)
    ax2.imshow(df_plot['regime'].values[np.newaxis, :], aspect='auto', cmap='viridis', 
               extent=[mdates.date2num(df_plot.index[0]), mdates.date2num(df_plot.index[-1]), 0, 1])
    ax2.set_yticks([])
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_title('Regime Timeline (Strip Chart)', fontsize=10)
    
    # Format Dates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    
    plt.tight_layout()
    
    # Save the plot
    analysis_dir = get_analysis_dir(stock_symbol)
    output_path = os.path.join(analysis_dir, "market_regimes_plot.png")
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"💾 Regime plot saved to {output_path}")
    plt.close(fig)


def main():
    """Main function to run the behavioral pattern analysis."""
    parser = argparse.ArgumentParser(
        description="Hedge Fund Grade Market Regime Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 04_behavioral_patterns.py analysis_results/RELIANCE.NS/data/RELIANCE.NS_analysis.csv
  python3 04_behavioral_patterns.py analysis_results/TCS.NS/data/TCS.NS_analysis.csv --clusters 4
  python3 04_behavioral_patterns.py analysis_results/INFY.NS/data/INFY.NS_analysis.csv --clusters 5
        """
    )
    parser.add_argument('file', nargs='?', help="Path to analysis CSV")
    parser.add_argument('--clusters', type=int, default=4, 
                        help="Number of regimes to identify (default: 4)")
    
    args = parser.parse_args()
    
    # Auto-find file if not provided
    file_path = args.file
    if not file_path:
        if os.path.exists(BASE_OUTPUT_DIR):
            for root, dirs, files in os.walk(BASE_OUTPUT_DIR):
                for file in files:
                    if file.endswith("_analysis.csv"):
                        file_path = os.path.join(root, file)
                        print(f"📁 Auto-detected file: {file_path}")
                        break
                if file_path:
                    break
    
    if not file_path:
        print("❌ No file provided/found.")
        print("   Usage: python3 04_behavioral_patterns.py <path_to_analysis.csv>")
        return
    
    stock_symbol = os.path.basename(file_path).split('_')[0] if '_' in os.path.basename(file_path) else os.path.basename(file_path).replace('.csv', '')
    print(f"\n📊 Analyzing Regimes for {stock_symbol}...")
    print("="*80)
    
    # 1. Load
    df_full = load_analysis_data(file_path)
    if df_full is None:
        return
    
    # 2. Feature Engineering (PCA + Scaling)
    df_indicators = get_indicator_columns(df_full)
    
    try:
        df_pca, pca_model, scaler = preprocess_features(df_indicators)
    except ValueError as e:
        print(f"❌ Preprocessing failed: {e}")
        return
    
    # 3. Clustering
    df_clustered = perform_clustering(df_pca, args.clusters)
    if df_clustered.empty:
        return
    
    # 4. Analysis
    regime_stats = interpret_regimes(df_full, df_clustered)
    transition_matrix = calculate_transition_matrix(df_clustered)
    
    # --- Output ---
    print("\n" + "="*80)
    print(f"📊 REGIME CHARACTERISTICS (Sorted by Annualized Return)")
    print("="*80)
    # Format for pretty printing
    display_cols = ['Ann. Return', 'Ann. Volatility', '% of Time', 'Label']
    display_df = regime_stats[display_cols].copy()
    display_df['Ann. Return'] = display_df['Ann. Return'].apply(lambda x: f"{x*100:.2f}%")
    display_df['Ann. Volatility'] = display_df['Ann. Volatility'].apply(lambda x: f"{x*100:.2f}%")
    display_df['% of Time'] = display_df['% of Time'].apply(lambda x: f"{x:.2f}%")
    print(display_df.to_string())
    
    print("\n" + "="*80)
    print(f"🔄 TRANSITION MATRIX (Probability of switching regimes)")
    print("="*80)
    print("   Rows = Current Regime, Columns = Next Regime")
    print("   High diagonal values = Stable regime")
    print("   Low diagonal values = Unstable regime")
    print("-"*80)
    print(transition_matrix.round(3).to_string())
    print("="*80)
    
    # 5. Visualization & Save
    plot_regimes_map(df_full, df_clustered, stock_symbol)
    
    # Save data
    analysis_dir = get_analysis_dir(stock_symbol)
    save_path = os.path.join(analysis_dir, "data_with_regimes.csv")
    df_out = df_full.join(df_clustered)
    df_out.to_csv(save_path)
    print(f"\n💾 Full data with regime labels saved to {save_path}")
    print(f"📁 All results saved in: {get_ticker_output_dir(stock_symbol)}/")


if __name__ == "__main__":
    main()
