"""
Pattern Matching Module with Feature Fusion (Hedge Fund Grade)

This script uses "Feature Fusion" to find similar trading days by combining:
1. Price Action (The "What"): Candle DNA - body size, wicks, volume patterns
2. Mathematical Context (The "Where"): Indicator state - RSI, MACD, Bollinger Bands

Features:
- Engineers "Candle DNA" features (body size, wick ratios, relative volume)
- Uses pattern window (last N days) for price action sequence matching
- Combines math indicators (single day) with price action sequence
- Generates "Spaghetti Plot" showing future path projections
- Calculates win rate and average return statistics

Version: 2.0 (Hedge Fund Grade)
- Feature Fusion: Price Action + Mathematical Context
- StandardScaler for robust normalization
- Future path projection visualization
- Data-driven expectancy calculations
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

# --- Configuration ---
BASE_OUTPUT_DIR = "analysis_results"


class PatternMatcher:
    """
    Wrapper class for pattern matching using NearestNeighbors.
    Provides fit_and_transform and kneighbors methods for compatibility.
    """
    def __init__(self, n_neighbors=10):
        self.scaler = StandardScaler()
        self.knn = None
        self.n_neighbors = n_neighbors
        self.fitted_data = None
    
    def fit_and_transform(self, df_indicators):
        """
        Fit the scaler and transform the indicator data.
        
        Args:
            df_indicators (pd.DataFrame): Indicator data to normalize
        
        Returns:
            pd.DataFrame: Normalized indicator data
        """
        # Fit scaler and transform
        normalized = self.scaler.fit_transform(df_indicators.values)
        self.fitted_data = normalized
        
        # Fit KNN on normalized data
        self.knn = NearestNeighbors(n_neighbors=self.n_neighbors)
        self.knn.fit(normalized)
        
        # Return as DataFrame with same index
        return pd.DataFrame(normalized, index=df_indicators.index, columns=df_indicators.columns)
    
    def kneighbors(self, X, n_neighbors=None):
        """
        Find k-nearest neighbors.
        
        Args:
            X: Query points (normalized)
            n_neighbors: Number of neighbors (defaults to self.n_neighbors)
        
        Returns:
            tuple: (distances, indices)
        """
        if self.knn is None:
            raise ValueError("PatternMatcher must be fitted before calling kneighbors")
        
        if n_neighbors is None:
            n_neighbors = self.n_neighbors
        
        # Create temporary KNN with requested neighbors
        temp_knn = NearestNeighbors(n_neighbors=min(n_neighbors, len(self.fitted_data)))
        temp_knn.fit(self.fitted_data)
        
        return temp_knn.kneighbors(X)

# How many days of history to look at for the pattern? (e.g., match the last 3 days of shape)
PATTERN_WINDOW = 3
# How many similar historical instances to find?
N_NEIGHBORS = 10
# How many days into the future to project?
PROJECTION_DAYS = 10


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory."""
    path = os.path.join(BASE_OUTPUT_DIR, stock_symbol, "analysis")
    os.makedirs(path, exist_ok=True)
    return path


