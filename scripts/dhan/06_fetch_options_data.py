"""
Fetch Historical Options Data from Dhan API

Fetches historical expired options data with Open Interest (OI) and Implied Volatility (IV)
using the rolling options endpoint. This allows backtesting with "Smart Money" sentiment.

Usage:
    python3 fetch_options_data.py NIFTY --strike-type ATM --option-type CE --from-date 2023-01-01 --to-date 2023-12-31
"""

import os
import sys
import pandas as pd
import numpy as np
import argparse
import logging
from datetime import datetime, timedelta

# Dhan API imports
try:
    from dhanhq import dhanhq
    DHAN_AVAILABLE = True
except ImportError:
    DHAN_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dhan API Configuration
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "1109130648")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY0MzQ2ODkzLCJpYXQiOjE3NjQyNjA0OTMsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5MTMwNjQ4In0.iJstgOK6mjdWKAgqPEiB1nHC0qf66BiEm1Ktr4Hj238ywZa0jQ8_MnosdDyE_cAqox2w3eo48iEjxT9HhdmRsw")
DHAN_SCRIP_MASTER_PATH = os.getenv("DHAN_SCRIP_MASTER_PATH", "/Users/av/Downloads/chrome downloads/api-scrip-master-detailed.csv")


class OptionsDataExtractor:
    """Extracts historical options data from Dhan API."""
    
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
    
    def fetch_rolling_options_data(self, symbol, from_date, to_date, strike_type="ATM", option_type="CE", 
                                   exchange_segment="NSE_FNO", instrument="OPTIDX", expiry_flag="MONTH", expiry_code=1, interval=1):
        """
        Fetch historical rolling options data with OI and IV.
        
        Based on Dhan API v2 documentation: https://dhanhq.co/docs/v2/expired-options-data/
        
        Args:
            symbol (str): Underlying symbol (e.g., "NIFTY", "BANKNIFTY")
            from_date (str): Start date in 'YYYY-MM-DD' format
            to_date (str): End date in 'YYYY-MM-DD' format (non-inclusive)
            strike_type (str): Strike selection - "ATM", "ATM+1", "ATM-1", etc. (up to ATM+10/ATM-10 for index options)
            option_type (str): "CE" (Call) or "PE" (Put) - will be converted to "CALL" or "PUT"
            exchange_segment (str): Exchange segment (default: "NSE_FNO")
            instrument (str): Instrument type - "OPTIDX" for index options, "OPTSTK" for stock options
            expiry_flag (str): "WEEK" or "MONTH" (default: "MONTH")
            expiry_code (int): Expiry code (default: 1 for current month)
            interval (int): Minute interval - 1, 5, 15, 25, 60 (default: 1)
        
        Returns:
            pandas.DataFrame: Options data with OHLCV, OI, IV, Strike, and Spot columns
        """
        if not self.dhan:
            self.logger.error("API not initialized. Call login() first.")
            return None
        
        # Convert option type to API format
        drv_option_type = "CALL" if option_type.upper() in ["CE", "CALL"] else "PUT"
        
        self.logger.info(f"Fetching rolling options data for {symbol} {drv_option_type} ({strike_type}) from {from_date} to {to_date}...")
        
        try:
            # Get security ID from scrip master
            security_id = self._get_security_id(symbol, exchange_segment)
            if security_id is None:
                self.logger.error(f"Could not find security ID for {symbol}")
                return None
            
            # Fetch via HTTP POST endpoint
            response = self._fetch_via_http_endpoint(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument=instrument,
                expiry_flag=expiry_flag,
                expiry_code=expiry_code,
                strike=strike_type,
                drv_option_type=drv_option_type,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            if response is None:
                return None
            
            # Parse response and convert to DataFrame
            df = self._parse_options_response(response, drv_option_type)
            
            if df is None or df.empty:
                self.logger.warning("No data returned from API.")
                return None
            
            self.logger.info(f"Fetched {len(df)} rows of options data.")
            return df
            
        except Exception as e:
            self.logger.error(f"Exception during fetch: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _get_security_id(self, symbol, exchange_segment):
        """Get security ID from scrip master."""
        try:
            # Import ScripMaster from complete_setup
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(script_dir)  # Go up to project root
            sys.path.insert(0, os.path.join(project_root, 'scripts', 'legacy'))
            from complete_setup import ScripMaster
            
            if not os.path.exists(DHAN_SCRIP_MASTER_PATH):
                self.logger.error(f"Scrip Master file not found: {DHAN_SCRIP_MASTER_PATH}")
                return None
            
            scrip_master = ScripMaster(DHAN_SCRIP_MASTER_PATH)
            scrip_master.load()
            
            # Search for symbol
            scrip_info = scrip_master.search(symbol.replace('.NS', ''), "NSE")
            
            if scrip_info:
                return scrip_info['security_id']
            else:
                self.logger.error(f"Symbol {symbol} not found in scrip master")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting security ID: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _fetch_via_http_endpoint(self, security_id, exchange_segment, instrument, expiry_flag, expiry_code,
                                  strike, drv_option_type, from_date, to_date, interval):
        """
        Fetch rolling options data via direct HTTP POST request to /v2/charts/rollingoption endpoint.
        
        Based on Dhan API v2 documentation: https://dhanhq.co/docs/v2/expired-options-data/
        
        Uses the dhanhq client's session/headers for proper authentication (same as intraday data).
        """
        try:
            # Dhan API v2 endpoint (from documentation)
            endpoint = "https://api.dhan.co/v2/charts/rollingoption"
            
            # Prepare request body as per API documentation
            # Note: interval should be string, securityId should be int
            request_body = {
                "exchangeSegment": exchange_segment,
                "interval": str(interval),  # API expects string: "1", "5", "15", "25", "60"
                "securityId": int(security_id),  # API expects integer
                "instrument": instrument,
                "expiryFlag": expiry_flag,
                "expiryCode": int(expiry_code),  # API expects integer
                "strike": strike,
                "drvOptionType": drv_option_type,
                "requiredData": [
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "iv",      # Implied Volatility
                    "oi",       # Open Interest
                    "strike",   # Strike price
                    "spot"      # Spot price
                ],
                "fromDate": from_date,
                "toDate": to_date
            }
            
            # Use dhanhq client's session and headers for authentication
            # This ensures we use the same authentication method as intraday data
            if not self.dhan:
                self.logger.error("Dhan client not initialized")
                return None
            
            # Get session and headers from dhanhq client (same as used for intraday data)
            session = getattr(self.dhan, 'session', None)
            headers = getattr(self.dhan, 'header', {}).copy()  # Make a copy to avoid modifying original
            
            # Client already has Content-type and Accept set, but ensure they're present
            # Note: client uses 'Content-type' (lowercase), API may accept either
            if 'Content-type' not in headers and 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            if 'Accept' not in headers:
                headers['Accept'] = 'application/json'
            
            self.logger.info(f"Making POST request to: {endpoint}")
            self.logger.debug(f"Request body: {request_body}")
            self.logger.debug(f"Using client session and headers for authentication")
            
            # Use client's session if available, otherwise fallback to requests
            if session:
                response = session.post(endpoint, json=request_body, headers=headers, timeout=60)
            else:
                # Fallback: use requests with client's headers
                import requests
                response = requests.post(endpoint, json=request_body, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                self.logger.error(f"HTTP 404: Endpoint not found at {endpoint}")
                self.logger.error(f"Response: {response.text}")
                return None
            elif response.status_code == 401:
                self.logger.error(f"HTTP 401: Unauthorized - Check access token")
                self.logger.error(f"Response: {response.text}")
                # Try to get more details from response
                try:
                    error_data = response.json()
                    self.logger.error(f"Error details: {error_data}")
                except:
                    pass
                return None
            else:
                self.logger.error(f"HTTP Error {response.status_code}: {response.text}")
                # Try to parse error response
                try:
                    error_data = response.json()
                    self.logger.error(f"Error details: {error_data}")
                except:
                    pass
                return None
                
        except ImportError:
            self.logger.warning("requests library not available. Install with: pip install requests")
            return None
        except Exception as e:
            self.logger.error(f"HTTP request failed: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _parse_options_response(self, response, option_type):
        """
        Parse the Dhan API response which returns arrays for each field.
        
        Response structure:
        {
            "data": {
                "ce": {
                    "open": [354, 360.3],
                    "high": [...],
                    "low": [...],
                    "close": [...],
                    "volume": [...],
                    "iv": [...],
                    "oi": [...],
                    "strike": [...],
                    "spot": [...],
                    "timestamp": [1756698300, 1756699200]
                },
                "pe": null
            }
        }
        """
        try:
            data = response.get('data', {})
            
            # Get the option type data (ce or pe)
            option_key = "ce" if option_type == "CALL" else "pe"
            option_data = data.get(option_key)
            
            if option_data is None:
                self.logger.warning(f"No data found for {option_type}")
                return pd.DataFrame()
            
            # Extract arrays
            timestamps = option_data.get('timestamp', [])
            
            if not timestamps:
                self.logger.warning("No timestamps in response")
                return pd.DataFrame()
            
            # Build DataFrame from arrays
            df_data = {
                'Date': pd.to_datetime(timestamps, unit='s'),  # Unix timestamp in seconds
                'Open': option_data.get('open', []),
                'High': option_data.get('high', []),
                'Low': option_data.get('low', []),
                'Close': option_data.get('close', []),
                'Volume': option_data.get('volume', []),
                'OI': option_data.get('oi', []),  # Open Interest
                'IV': option_data.get('iv', []),  # Implied Volatility
                'Strike': option_data.get('strike', []),
                'Spot': option_data.get('spot', [])  # Underlying spot price
            }
            
            # Find maximum length to handle arrays of different lengths
            max_len = len(timestamps)
            
            # Ensure all arrays are the same length (pad with NaN if needed)
            for key, values in df_data.items():
                if key == 'Date':
                    continue
                if len(values) < max_len:
                    df_data[key].extend([np.nan] * (max_len - len(values)))
                elif len(values) > max_len:
                    df_data[key] = values[:max_len]
            
            # Create DataFrame
            df = pd.DataFrame(df_data)
            
            # Set Date as index
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            # Remove rows where all data is NaN
            df = df.dropna(how='all')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def _fetch_via_option_chain(self, symbol, from_date, to_date, strike_type, option_type):
        """
        Fallback method: Fetch via option chain if rolling endpoint isn't available.
        This requires fetching daily and extracting ATM options.
        
        Note: This is a workaround that builds historical series from daily option chains.
        It's more complex but works if the rolling endpoint isn't accessible.
        """
        self.logger.info("Using option_chain method as fallback...")
        self.logger.info("This method builds historical series from daily option chains.")
        self.logger.warning("⚠️  This is computationally intensive and may take time.")
        
        try:
            # We need to:
            # 1. Get underlying security ID from scrip master
            # 2. For each date in range, fetch option chain
            # 3. Identify ATM strike
            # 4. Extract the specific option contract data
            # 5. Build historical series
            
            # For now, return None and suggest using HTTP endpoint
            self.logger.warning("Option chain fallback requires:")
            self.logger.warning("  1. Scrip master lookup for underlying")
            self.logger.warning("  2. Daily option chain fetching")
            self.logger.warning("  3. ATM strike identification")
            self.logger.warning("  4. Historical data aggregation")
            self.logger.info("💡 Recommendation: Use HTTP endpoint method or check Dhan API documentation")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Option chain fallback failed: {e}")
            return None
    
    def _standardize_columns(self, df):
        """Standardize column names to consistent format."""
        column_mapping = {
            # Price columns
            'open': 'Open', 'OPEN': 'Open',
            'high': 'High', 'HIGH': 'High',
            'low': 'Low', 'LOW': 'Low',
            'close': 'Close', 'CLOSE': 'Close',
            'volume': 'Volume', 'VOLUME': 'Volume',
            
            # Options-specific columns
            'oi': 'OI', 'open_interest': 'OI', 'OPEN_INTEREST': 'OI',
            'iv': 'IV', 'implied_volatility': 'IV', 'IMPLIED_VOLATILITY': 'IV',
            'strike': 'Strike', 'STRIKE': 'Strike',
            'expiry': 'Expiry', 'EXPIRY': 'Expiry',
            'option_type': 'OptionType', 'OPTION_TYPE': 'OptionType',
            
            # Date columns
            'timestamp': 'Date', 'Timestamp': 'Date', 'TIMESTAMP': 'Date',
            'date': 'Date', 'Date': 'Date', 'DATE': 'Date',
            'start_time': 'Date', 'START_TIME': 'Date', 'start_Time': 'Date'
        }
        
        # Rename columns
        df.columns = [col.strip() for col in df.columns]
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)
        
        # Convert date column to datetime
        if 'Date' in df.columns:
            # Handle Unix timestamps (milliseconds or seconds)
            if df['Date'].dtype in [np.int64, np.float64]:
                # Check if values are in milliseconds (> 1e10) or seconds
                sample_val = df['Date'].iloc[0] if len(df) > 0 else 0
                if sample_val > 1e10:
                    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
                else:
                    df['Date'] = pd.to_datetime(df['Date'], unit='s')
            else:
                df['Date'] = pd.to_datetime(df['Date'])
            
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
        
        return df


def fetch_options_data(symbol, from_date, to_date, strike_type="ATM", option_type="CE", 
                       exchange_segment="NSE_FNO", instrument="OPTIDX", expiry_flag="MONTH", 
                       expiry_code=1, interval=1, output_dir=None):
    """
    Main function to fetch historical options data.
    
    Args:
        symbol (str): Underlying symbol (e.g., "NIFTY", "BANKNIFTY")
        from_date (str): Start date in 'YYYY-MM-DD' format
        to_date (str): End date in 'YYYY-MM-DD' format
        strike_type (str): "ATM", "ITM", "OTM", or strike offset
        option_type (str): "CE" or "PE"
        output_dir (str): Optional output directory to save CSV
    
    Returns:
        pandas.DataFrame: Options data with OHLCV, OI, and IV
    """
    if not DHAN_AVAILABLE:
        logger.error("Dhan API library (dhanhq) not available. Install with: pip install dhanhq")
        return None
    
    logger.info("="*80)
    logger.info(f"📊 FETCHING HISTORICAL OPTIONS DATA")
    logger.info("="*80)
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Option Type: {option_type}")
    logger.info(f"Strike Type: {strike_type}")
    logger.info(f"Date Range: {from_date} to {to_date}")
    
    # Initialize extractor
    try:
        extractor = OptionsDataExtractor(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        extractor.login()
    except Exception as e:
        logger.error(f"Failed to initialize Dhan API: {e}")
        return None
    
    # Fetch data
    df = extractor.fetch_rolling_options_data(
        symbol=symbol,
        from_date=from_date,
        to_date=to_date,
        strike_type=strike_type,
        option_type=option_type,
        exchange_segment=exchange_segment,
        instrument=instrument,
        expiry_flag=expiry_flag,
        expiry_code=expiry_code,
        interval=interval
    )
    
    if df is None or df.empty:
        logger.error("No options data returned from Dhan API.")
        logger.info("\n💡 Note: The rolling options endpoint may require:")
        logger.info("   1. Specific API method name (check dhanhq documentation)")
        logger.info("   2. Different parameter format")
        logger.info("   3. Direct HTTP request to /charts/rollingoption endpoint")
        return None
    
    # Display summary
    logger.info("\n" + "="*80)
    logger.info("✅ DATA FETCHED SUCCESSFULLY")
    logger.info("="*80)
    logger.info(f"Rows: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"\nFirst few rows:")
    logger.info(f"\n{df.head()}")
    logger.info(f"\nData Summary:")
    logger.info(f"{df.describe()}")
    
    # Save to CSV if output directory provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{symbol}_{option_type}_{strike_type}_options_{from_date}_to_{to_date}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath)
        logger.info(f"\n💾 Data saved to: {filepath}")
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description='Fetch Historical Options Data from Dhan API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch ATM Call options for NIFTY
  python3 fetch_options_data.py NIFTY --strike-type ATM --option-type CE --from-date 2023-01-01 --to-date 2023-12-31
  
  # Fetch OTM Put options for BANKNIFTY
  python3 fetch_options_data.py BANKNIFTY --strike-type OTM --option-type PE --from-date 2023-01-01 --to-date 2023-12-31
        """
    )
    
    parser.add_argument('symbol', help='Underlying symbol (e.g., NIFTY, BANKNIFTY)')
    parser.add_argument('--strike-type', default='ATM', 
                       help='Strike selection: ATM, ATM+1, ATM-1, etc. (up to ATM+10/ATM-10 for index options)')
    parser.add_argument('--option-type', default='CE', choices=['CE', 'PE'], 
                       help='Option type: CE (Call) or PE (Put)')
    parser.add_argument('--from-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', required=True, help='End date (YYYY-MM-DD, non-inclusive)')
    parser.add_argument('--exchange-segment', default='NSE_FNO', 
                       help='Exchange segment (default: NSE_FNO)')
    parser.add_argument('--instrument', default='OPTIDX', choices=['OPTIDX', 'OPTSTK'],
                       help='Instrument type: OPTIDX (Index Options) or OPTSTK (Stock Options)')
    parser.add_argument('--expiry-flag', default='MONTH', choices=['WEEK', 'MONTH'],
                       help='Expiry interval: WEEK or MONTH (default: MONTH)')
    parser.add_argument('--expiry-code', type=int, default=1,
                       help='Expiry code (default: 1 for current month)')
    parser.add_argument('--interval', type=int, default=1, choices=[1, 5, 15, 25, 60],
                       help='Minute interval: 1, 5, 15, 25, 60 (default: 1)')
    parser.add_argument('--output-dir', help='Output directory for CSV file')
    
    args = parser.parse_args()
    
    fetch_options_data(
        symbol=args.symbol,
        from_date=args.from_date,
        to_date=args.to_date,
        strike_type=args.strike_type,
        option_type=args.option_type,
        exchange_segment=args.exchange_segment,
        instrument=args.instrument,
        expiry_flag=args.expiry_flag,
        expiry_code=args.expiry_code,
        interval=args.interval,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()

