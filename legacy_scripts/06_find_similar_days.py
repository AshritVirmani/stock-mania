"""
Pattern Matching Module to Find Similar Trading Days

This script analyzes the technical indicators from a stock analysis CSV file
to find trading days that have a similar "fingerprint" or pattern to a
specified target day.

-   Loads and normalizes indicator data using a consistent MinMaxScaler.
-   Calculates similarity scores (Euclidean Distance).
-   Identifies the top N most similar days.
-   Displays a comparison, including subsequent price performance, to evaluate
    if similar patterns lead to similar outcomes.
"""

import os
import sys
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import euclidean_distances
import numpy as np

# Directory for output plots and data
BASE_OUTPUT_DIR = "analysis_results"
DEFAULT_STOCK_FILE = "output/RELIANCE.NS_analysis.csv"  # Kept for backward compatibility


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


def find_analysis_file(stock_symbol):
    """Find analysis file in ticker-specific folder first, then fallback to old location."""
    # New location: ticker-specific folder
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    new_path = os.path.join(ticker_dir, f"{stock_symbol}_analysis.csv")
    if os.path.exists(new_path):
        return new_path
    
    # Old location: output folder (for backward compatibility)
    old_path = os.path.join("output", f"{stock_symbol}_analysis.csv")
    if os.path.exists(old_path):
        return old_path
    
    # Return new path as default (will be created there)
    return new_path


