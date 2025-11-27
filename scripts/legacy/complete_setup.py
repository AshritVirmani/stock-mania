"""
Complete Setup for New Ticker

This script runs the complete analysis workflow for a new stock ticker:
1. Fetch data and calculate all 86 indicators
2. Intrinsic value calculation
3. Correlation analysis
4. Behavioral pattern analysis (market regimes)
5. Similarity analysis
6. Standard Donchian MCPT backtest
7. Enhanced Donchian MCPT backtest (with Red Light filtering + pattern exits)
8. Drawdown analysis
9. Strategy comparison & regime risk analysis
10. Comprehensive report
11. Whale calendar (macro + micro strategy)
12. Professional whale chart (Bloomberg-style deep dive)
13. Final dashboard (Alpha Deck - Portfolio Manager's Monitor)

Usage:
    python3 complete_setup.py TICKER.NS
    python3 complete_setup.py TCS.NS
"""

import os
import sys
import subprocess
import pandas as pd
import yfinance as yf
import time
import logging
import pytz
from datetime import datetime

# Dhan API imports (optional - only used if user chooses Dhan)
try:
    from dhanhq import dhanhq
    DHAN_AVAILABLE = True
except ImportError:
    DHAN_AVAILABLE = False

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root (go up two levels from scripts/legacy/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

BASE_ANALYSIS_DIR = os.path.join(PROJECT_ROOT, "analysis_results")

# ==========================================
# DHAN API CONFIGURATION
# ==========================================
# Default Dhan API credentials (can be overridden via environment variables)
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "1109130648")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY0MzQ2ODkzLCJpYXQiOjE3NjQyNjA0OTMsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5MTMwNjQ4In0.iJstgOK6mjdWKAgqPEiB1nHC0qf66BiEm1Ktr4Hj238ywZa0jQ8_MnosdDyE_cAqox2w3eo48iEjxT9HhdmRsw")
DHAN_SCRIP_MASTER_PATH = os.getenv("DHAN_SCRIP_MASTER_PATH", "/Users/av/Downloads/chrome downloads/api-scrip-master-detailed.csv")


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_data_dir(stock_symbol):
    """Get data subdirectory for main analysis CSV."""
    data_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory for correlation, regimes, similarity."""
    analysis_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "analysis")
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    return analysis_dir


def get_backtests_dir(stock_symbol, strategy="standard"):
    """Get backtests subdirectory for strategy results."""
    backtests_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "backtests", strategy)
    if not os.path.exists(backtests_dir):
        os.makedirs(backtests_dir)
    return backtests_dir


def get_valuation_dir(stock_symbol):
    """Get valuation subdirectory for intrinsic value results."""
    valuation_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "valuation")
    if not os.path.exists(valuation_dir):
        os.makedirs(valuation_dir)
    return valuation_dir


def get_reports_dir(stock_symbol):
    """Get reports subdirectory for final reports."""
    reports_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir


# ==========================================
# DHAN API EXTRACTOR CLASSES
# ==========================================

class ScripMaster:
    """Handles Scrip Master CSV lookup for Dhan API."""
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.logger = logging.getLogger(__name__)
    
    def load(self):
        """Load the Scrip Master CSV file."""
        try:
            self.logger.info(f"Loading Scrip Master from {self.csv_path}...")
            cols = ['EXCH_ID', 'SECURITY_ID', 'SYMBOL_NAME', 'INSTRUMENT', 'SEGMENT', 'UNDERLYING_SYMBOL', 'DISPLAY_NAME']
            self.df = pd.read_csv(self.csv_path, usecols=cols, dtype={'SECURITY_ID': str})
            
            # Clean strings
            for col in ['SYMBOL_NAME', 'UNDERLYING_SYMBOL', 'DISPLAY_NAME', 'EXCH_ID', 'INSTRUMENT']:
                if col in self.df.columns:
                    self.df[col] = self.df[col].astype(str).str.strip().str.upper()
            
            self.logger.info(f"Scrip Master loaded. {len(self.df)} records.")
        except Exception as e:
            self.logger.error(f"Failed to load Scrip Master: {e}")
            self.df = None
    
    def search(self, symbol, exchange="NSE"):
        """Search for a symbol in the Scrip Master."""
        if self.df is None:
            return None
        
        symbol = symbol.strip().upper()
        exchange = exchange.strip().upper()
        
        # Filter by Exchange first
        matches = self.df[self.df['EXCH_ID'] == exchange]
        if matches.empty:
            return None
        
        # Remove .NS suffix if present for search
        search_symbol = symbol.replace('.NS', '')
        
        # 1. Try exact match on UNDERLYING_SYMBOL
        exact_underlying = matches[matches['UNDERLYING_SYMBOL'] == search_symbol]
        
        target_row = None
        
        if not exact_underlying.empty:
            # Prefer EQUITY
            equity_match = exact_underlying[exact_underlying['INSTRUMENT'] == 'EQUITY']
            if not equity_match.empty:
                target_row = equity_match.iloc[0]
            else:
                target_row = exact_underlying.iloc[0]
        else:
            # 2. Try exact match on SYMBOL_NAME or DISPLAY_NAME
            exact_name = matches[(matches['SYMBOL_NAME'] == search_symbol) | (matches['DISPLAY_NAME'] == search_symbol)]
            if not exact_name.empty:
                equity_match = exact_name[exact_name['INSTRUMENT'] == 'EQUITY']
                if not equity_match.empty:
                    target_row = equity_match.iloc[0]
                else:
                    target_row = exact_name.iloc[0]
            else:
                # 3. Try contains (Startswith preferred)
                starts = matches[matches['SYMBOL_NAME'].str.startswith(search_symbol, na=False) | 
                                matches['DISPLAY_NAME'].str.startswith(search_symbol, na=False)]
                candidates = starts if not starts.empty else matches[matches['SYMBOL_NAME'].str.contains(search_symbol, na=False)]
                
                if candidates.empty:
                    return None
                
                # Prioritize Equity/Index
                equity_cands = candidates[candidates['INSTRUMENT'] == 'EQUITY']
                if not equity_cands.empty:
                    target_row = equity_cands.iloc[0]
                else:
                    index_cands = candidates[candidates['INSTRUMENT'].isin(['INDEX', 'IDX'])]
                    if not index_cands.empty:
                        target_row = index_cands.iloc[0]
                    else:
                        target_row = candidates.iloc[0]
        
        if target_row is None:
            return None
        
        # Map details
        exch_id = target_row['EXCH_ID']
        instr = target_row['INSTRUMENT']
        
        return {
            "security_id": target_row['SECURITY_ID'],
            "symbol_name": target_row['SYMBOL_NAME'],
            "exchange_segment": self._get_segment(exch_id, instr),
            "instrument_type": instr
        }
    
    def _get_segment(self, exch_id, instr):
        """Map exchange and instrument to Dhan API segment."""
        if exch_id == "NSE":
            if instr == "EQUITY":
                return "NSE_EQ"
            elif instr in ["INDEX", "IDX"]:
                return "IDX"
            elif "FUT" in instr or "OPT" in instr:
                return "NSE_FNO"
            return "NSE_EQ"
        elif exch_id == "BSE":
            if instr == "EQUITY":
                return "BSE_EQ"
            return "BSE_FNO"
        elif exch_id == "MCX":
            return "MCX_COMM"
        return "NSE_EQ"


class DhanDataExtractor:
    """Extracts historical data from Dhan API."""
    
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.dhan = None
        self.logger = logging.getLogger(__name__)
    
    def login(self):
        """Initialize Dhan API connection."""
        try:
            self.dhan = dhanhq(self.client_id, self.access_token)
            self.logger.info("Dhan API initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Dhan API: {e}")
            raise
    
    def fetch_data(self, security_id, exchange_segment, instrument_type, from_date, to_date, interval="D"):
        """Fetch historical data from Dhan API."""
        if not self.dhan:
            self.logger.error("API not initialized. Call login() first.")
            return None
        
        self.logger.info(f"Fetching data for Security ID: {security_id} ({interval}) from {from_date} to {to_date}...")
        
        try:
            response = None
            
            # Choose method based on interval
            if interval.upper() in ['D', 'DAY', '1D']:
                response = self.dhan.historical_daily_data(
                    security_id=security_id,
                    exchange_segment=exchange_segment,
                    instrument_type=instrument_type,
                    expiry_code=0,
                    from_date=from_date,
                    to_date=to_date
                )
            else:
                # Assumes minute data for other intervals
                # The Dhan API intraday_minute_data may need interval parameter
                # Check API documentation for exact parameter name
                try:
                    response = self.dhan.intraday_minute_data(
                        security_id=security_id,
                        exchange_segment=exchange_segment,
                        instrument_type=instrument_type,
                        from_date=from_date,
                        to_date=to_date
                    )
                except TypeError:
                    # If interval parameter is required, try with interval
                    try:
                        response = self.dhan.intraday_minute_data(
                            security_id=security_id,
                            exchange_segment=exchange_segment,
                            instrument_type=instrument_type,
                            from_date=from_date,
                            to_date=to_date,
                            interval=interval
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to fetch intraday data: {e}")
                        return None
            
            if response.get('status') == 'failure':
                self.logger.error(f"API Error: {response.get('remarks', 'Unknown error')}")
                return None
            
            data = response.get('data', {})
            if not data:
                self.logger.warning("No data returned from API.")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            self.logger.info(f"Fetched {len(df)} rows.")
            return df
        except Exception as e:
            self.logger.error(f"Exception during fetch: {e}")
            return None


def fetch_dhan_data(stock_symbol, from_date=None, to_date=None):
    """
    Fetches historical stock data from Dhan API.
    Returns a pandas DataFrame in yfinance format or None if it fails.
    """
    if not DHAN_AVAILABLE:
        print("❌ Dhan API library (dhanhq) not available. Install with: pip install dhanhq")
        return None
    
    print(f"📡 Fetching data from Dhan API for {stock_symbol}...")
    
    # Remove .NS suffix for symbol search
    search_symbol = stock_symbol.replace('.NS', '')
    
    # Initialize Scrip Master
    if not os.path.exists(DHAN_SCRIP_MASTER_PATH):
        print(f"❌ Scrip Master file not found: {DHAN_SCRIP_MASTER_PATH}")
        print("   Please set DHAN_SCRIP_MASTER_PATH environment variable or update the path in the script.")
        return None
    
    scrip_master = ScripMaster(DHAN_SCRIP_MASTER_PATH)
    scrip_master.load()
    
    # Find Security ID
    scrip_info = scrip_master.search(search_symbol, "NSE")
    
    if not scrip_info:
        print(f"❌ Could not find symbol '{search_symbol}' in Scrip Master.")
        return None
    
    print(f"✅ Found: {scrip_info['symbol_name']} -> ID: {scrip_info['security_id']} ({scrip_info['exchange_segment']})")
    
    # Initialize Extractor
    try:
        extractor = DhanDataExtractor(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        extractor.login()
    except Exception as e:
        print(f"❌ Failed to initialize Dhan API: {e}")
        return None
    
    # Set date range (default to entire stock lifecycle if not specified)
    if to_date is None:
        to_date = datetime.now().strftime('%Y-%m-%d')
    if from_date is None:
        # Default to very early date to fetch entire stock lifecycle
        # Most Indian stocks were listed after 1990, so start from 1990
        from_date = "1990-01-01"
    
    # Print date range for debugging
    print(f"   📅 Date Range: {from_date} to {to_date} (entire stock lifecycle)")
    
    # Fetch Data - Dhan API may have limitations, so we'll try fetching in chunks if needed
    # First, try fetching all data at once
    df = extractor.fetch_data(
        security_id=scrip_info['security_id'],
        exchange_segment=scrip_info['exchange_segment'],
        instrument_type=scrip_info['instrument_type'],
        from_date=from_date,
        to_date=to_date,
        interval="D"  # Daily data
    )
    
    # If we got limited data, try chunking the requests
    # For full lifecycle data, we need to chunk by years to handle long histories
    if df is not None and not df.empty:
        # Calculate expected trading days (approximately 252 trading days per year)
        date_range_days = (datetime.strptime(to_date, '%Y-%m-%d') - datetime.strptime(from_date, '%Y-%m-%d')).days
        expected_trading_days = int(date_range_days * 0.7)  # ~70% of calendar days are trading days
        
        # If we got significantly less data than expected, try chunking
        if len(df) < expected_trading_days * 0.5:  # If we got less than 50% of expected days
            print(f"   ⚠️  Only got {len(df)} rows, expected ~{expected_trading_days} trading days")
            print(f"   📦 Attempting to fetch data in chunks (full lifecycle)...")
            
            # Try fetching in 1-year chunks to get entire lifecycle
            all_chunks = []
            current_date = datetime.strptime(from_date, '%Y-%m-%d')
            end_date = datetime.strptime(to_date, '%Y-%m-%d')
            
            while current_date < end_date:
                chunk_end = min(current_date + pd.DateOffset(years=1), end_date)
                chunk_from = current_date.strftime('%Y-%m-%d')
                chunk_to = chunk_end.strftime('%Y-%m-%d')
                
                print(f"   📥 Fetching chunk: {chunk_from} to {chunk_to}")
                chunk_df = extractor.fetch_data(
                    security_id=scrip_info['security_id'],
                    exchange_segment=scrip_info['exchange_segment'],
                    instrument_type=scrip_info['instrument_type'],
                    from_date=chunk_from,
                    to_date=chunk_to,
                    interval="D"
                )
                
                if chunk_df is not None and not chunk_df.empty:
                    all_chunks.append(chunk_df)
                    print(f"      ✅ Got {len(chunk_df)} rows")
                else:
                    print(f"      ⚠️  No data for this chunk (stock may not have been listed yet)")
                
                current_date = chunk_end
            
            # Combine all chunks
            if all_chunks:
                df = pd.concat(all_chunks, ignore_index=False)
                df = df[~df.index.duplicated(keep='first')]  # Remove duplicates
                df.sort_index(inplace=True)
                print(f"   ✅ Combined chunks: {len(df)} total rows (full lifecycle)")
    
    if df is None or df.empty:
        print("❌ No data returned from Dhan API.")
        return None
    
    # Convert Dhan API format to yfinance format
    # Dhan API typically returns: Date, Open, High, Low, Close, Volume
    # Map column names to match yfinance format
    column_mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'OPEN': 'Open',
        'HIGH': 'High',
        'LOW': 'Low',
        'CLOSE': 'Close',
        'VOLUME': 'Volume'
    }
    
    # Rename columns
    df.columns = [col.strip() for col in df.columns]
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)
    
    # Debug: Print available columns
    print(f"   Available columns: {list(df.columns)}")
    
    # Set date as index if present
    # Dhan API typically returns 'timestamp' column (Unix timestamp in milliseconds or seconds)
    date_cols = ['timestamp', 'Timestamp', 'TIMESTAMP', 'date', 'Date', 'DATE', 'start_Time', 'START_TIME', 'start_time']
    date_found = False
    for date_col in date_cols:
        if date_col in df.columns:
            try:
                # Try parsing as Unix timestamp (could be in seconds or milliseconds)
                timestamp_values = df[date_col]
                # Check if values are numeric (Unix timestamp)
                if pd.api.types.is_numeric_dtype(timestamp_values):
                    # If values are very large (> 1e12), they're likely in milliseconds
                    if timestamp_values.max() > 1e12:
                        df[date_col] = pd.to_datetime(timestamp_values, unit='ms')
                    else:
                        df[date_col] = pd.to_datetime(timestamp_values, unit='s')
                else:
                    # Try parsing as regular datetime string
                    df[date_col] = pd.to_datetime(df[date_col])
                
                df.set_index(date_col, inplace=True)
                df.index.name = 'Date'
                date_found = True
                print(f"   ✅ Using '{date_col}' as date column")
                break
            except Exception as e:
                print(f"   Warning: Could not parse date column '{date_col}': {e}")
                continue
    
    # If no date column found, check if index is already a datetime
    if not date_found:
        if isinstance(df.index, pd.DatetimeIndex):
            df.index.name = 'Date'
            date_found = True
        else:
            print(f"   ⚠️  No date column found. Creating sequential date index.")
            # Create a date range index (fallback)
            df.index = pd.date_range(start='2020-01-01', periods=len(df), freq='D')
            df.index.name = 'Date'
    
    # Ensure required columns exist
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing required columns: {missing_cols}")
        print(f"   Available columns: {list(df.columns)}")
        return None
    
    # Select only required columns and ensure proper data types
    df = df[required_cols].copy()
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort by date
    df.sort_index(inplace=True)
    
    # Remove any rows with NaN values
    df.dropna(inplace=True)
    
    # Format date output safely
    try:
        if isinstance(df.index, pd.DatetimeIndex):
            date_range = f"{df.index.min().date()} to {df.index.max().date()}"
        else:
            date_range = f"{len(df)} rows"
        print(f"  ✅ Fetched {len(df)} rows ({date_range})")
    except Exception as e:
        print(f"  ✅ Fetched {len(df)} rows")
    
    return df


def fetch_stock_data(stock_symbol):
    """
    Fetches historical stock data from Yahoo Finance.
    Returns a pandas DataFrame or None if it fails.
    """
    print(f"Fetching data for {stock_symbol}...")
    try:
        # Fetch all available historical data
        stock_data = yf.download(stock_symbol, start="1990-01-01", progress=False)
        
        if stock_data.empty:
            print(f"❌ No data found for {stock_symbol}.")
            return None
    except Exception as e:
        error_message = str(e).lower()
        print(f"❌ An error occurred while fetching data for {stock_symbol}:")
        print(f"   {e}")
        if "ssl" in error_message or "certificate" in error_message or "curl" in error_message:
            print("\n💡 HINT: This looks like a network SSL/Certificate issue.")
            print("   This can happen when the script is run in a sandboxed environment")
            print("   that blocks access to system security certificates.")
            print("   Try re-running the command with elevated network permissions.")
        return None

    print(f"  Fetched {len(stock_data)} rows ({stock_data.index.min().date()} to {stock_data.index.max().date()})")
    
    # Standardize column names, handling potential tuples
    # Convert to lowercase first, then capitalize for ta library compatibility
    new_columns = []
    for col in stock_data.columns:
        if isinstance(col, tuple):
            new_columns.append(col[0].lower() if col[0] else '')
        else:
            new_columns.append(str(col).lower())
    stock_data.columns = new_columns
    
    # Capitalize column names for ta library (Open, High, Low, Close, Volume)
    column_capitalization = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'adj close': 'Adj Close'
    }
    for old_col, new_col in column_capitalization.items():
        if old_col in stock_data.columns:
            stock_data.rename(columns={old_col: new_col}, inplace=True)
    
    return stock_data


def get_analysis_file_path(stock_symbol):
    """Constructs the full path for a stock's analysis CSV file."""
    output_dir = os.path.join("analysis_results", stock_symbol, "data")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.join(output_dir, f"{stock_symbol}_analysis.csv")