def load_and_prep_data(file_path):
    """
    Loads data and engineers 'Candle DNA' features (Price Action).
    
    Args:
        file_path (str): Path to analysis CSV file.
    
    Returns:
        pandas.DataFrame: DataFrame with Price Action features added.
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None

    try:
        # Sniff header for dynamic detection
        with open(file_path, 'r') as f:
            _ = f.readline()
            h2 = f.readline()
        skip = [1, 2] if ("Ticker" in h2 or "Price" in h2) else []
        
        df = pd.read_csv(file_path, skiprows=skip, index_col=0, parse_dates=True)
        df.index.name = 'Date'
        
        # --- 1. Engineer Price Action Features (The "Candle DNA") ---
        # Body Size relative to range (Is it a Doji or a Marubozu?)
        df['PA_Body_Size'] = abs(df['Close'] - df['Open']) / (df['High'] - df['Low'] + 1e-8)  # Add small epsilon to avoid division by zero
        
        # Wick Ratios (Is there buying pressure from below?)
        body_min = pd.concat([df['Open'], df['Close']], axis=1).min(axis=1)
        body_max = pd.concat([df['Open'], df['Close']], axis=1).max(axis=1)
        df['PA_Lower_Wick'] = (body_min - df['Low']) / (df['High'] - df['Low'] + 1e-8)
        df['PA_Upper_Wick'] = (df['High'] - body_max) / (df['High'] - df['Low'] + 1e-8)
        
        # Relative Volume (Is this move significant?)
        # We use a 20-day rolling median for volume baseline
        df['PA_RVOL'] = df['Volume'] / (df['Volume'].rolling(20).median() + 1e-8)
        
        # Returns (The shape of the trend)
        df['PA_Return'] = df['Close'].pct_change()
        
        # Drop NaN created by rolling/pct_change
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"✅ Data loaded and Price Action features engineered. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"❌ Data Load Error: {e}")
        return None


def get_feature_vector(df, target_idx):
    """
    Constructs a specific feature vector combining Math + Price Action.
    
    Args:
        df (pandas.DataFrame): Full dataset with indicators and PA features.
        target_idx (int): Index position of target date.
    
    Returns:
        tuple: (full_vector, math_cols, pa_cols) or (None, None, None) if insufficient history.
    """
    target_date = df.index[target_idx]
    
    # 1. Mathematical Context (Indicators) - Single Day Snapshot
    # Select key indicators that define "Context"
    math_cols = [c for c in df.columns if any(x in c.lower() for x in ['rsi', 'macd', 'bollinger_pband', 'bollinger_hband', 'bollinger_lband'])]
    if not math_cols:
        # Fallback to Close if no indicators found
        math_cols = ['Close']
    
    # Ensure all math columns exist
    math_cols = [c for c in math_cols if c in df.columns]
    if not math_cols:
        math_cols = ['Close']
    
    math_vector = df.iloc[target_idx][math_cols].values
    
    # 2. Price Action Sequence (Last N days of candle shapes)
    pa_cols = ['PA_Body_Size', 'PA_Lower_Wick', 'PA_Upper_Wick', 'PA_RVOL', 'PA_Return']
    
    # We flatten the last N rows of PA data into a single 1D vector
    # e.g. [Day1_Body, Day1_Wick, ... Day3_Body, Day3_Wick]
    start_pos = target_idx - PATTERN_WINDOW + 1
    if start_pos < 0:
        return None, None, None  # Not enough history
    
    pa_vector = df.iloc[start_pos : target_idx + 1][pa_cols].values.flatten()
    
    # Combine them
    full_vector = np.concatenate([math_vector, pa_vector])
    
    return full_vector, math_cols, pa_cols


def build_search_space(df, math_cols, pa_cols):
    """
    Prepares the entire historical dataset in the same Vector format as the target.
    
    Args:
        df (pandas.DataFrame): Full dataset.
        math_cols (list): List of mathematical indicator column names.
        pa_cols (list): List of Price Action column names.
    
    Returns:
        tuple: (vectors_array, valid_indices) - Feature matrix and corresponding DataFrame indices.
    """
    vectors = []
    valid_indices = []
    
    # We can only start searching after we have enough history for the window
    # And we stop before the end to ensure we don't look-ahead or crash on the last day
    for i in range(PATTERN_WINDOW, len(df)):
        # Math part
        math_v = df.iloc[i][math_cols].values
        
        # PA part
        pa_v = df.iloc[i - PATTERN_WINDOW + 1 : i + 1][pa_cols].values.flatten()
        
        full_v = np.concatenate([math_v, pa_v])
        vectors.append(full_v)
        valid_indices.append(i)
    
    return np.array(vectors), valid_indices


def visualize_projections(df, similar_indices, target_date, stock_symbol, output_dir):
    """
    Plots the 'Spaghetti Chart' - The target path vs the historical similar paths.
    
    Args:
        df (pandas.DataFrame): Full dataset with price data.
        similar_indices (list): List of DataFrame indices for similar days.
        target_date (pd.Timestamp): Target date to analyze.
        stock_symbol (str): Stock symbol for title.
        output_dir (str): Directory to save the plot.
    
    Returns:
        list: List of future returns for statistics.
    """
    print("Generating Spaghetti Plot (Future Path Projection)...")
    
    plt.figure(figsize=(14, 8))
    
    # 1. Plot Target History (The "Ask")
    # Get recent price action leading up to target
    target_loc = df.index.get_loc(target_date)
    lookback = 20
    target_slice = df.iloc[target_loc - lookback : target_loc + 1]['Close']
    
    # Re-index to relative days (0 = Today)
    rel_indices = range(-lookback, 1)
    
    # Plot Target (Thick Black Line)
    # Normalize to % change so we can compare price levels
    base_price = target_slice.iloc[-1]
    norm_target = (target_slice / base_price - 1) * 100
    
    plt.plot(rel_indices, norm_target, color='black', linewidth=3, 
             label=f'Current Context ({target_date.date()})', zorder=10)
    
    # 2. Plot Historical Analogs (The "Answers")
    future_returns = []
    
    print(f"   🔍 Found {len(similar_indices)} historical analogs. Projecting future...")
    
    for idx in similar_indices:
        # We ignore the match if it's the target date itself
        if df.index[idx] == target_date:
            continue
        
        # Get the history AND future of the match
        # History: -20 days. Future: +10 days.
        start_hist = idx - lookback
        end_fut = idx + PROJECTION_DAYS
        
        if end_fut >= len(df):
            continue  # Skip if match is too recent to have a future
        
        analog_slice = df.iloc[start_hist : end_fut + 1]['Close']
        match_date = df.index[idx]
        
        # Normalize to the "Match Day" price (Day 0)
        match_base_price = df.iloc[idx]['Close']
        norm_analog = (analog_slice / match_base_price - 1) * 100
        
        # Plot (Thin colored lines)
        plt.plot(range(-lookback, PROJECTION_DAYS + 1), norm_analog, alpha=0.3, linewidth=1.5)
        
        # Store the future return (Day +10) for statistics
        future_return = norm_analog.iloc[-1]
        future_returns.append(future_return)
    
    # 3. Plot Average Projection (The "Mean Path")
    if future_returns:
        avg_ret = np.mean(future_returns)
        win_rate = sum(x > 0 for x in future_returns) / len(future_returns)
        
        title = (f"Pattern Projection: {stock_symbol}\n"
                 f"Based on {len(similar_indices)} similar days (Fusion: Math + Price Action)\n"
                 f"Expected Move ({PROJECTION_DAYS} days): {avg_ret:.2f}% | Win Rate: {win_rate:.0%}")
        
        plt.title(title, fontsize=14, fontweight='bold')
    
    plt.axvline(x=0, color='black', linestyle='--', alpha=0.5, label="Today")
    plt.axhline(y=0, color='black', linewidth=0.5)
    plt.xlabel("Days (Relative to Signal)", fontsize=12)
    plt.ylabel("Price Change (%)", fontsize=12)
    plt.legend(loc='upper left', fontsize=9)
    plt.grid(True, alpha=0.3)
    
    # Save
    output_path = os.path.join(output_dir, f"{stock_symbol}_future_projection_spaghetti.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"💾 Spaghetti plot saved to {output_path}")
    plt.close()
    
    return future_returns


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Price Action & Math Fusion Analyzer (Hedge Fund Grade)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 06_find_similar_days.py analysis_results/RELIANCE.NS/data/RELIANCE.NS_analysis.csv --date 2024-03-15
  python3 06_find_similar_days.py analysis_results/TCS.NS/data/TCS.NS_analysis.csv
        """
    )
    parser.add_argument('file', help="Path to analysis CSV")
    parser.add_argument('--date', type=str, default=None, 
                        help="Target date (YYYY-MM-DD). Default: Latest date")
    
    args = parser.parse_args()
    
    # Load
    df = load_and_prep_data(args.file)
    if df is None:
        return
    
    stock_symbol = os.path.basename(args.file).split('_')[0] if '_' in os.path.basename(args.file) else "STOCK"
    
    # Determine Target Date
    if args.date:
        target_date_input = pd.to_datetime(args.date)
        # Match by date only (ignore time component) since data may have timestamps
        # Find the first date that matches the target date
        matching_dates = df.index[df.index.date == target_date_input.date()]
        if len(matching_dates) == 0:
            print(f"❌ Target date {args.date} not in data.")
            print(f"   Available date range: {df.index.min().date()} to {df.index.max().date()}")
            return
        target_date = matching_dates[0]  # Use first match if multiple (shouldn't happen for daily data)
        target_idx = df.index.get_loc(target_date)
    else:
        target_idx = len(df) - 1
        target_date = df.index[target_idx]
    
    print(f"\n🧩 Analyzing Pattern for: {target_date.date()}...")
    print("="*80)
    
    # 1. Construct Vectors
    # Get vector for target
    target_vector, math_cols, pa_cols = get_feature_vector(df, target_idx)
    if target_vector is None:
        print("❌ Not enough history for pattern matching.")
        print(f"   Need at least {PATTERN_WINDOW} days of history before target date.")
        return
    
    print(f"   ✅ Feature vector constructed:")
    print(f"      - Math indicators: {len(math_cols)} features")
    print(f"      - Price Action sequence: {len(pa_cols)} features × {PATTERN_WINDOW} days = {len(pa_cols) * PATTERN_WINDOW} features")
    print(f"      - Total: {len(target_vector)} features")
    
    # Get vectors for all history
    search_matrix, valid_indices = build_search_space(df, math_cols, pa_cols)
    
    if len(search_matrix) == 0:
        print("❌ No valid search space found.")
        return
    
    print(f"   ✅ Search space: {len(search_matrix)} historical patterns")
    
    # 2. Normalize (StandardScaler - Critical for Euclidean Distance)
    # We fit on history, transform target.
    scaler = StandardScaler()
    search_matrix_scaled = scaler.fit_transform(search_matrix)
    target_vector_scaled = scaler.transform(target_vector.reshape(1, -1))
    
    print("   ✅ Features normalized using StandardScaler")
    
    # 3. Find Neighbors (KNN)
    knn = NearestNeighbors(n_neighbors=min(N_NEIGHBORS + 1, len(search_matrix)))  # +1 because the day itself might be found
    knn.fit(search_matrix_scaled)
    
    distances, indices = knn.kneighbors(target_vector_scaled)
    
    # Map local KNN indices back to DataFrame indices
    matched_df_indices = [valid_indices[i] for i in indices[0]]
    
    # Filter out the target date itself if present
    matched_df_indices = [idx for idx in matched_df_indices if df.index[idx] != target_date]
    
    print(f"   ✅ Found {len(matched_df_indices)} similar historical patterns")
    
    # 4. Visualize & Report
    output_dir = get_analysis_dir(stock_symbol)
    future_returns = visualize_projections(df, matched_df_indices, target_date, stock_symbol, output_dir)
    
    # 5. Display Statistics
    if future_returns:
        print("\n" + "="*80)
        print(f"🔮 PROJECTION STATISTICS (Next {PROJECTION_DAYS} Days)")
        print("="*80)
        print(f"Matches Found: {len(future_returns)}")
        print(f"   🟢 Bullish outcomes: {sum(x > 0 for x in future_returns)}")
        print(f"   🔴 Bearish outcomes: {sum(x < 0 for x in future_returns)}")
        print("-" * 80)
        print(f"Avg Return:  {np.mean(future_returns):.2f}%")
        print(f"Median Ret:  {np.median(future_returns):.2f}%")
        print(f"Max Upside:  {np.max(future_returns):.2f}%")
        print(f"Max Drawdown: {np.min(future_returns):.2f}%")
        print(f"Win Rate:    {(sum(x > 0 for x in future_returns) / len(future_returns) * 100):.1f}%")
        print("="*80)
        
        # Save results
        results_df = pd.DataFrame({
            'Date': [df.index[idx] for idx in matched_df_indices[:len(future_returns)]],
            'Future_Return_%': future_returns,
            'Distance': distances[0][:len(future_returns)]
        })
        results_df.set_index('Date', inplace=True)
        
        output_path = os.path.join(output_dir, f"similar_days_euclidean_{target_date.strftime('%Y-%m-%d')}.csv")
        results_df.to_csv(output_path)
        print(f"\n💾 Results saved to {output_path}")
    else:
        print("\n⚠️  No future projections available (matches too recent)")
    
    print(f"📁 All results saved in: {output_dir}/")


if __name__ == "__main__":
    main()
