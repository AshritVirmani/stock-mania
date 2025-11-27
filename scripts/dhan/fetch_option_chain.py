"""
Fetch Option Chain Data from Dhan API

Fetches option chain data (multiple strikes) for stock options.
Saves both CSV and JSON formats.

Usage:
    python3 fetch_option_chain.py ICICIBANK.NS --from-date 2024-01-01 --to-date 2024-12-31
"""

import os
import sys
import json
import time
import pandas as pd
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.append(str(SCRIPT_DIR))
sys.path.append(str(SCRIPT_DIR.parent / "legacy"))

# Import options extractor using importlib (module name starts with number)
import importlib.util
options_module_path = SCRIPT_DIR / "06_fetch_options_data.py"
spec = importlib.util.spec_from_file_location("fetch_options_data", options_module_path)
options_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(options_module)

OptionsDataExtractor = options_module.OptionsDataExtractor
DHAN_CLIENT_ID = options_module.DHAN_CLIENT_ID
DHAN_ACCESS_TOKEN = options_module.DHAN_ACCESS_TOKEN
DHAN_AVAILABLE = options_module.DHAN_AVAILABLE

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_option_chain(symbol, from_date, to_date, output_dir=None, min_years=None):
    """
    Fetch option chain data for a stock (multiple strikes, both CE and PE).
    
    Args:
        symbol: Stock symbol (e.g., 'ICICIBANK.NS')
        from_date: Start date 'YYYY-MM-DD'
        to_date: End date 'YYYY-MM-DD'
        output_dir: Output directory (default: analysis_results/{SYMBOL}/options/)
    
    Returns:
        dict: Dictionary with all option chain data
    """
    if not DHAN_AVAILABLE:
        logger.error("Dhan API library (dhanhq) not available.")
        return None
    
    # Clean symbol
    clean_symbol = symbol.replace('.NS', '').upper()
    
    # Setup output directory
    if output_dir is None:
        output_dir = PROJECT_ROOT / "analysis_results" / symbol / "options" / "data"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("="*80)
    logger.info(f"📊 FETCHING OPTION CHAIN DATA")
    logger.info("="*80)
    logger.info(f"Symbol: {clean_symbol}")
    logger.info(f"Date Range: {from_date} to {to_date}")
    logger.info(f"Output: {output_dir}")
    
    # Initialize extractor
    try:
        extractor = OptionsDataExtractor(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        extractor.login()
    except Exception as e:
        logger.error(f"Failed to initialize Dhan API: {e}")
        return None
    
    # Define strikes to fetch (start with ATM, can expand later)
    # Note: Some strikes may not be available for stock options
    # For now, fetch ATM only - this is the most liquid and reliable
    strikes = ["ATM"]
    option_types = ["CE", "PE"]
    
    # Calculate target years if min_years specified
    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
    to_dt = datetime.strptime(to_date, '%Y-%m-%d')
    requested_years = (to_dt - from_dt).days / 365.25
    logger.info(f"📊 Requested date range: {requested_years:.1f} years ({from_date} to {to_date})")
    if min_years:
        logger.info(f"🎯 Target: Minimum {min_years} years of data")
    
    all_data = {}
    successful_fetches = 0
    
    # Parse dates for chunking (30-day chunks for better reliability)
    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
    to_dt = datetime.strptime(to_date, '%Y-%m-%d')
    
    # Fetch data for each strike and option type, chunking by 30 days
    for strike_type in strikes:
        for option_type in option_types:
            logger.info(f"\n📡 Fetching {strike_type} {option_type}...")
            
            chunk_dfs = []
            successful_chunks = 0
            failed_chunks = 0
            current_start = from_dt
            
            # Chunk into 30-day periods (more reliable than 90 days for options data)
            # Use smaller chunks (20 days) for better reliability with historical data
            chunk_size_days = 20
            total_chunks = int((to_dt - from_dt).days / chunk_size_days) + 1
            chunk_num = 0
            
            while current_start < to_dt:
                chunk_num += 1
                current_end = min(current_start + timedelta(days=chunk_size_days - 1), to_dt)
                chunk_from = current_start.strftime('%Y-%m-%d')
                chunk_to = current_end.strftime('%Y-%m-%d')
                
                logger.info(f"   📅 Chunk {chunk_num}/{total_chunks}: {chunk_from} to {chunk_to} ({strike_type} {option_type})")
                
                # Retry logic for failed chunks with exponential backoff
                max_retries = 3
                chunk_success = False
                
                for attempt in range(max_retries + 1):
                    try:
                        if attempt > 0:
                            wait_time = min(2 ** attempt, 8)  # Max 8 seconds
                            logger.info(f"      🔄 Retry attempt {attempt}/{max_retries} after {wait_time}s...")
                            time.sleep(wait_time)
                        
                        df_chunk = extractor.fetch_rolling_options_data(
                            symbol=clean_symbol,
                            from_date=chunk_from,
                            to_date=chunk_to,
                            strike_type=strike_type,
                            option_type=option_type,
                            exchange_segment="NSE_FNO",
                            instrument="OPTSTK",  # Stock options
                            expiry_flag="MONTH",
                            expiry_code=1,  # Current month
                            interval=1  # 1-minute data
                        )
                        
                        if df_chunk is not None and not df_chunk.empty:
                            chunk_dfs.append(df_chunk)
                            successful_chunks += 1
                            chunk_success = True
                            logger.info(f"      ✅ Got {len(df_chunk)} rows (chunk {chunk_num}/{total_chunks})")
                            break
                        else:
                            if attempt == max_retries:
                                logger.warning(f"      ⚠️  No data for chunk {chunk_from} to {chunk_to} (after {max_retries + 1} attempts)")
                            else:
                                logger.debug(f"      Empty response, will retry...")
                                
                    except Exception as e:
                        error_msg = str(e)
                        if attempt == max_retries:
                            failed_chunks += 1
                            logger.warning(f"      ⚠️  Error on chunk {chunk_from} (after {max_retries + 1} attempts): {error_msg[:150]}")
                        else:
                            logger.debug(f"      Error on attempt {attempt + 1}, will retry: {error_msg[:80]}")
                
                current_start = current_end + timedelta(days=1)
                # Progressive delay between chunks to avoid rate limiting
                if chunk_success:
                    time.sleep(0.8)  # 800ms after successful fetch
                else:
                    time.sleep(2.0)  # 2 seconds after failed/empty chunk
                
                # Progress update every 5 chunks
                if chunk_num % 5 == 0:
                    logger.info(f"   📊 Progress: {chunk_num}/{total_chunks} chunks, {successful_chunks} successful, {failed_chunks} failed")
            
            logger.info(f"   📊 Chunk summary: {successful_chunks} successful, {failed_chunks} failed")
            
            # Combine chunks for this strike/type
            if chunk_dfs:
                try:
                    df = pd.concat(chunk_dfs, axis=0)
                    df = df.sort_index().drop_duplicates()
                    
                    # Ensure timezone is IST and filter to market hours if not already done
                    import pytz
                    ist = pytz.timezone('Asia/Kolkata')
                    if df.index.tz is None:
                        # If timezone-naive, assume UTC and convert to IST
                        utc = pytz.UTC
                        df.index = df.index.tz_localize(utc).tz_convert(ist)
                    elif df.index.tz != ist:
                        df.index = df.index.tz_convert(ist)
                    
                    # Filter to market hours (09:15 - 15:30 IST) if not already filtered
                    before_filter = len(df)
                    df = df.between_time('09:15', '15:30')
                    after_filter = len(df)
                    if before_filter > after_filter:
                        logger.info(f"   📊 Filtered to market hours: {after_filter} rows (removed {before_filter - after_filter})")
                    
                    key = f"{strike_type}_{option_type}"
                    all_data[key] = df
                    successful_fetches += 1
                    logger.info(f"   ✅ Total {len(df)} rows for {strike_type} {option_type} (market hours: 09:15-15:30 IST)")
                except Exception as e:
                    logger.error(f"   ❌ Error combining chunks for {strike_type} {option_type}: {e}")
            else:
                logger.warning(f"   ⚠️  No data for {strike_type} {option_type}")
    
    if not all_data:
        logger.error("❌ No option chain data fetched")
        return None
    
    # Calculate actual data range
    all_dfs_list = list(all_data.values())
    if all_dfs_list:
        combined_test = pd.concat(all_dfs_list, axis=0)
        actual_start = combined_test.index.min()
        actual_end = combined_test.index.max()
        actual_years = (actual_end - actual_start).days / 365.25
        logger.info(f"\n✅ Successfully fetched {successful_fetches} option series")
        logger.info(f"📊 Actual data range: {actual_start.date()} to {actual_end.date()}")
        logger.info(f"📊 Actual coverage: {actual_years:.2f} years")
        
        if min_years and actual_years < min_years:
            logger.warning(f"⚠️  Only got {actual_years:.2f} years, but target was {min_years} years")
            logger.info(f"💡 Consider extending the date range or checking API availability")
        elif min_years:
            logger.info(f"✅ Successfully obtained {actual_years:.2f} years (target: {min_years} years)")
    
    # Save individual CSV files for each strike/type
    csv_files = []
    for key, df in all_data.items():
        csv_file = output_dir / f"{symbol}_{key}_options.csv"
        df.to_csv(csv_file)
        csv_files.append(str(csv_file))
        logger.info(f"   💾 Saved: {csv_file.name}")
    
    # Combine all data into one DataFrame (if possible)
    try:
        combined_df = pd.concat(all_data.values(), axis=0)
        combined_df = combined_df.sort_index()
        
        combined_csv = output_dir / f"{symbol}_option_chain_combined.csv"
        combined_df.to_csv(combined_csv)
        logger.info(f"   💾 Saved combined: {combined_csv.name}")
    except Exception as e:
        logger.warning(f"   ⚠️  Could not combine dataframes: {e}")
        combined_df = None
    
    # Save JSON format
    json_data = {
        'symbol': symbol,
        'date_range': {
            'start': from_date,
            'end': to_date
        },
        'strikes_fetched': strikes,
        'option_types': option_types,
        'total_series': len(all_data),
        'data': {}
    }
    
    # Convert each DataFrame to JSON
    for key, df in all_data.items():
        df_json = df.reset_index()
        df_json['Date'] = df_json['Date'].astype(str)
        json_data['data'][key] = {
            'rows': len(df),
            'date_range': {
                'start': str(df.index.min()),
                'end': str(df.index.max())
            },
            'columns': list(df.columns),
            'data': df_json.to_dict('records')
        }
    
    json_file = output_dir / f"{symbol}_option_chain.json"
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    logger.info(f"   💾 Saved JSON: {json_file.name}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("✅ OPTION CHAIN DATA FETCH COMPLETE")
    logger.info("="*80)
    logger.info(f"Total series fetched: {len(all_data)}")
    if combined_df is not None:
        logger.info(f"Combined rows: {len(combined_df):,}")
    logger.info(f"Files saved in: {output_dir}")
    
    return {
        'individual': all_data,
        'combined': combined_df,
        'json_file': str(json_file),
        'csv_files': csv_files
    }


def main():
    parser = argparse.ArgumentParser(description='Fetch Option Chain Data from Dhan API')
    parser.add_argument('symbol', help='Stock symbol (e.g., ICICIBANK.NS)')
    parser.add_argument('--from-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', help='Output directory (optional)')
    parser.add_argument('--min-years', type=float, help='Minimum years of data to fetch (will extend date range if needed)')
    
    args = parser.parse_args()
    
    # Adjust date range if min_years specified
    from_date = args.from_date
    to_date = args.to_date
    
    if args.min_years:
        from_dt = datetime.strptime(from_date, '%Y-%m-%d')
        to_dt = datetime.strptime(to_date, '%Y-%m-%d')
        current_years = (to_dt - from_dt).days / 365.25
        
        if current_years < args.min_years:
            # Extend start date backwards
            years_to_add = args.min_years - current_years
            new_start = from_dt - timedelta(days=int(years_to_add * 365.25) + 30)  # Add buffer
            from_date = new_start.strftime('%Y-%m-%d')
            logger.info(f"📅 Extended date range to meet {args.min_years} year minimum:")
            logger.info(f"   Original: {args.from_date} to {to_date} ({current_years:.1f} years)")
            logger.info(f"   Extended: {from_date} to {to_date} (target: {args.min_years} years)")
    
    result = fetch_option_chain(
        symbol=args.symbol,
        from_date=from_date,
        to_date=to_date,
        output_dir=args.output_dir,
        min_years=args.min_years
    )
    
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()

