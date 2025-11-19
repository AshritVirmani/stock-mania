"""
Correlation Analysis Module

This script provides functions to analyze and visualize the correlation between
technical analysis indicators from a stock analysis CSV file.

-   Loads data from analysis CSVs.
-   Calculates the correlation matrix for all indicator columns.
-   Generates and saves a heatmap of the correlation matrix.
-   Identifies and prints pairs of indicators with high correlation.
-   Exports the full correlation matrix to a CSV file.
"""

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Directory for output plots and data
BASE_OUTPUT_DIR = "analysis_results"
DEFAULT_STOCK_FILE = "output/RELIANCE.NS_analysis.csv"


def get_ticker_output_dir(stock_symbol):
    """Get ticker-specific output directory."""
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory for correlation, regimes, similarity."""
    analysis_dir = os.path.join(get_ticker_output_dir(stock_symbol), "analysis")
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    return analysis_dir


def load_analysis_data(file_path, tail=None):
    """
    Loads stock analysis data from a CSV file.
    Handles the specific multi-row header format.

    Args:
        file_path (str): The path to the input CSV file.
        tail (int, optional): If provided, loads only the last N rows of data.

    Returns:
        pandas.DataFrame: A DataFrame with the loaded data, or None if loading fails.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        print("Please run 'python3 analyze_indian_stocks.py' first to generate analysis files.")
        return None
    
    try:
        print(f"🔄 Loading data from {file_path}...")
        # The CSV has a multi-row header structure that needs specific parsing
        df = pd.read_csv(file_path, header=0, skiprows=[1, 2])
        
        # The first column is the date, rename it and set as index
        first_col = df.columns[0]
        df = df.rename(columns={first_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        if tail:
            print(f"🔄 Using last {tail} rows of data for analysis.")
            df = df.tail(tail)

        print(f"✅ Data loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"❌ Error loading or parsing data: {e}")
        return None


def get_indicator_columns(df):
    """
    Filters the DataFrame to get only the technical indicator columns.

    Args:
        df (pandas.DataFrame): The input DataFrame.

    Returns:
        pandas.DataFrame: A DataFrame containing only the indicator columns.
    """
    indicator_prefixes = ['volume_', 'volatility_', 'trend_', 'momentum_', 'others_']
    indicator_cols = [col for col in df.columns if any(col.startswith(prefix) for prefix in indicator_prefixes)]
    print(f"Found {len(indicator_cols)} indicator columns.")
    return df[indicator_cols]


def calculate_correlation_matrix(df_indicators):
    """
    Calculates the correlation matrix for the indicator DataFrame.
    Drops rows with any NaN values before calculation to ensure consistency.

    Args:
        df_indicators (pandas.DataFrame): DataFrame with indicator data.

    Returns:
        pandas.DataFrame: A correlation matrix.
    """
    print("Calculating correlation matrix...")
    
    # Explicitly drop rows with any NaNs to ensure the correlation is based on the same set of dates
    # for all pairs.
    df_cleaned = df_indicators.dropna()
    
    print(f"Dropped {len(df_indicators) - len(df_cleaned)} rows with missing indicator data.")
    
    if df_cleaned.empty:
        print("❌ Error: No clean data available for correlation calculation.")
        return pd.DataFrame()  # Return empty DataFrame
        
    correlation_matrix = df_cleaned.corr()
    
    return correlation_matrix


def plot_correlation_heatmap(correlation_matrix, stock_symbol):
    """
    Generates and saves improved correlation heatmaps.

    Args:
        correlation_matrix (pandas.DataFrame): The correlation matrix.
        stock_symbol (str): The stock symbol for titling the plot.
    """
    if correlation_matrix.empty:
        print("⚠️ Cannot plot heatmap: Correlation matrix is empty.")
        return
        
    analysis_dir = get_analysis_dir(stock_symbol)
    
    # Create filtered heatmap showing only significant correlations (more useful than full)
    print("Generating correlation heatmap (significant correlations only)...")
    create_filtered_heatmap(correlation_matrix, stock_symbol, analysis_dir)
    
    # Also save correlation matrix CSV
    csv_path = os.path.join(analysis_dir, "correlation_matrix.csv")
    correlation_matrix.to_csv(csv_path)
    print(f"💾 Correlation matrix saved to {csv_path}")


def create_filtered_heatmap(correlation_matrix, stock_symbol, ticker_dir, threshold=0.7):
    """
    Creates a filtered heatmap showing only significant correlations.
    This makes it easier to see important relationships.
    """
    # Create a filtered matrix (only show correlations above threshold)
    filtered_matrix = correlation_matrix.copy()
    
    # Mask correlations below threshold (set to 0 for visualization)
    # Keep self-correlation (1.0) for visual clarity (diagonal line)
    mask = (filtered_matrix.abs() < threshold)
    filtered_matrix[mask] = np.nan  # Use NaN to make these cells invisible/white in the heatmap
    
    # Count how many significant correlations we have (excluding self-correlation)
    significant_pairs = ((correlation_matrix.abs() >= threshold) & 
                        (correlation_matrix.abs() < 1.0)).sum().sum() // 2
    
    fig, ax = plt.subplots(figsize=(20, 18))
    
    sns.heatmap(
        filtered_matrix,
        annot=False,
        cmap='RdBu_r',
        center=0,
        vmin=-1, vmax=1,
        square=True,
        cbar_kws={'label': 'Correlation Coefficient', 'shrink': 0.8},
        ax=ax,
        linewidths=0.2,
        linecolor='gray',
        mask=filtered_matrix.isnull()  # Mask where we set NaN
    )
    
    ax.set_title(
        f'Significant Correlations (|r| ≥ {threshold}): {stock_symbol}\n'
        f'Showing {significant_pairs} significant indicator pairs',
        fontsize=14,
        pad=15,
        fontweight='bold'
    )
    
    ax.set_xlabel('Indicators', fontsize=11, fontweight='bold')
    ax.set_ylabel('Indicators', fontsize=11, fontweight='bold')
    
    plt.setp(ax.get_xticklabels(), rotation=90, ha='right', fontsize=7)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=7)
    
    plt.tight_layout()
    
    # Save as correlation_heatmap.png (no threshold suffix, single file)
    output_path = os.path.join(ticker_dir, "correlation_heatmap.png")
    fig.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"💾 Correlation heatmap saved to {output_path}")
    plt.close(fig)


def find_highly_correlated_pairs(correlation_matrix, threshold=0.95):
    """
    Finds and prints pairs of indicators with a correlation above a certain threshold.

    Args:
        correlation_matrix (pandas.DataFrame): The correlation matrix.
        threshold (float): The correlation threshold to consider as 'high'.
    """
    if correlation_matrix.empty:
        print("⚠️ Cannot find highly correlated pairs: Correlation matrix is empty.")
        return
        
    print(f"Finding highly correlated pairs (threshold > {threshold})...")
    # Create a boolean mask for correlations above the threshold
    # Use abs() to find both positive and negative high correlations
    high_corr_matrix = correlation_matrix.abs()
    
    # Unstack the matrix to get a Series of pairs
    # and drop correlations with 1.0 (self-correlation)
    sol = high_corr_matrix.unstack()
    sol = sol[sol > threshold]
    sol = sol[sol < 1.0]
    
    # Remove duplicate pairs (e.g., (A, B) and (B, A))
    # Note: Use a more efficient method to remove duplicates
    pairs = sol.index.tolist()
    unique_pairs = []
    seen = set()
    for ind1, ind2 in pairs:
        # Sort the tuple to ensure (A, B) and (B, A) are treated the same
        canonical_pair = tuple(sorted((ind1, ind2)))
        if canonical_pair not in seen:
            unique_pairs.append((ind1, ind2))
            seen.add(canonical_pair)

    print("\n" + "="*70)
    print(f"HIGHLY CORRELATED INDICATOR PAIRS (Correlation > {threshold})")
    print("="*70)
    
    if not unique_pairs:
        print("No pairs found above the threshold.")
    else:
        # Re-sort for cleaner presentation
        unique_pairs.sort()
        for ind1, ind2 in unique_pairs:
            corr_value = correlation_matrix.loc[ind1, ind2]
            print(f"- {ind1:<30} | {ind2:<30} | Correlation: {corr_value:.4f}")
            
    print("="*70)


def main():
    """
    Main function to run the correlation analysis.
    """
    # Determine which file to analyze
    file_path = DEFAULT_STOCK_FILE
    
    # Check if a file path was provided as the first argument
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        file_path = sys.argv[1]
    else:
        # Check for --file argument if not provided as positional
        file_arg = [arg for arg in sys.argv if arg.startswith('--file=')]
        if file_arg:
            file_path = file_arg[0].split('=')[1]
        
    print(f"Analyzing file: {file_path}")

    # Add argument for tailing data
    tail_arg = [arg for arg in sys.argv if arg.startswith('--tail=')]
    tail_value = int(tail_arg[0].split('=')[1]) if tail_arg else None
        
    # Extract stock symbol from filename for labeling outputs
    stock_symbol = os.path.basename(file_path).replace('_analysis.csv', '').replace('.csv', '')
    
    if not stock_symbol:
        print("❌ Error: Could not determine stock symbol from file path.")
        return

    # --- Main Workflow ---
    df = load_analysis_data(file_path, tail=tail_value)
    
    if df is not None:
        print("Step 1: Data loaded.")
        df_indicators = get_indicator_columns(df)
        print("Step 2: Indicator columns extracted.")
        
        # Calculate matrix and handle NaNs
        correlation_matrix = calculate_correlation_matrix(df_indicators)
        
        if correlation_matrix.empty:
            return
            
        print("Step 3: Correlation matrix calculated.")
        plot_correlation_heatmap(correlation_matrix, stock_symbol)
        print("Step 4: Heatmap plotted and saved.")
        find_highly_correlated_pairs(correlation_matrix, threshold=0.95)
        print("Step 5: Highly correlated pairs found.")
        print(f"\n✅ Correlation analysis complete.")
        print(f"📁 Results saved in: {get_ticker_output_dir(stock_symbol)}/")


if __name__ == "__main__":
    main()