def create_analysis_file(stock_symbol):
    """
    Fetches stock data, calculates TA indicators, and saves to a CSV file.
    Returns the path to the file, or None if it fails.
    """
    print(f"\n{'='*80}")
    print("STEP 1: Fetching Data and Calculating Indicators")
    print(f"{'='*80}")
    print(f"📥 Fetching historical data for {stock_symbol}...")
    print("   (This may take a few minutes for stocks with long histories)")
    
    # Check if a recent analysis file already exists
    analysis_file_path = get_analysis_file_path(stock_symbol)
    if os.path.exists(analysis_file_path):
        # Check file age
        file_mod_time = os.path.getmtime(analysis_file_path)
        if (time.time() - file_mod_time) / 3600 < 24: # If less than 24 hours old
            print(f"✅ Using recent analysis file: {analysis_file_path}")
            return analysis_file_path

    # Proceed with fetching and analysis if no recent file
    stock_data = fetch_stock_data(stock_symbol)
    if stock_data is None:
        print("❌ Failed to generate analysis file")
        return None

    print("Applying technical analysis indicators...")
    
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '01_analyze_indian_stocks.py'), stock_symbol],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        data_dir = get_data_dir(stock_symbol)
        analysis_file = os.path.join(data_dir, f"{stock_symbol}_analysis.csv")
        
        if not os.path.exists(analysis_file):
            print(f"❌ Failed to generate analysis file")
            return False
        
        print(f"✅ Analysis file created: {analysis_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching data: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️  Setup cancelled by user")
        return False
    
    return analysis_file


