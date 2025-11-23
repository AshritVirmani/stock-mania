"""
Advanced Intraday Feature Engineer

Generates professional-grade alpha factors including:
1. Technical Indicators (RSI, MACD, VWAP, ATR)
2. Smart Money Signals (Synthetic IV, Detrended OBV)
3. Multi-Timeframe Context (5m/15m Trends)
4. Lagged Features for ML Models
"""

import os
import sys
import pandas as pd
import numpy as np
import ta
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger("FeatureEngineer")


@dataclass
class FeatureConfig:
    """Configuration for feature generation."""
    rsi_window: int = 14
    mac_fast: int = 12
    mac_slow: int = 26
    mac_signal: int = 9
    atr_window: int = 14
    bb_window: int = 20
    bb_std: float = 2.0
    synthetic_iv_window: int = 30
    smart_money_window: int = 200


class IntradayFeatureEngineer:
    """
    Advanced feature engineering for intraday trading data.
    Generates technical indicators, Smart Money signals, and multi-timeframe context.
    """
    
    def __init__(self, config: FeatureConfig = FeatureConfig()):
        """
        Initialize the feature engineer with configuration.
        
        Args:
            config: FeatureConfig instance with indicator parameters
        """
        self.cfg = config

    def _validate_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Ensure data has required columns and proper index.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Validated DataFrame or None if validation fails
        """
        if df is None or df.empty:
            logger.error("Empty dataframe provided.")
            return None
            
        # Standardize Columns
        col_map = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume',
            'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low',
            'CLOSE': 'Close', 'VOLUME': 'Volume'
        }
        df = df.rename(columns=col_map)
        
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required):
            missing = [col for col in required if col not in df.columns]
            logger.error(f"Missing required columns: {missing}. Found: {list(df.columns)}")
            return None
            
        # Standardize Index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            # Try converting index
            try:
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                logger.error(f"Index is not datetime and no 'Date' column found: {e}")
                return None
        
        df = df.sort_index()
        return df

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add standard momentum, trend, and volatility indicators.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with technical indicators added
        """
        c = self.cfg
        
        # 1. Momentum: RSI & Stochastic
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=c.rsi_window).rsi()
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
        df['Stoch_K'] = stoch.stoch()
        
        # 2. Trend: MACD & ADX
        macd = ta.trend.MACD(
            df['Close'], 
            window_slow=c.mac_slow, 
            window_fast=c.mac_fast, 
            window_sign=c.mac_signal
        )
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff()
        
        # 3. Volatility: ATR & Bollinger Bands
        df['ATR'] = ta.volatility.AverageTrueRange(
            df['High'], df['Low'], df['Close'], window=c.atr_window
        ).average_true_range()
        
        bb = ta.volatility.BollingerBands(
            df['Close'], window=c.bb_window, window_dev=c.bb_std
        )
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Lower'] = bb.bollinger_lband()
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['Close']
        
        # 4. Volume: VWAP (Critical for Intraday)
        vwap = ta.volume.VolumeWeightedAveragePrice(
            df['High'], df['Low'], df['Close'], df['Volume'], window=c.bb_window
        )
        df['VWAP'] = vwap.volume_weighted_average_price()
        df['Dist_VWAP'] = (df['Close'] - df['VWAP']) / df['VWAP']  # Percentage distance from VWAP
        
        return df

    def add_smart_money_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add synthetic institutional metrics.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with Smart Money features added
        """
        c = self.cfg
        
        # 1. Synthetic IV (Parkinson Volatility)
        # Measures High/Low expansion (True Range Volatility)
        const_parkinson = 1.0 / (4.0 * np.log(2.0))
        log_hl = np.log(df['High'] / df['Low']).replace(0, 0.00001)
        df['Parkinson_Var'] = (log_hl ** 2).rolling(window=c.synthetic_iv_window).sum() * const_parkinson
        df['Synthetic_IV'] = np.sqrt(df['Parkinson_Var']) * 100
        
        # 2. Smart Money Flow (Detrended OBV)
        # Isolates volume buying pressure from price trend
        obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        df['Smart_Money_Flow'] = obv - obv.rolling(window=c.smart_money_window).mean()
        
        # 3. Sentiment Skew (Fear vs Greed)
        # Skewness of returns over last hour (60 mins)
        df['Returns'] = df['Close'].pct_change()
        df['Sentiment_Skew'] = df['Returns'].rolling(window=60).skew()
        
        return df

    def add_multi_timeframe_context(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resamples data to 5m/15m to get trend context, then maps it back to 1m.
        
        Args:
            df: DataFrame with 1-minute data
            
        Returns:
            DataFrame with multi-timeframe features added
        """
        logger.info("   Adding Multi-Timeframe Context (5m, 15m)...")
        
        # Extract only OHLCV columns for resampling (avoid resampling derived features)
        ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df_ohlcv = df[ohlcv_cols].copy()
        
        # Define aggregations
        agg_dict = {
            'Open': 'first', 
            'High': 'max', 
            'Low': 'min', 
            'Close': 'last', 
            'Volume': 'sum'
        }
        
        # 1. Generate 5-min Context
        df_5m = df_ohlcv.resample('5min').agg(agg_dict).dropna()
        if len(df_5m) > 0:
            df_5m['RSI_5m'] = ta.momentum.RSIIndicator(df_5m['Close'], window=14).rsi()
            df_5m['EMA_5m'] = ta.trend.EMAIndicator(df_5m['Close'], window=20).ema_indicator()
            df_5m['Trend_5m'] = np.where(df_5m['Close'] > df_5m['EMA_5m'], 1, -1)
            
            # Merge back to 1-minute data (Forward Fill to avoid look-ahead bias)
            features_5m = df_5m[['RSI_5m', 'Trend_5m']].reindex(df.index).ffill()
            df = pd.concat([df, features_5m], axis=1)
        
        # 2. Generate 15-min Context
        df_15m = df_ohlcv.resample('15min').agg(agg_dict).dropna()
        if len(df_15m) > 0:
            df_15m['RSI_15m'] = ta.momentum.RSIIndicator(df_15m['Close'], window=14).rsi()
            df_15m['ATR_15m'] = ta.volatility.AverageTrueRange(
                df_15m['High'], df_15m['Low'], df_15m['Close']
            ).average_true_range()
            
            # Merge back to 1-minute data
            features_15m = df_15m[['RSI_15m', 'ATR_15m']].reindex(df.index).ffill()
            df = pd.concat([df, features_15m], axis=1)
        
        return df

    def add_lag_features(self, df: pd.DataFrame, lags: List[int] = None) -> pd.DataFrame:
        """
        Add lagged returns for ML prediction.
        
        Args:
            df: DataFrame with price data
            lags: List of lag periods (default: [1, 2, 3, 5])
            
        Returns:
            DataFrame with lag features added
        """
        if lags is None:
            lags = [1, 2, 3, 5]
        
        for lag in lags:
            df[f'Return_Lag_{lag}'] = df['Close'].pct_change(lag)
            df[f'Vol_Lag_{lag}'] = df['Volume'].pct_change(lag)
        
        return df

    def generate_features(self, input_file: str, output_dir: Optional[str] = None, 
                         symbol: Optional[str] = None) -> Optional[str]:
        """
        Main execution pipeline.
        
        Args:
            input_file: Path to input CSV file
            output_dir: Output directory (defaults to input file directory)
            symbol: Stock symbol (for backward compatibility)
            
        Returns:
            Path to saved file or None if fails
        """
        logger.info(f"📂 Loading data from {input_file}...")
        
        try:
            # Try reading with index_col=0 first (common format)
            try:
                df = pd.read_csv(input_file, index_col=0, parse_dates=True)
            except Exception:
                # Fallback: read without index_col
                df = pd.read_csv(input_file, parse_dates=True)
            
            df = self._validate_data(df)
            
            if df is None:
                return None
            
            logger.info(f"   ✅ Loaded {len(df)} rows")
            
            # Feature Engineering Pipeline
            logger.info("   1/4 Calculating Technical Indicators...")
            df = self.add_technical_indicators(df)
            
            logger.info("   2/4 Calculating Smart Money Features...")
            df = self.add_smart_money_features(df)
            
            logger.info("   3/4 Adding Multi-Timeframe Context...")
            df = self.add_multi_timeframe_context(df)
            
            logger.info("   4/4 Adding Lag Features...")
            df = self.add_lag_features(df)
            
            # Clean up (Drop initial NaNs from rolling windows)
            original_len = len(df)
            df.dropna(inplace=True)
            dropped = original_len - len(df)
            if dropped > 0:
                logger.info(f"   Dropped {dropped} rows of NaN values (startup period).")
            
            # Save
            if output_dir is None:
                output_dir = os.path.dirname(input_file)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Infer symbol from filename if possible
            filename_base = os.path.basename(input_file).replace('.csv', '').replace('_raw', '')
            if symbol:
                output_filename = f"{symbol}_intraday_features.csv"
            else:
                output_filename = f"{filename_base}_features.csv"
            
            output_path = os.path.join(output_dir, output_filename)
            
            df.to_csv(output_path)
            logger.info(f"✅ Features saved to: {output_path}")
            logger.info(f"   Final Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return None


# --- Backward Compatibility Functions ---
def calculate_intraday_indicators(df: pd.DataFrame, symbol: str, interval: str = '1') -> Optional[pd.DataFrame]:
    """
    Backward compatibility wrapper for the class-based implementation.
    
    Args:
        df: DataFrame with OHLCV data and Date index
        symbol: Stock symbol
        interval: Interval in minutes (default: '1')
    
    Returns:
        DataFrame with all indicators added, or None if fails
    """
    logger.info(f"📊 Calculating technical indicators for {symbol} ({interval}-minute data)...")
    logger.info(f"   Input data: {len(df)} rows, {len(df.columns)} columns")
    
    try:
        engineer = IntradayFeatureEngineer()
        
        # Validate and process directly
        df_validated = engineer._validate_data(df)
        if df_validated is None:
            return None
        
        # Apply feature engineering pipeline
        df_result = engineer.add_technical_indicators(df_validated)
        df_result = engineer.add_smart_money_features(df_result)
        df_result = engineer.add_multi_timeframe_context(df_result)
        df_result = engineer.add_lag_features(df_result)
        
        # Clean up NaNs
        original_len = len(df_result)
        df_result.dropna(inplace=True)
        dropped = original_len - len(df_result)
        if dropped > 0:
            logger.info(f"   Dropped {dropped} rows of NaN values (startup period).")
        
        logger.info(f"✅ Calculated indicators: {len(df_result.columns)} total columns")
        logger.info(f"   - Original columns: {len(df.columns)}")
        logger.info(f"   - Indicator columns: {len(df_result.columns) - len(df.columns)}")
        
        return df_result
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}", exc_info=True)
        return None


