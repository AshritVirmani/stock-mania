"""
Intraday Data Fetcher for Dhan API

Fetches 1-minute intraday data from Dhan API, handles pagination limits,
and normalizes data for downstream analysis.
"""

import os
import sys
import logging
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union
from pathlib import Path
import pytz

# Setup Project Paths (More robust than sys.path.insert)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Go up two levels: scripts/dhan -> scripts -> project root
LEGACY_SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "legacy"
sys.path.append(str(LEGACY_SCRIPTS_DIR))
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

    def fetch_data(self, symbol: str, from_date: str, to_date: str, interval: str = '1', min_years: float = None) -> Optional[pd.DataFrame]:
        """
        Main method to fetch data. Handles 90-day chunking automatically.
        
        Args:
            symbol: Stock symbol (e.g., 'TCS.NS')
            from_date: 'YYYY-MM-DD'
            to_date: 'YYYY-MM-DD'
            interval: '1', '5', '15', etc.
            min_years: Minimum years of data required. If not met, will try fetching from earlier date.
        """
        scrip_info = self.get_scrip_info(symbol)
        if not scrip_info:
            return None

        from_dt = datetime.strptime(from_date, '%Y-%m-%d')
        to_dt = datetime.strptime(to_date, '%Y-%m-%d')
        
        all_dfs = []
        current_start = from_dt
        successful_chunks = []
        failed_chunks = []
        empty_chunks = []

        # --- Logic Simplification: The loop handles BOTH short and long durations ---
        while current_start < to_dt:
            # End of this chunk is start + 90 days, or the actual end date (whichever is sooner)
            # We use 89 days to be safe with inclusive boundaries
            current_end = min(current_start + timedelta(days=89), to_dt)
            
            s_date_str = current_start.strftime('%Y-%m-%d')
            e_date_str = current_end.strftime('%Y-%m-%d')

            logger.info(f"📡 Fetching chunk: {s_date_str} to {e_date_str}")

            # Retry logic for failed chunks
            max_retries = 2
            chunk_df = None
            chunk_success = False
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        # Wait before retry (exponential backoff)
                        wait_time = min(2 ** attempt, 10)  # Max 10 seconds
                        logger.info(f"   🔄 Retry attempt {attempt}/{max_retries} after {wait_time}s...")
                        time.sleep(wait_time)
                    
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
                        successful_chunks.append((s_date_str, e_date_str, len(chunk_df)))
                        logger.info(f"   ✅ Chunk {s_date_str} to {e_date_str}: {len(chunk_df)} rows")
                        chunk_success = True
                        break
                    else:
                        if attempt == max_retries:
                            empty_chunks.append((s_date_str, e_date_str))
                            logger.warning(f"   ⚠️  No data returned for chunk {s_date_str} to {e_date_str} (after {max_retries + 1} attempts)")
                        else:
                            logger.debug(f"   Empty response, will retry...")

                except Exception as e:
                    if attempt == max_retries:
                        failed_chunks.append((s_date_str, e_date_str, str(e)))
                        logger.error(f"   ❌ API Error on chunk {s_date_str} to {e_date_str} (after {max_retries + 1} attempts): {e}")
                    else:
                        logger.warning(f"   ⚠️  Error on attempt {attempt + 1}, will retry: {e}")
            
            # Small delay between chunks to avoid rate limiting
            if chunk_success:
                time.sleep(0.1)  # 100ms delay after successful fetch
            else:
                time.sleep(0.5)  # 500ms delay after failed/empty chunk

            # Move start pointer to the next day
            current_start = current_end + timedelta(days=1)

        # Summary of fetch results
        logger.info("\n" + "="*80)
        logger.info("📊 FETCH SUMMARY")
        logger.info("="*80)
        logger.info(f"Requested date range: {from_date} to {to_date}")
        logger.info(f"Successful chunks: {len(successful_chunks)}")
        logger.info(f"Empty chunks (no data): {len(empty_chunks)}")
        logger.info(f"Failed chunks (errors): {len(failed_chunks)}")
        
        if successful_chunks:
            total_rows = sum(rows for _, _, rows in successful_chunks)
            logger.info(f"Total rows fetched: {total_rows:,}")
            first_chunk_start = successful_chunks[0][0]
            last_chunk_end = successful_chunks[-1][1]
            logger.info(f"Actual data range: {first_chunk_start} to {last_chunk_end}")
        
        if empty_chunks:
            logger.warning(f"\n⚠️  Empty chunks (no data available):")
            for start, end in empty_chunks[:10]:  # Show first 10
                logger.warning(f"   - {start} to {end}")
            if len(empty_chunks) > 10:
                logger.warning(f"   ... and {len(empty_chunks) - 10} more empty chunks")
        
        if failed_chunks:
            logger.error(f"\n❌ Failed chunks (API errors):")
            for start, end, error in failed_chunks[:10]:  # Show first 10
                logger.error(f"   - {start} to {end}: {error[:100]}")
            if len(failed_chunks) > 10:
                logger.error(f"   ... and {len(failed_chunks) - 10} more failed chunks")
        
        logger.info("="*80 + "\n")

        if not all_dfs:
            logger.warning(f"No data returned for {symbol} across requested range.")
            return None

        # Combine and Normalize
        result_df = self._process_dataframe(all_dfs)
        
        # Workaround: Validate we got at least 6 years of data, if min_years specified
        if result_df is not None and min_years is not None:
            actual_years = (result_df.index.max() - result_df.index.min()).days / 365.25
            if actual_years < min_years:
                logger.warning(f"⚠️  Only got {actual_years:.1f} years of data, but need {min_years} years")
                logger.info(f"🔄 Workaround: Trying to fetch from earlier date to get at least {min_years} years...")
                
                # Calculate how much earlier we need to go
                years_short = min_years - actual_years
                # Add buffer of 1 year to account for data gaps
                buffer_years = years_short + 1
                from_dt_obj = datetime.strptime(from_date, '%Y-%m-%d')
                new_start_date_obj = from_dt_obj - timedelta(days=int(buffer_years * 365.25))
                new_start_date = new_start_date_obj.strftime('%Y-%m-%d')
                
                logger.info(f"   📅 Retrying with extended range: {new_start_date} to {to_date}")
                
                # Fetch additional data from earlier period
                additional_dfs = []
                current_start = new_start_date_obj
                original_start = datetime.strptime(from_date, '%Y-%m-%d')
                
                while current_start < original_start:
                    current_end = min(current_start + timedelta(days=89), original_start)
                    s_date_str = current_start.strftime('%Y-%m-%d')
                    e_date_str = current_end.strftime('%Y-%m-%d')
                    
                    logger.info(f"📡 Fetching additional chunk: {s_date_str} to {e_date_str}")
                    
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
                            additional_dfs.append(chunk_df)
                            logger.info(f"   ✅ Additional chunk {s_date_str} to {e_date_str}: {len(chunk_df)} rows")
                        else:
                            logger.debug(f"   No data in additional chunk {s_date_str} to {e_date_str}")
                    except Exception as e:
                        logger.debug(f"   No data available for additional chunk {s_date_str} to {e_date_str}: {e}")
                    
                    current_start = current_end + timedelta(days=1)
                    time.sleep(0.1)  # Small delay
                
                # Combine with original data
                if additional_dfs:
                    logger.info(f"   ✅ Found {len(additional_dfs)} additional chunks")
                    all_dfs = additional_dfs + all_dfs  # Put earlier data first
                    result_df = self._process_dataframe(all_dfs)
                    
                    if result_df is not None:
                        final_years = (result_df.index.max() - result_df.index.min()).days / 365.25
                        logger.info(f"   ✅ After workaround: Got {final_years:.1f} years of data")
                        if final_years >= min_years:
                            logger.info(f"   ✅ Successfully obtained at least {min_years} years of data!")
                        else:
                            logger.warning(f"   ⚠️  Still only {final_years:.1f} years available (requested {min_years})")
        
        return result_df

    def _process_dataframe(self, dfs: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Merges chunks, normalizes columns, sets index, converts to IST, and filters market hours."""
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

            # Convert to IST timezone if not already
            # Dhan API typically returns data in UTC or IST-naive
            # We need to ensure it's in IST for proper market hours filtering
            if full_df.index.tz is None:
                # If timezone-naive, assume it's IST (Indian Standard Time)
                # IST is UTC+5:30
                ist = pytz.timezone('Asia/Kolkata')
                full_df.index = full_df.index.tz_localize(ist)
                logger.info("   🌏 Converted timezone-naive timestamps to IST")
            elif full_df.index.tz != pytz.timezone('Asia/Kolkata'):
                # If in different timezone, convert to IST
                ist = pytz.timezone('Asia/Kolkata')
                full_df.index = full_df.index.tz_convert(ist)
                logger.info(f"   🌏 Converted from {full_df.index.tz} to IST")

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

            # Filter to market hours (09:15 - 15:30 IST)
            # Indian stock market trading hours
            before_filter = len(full_df)
            full_df = full_df.between_time('09:15', '15:30')
            after_filter = len(full_df)
            if before_filter > after_filter:
                logger.info(f"   📊 Filtered to market hours (09:15-15:30 IST): {after_filter} rows (removed {before_filter - after_filter} non-market hours)")

            logger.info(f"✅ Final Dataset: {len(full_df)} rows ({full_df.index.min()} to {full_df.index.max()})")
            return full_df

        except Exception as e:
            logger.error(f"Data Processing Failed: {e}", exc_info=True)
            return None

    def save_to_csv(self, df: pd.DataFrame, symbol: str, interval: str, output_dir: str = "data"):
        """
        Saves the dataframe to CSV with _raw suffix.
        Data is already filtered to market hours in _process_dataframe.
        """
        if df is None or df.empty:
            return None
        
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save with _raw suffix to match expected naming convention
        filename = path / f"{symbol}_intraday_{interval}min_raw.csv"
        
        # Remove timezone info for CSV (keep as naive datetime in IST)
        df_to_save = df.copy()
        if df_to_save.index.tz is not None:
            df_to_save.index = df_to_save.index.tz_localize(None)
        
        df_to_save.to_csv(filename)
        logger.info(f"💾 Saved to: {filename}")
        logger.info(f"   Date range: {df.index.min()} to {df.index.max()} (IST, market hours only)")
        logger.info(f"   Total rows: {len(df)} (09:15-15:30 IST)")
        return str(filename)
    
    def save_to_json(self, df: pd.DataFrame, symbol: str, interval: str, output_dir: str = "data"):
        """
        Save DataFrame to JSON file (for intraday data export).
        Data is already filtered to market hours (09:15 - 15:30 IST) in _process_dataframe.
        
        Args:
            df: DataFrame to save (already filtered to market hours)
            symbol: Stock symbol
            interval: Time interval in minutes
            output_dir: Output directory path
            
        Returns:
            Path to saved file, or None if fails
        """
        import json
        if df is None or df.empty:
            return None
        
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        
        filename = path / f"{symbol}_intraday_{interval}min_raw.json"
        
        # Data is already filtered to market hours in _process_dataframe
        df_filtered = df
        
        # Convert DataFrame to JSON-friendly format
        # Reset index to include date as a column
        df_json = df_filtered.reset_index()
        
        # Convert datetime to string (remove timezone info for JSON)
        if df_json['Date'].dt.tz is not None:
            df_json['Date'] = df_json['Date'].dt.tz_localize(None).astype(str)
        else:
            df_json['Date'] = df_json['Date'].astype(str)
        
        # Convert to dict with records orientation
        data_dict = {
            'symbol': symbol,
            'interval': interval,
            'timezone': 'IST (Asia/Kolkata)',
            'market_hours_only': True,
            'market_hours': '09:15 - 15:30 IST',
            'date_range': {
                'start': str(df_filtered.index.min()),
                'end': str(df_filtered.index.max()),
                'total_rows': len(df_filtered),
                'days_covered': (df_filtered.index.max() - df_filtered.index.min()).days
            },
            'data': df_json.to_dict('records')
        }
        
        with open(filename, 'w') as f:
            json.dump(data_dict, f, indent=2)
        
        logger.info(f"💾 Saved JSON to: {filename}")
        logger.info(f"   Date range: {df_filtered.index.min()} to {df_filtered.index.max()} (IST)")
        logger.info(f"   Total rows: {len(df_filtered)} (market hours only: 09:15-15:30 IST)")
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
    parser.add_argument('--min-years', type=float, help='Minimum years of data required (will retry if not met)')
    
    args = parser.parse_args()

    try:
        fetcher = DhanIntradayFetcher()
        df = fetcher.fetch_data(args.symbol, args.start, args.end, args.interval, min_years=args.min_years)
        
        if df is not None:
            print(f"\n✅ Successfully fetched {len(df)} rows")
            print(f"Date range: {df.index.min()} to {df.index.max()}")
            print(f"\nFirst few rows:")
            print(df.head())
            print(f"\nLast few rows:")
            print(df.tail())
            
            output_dir = args.output_dir if args.output_dir else "data"
            # Save both CSV and JSON
            csv_file = fetcher.save_to_csv(df, args.symbol, args.interval, output_dir)
            json_file = fetcher.save_to_json(df, args.symbol, args.interval, output_dir)
            if csv_file:
                print(f"\n💾 CSV saved: {csv_file}")
            if json_file:
                print(f"💾 JSON saved: {json_file}")
            
    except Exception as main_err:
        logger.critical(f"Execution failed: {main_err}", exc_info=True)