def load_analysis_data(file_path):
    """
    Loads stock analysis data from a CSV file, handling multi-row headers.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return None
    
    try:
        print(f"🔄 Loading data from {file_path}...")
        df = pd.read_csv(file_path, header=0, skiprows=[1, 2])
        first_col = df.columns[0]
        df = df.rename(columns={first_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        print(f"✅ Data loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"❌ Error loading or parsing data: {e}")
        return None


def get_indicator_columns(df):
    """
    Filters the DataFrame to get only the technical indicator columns.
    """
    indicator_prefixes = ['volume_', 'volatility_', 'trend_', 'momentum_', 'others_']
    indicator_cols = [col for col in df.columns if any(col.startswith(prefix) for prefix in indicator_prefixes)]
    return df[indicator_cols]


class PatternMatcher:
    """
    Handles normalization, distance calculation, and outcome analysis.
    """
    def __init__(self):
        # Store the scaler object to ensure consistent scaling
        self.scaler = MinMaxScaler()
        self.indicator_cols = None

    def fit_and_transform(self, df_indicators):
        """
        Fits the scaler on historical data and transforms it.
        Drops rows/columns containing NaNs/Infs during the fitting process.
        """
        print("Normalizing indicator data...")
        df_indicators_cleaned = df_indicators.replace([np.inf, -np.inf], np.nan)
        
        # Drop columns with all NaNs first
        df_indicators_cleaned = df_indicators_cleaned.dropna(axis=1, how='all')
        
        # Drop rows with any remaining NaNs (required for consistent distance calculation)
        df_indicators_cleaned = df_indicators_cleaned.dropna(axis=0, how='any')
        if df_indicators_cleaned.empty:
            raise ValueError("Dataset is empty after cleaning NaN/Inf values. Cannot perform normalization.")
            
        self.indicator_cols = df_indicators_cleaned.columns
        
        # Fit scaler on the cleaned historical data
        normalized_data = self.scaler.fit_transform(df_indicators_cleaned)
        
        print(f"✅ Scaler fitted on {len(self.indicator_cols)} features.")
        return pd.DataFrame(normalized_data, index=df_indicators_cleaned.index, columns=self.indicator_cols)

    def find_similar_days(self, df_normalized, target_date_str):
        """
        Finds days with the most similar indicator profiles to a target date.
        """
        try:
            target_date = pd.to_datetime(target_date_str)
            
            # 1. Get the target vector from the normalized data
            target_vector = df_normalized.loc[target_date].values.reshape(1, -1)
            
        except KeyError:
            # Note: The data frame df_normalized already excluded dates with NaNs.
            print(f"❌ Error: Target date '{target_date_str}' not found in the *clean* historical data.")
            return None
        print(f"Finding days similar to {target_date_str}...")
        
        # Calculate Euclidean distance from the target vector to all other vectors
        # Lower distance = Higher similarity
        distances = euclidean_distances(df_normalized.values, target_vector)
        
        # Create a Series with dates as index and distances as values
        similarity_scores = pd.Series(distances.flatten(), index=df_normalized.index, name='Similarity_Score(dist)')
        
        # Drop the target date itself (distance will be 0)
        similarity_scores = similarity_scores.drop(target_date)
        
        # Sort by distance (lower is more similar)
        return similarity_scores.sort_values()


def analyze_outcomes(df, similar_days_series, target_date, N=10):
    """
    Analyzes the price performance following the similar days.
    """
    outcomes = []
    
    # Convert target_date to datetime if it's a string
    target_date = pd.to_datetime(target_date)
    
    # Include the target date in the dates to analyze for the comparison info
    dates_to_analyze = [target_date] + similar_days_series.head(N).index.tolist()
    
    for date in dates_to_analyze:
        is_target = date == target_date
        
        try:
            # Get the index location of the date
            loc = df.index.get_loc(date)
            
            # Calculate future price changes (returns)
            price_today = df.iloc[loc]['Close']
            
            # Use iloc[loc + X] to get the price X trading days later
            # Use .get() with default=np.nan to handle index errors gracefully near end of data
            price_1d = df.iloc[loc + 1].get('Close') if loc + 1 < len(df) else np.nan
            price_5d = df.iloc[loc + 5].get('Close') if loc + 5 < len(df) else np.nan
            price_10d = df.iloc[loc + 10].get('Close') if loc + 10 < len(df) else np.nan
            
            # Calculate returns as percentage change from price_today
            ret_1d = (price_1d - price_today) / price_today * 100 if not np.isnan(price_1d) else np.nan
            ret_5d = (price_5d - price_today) / price_today * 100 if not np.isnan(price_5d) else np.nan
            ret_10d = (price_10d - price_today) / price_today * 100 if not np.isnan(price_10d) else np.nan
            
            row = {
                'Close Price': price_today,
                'Return_+1d_%': ret_1d,
                'Return_+5d_%': ret_5d,
                'Return_+10d_%': ret_10d
            }
            if not is_target:
                row['Similarity_Score(dist)'] = similar_days_series.loc[date]
                
            outcomes.append(pd.Series(row, name=date))
            
        except IndexError:
            # Handle cases where the date is too close to the end of the DataFrame
            continue
            
    outcomes_df = pd.DataFrame(outcomes)
    # Set the date index explicitly after creating the DataFrame
    outcomes_df.set_index(pd.to_datetime(dates_to_analyze[:len(outcomes_df)]), inplace=True)
    # Separate target row from similar days rows
    target_info = outcomes_df[outcomes_df.index == target_date]
    results = outcomes_df[outcomes_df.index != target_date]
    
    return target_info, results


def main():
    """
    Main function to run the similarity analysis.
    """
    # --- Argument Parsing ---
    if len(sys.argv) < 2:
        print("Usage: python3 find_similar_days.py <target_date_YYYY-MM-DD> [file_path]")
        print(f"Example: python3 find_similar_days.py 2024-03-15 {DEFAULT_STOCK_FILE}")
        return

    target_date = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_STOCK_FILE
    stock_symbol = os.path.basename(file_path).replace('_analysis.csv', '').replace('.csv', '')
    
    # --- Main Workflow ---
    df_full = load_analysis_data(file_path)
    if df_full is None:
        return
    df_indicators = get_indicator_columns(df_full)
    
    # Initialize and train the PatternMatcher
    matcher = PatternMatcher()
    try:
        df_normalized = matcher.fit_and_transform(df_indicators)
    except ValueError as e:
        print(f"❌ Error during normalization: {e}")
        return

    # 1. Find similar days (Euclidean distance)
    # Note: df_normalized already contains only clean historical data
    similarity_scores = matcher.find_similar_days(df_normalized, target_date)
    
    if similarity_scores is None:
        # Check if the target day was in the clean data, if not, report error
        if pd.to_datetime(target_date) not in df_full.index:
            print(f"❌ Error: Target date {target_date} is not a valid trading day in the source data.")
        elif pd.to_datetime(target_date) not in df_normalized.index:
            print(f"❌ Error: Target day {target_date} has missing or invalid indicator data and was excluded from analysis.")
        return
    
    # 2. Analyze outcomes for top 10 similar days
    target_info, results_df = analyze_outcomes(df_full, similarity_scores, target_date, N=10)
    
    # 3. Display Results
    print("\n" + "="*90)
    print(f"🎯 PATTERN MATCHING ANALYSIS FOR TARGET DAY: {target_date} ({stock_symbol})")
    print("="*90)
    
    print("\n[ Target Day Performance ]")
    print(target_info.to_string(float_format="%.4f"))
    
    print("\n[ Top 10 Most Similar Historical Days & Subsequent Performance ]")
    print("Lower Distance Score = More Similar Pattern")
    print(results_df.to_string(float_format="%.4f"))
    print("="*90)
    
    # 4. Save results to CSV in analysis subdirectory (no date suffix, always latest)
    analysis_dir = get_analysis_dir(stock_symbol)
    output_path = os.path.join(analysis_dir, "similar_days_latest.csv")
    results_df.to_csv(output_path)
    print(f"\n💾 Results saved to {output_path}")
    print(f"📁 All results saved in: {analysis_dir}/")


if __name__ == "__main__":
    main()