def save_intraday_indicators(df_ta: pd.DataFrame, symbol: str, interval: str, output_dir: str) -> Optional[str]:
    """
    Backward compatibility wrapper for saving indicators.
    
    Args:
        df_ta: DataFrame with indicators
        symbol: Stock symbol
        interval: Interval in minutes
        output_dir: Output directory path
    
    Returns:
        Path to saved file, or None if fails
    """
    if df_ta is None or df_ta.empty:
        logger.warning("No data to save.")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{symbol}_intraday_{interval}min_indicators.csv")
    df_ta.to_csv(filename)
    logger.info(f"💾 Saved indicators data to {filename}")
    return filename


def process_intraday_file(input_file: str, symbol: str, interval: str = '1', 
                         output_dir: Optional[str] = None) -> Optional[str]:
    """
    Backward compatibility wrapper for processing files.
    
    Args:
        input_file: Path to input CSV file
        symbol: Stock symbol
        interval: Interval in minutes
        output_dir: Output directory (optional, defaults to same as input)
    
    Returns:
        Path to saved file with indicators, or None if fails
    """
    engineer = IntradayFeatureEngineer()
    
    if output_dir is None:
        output_dir = os.path.dirname(input_file)
    
    return engineer.generate_features(input_file, output_dir, symbol)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Advanced Intraday Feature Engineer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 calculate_intraday_indicators.py data.csv --symbol HDFCBANK.NS
  python3 calculate_intraday_indicators.py data.csv --symbol RELIANCE.NS --output-dir results/
        """
    )
    parser.add_argument('input_file', help='Path to raw OHLCV CSV')
    parser.add_argument('--symbol', help='Stock symbol (optional, inferred from filename if not provided)')
    parser.add_argument('--output-dir', help='Directory to save processed data')
    parser.add_argument('--interval', default='1', help='Interval in minutes (for backward compatibility)')
    
    args = parser.parse_args()
    
    engineer = IntradayFeatureEngineer()
    result_path = engineer.generate_features(
        args.input_file, 
        args.output_dir, 
        symbol=args.symbol
    )
    
    if result_path:
        print(f"\n✅ Successfully generated features")
        print(f"   Output file: {result_path}")
        
        # Show summary
        try:
            df_ta = pd.read_csv(result_path, index_col=0, parse_dates=True, nrows=5)
            print(f"\n   Columns: {len(df_ta.columns)}")
            print(f"   Sample data:")
            print(df_ta.head())
        except Exception as e:
            logger.warning(f"Could not display summary: {e}")
    else:
        print("\n❌ Feature generation failed")
        sys.exit(1)