def run_complete_setup(stock_symbol, use_dhan=False):
    """Run complete analysis setup for a new ticker."""
    print("\n" + "="*80)
    print(f"🚀 COMPLETE SETUP FOR {stock_symbol}")
    print("="*80)
    
    # Step 1: Fetch data and calculate indicators
    print("\n" + "="*80)
    print("STEP 1: Fetching Data and Calculating Indicators")
    print("="*80)
    print(f"📥 Fetching historical data for {stock_symbol}...")
    print("   (This may take a few minutes for stocks with long histories)")
    
    # Check if a recent analysis file already exists
    analysis_file_path = get_analysis_file_path(stock_symbol)
    if os.path.exists(analysis_file_path):
        # Check file age
        file_mod_time = os.path.getmtime(analysis_file_path)
        if (time.time() - file_mod_time) / 3600 < 24: # If less than 24 hours old
            print(f"✅ Using recent analysis file: {analysis_file_path}")
            analysis_file = analysis_file_path
        else:
            # File exists but is old, proceed with fetching
            analysis_file = None
    else:
        analysis_file = None

    # Proceed with fetching and analysis if no recent file
    if analysis_file is None:
        if use_dhan:
            stock_data = fetch_dhan_data(stock_symbol)
        else:
            stock_data = fetch_stock_data(stock_symbol)
        
        if stock_data is None:
            return None
        
        print("Applying technical analysis indicators...")
        
        try:
            # Import ta module to calculate indicators directly
            import ta
            
            # Ensure column names are capitalized correctly for ta library
            if 'open' in stock_data.columns:
                stock_data.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)
            
            # Calculate all TA indicators
            print("   Calculating 86 technical indicators...")
            df_ta = ta.add_all_ta_features(
                stock_data, 
                open="Open", 
                high="High", 
                low="Low", 
                close="Close", 
                volume="Volume", 
                fillna=True
            )
            
            # Save to analysis file
            data_dir = get_data_dir(stock_symbol)
            analysis_file = os.path.join(data_dir, f"{stock_symbol}_analysis.csv")
            df_ta.to_csv(analysis_file)
            
            print(f"✅ Analysis file created: {analysis_file}")
            print(f"   - {len(df_ta)} rows of data")
            print(f"   - {len(df_ta.columns)} columns (OHLCV + {len(df_ta.columns) - 5} indicators)")
            
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            # Fallback to subprocess method (for yfinance data)
            if not use_dhan:
                print("   Attempting fallback method...")
                try:
                    result = subprocess.run(
                        ['python3', os.path.join(SCRIPT_DIR, '01_analyze_indian_stocks.py'), stock_symbol],
                        check=True,
                        capture_output=False,
                        cwd=PROJECT_ROOT
                    )
                    data_dir = get_data_dir(stock_symbol)
                    analysis_file = os.path.join(data_dir, f"{stock_symbol}_analysis.csv")
                    
                    if not os.path.exists(analysis_file):
                        print(f"❌ Failed to generate analysis file")
                        return False
                    
                    print(f"✅ Analysis file created: {analysis_file}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Error in fallback method: {e}")
                    return False
                except KeyboardInterrupt:
                    print(f"\n⚠️  Setup cancelled by user")
                    return False
            else:
                print(f"❌ Failed to process Dhan data")
                return False
    else:
        # Use existing analysis file
        analysis_file = analysis_file_path
    
    # Step 2: Intrinsic Value Calculation
    print("\n" + "="*80)
    print("STEP 2: Intrinsic Value Calculation")
    print("="*80)
    print("💰 Calculating intrinsic value using multiple valuation methods...")
    print("   (Output will be displayed and saved to valuation folder)\n")
    try:
        # Use the calculate_intrinsic_value.py from scripts/utils (after reorganization)
        calc_script = os.path.join(PROJECT_ROOT, 'scripts', 'utils', 'calculate_intrinsic_value.py')
        valuation_dir = get_valuation_dir(stock_symbol)
        output_file = os.path.join(valuation_dir, "valuation_output.txt")
        
        # Run the script and capture output while displaying it
        result = subprocess.run(
            ['python3', calc_script, stock_symbol],
            check=True,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Display the output
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Save output to text file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n--- ERRORS/WARNINGS ---\n")
                f.write(result.stderr)
        
        print(f"\n✅ Intrinsic value calculation complete")
        print(f"   - Intrinsic value calculated using 5 methods (Graham, DCF, P/E, P/B, PEG)")
        print(f"   - Results saved to valuation/intrinsic_value.json")
        print(f"   - Terminal output saved to valuation/valuation_output.txt")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Intrinsic value calculation failed: {e}")
        if hasattr(e, 'stdout') and e.stdout:
            print(e.stdout)
        if hasattr(e, 'stderr') and e.stderr:
            print(e.stderr, file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Intrinsic value calculation error: {e}")
    
    # Step 3: Correlation Analysis
    print("\n" + "="*80)
    print("STEP 3: Correlation Analysis")
    print("="*80)
    try:
        subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '03_analyze_correlations.py'), analysis_file],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT
        )
        print("✅ Correlation analysis complete")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Correlation analysis failed: {e}")
    
    # Step 4: Behavioral Pattern Analysis
    print("\n" + "="*80)
    print("STEP 4: Behavioral Pattern Analysis (Market Regimes)")
    print("="*80)
    print("🔍 Identifying market regimes (this may take a few minutes)...")
    try:
        subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '04_behavioral_patterns.py'), analysis_file],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT
        )
        print("✅ Behavioral pattern analysis complete")
        print("   - Market regimes identified")
        print("   - Regime data saved")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Behavioral pattern analysis failed: {e}")
        print("   ⚠️  Enhanced Donchian will run without regime filtering")
    
    # Step 5: Identify Red Light Regime
    print("\n" + "="*80)
    print("STEP 4: Identifying Red Light Regime")
    print("="*80)
    analysis_dir = get_analysis_dir(stock_symbol)
    regime_file = os.path.join(analysis_dir, "data_with_regimes.csv")
    
    if os.path.exists(regime_file):
        try:
            subprocess.run(
                ['python3', os.path.join(SCRIPT_DIR, '05_identify_red_light_regime.py'), regime_file],
                check=True,
                capture_output=False,
                cwd=PROJECT_ROOT
            )
        except Exception as e:
            print(f"⚠️  Red Light identification failed: {e}")
    else:
        print("⚠️  Regime data not found. Skipping Red Light identification.")
    
    # Step 6: Similarity Analysis
    print("\n" + "="*80)
    print("STEP 5: Similarity Analysis")
    print("="*80)
    if os.path.exists(regime_file):
        try:
            # Get latest date for similarity analysis
            df = pd.read_csv(regime_file, index_col=0, parse_dates=True)
            latest_date = df.index.max().strftime('%Y-%m-%d')
            print(f"📅 Analyzing similarity for latest date: {latest_date}")
            subprocess.run(
                ['python3', os.path.join(SCRIPT_DIR, '06_find_similar_days.py'), analysis_file, '--date', latest_date],
                check=True,
                capture_output=True,
                cwd=PROJECT_ROOT
            )
            print(f"✅ Similarity analysis complete for {latest_date}")
        except Exception as e:
            print(f"⚠️  Similarity analysis failed: {e}")
    else:
        print("⚠️  Regime data not found. Skipping similarity analysis.")
    
    # Step 7: Standard Donchian MCPT Backtest
    print("\n" + "="*80)
    print("STEP 6: Standard Donchian MCPT Backtest")
    print("="*80)
    
    # Check data requirements first
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from walkforward_mcpt import load_stock_data
        ohlc_data = load_stock_data(analysis_file)
        if ohlc_data is not None:
            min_required_days = 730 + 182  # 2 years training + 6 months testing
            if len(ohlc_data) < min_required_days:
                print(f"⚠️  INSUFFICIENT DATA for walk-forward analysis")
                print(f"   Available: {len(ohlc_data)} days")
                print(f"   Required: {min_required_days} days (~3 years)")
                print(f"   {stock_symbol} is too new (recently listed)")
                print(f"\n💡 Running Simple Backtest instead (70/30 split)...")
                try:
                    subprocess.run(
                        ['python3', os.path.join(SCRIPT_DIR, '07a_simple_backtest_for_new_stocks.py'), analysis_file],
                        check=True,
                        capture_output=False,
                        cwd=PROJECT_ROOT
                    )
                    print("✅ Simple backtest complete")
                except Exception as e:
                    print(f"⚠️  Simple backtest failed: {e}")
                print(f"\n   → Walk-forward analysis requires ~3 years of data")
                print(f"   → Other analyses (correlation, regimes) are still available")
            else:
                print("📊 Running walk-forward analysis with Monte Carlo Permutation Test...")
                result = subprocess.run(
                    ['python3', os.path.join(SCRIPT_DIR, '07b_donchian_mcpt_backtest.py'), analysis_file],
                    check=True,
                    capture_output=False,
                    cwd=PROJECT_ROOT
                )
                print("✅ Standard Donchian MCPT backtest complete")
        else:
            print("⚠️  Could not load data. Skipping Donchian backtest.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Standard Donchian backtest failed: {e}")
    except Exception as e:
        print(f"⚠️  Error checking data requirements: {e}")
    
    # Step 8: Enhanced Donchian MCPT Backtest
    print("\n" + "="*80)
    print("STEP 7: Enhanced Donchian MCPT Backtest")
    print("="*80)
    
    # Check data requirements first
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from walkforward_mcpt import load_stock_data
        ohlc_data = load_stock_data(analysis_file)
        if ohlc_data is not None:
            min_required_days = 730 + 182  # 2 years training + 6 months testing
            if len(ohlc_data) < min_required_days:
                print(f"⚠️  INSUFFICIENT DATA for walk-forward analysis")
                print(f"   Available: {len(ohlc_data)} days")
                print(f"   Required: {min_required_days} days (~3 years)")
                print(f"   → Skipping Enhanced Donchian backtest (requires walk-forward)")
                print(f"   → Use simple backtest or wait for more data")
            else:
                print("📊 Running enhanced backtest with:")
                print("   - Red Light regime filtering")
                print("   - Pattern-based early exits (-2.0% threshold, 10 similar days)")
                print("   - Walk-forward MCPT")
                result = subprocess.run(
                    ['python3', os.path.join(SCRIPT_DIR, '08_donchian_enhanced_backtest.py'), analysis_file],
                    check=True,
                    capture_output=False,
                    cwd=PROJECT_ROOT
                )
                print("✅ Enhanced Donchian MCPT backtest complete")
        else:
            print("⚠️  Could not load data. Skipping Enhanced Donchian backtest.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Enhanced Donchian backtest failed: {e}")
    except Exception as e:
        print(f"⚠️  Error checking data requirements: {e}")
    
    # Step 8: Drawdown Analysis
    print("\n" + "="*80)
    print("STEP 8: Drawdown Analysis")
    print("="*80)
    backtests_standard_dir = get_backtests_dir(stock_symbol, "standard")
    walkforward_file = os.path.join(backtests_standard_dir, "results.csv")
    if os.path.exists(walkforward_file) and os.path.exists(regime_file):
        try:
            subprocess.run(
                ['python3', os.path.join(SCRIPT_DIR, '09_analyze_drawdowns.py'), walkforward_file, regime_file],
                check=True,
                capture_output=False,
                cwd=PROJECT_ROOT
            )
            print("✅ Drawdown analysis complete")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Drawdown analysis failed: {e}")
        except Exception as e:
            print(f"⚠️  Drawdown analysis error: {e}")
    else:
        print("⚠️  Required files not found. Skipping drawdown analysis.")
        if not os.path.exists(walkforward_file):
            print(f"   Missing: {walkforward_file}")
        if not os.path.exists(regime_file):
            print(f"   Missing: {regime_file}")
    
    # Step 9: Strategy Comparison & Regime Risk Analysis
    print("\n" + "="*80)
    print("STEP 9: Strategy Comparison & Regime Risk Analysis")
    print("="*80)
    print("📊 Comparing strategies and performing Bayesian regime risk analysis...")
    print("   (This includes probabilistic regime audit and filtering simulation)")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '10_compare_backtests.py'), stock_symbol],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Strategy comparison and regime risk analysis complete")
        print("   - Standard vs Enhanced strategy comparison")
        print("   - Bayesian regime risk analysis (if regime data available)")
        print("   - Filter impact equity curve generated")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Strategy comparison failed: {e}")
        print("   → This step can run independently later if needed")
    except Exception as e:
        print(f"⚠️  Strategy comparison error: {e}")
        print("   → This step can run independently later if needed")
    
    # Step 10: Generate Comprehensive Report
    print("\n" + "="*80)
    print("STEP 10: Generating Comprehensive Report")
    print("="*80)
    try:
        subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '11_generate_analysis_report.py'), stock_symbol],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT
        )
        print("✅ Comprehensive report generated")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Report generation failed: {e}")
    
    # Step 11: Generate Whale Calendar
    print("\n" + "="*80)
    print("STEP 11: Generating Whale Calendar (Macro + Micro Strategy)")
    print("="*80)
    print("📅 Generating complete strategy calendar with regime filtering...")
    print("   - Whale signals (volume, spread, CLV analysis)")
    print("   - Regime-aware filtering (Regime 3 = blocked, Regime 1 = high conviction)")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '12_whale_calendar.py'), analysis_file],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Whale calendar generated")
        print("   - Combines whale buy signals with regime data")
        print("   - Regime 3 (Crash) signals are blocked (⛔)")
        print("   - Regime 1 (Rally) signals get gold star (⭐)")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Whale calendar generation failed: {e}")
        print("   → This step can run independently later if needed")
    except Exception as e:
        print(f"⚠️  Whale calendar error: {e}")
        print("   → This step can run independently later if needed")
    
    # Step 12: Generate Professional Whale Chart
    print("\n" + "="*80)
    print("STEP 12: Generating Professional Whale Chart (Bloomberg-Style)")
    print("="*80)
    print("📊 Generating Bloomberg-style candlestick chart with whale signals...")
    print("   - Professional candlestick visualization")
    print("   - Whale signals overlaid on price action")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '14_whale_hunter_pro.py'), analysis_file],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Professional whale chart generated")
        print("   - Bloomberg-style candlestick chart")
        print("   - Whale signals (Ignition, Stealth, Trap) overlaid")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Professional whale chart generation failed: {e}")
        print("   → This step can run independently later if needed")
        print("   → Note: Requires mplfinance library (pip install mplfinance)")
    except Exception as e:
        print(f"⚠️  Professional whale chart error: {e}")
        print("   → This step can run independently later if needed")
    
    # Step 13: Dhan Intraday Analysis (if using Dhan API)
    if use_dhan:
        print("\n" + "="*80)
        print("STEP 13: Dhan API Intraday Analysis")
        print("="*80)
        print("📊 Running complete intraday analysis workflow...")
        print("   - Fetching 1-minute intraday data")
        print("   - Smart Money pattern analysis")
        print("   - Feature engineering & indicators")
        print("   - TA accuracy analysis")
        print("   - Pattern discovery")
        try:
            # Calculate date range for intraday data
            # Dhan API supports historical 1-minute data (fetching 6 years for consistency)
            from datetime import datetime, timedelta
            import pandas as pd
            end_date = datetime.now().strftime('%Y-%m-%d')
            # Fetch 6 years of intraday data (workaround for consistent availability)
            intraday_years = 6
            start_date_obj = datetime.now() - pd.DateOffset(years=intraday_years)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            print(f"   📅 Intraday date range: {start_date} to {end_date} ({intraday_years} years)")
            
            dhan_script = os.path.join(PROJECT_ROOT, 'scripts', 'dhan', '00_complete_setup_dhan.py')
            result = subprocess.run(
                ['python3', dhan_script, stock_symbol, '--start', start_date, '--end', end_date, '--interval', '1'],
                check=True,
                capture_output=False,
                cwd=PROJECT_ROOT
            )
            print("✅ Dhan intraday analysis complete")
            print("   - Intraday data fetched and analyzed")
            print("   - Smart Money patterns identified")
            print("   - All intraday results saved to intraday_analysis/")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Intraday analysis failed: {e}")
            print("   → This step can run independently later if needed")
            print("   → Run: python3 scripts/dhan/00_complete_setup_dhan.py {stock_symbol}")
        except Exception as e:
            print(f"⚠️  Intraday analysis error: {e}")
            print("   → This step can run independently later if needed")
    
    # Step 14: Generate Final Dashboard (Alpha Deck)
    print("\n" + "="*80)
    print("STEP 14: Generating Final Dashboard (Alpha Deck)")
    print("="*80)
    print("🏛️  Assembling Portfolio Manager's Monitor...")
    print("   - Unified dashboard combining all analyses")
    print("   - Strategy validation, whale signals, regimes, forecasts")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '13_generate_final_dashboard.py'), stock_symbol],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Final dashboard (Alpha Deck) generated")
        print("   - Portfolio Manager's unified view")
        print("   - All PhD-grade artifacts in one place")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Final dashboard generation failed: {e}")
        print("   → This step can run independently later if needed")
    except Exception as e:
        print(f"⚠️  Final dashboard error: {e}")
        print("   → This step can run independently later if needed")
    
    # Final Summary
    print("\n" + "="*80)
    print(f"✅ COMPLETE SETUP FINISHED FOR {stock_symbol}")
    print("="*80)
    
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    print(f"\n📁 All results saved in: {ticker_dir}/")
    print("\n📊 Key Files Generated:")
    print(f"   ✅ Analysis data: data/{stock_symbol}_analysis.csv")
    print(f"   ✅ Valuation: valuation/intrinsic_value.json")
    print(f"   ✅ Valuation output: valuation/valuation_output.txt")
    print(f"   ✅ Correlation heatmap: analysis/correlation_heatmap.png")
    print(f"   ✅ Market regimes: analysis/market_regimes_plot.png")
    print(f"   ✅ Regime data: analysis/data_with_regimes.csv")
    print(f"   ✅ Standard Donchian: backtests/standard/results.csv")
    print(f"   ✅ Enhanced Donchian: backtests/enhanced/results.csv")
    print(f"   ✅ Strategy comparison: reports/backtest_comparison.csv")
    print(f"   ✅ Filter impact curve: reports/filter_impact_equity_curve.png")
    print(f"   ✅ Comprehensive report: reports/comprehensive_report.html")
    print(f"   ✅ Whale calendar: analysis/complete_whale_calendar.html")
    print(f"   ✅ Professional whale chart: analysis/whale_entry_map_pro.png")
    if use_dhan:
        print(f"   ✅ Intraday data: intraday_analysis/data/{stock_symbol}_intraday_1min_raw.csv")
        print(f"   ✅ Intraday indicators: intraday_analysis/data/{stock_symbol}_intraday_1min_indicators.csv")
        print(f"   ✅ Smart Money patterns: intraday_analysis/pattern_analysis/smart_money/")
        print(f"   ✅ TA accuracy: intraday_analysis/results/")
    print(f"   ✅ Alpha Deck dashboard: {stock_symbol}_Alpha_Deck.html")
    
    print("\n💡 Quick Commands:")
    print(f"   # View simple summary:")
    print(f"   python3 donchian_simple_summary.py {ticker_dir}/backtests/standard/results.csv")
    print(f"   python3 donchian_simple_summary.py {ticker_dir}/backtests/enhanced/results.csv")
    print(f"   # View comprehensive report:")
    print(f"   open {ticker_dir}/reports/comprehensive_report.html")
    
    return True


