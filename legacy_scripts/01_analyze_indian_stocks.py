import argparse
import os
import pandas as pd
import ta
import yfinance as yf

# Base directory for analysis results
BASE_ANALYSIS_DIR = "analysis_results"


def fetch_stock_data(symbol, start_date=None):
    """
    Fetches historical stock data from Yahoo Finance.
    Fetches all available data from the stock's listing date if start_date is None.

    Args:
        symbol (str): The stock symbol to fetch (e.g., 'RELIANCE.NS').
        start_date (str, optional): The start date for the data in 'YYYY-MM-DD' format.
                                   If None, fetches all available historical data.

    Returns:
        pandas.DataFrame: A DataFrame with the stock data, or None if fetching fails.
    """
    print(f"Fetching data for {symbol}...")
    try:
        # Try to get listing date first
        listing_date_str = None
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if 'listDate' in info and info['listDate']:
                listing_date_str = info['listDate']
                print(f"  Stock listed on: {listing_date_str}")
        except Exception as e:
            print(f"  Could not fetch listing date: {e}")
        
        # If start_date is None, fetch all available historical data
        # Use a very early date (1990) to ensure we get all data
        if start_date is None:
            print("  Fetching all available historical data from listing date...")
            # Use 1990-01-01 as start to get maximum historical data
            # yfinance will return data from the actual listing date
            data = yf.download(symbol, start="1990-01-01", progress=False, auto_adjust=True)
        else:
            data = yf.download(symbol, start=start_date, progress=False, auto_adjust=True)
        
        if data.empty:
            print(f"No data found for symbol {symbol}. It might be delisted or an invalid symbol.")
            return None
        
        print(f"  Fetched {len(data)} days of data")
        print(f"  Date range: {data.index.min().date()} to {data.index.max().date()}")
        
        # Warn if data seems limited
        if len(data) < 100:
            print(f"  ⚠️  Warning: Only {len(data)} days of data. Some indicators may not work properly.")
            print(f"     (Most indicators need at least 50-200 days of data)")
        
        # yfinance column names are already in the correct format (Open, High, Low, Close, Volume)
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def analyze_stock(df):
    """
    Applies all technical analysis features to the stock data.

    Args:
        df (pandas.DataFrame): The DataFrame with stock data.

    Returns:
        pandas.DataFrame: DataFrame with all TA features added.
    """
    print("Applying technical analysis indicators...")
    df = ta.utils.dropna(df)
    df_ta = ta.add_all_ta_features(
        df, open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=True
    )
    return df_ta


def get_ticker_analysis_dir(symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_data_dir(symbol):
    """Get data subdirectory for main analysis CSV."""
    data_dir = os.path.join(get_ticker_analysis_dir(symbol), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


def save_to_csv(df, symbol):
    """
    Saves the DataFrame to a CSV file in the data/ subdirectory.

    Args:
        df (pandas.DataFrame): The DataFrame to save.
        symbol (str): The stock symbol, used for the filename.
    """
    data_dir = get_data_dir(symbol)
    filename = os.path.join(data_dir, f"{symbol}_analysis.csv")
    df.to_csv(filename)
    print(f"Analysis saved to {filename}")


def print_summary(df, symbol):
    """
    Prints a summary of the analysis.

    Args:
        df (pandas.DataFrame): The DataFrame with TA features.
        symbol (str): The stock symbol.
    """
    print(f"\n--- Analysis Summary for {symbol} ---")
    print(f"Date range: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Number of TA features: {len(df.columns) - 6}") # Original columns: O,H,L,C,Adj Close,V
    print("Last 5 days of data with a few TA indicators:")
    
    # Display a small subset of columns for brevity
    summary_cols = [
        'Close',
        'volume_obv', 
        'volatility_bbm',
        'trend_macd',
        'momentum_rsi'
    ]
    
    # Filter for columns that exist in the dataframe
    existing_summary_cols = [col for col in summary_cols if col in df.columns]
    
    print(df[existing_summary_cols].tail())
    print("---------------------------------------\n")


def process_stock(symbol, start_date=None):
    """
    Fetches, analyzes, and saves data for a single stock.
    
    Args:
        symbol (str): Stock symbol (e.g., 'RELIANCE.NS')
        start_date (str, optional): Start date in 'YYYY-MM-DD' format. If None, fetches all available data.
    """
    if not isinstance(symbol, str) or not symbol.endswith(".NS"):
        print(f"Invalid symbol format: '{symbol}'. Please use '.NS' suffix for Indian stocks (e.g., 'RELIANCE.NS').")
        return

    data = fetch_stock_data(symbol, start_date=start_date)
    if data is not None:
        analyzed_data = analyze_stock(data)
        save_to_csv(analyzed_data, symbol)
        print_summary(analyzed_data, symbol)


def main():
    """
    Main function to run the analysis.
    """
    parser = argparse.ArgumentParser(description="Perform technical analysis on Indian stocks.")
    parser.add_argument('stocks', nargs='*', help="One or more stock symbols (e.g., RELIANCE.NS TCS.NS).")
    parser.add_argument('--start-date', type=str, default=None,
                        help="Start date for data in 'YYYY-MM-DD' format. If not specified, fetches all available historical data from listing date.")
    args = parser.parse_args()

    if args.stocks:
        stocks_to_process = args.stocks
    else:
        # Default stocks if none are provided via command line
        default_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
        print("No stock symbols provided. Running analysis for default stocks:")
        print(", ".join(default_stocks))
        stocks_to_process = default_stocks
    
    # Display data range info
    if args.start_date:
        print(f"\n📅 Using custom start date: {args.start_date}")
    else:
        print(f"\n📅 Fetching ALL available historical data from listing date for each stock")
        print("   (This may take a few minutes for stocks with long histories)")
    
    for stock in stocks_to_process:
        process_stock(stock, start_date=args.start_date)

    # Interactive mode for user input after processing initial stocks
    while True:
        try:
            user_input = input("Enter a stock symbol to analyze (or 'quit' to exit): ").strip()
            if user_input.lower() == 'quit':
                break
            if user_input:
                process_stock(user_input, start_date=args.start_date)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    main()
