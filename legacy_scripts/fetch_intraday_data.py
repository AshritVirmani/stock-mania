"""
Intraday Data Fetcher for Dhan API

Fetches 1-minute intraday data from Dhan API, handles pagination limits,
and normalizes data for downstream analysis.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union
from pathlib import Path

# Setup Project Paths (More robust than sys.path.insert)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(SCRIPT_DIR))

# Import dependencies
try:
    from complete_setup import (
        ScripMaster, 
        DhanDataExtractor,
        DHAN_CLIENT_ID,
        DHAN_ACCESS_TOKEN,
        DHAN_SCRIP_MASTER_PATH,
        DHAN_AVAILABLE
    )
except ImportError as e:
    # Fallback/Mocking for linting purposes if complete_setup is missing
    logging.error(f"Import Error: {e}. Ensure complete_setup.py is accessible.")
    DHAN_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger("DhanFetcher")


class DhanIntradayFetcher:
    """
    A robust class to handle authentication, symbol lookup, and 
    historical data fetching from Dhan API.
    """

    COLUMN_MAPPING = {
        'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume',
        'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 'CLOSE': 'Close', 'VOLUME': 'Volume',
        'start_Time': 'Date', 'start_time': 'Date', 'START_TIME': 'Date', 
        'timestamp': 'Date', 'Timestamp': 'Date', 'TIMESTAMP': 'Date',
        'date': 'Date', 'DATE': 'Date'
    }

    REQUIRED_COLS = ['Open', 'High', 'Low', 'Close', 'Volume']

    def __init__(self):
        """Initialize connection and load Scrip Master."""
        if not DHAN_AVAILABLE:
            raise ImportError("Dhan API library not installed.")
        
        self.extractor = None
        self.scrip_master = None
        self._initialize_api()

    def _initialize_api(self):
        """Internal method to setup API connection and ScripMaster."""
        # 1. Load Scrip Master
        if not os.path.exists(DHAN_SCRIP_MASTER_PATH):
            raise FileNotFoundError(f"Scrip Master file not found at: {DHAN_SCRIP_MASTER_PATH}")
        
        logger.info("Loading Scrip Master...")
        self.scrip_master = ScripMaster(DHAN_SCRIP_MASTER_PATH)
        self.scrip_master.load()

        # 2. Login to Dhan
        try:
            self.extractor = DhanDataExtractor(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
            self.extractor.login()
            logger.info("✅ Dhan API Connection Established.")
        except Exception as e:
            logger.error(f"Failed to initialize Dhan API: {e}")
            raise

    def get_scrip_info(self, symbol: str) -> Optional[Dict]:
        """Resolves a symbol (e.g., 'RELIANCE.NS') to Dhan Security ID."""
        search_symbol = symbol.replace('.NS', '').replace('.BO', '')
        # Defaulting to NSE for standard fetch; extend logic if BSE needed
        scrip_info = self.scrip_master.search(search_symbol, "NSE")
        
        if scrip_info:
            logger.info(f"Symbol Resolved: {scrip_info['symbol_name']} -> ID: {scrip_info['security_id']}")
        else:
            logger.error(f"Symbol '{search_symbol}' not found in Scrip Master.")
        
        return scrip_info

    def fetch_data(self, symbol: str, from_date: str, to_date: str, interval: str = '1') -> Optional[pd.DataFrame]:
        """
        Main method to fetch data. Handles 90-day chunking automatically.
        
        Args:
            symbol: Stock symbol (e.g., 'TCS.NS')
            from_date: 'YYYY-MM-DD'
            to_date: 'YYYY-MM-DD'
            interval: '1', '5', '15', etc.
        """
        scrip_info = self.get_scrip_info(symbol)
        if not scrip_info:
            return None

        from_dt = datetime.strptime(from_date, '%Y-%m-%d')
        to_dt = datetime.strptime(to_date, '%Y-%m-%d')
        
        all_dfs = []
        current_start = from_dt

        # --- Logic Simplification: The loop handles BOTH short and long durations ---
        while current_start < to_dt:
            # End of this chunk is start + 90 days, or the actual end date (whichever is sooner)
            # We use 89 days to be safe with inclusive boundaries
            current_end = min(current_start + timedelta(days=89), to_dt)
            
            s_date_str = current_start.strftime('%Y-%m-%d')
            e_date_str = current_end.strftime('%Y-%m-%d')

            logger.info(f"📡 Fetching chunk: {s_date_str} to {e_date_str}")

            try:
                chunk_df = self.extractor.fetch_data(
                    security_id=scrip_info['security_id'],
                    exchange_segment=scrip_info['exchange_segment'],
                    instrument_type=scrip_info['instrument_type'],
                    from_date=s_date_str,
                    to_date=e_date_str,
                    interval=interval
                )

                if chunk_df is not None and not chunk_df.empty:
                    all_dfs.append(chunk_df)
                else:
                    logger.debug(f"No data in chunk {s_date_str} to {e_date_str}")

            except Exception as e:
                logger.error(f"API Error on chunk {s_date_str}: {e}")

            # Move start pointer to the next day
            current_start = current_end + timedelta(days=1)

        if not all_dfs:
            logger.warning(f"No data returned for {symbol} across requested range.")
            return None

        # Combine and Normalize
        return self._process_dataframe(all_dfs)

    def _process_dataframe(self, dfs: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Merges chunks, normalizes columns, and sets index."""
        try:
            full_df = pd.concat(dfs, axis=0)
            
            # Clean column names (strip whitespace)
            full_df.columns = [col.strip() for col in full_df.columns]
            
            # Remove duplicates based on timestamp if overlaps occurred
            # Renaming columns first makes logic cleaner
            full_df = full_df.rename(columns=self.COLUMN_MAPPING)
            
            # Locate the Date column - check multiple possible names
            date_found = False
            if 'Date' in full_df.columns:
                try:
                    # Convert explicitly. Dhan usually uses Epoch Seconds or Ints.
                    # 'coerce' turns errors to NaT, which we drop later
                    date_values = full_df['Date']
                    
                    # Check if values are numeric (Unix timestamp)
                    if pd.api.types.is_numeric_dtype(date_values):
                        # Check magnitude to decide unit (ms vs s)
                        # 1e11 is roughly year 1973 in ms, safe threshold
                        if date_values.median() > 1e11:
                            full_df['Date'] = pd.to_datetime(date_values, unit='ms')
                        else:
                            full_df['Date'] = pd.to_datetime(date_values, unit='s')
                    else:
                        # Try parsing as regular datetime string
                        full_df['Date'] = pd.to_datetime(full_df['Date'])
                    
                    full_df = full_df.set_index('Date')
                    full_df.index.name = 'Date'
                    date_found = True
                    logger.debug("✅ Using 'Date' column as index")
                except Exception as e:
                    logger.warning(f"Could not parse 'Date' column: {e}")
            
            # Check if index is already a datetime
            if not date_found and isinstance(full_df.index, pd.DatetimeIndex):
                full_df.index.name = 'Date'
                date_found = True
                logger.debug("✅ Using existing DatetimeIndex")
            
            if not date_found:
                logger.error("Could not identify a Date/Timestamp column.")
                logger.error(f"Available columns: {list(full_df.columns)}")
                return None

            # Filter Columns - ensure all required columns are present
            missing_cols = [c for c in self.REQUIRED_COLS if c not in full_df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                logger.error(f"Available columns: {list(full_df.columns)}")
                return None
            
            full_df = full_df[self.REQUIRED_COLS]

            # Enforce numeric types
            full_df = full_df.apply(pd.to_numeric, errors='coerce')

            # Clean up
            full_df = full_df.sort_index().drop_duplicates()
            full_df = full_df.dropna()

            logger.info(f"✅ Final Dataset: {len(full_df)} rows ({full_df.index.min()} to {full_df.index.max()})")
            return full_df

        except Exception as e:
            logger.error(f"Data Processing Failed: {e}", exc_info=True)
            return None

    def save_to_csv(self, df: pd.DataFrame, symbol: str, interval: str, output_dir: str = "data"):
        """Saves the dataframe to CSV."""
        if df is None or df.empty:
            return None
        
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        
        filename = path / f"{symbol}_intraday_{interval}min.csv"
        df.to_csv(filename)
        logger.info(f"💾 Saved to: {filename}")
        return str(filename)


# --- Backward compatibility functions ---
def fetch_intraday_dhan_data(symbol: str, from_date: str, to_date: str, interval: str = '1') -> Optional[pd.DataFrame]:
    """
    Backward compatibility wrapper for the class-based implementation.
    
    Args:
        symbol (str): Stock symbol (e.g., 'HDFCBANK.NS')
        from_date (str): Start date in 'YYYY-MM-DD' format
        to_date (str): End date in 'YYYY-MM-DD' format
        interval (str): Interval in minutes ('1' for 1-minute, '5' for 5-minute)
    
    Returns:
        pandas.DataFrame: DataFrame with OHLCV data and Date index, or None if fails
    """
    try:
        fetcher = DhanIntradayFetcher()
        return fetcher.fetch_data(symbol, from_date, to_date, interval)
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return None


def save_intraday_data(df: pd.DataFrame, symbol: str, interval: str, output_dir: str) -> Optional[str]:
    """
    Backward compatibility wrapper for saving data.
    
    Args:
        df (pandas.DataFrame): DataFrame with intraday data
        symbol (str): Stock symbol
        interval (str): Interval in minutes
        output_dir (str): Output directory path
    
    Returns:
        str: Path to saved file, or None if fails
    """
    try:
        fetcher = DhanIntradayFetcher()
        return fetcher.save_to_csv(df, symbol, interval, output_dir)
    except Exception as e:
        logger.error(f"Failed to save data: {e}")
        return None


# --- Entry Point ---
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Dhan Intraday Fetcher')
    parser.add_argument('symbol', help='Symbol (e.g., RELIANCE.NS)')
    parser.add_argument('--start', required=True, help='YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='YYYY-MM-DD')
    parser.add_argument('--interval', default='1', help='Timeframe (min)')
    parser.add_argument('--output-dir', help='Output directory (optional)')
    
    args = parser.parse_args()

    try:
        fetcher = DhanIntradayFetcher()
        df = fetcher.fetch_data(args.symbol, args.start, args.end, args.interval)
        
        if df is not None:
            print(f"\n✅ Successfully fetched {len(df)} rows")
            print(f"Date range: {df.index.min()} to {df.index.max()}")
            print(f"\nFirst few rows:")
            print(df.head())
            print(f"\nLast few rows:")
            print(df.tail())
            
            output_dir = args.output_dir if args.output_dir else "data"
            fetcher.save_to_csv(df, args.symbol, args.interval, output_dir)
            
    except Exception as main_err:
        logger.critical(f"Execution failed: {main_err}", exc_info=True)