def fetch_raw_data_only(stock_symbol, use_dhan=False):
    """
    Fetch only raw data files:
    1. Historical daily data (raw OHLCV)
    2. Intraday data (raw 1-minute OHLCV, if Dhan API available)
    3. Analysis CSV (with all 86 indicators for complete stock lifecycle)
    """
    print("\n" + "="*80)
    print("📥 RAW DATA DOWNLOAD MODE")
    print("="*80)
    print(f"📊 Stock Symbol: {stock_symbol}")
    print("\nThis will download:")
    print("  1. Historical daily data (raw OHLCV)")
    print("  2. Intraday data (raw 1-minute OHLCV, if Dhan API available)")
    print("  3. Analysis CSV (with 86 indicators for complete stock lifecycle)")
    print()
    
    # Step 1: Fetch daily data and create analysis CSV
    print("="*80)
    print("STEP 1: Fetching Daily Data & Creating Analysis CSV")
    print("="*80)
    print(f"📥 Fetching historical daily data for {stock_symbol}...")
    print("   (This will fetch the complete stock lifecycle)")
    
    if use_dhan:
        stock_data = fetch_dhan_data(stock_symbol)
    else:
        stock_data = fetch_stock_data(stock_symbol)
    
    if stock_data is None:
        print("❌ Failed to fetch daily data")
        return False
    
    print("   ✅ Daily data fetched")
    print(f"   Date range: {stock_data.index.min().date()} to {stock_data.index.max().date()}")
    print(f"   Total rows: {len(stock_data):,}")
    
    # Save raw daily data
    data_dir = get_data_dir(stock_symbol)
    raw_daily_file = os.path.join(data_dir, f"{stock_symbol}_daily_raw.csv")
    stock_data.to_csv(raw_daily_file)
    print(f"   💾 Raw daily data saved: {raw_daily_file}")
    
    # Generate JSON for daily data
    try:
        import json
        daily_json_file = os.path.join(data_dir, f"{stock_symbol}_daily_raw.json")
        
        # Convert timestamps to strings for JSON
        df_json = stock_data.copy().reset_index()
        # Handle various date column names or index
        date_col = None
        if 'Date' in df_json.columns:
            date_col = 'Date'
        elif 'index' in df_json.columns:
            date_col = 'index'
            
        if date_col:
            df_json[date_col] = df_json[date_col].astype(str)
            
        daily_data_dict = {
            'symbol': stock_symbol,
            'interval': '1D',
            'type': 'Daily',
            'date_range': {
                'start': str(stock_data.index.min().date()),
                'end': str(stock_data.index.max().date()),
                'total_rows': len(stock_data),
                'days_covered': (stock_data.index.max() - stock_data.index.min()).days
            },
            'data': df_json.to_dict('records')
        }
        
        with open(daily_json_file, 'w') as f:
            json.dump(daily_data_dict, f, indent=2)
        print(f"   💾 Raw daily JSON saved: {daily_json_file}")
        
    except Exception as e:
        print(f"   ⚠️  Failed to generate daily JSON: {e}")
    
    # Calculate indicators and save analysis CSV
    print("\n   Calculating 86 technical indicators...")
    try:
        import ta
        
        # Ensure column names are capitalized correctly for ta library
        if 'open' in stock_data.columns:
            stock_data.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)
        
        df_ta = ta.add_all_ta_features(
            stock_data, 
            open="Open", 
            high="High", 
            low="Low", 
            close="Close", 
            volume="Volume", 
            fillna=True
        )
        
        analysis_file = os.path.join(data_dir, f"{stock_symbol}_analysis.csv")
        df_ta.to_csv(analysis_file)
        
        # Generate JSON for analysis data
        try:
            analysis_json_file = os.path.join(data_dir, f"{stock_symbol}_analysis.json")
            
            # Convert timestamps to strings for JSON
            df_analysis_json = df_ta.copy().reset_index()
            # Handle various date column names or index
            date_col = None
            if 'Date' in df_analysis_json.columns:
                date_col = 'Date'
            elif 'index' in df_analysis_json.columns:
                date_col = 'index'
                
            if date_col:
                df_analysis_json[date_col] = df_analysis_json[date_col].astype(str)
                
            analysis_data_dict = {
                'symbol': stock_symbol,
                'interval': '1D',
                'type': 'Analysis (Technical Indicators)',
                'date_range': {
                    'start': str(df_ta.index.min().date()),
                    'end': str(df_ta.index.max().date()),
                    'total_rows': len(df_ta),
                    'days_covered': (df_ta.index.max() - df_ta.index.min()).days
                },
                'columns': list(df_ta.columns),
                'data': df_analysis_json.to_dict('records')
            }
            
            with open(analysis_json_file, 'w') as f:
                json.dump(analysis_data_dict, f, indent=2)
            print(f"   💾 Analysis JSON saved: {analysis_json_file}")
        except Exception as e:
            print(f"   ⚠️  Failed to generate analysis JSON: {e}")
        
        print(f"   ✅ Analysis CSV created: {analysis_file}")
        print(f"   - {len(df_ta)} rows of data")
        print(f"   - {len(df_ta.columns)} columns (OHLCV + {len(df_ta.columns) - 5} indicators)")
        
    except Exception as e:
        print(f"   ❌ Error calculating indicators: {e}")
        return False
    
    # Step 2: Fetch intraday data (if Dhan API available)
    if use_dhan:
        print("\n" + "="*80)
        print("STEP 2: Fetching Intraday Data (1-minute)")
        print("="*80)
        print("📥 Fetching historical intraday data...")
        
        try:
            from datetime import datetime
            import pandas as pd
            
            # Use subprocess to call the Dhan intraday fetcher script
            # This avoids import issues and uses the existing working script
            dhan_fetch_script = os.path.join(PROJECT_ROOT, 'scripts', 'dhan', '01_fetch_intraday_data.py')
            
            # Calculate date range (6 years - workaround for consistent data availability)
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date_obj = datetime.now() - pd.DateOffset(years=6)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            
            print(f"   📅 Date range: {start_date} to {end_date} (6 years)")
            print(f"   📡 Fetching intraday data...")
            
            # Define output directory
            intraday_data_dir = os.path.join("analysis_results", stock_symbol, "intraday_analysis", "data")
            # Ensure absolute path for subprocess
            abs_intraday_data_dir = os.path.join(PROJECT_ROOT, intraday_data_dir)
            os.makedirs(abs_intraday_data_dir, exist_ok=True)
            
            # Call the fetcher script via subprocess with 6-year minimum requirement
            result = subprocess.run(
                ['python3', dhan_fetch_script, stock_symbol, 
                 '--start', start_date, '--end', end_date, '--interval', '1',
                 '--output-dir', abs_intraday_data_dir, '--min-years', '6'],
                check=False,  # Don't fail if intraday fetch fails
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            
            # Check if data was saved (the script saves to analysis_results/{SYMBOL}/intraday_analysis/data/)
            
            # The script saves with this naming pattern
            raw_intraday_file = os.path.join(intraday_data_dir, f"{stock_symbol}_intraday_1min_raw.csv")
            json_file = os.path.join(intraday_data_dir, f"{stock_symbol}_intraday_1min_raw.json")
            
            # Also check alternative naming (without _raw suffix)
            alt_file = os.path.join(intraday_data_dir, f"{stock_symbol}_intraday_1min.csv")
            
            # Check for saved file (try both naming patterns)
            saved_file = None
            if os.path.exists(raw_intraday_file):
                saved_file = raw_intraday_file
            elif os.path.exists(alt_file):
                saved_file = alt_file
            
            if saved_file:
                # Load to verify and get stats
                df_intraday = pd.read_csv(saved_file, index_col=0, parse_dates=True)
                print(f"   ✅ Intraday data fetched and saved")
                print(f"   - {len(df_intraday):,} rows")
                print(f"   - Date range: {df_intraday.index.min()} to {df_intraday.index.max()}")
                print(f"   💾 Raw intraday CSV: {saved_file}")
                
                # Always generate JSON file (regenerate every time)
                try:
                    # Import and use the fetcher to save JSON
                    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts', 'dhan'))
                    # Import using importlib since module name starts with number
                    import importlib.util
                    fetch_module_path = os.path.join(PROJECT_ROOT, 'scripts', 'dhan', '01_fetch_intraday_data.py')
                    spec = importlib.util.spec_from_file_location("fetch_intraday_data", fetch_module_path)
                    fetch_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(fetch_module)
                    DhanIntradayFetcher = fetch_module.DhanIntradayFetcher
                    fetcher = DhanIntradayFetcher()
                    # Convert to DatetimeIndex with timezone if needed
                    if not isinstance(df_intraday.index, pd.DatetimeIndex):
                        df_intraday.index = pd.to_datetime(df_intraday.index)
                    # Localize to IST if timezone-naive
                    if df_intraday.index.tz is None:
                        df_intraday.index = df_intraday.index.tz_localize(pytz.timezone('Asia/Kolkata'))
                    json_file_path = fetcher.save_to_json(df_intraday, stock_symbol, '1', intraday_data_dir)
                    if json_file_path:
                        print(f"   💾 JSON export: {json_file_path}")
                except Exception as e:
                    print(f"   ⚠️  JSON export failed (non-critical): {e}")
            else:
                print("   ⚠️  No intraday data returned (may be outside API limits)")
                if result.stderr:
                    error_msg = result.stderr[:200] if len(result.stderr) > 200 else result.stderr
                    print(f"   Error: {error_msg}")
                
        except Exception as e:
            print(f"   ⚠️  Intraday data fetch failed: {e}")
            print("   → Daily data and analysis CSV are still available")
    else:
        print("\n" + "="*80)
        print("STEP 2: Intraday Data")
        print("="*80)
        print("   ⚠️  Intraday data requires Dhan API")
        print("   → Skipping intraday data fetch")
    
    # Summary
    print("\n" + "="*80)
    print("✅ RAW DATA DOWNLOAD COMPLETE")
    print("="*80)
    print(f"\n📁 Files saved in: analysis_results/{stock_symbol}/")
    print(f"   ✅ Raw daily data: data/{stock_symbol}_daily_raw.csv")
    print(f"   ✅ Raw daily JSON: data/{stock_symbol}_daily_raw.json")
    print(f"   ✅ Analysis CSV: data/{stock_symbol}_analysis.csv")
    print(f"   ✅ Analysis JSON: data/{stock_symbol}_analysis.json")
    if use_dhan:
        print(f"   ✅ Raw intraday CSV: intraday_analysis/data/{stock_symbol}_intraday_1min_raw.csv")
        print(f"   ✅ Raw intraday JSON: intraday_analysis/data/{stock_symbol}_intraday_1min_raw.json")
    
    return True


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 complete_setup.py TICKER.NS")
        print("\nExample:")
        print("  python3 complete_setup.py TCS.NS")
        print("  python3 complete_setup.py RELIANCE.NS")
        print("  python3 complete_setup.py INFY.NS")
        print("\nThis will run an interactive workflow with three options:")
        print("  1. Do you have Dhan API?")
        print("  2. Do you want to only have raw data?")
        print("  3. Complete setup (full analysis workflow)")
        return
    
    stock_symbol = sys.argv[1].strip().upper()
    
    # Ensure .NS suffix for Indian stocks
    if not stock_symbol.endswith('.NS'):
        print(f"⚠️  Adding .NS suffix for Indian stock")
        stock_symbol = stock_symbol + '.NS'
    
    print("\n" + "="*80)
    print("🚀 STOCK ANALYSIS WORKFLOW")
    print("="*80)
    print(f"📊 Stock Symbol: {stock_symbol}")
    
    # Question 1: Do you have Dhan API?
    print("\n" + "="*80)
    print("QUESTION 1: Do you have Dhan API?")
    print("="*80)
    use_dhan = False
    if DHAN_AVAILABLE:
        print("\nDhan API library is available.")
        print("Choose your data source:")
        print("  [y] Yes, use Dhan API (Daily + Intraday data)")
        print("  [n] No, use Yahoo Finance (Daily data only)")
        print()
        response = input("Use Dhan API? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            use_dhan = True
            print("\n✅ Selected: Dhan API")
        else:
            print("\n✅ Selected: Yahoo Finance")
    else:
        print("\n⚠️  Dhan API library (dhanhq) not installed.")
        print("   Will use Yahoo Finance for data fetching.")
        print("\n💡 To enable Dhan API:")
        print("   pip install dhanhq")
        print("   Then set DHAN_ACCESS_TOKEN environment variable")
        use_dhan = False
    
    # Question 2: Do you want to only have raw data?
    print("\n" + "="*80)
    print("QUESTION 2: What do you want to do?")
    print("="*80)
    print("\nChoose an option:")
    print("  [1] Download raw data only")
    print("      → Historical daily data (raw OHLCV)")
    print("      → Intraday data (raw 1-minute OHLCV, if Dhan API)")
    print("      → Analysis CSV (with 86 indicators)")
    print()
    print("  [2] Complete setup (full analysis workflow)")
    print("      → All raw data + indicators")
    print("      → Intrinsic value calculation")
    print("      → Correlation analysis")
    print("      → Behavioral patterns & market regimes")
    print("      → Backtests, reports, dashboards")
    print("      → Intraday analysis (if Dhan API)")
    print()
    response = input("Choose option (1 or 2): ").strip()
    
    if response == '1':
        # Raw data only mode
        print("\n" + "="*80)
        print("📥 RAW DATA MODE SELECTED")
        print("="*80)
        success = fetch_raw_data_only(stock_symbol, use_dhan=use_dhan)
        if not success:
            print("\n❌ Raw data download failed. Check errors above.")
            sys.exit(1)
    elif response == '2':
        # Complete setup mode
        print("\n" + "="*80)
        print("🚀 COMPLETE SETUP MODE SELECTED")
        print("="*80)
        run_complete_setup(stock_symbol, use_dhan=use_dhan)
    else:
        print("\n❌ Invalid option. Please choose 1 or 2.")
        sys.exit(1)


if __name__ == "__main__":
    main()

