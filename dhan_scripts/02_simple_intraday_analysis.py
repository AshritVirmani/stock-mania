"""
Institutional Intraday Pattern Analyzer

A professional-grade analysis tool that derives "Smart Money" features 
(Synthetic IV, Order Flow, Sentiment Skew) from raw OHLCV data to detect 
institutional footprints like Accumulation, Stop Hunts, and Liquidity Sweeps.
"""

import os
import sys
import pandas as pd
import numpy as np
import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger("SmartMoneyAnalyzer")


@dataclass
class AnalysisConfig:
    """Configuration for sensitive pattern detection."""
    vol_z_threshold: float = 3.0       # Standard deviations for "High Volume"
    iceberg_z_threshold: float = 2.5   # Volume threshold for absorption
    volatility_window: int = 20        # Rolling window for standard volatility
    smart_money_window: int = 50       # Window for Smart Money/Liquidity checks
    synthetic_iv_window: int = 30      # Window for Parkinson Volatility
    sentiment_window: int = 60         # Window for Skewness (Fear/Greed)
    min_wick_ratio: float = 2.0        # Wick must be 2x the body size for sweeps


class SmartMoneyAnalyzer:
    """
    Analyzes intraday data to detect institutional trading patterns
    using advanced Smart Money indicators.
    """
    
    def __init__(self, config: AnalysisConfig = AnalysisConfig()):
        """
        Initialize the analyzer with configuration.
        
        Args:
            config: AnalysisConfig instance with pattern detection parameters
        """
        self.cfg = config

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data and calculate advanced "Smart Money" features.
        
        Args:
            df: Raw OHLCV DataFrame
            
        Returns:
            DataFrame with Smart Money features added
        """
        df = df.copy()
        c = self.cfg
        
        # 1. Standardize Data Structure
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            # Try to convert index if it's string
            try:
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                logger.warning(f"Could not parse index as datetime: {e}")
                # If index_col was used, try parsing first column
                if df.index.name is None or df.index.name == 'Unnamed: 0':
                    logger.info("Attempting to parse first column as date...")
            
        df.sort_index(inplace=True)
        
        # Standardize Columns
        col_map = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume',
            'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low',
            'CLOSE': 'Close', 'VOLUME': 'Volume'
        }
        df = df.rename(columns=col_map)
        
        # Validate required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}. Available: {list(df.columns)}")
        
        # 2. Basic Candle Features
        df['Returns'] = df['Close'].pct_change()
        df['Body_Size'] = abs(df['Close'] - df['Open']).replace(0, 0.01)
        df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        df['Lower_Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
        df['Candle_Range'] = df['High'] - df['Low']
        df['Avg_Range'] = df['Candle_Range'].rolling(window=c.volatility_window).mean()
        
        # 3. Volume Statistics
        df['Vol_Mean'] = df['Volume'].rolling(window=c.volatility_window).mean()
        df['Vol_Std'] = df['Volume'].rolling(window=c.volatility_window).std().replace(0, 1)
        df['Vol_Z'] = (df['Volume'] - df['Vol_Mean']) / df['Vol_Std']
        
        # -------------------------------------------------------------------
        # 🚀 SMART MONEY FEATURES (The "Hidden" Signals)
        # -------------------------------------------------------------------
        
        # A. Synthetic IV (Parkinson Volatility)
        # Formula: High/Low range is a better estimator of variance than Close/Close
        # High Synthetic IV = Market is tense, expect a big move.
        const_parkinson = 1.0 / (4.0 * np.log(2.0))
        df['Log_HL'] = np.log(df['High'] / df['Low']).replace(0, 0.0001)
        df['Parkinson_Var'] = (df['Log_HL'] ** 2).rolling(window=c.synthetic_iv_window).sum() * const_parkinson
        df['Synthetic_IV'] = np.sqrt(df['Parkinson_Var']) * 100
        
        # B. Smart Money Flow (Detrended OBV)
        # Logic: OBV tracks cumulative volume. Detrending it removes the "drift" 
        # and shows us pure Accumulation (Positive) vs Distribution (Negative).
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        df['Smart_Money_Flow'] = df['OBV'] - df['OBV'].rolling(window=200).mean()
        
        # C. Sentiment Skew (Fear vs Greed)
        # Logic: Negative Skew = Frequent small gains, rare massive drops (Put Buying behavior).
        # Positive Skew = Frequent small losses, rare massive pumps (Call Buying behavior/Lottery tickets).
        df['Sentiment_Skew'] = df['Returns'].rolling(window=c.sentiment_window).skew()
        
        # D. Liquidity Levels (Rolling Support/Resistance)
        # Used to detect Stop Hunts.
        df['Rolling_Min'] = df['Low'].rolling(window=c.smart_money_window).min().shift(1)
        df['Rolling_Max'] = df['High'].rolling(window=c.smart_money_window).max().shift(1)
        
        return df

    def detect_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Use Smart Money features to detect institutional activity.
        
        Args:
            df: DataFrame with Smart Money features
            
        Returns:
            DataFrame with pattern flags added
        """
        df = df.copy()
        c = self.cfg
        
        # 1. HIDDEN ACCUMULATION (The "Smart Money Buy")
        # Scenario: Price is making Lower Lows (or flat), but Money Flow is making Higher Highs.
        # This implies aggressive limit order buying absorbing the selling.
        price_trend = df['Close'].diff(10)
        flow_trend = df['Smart_Money_Flow'].diff(10)
        
        df['Hidden_Accumulation'] = (
            (price_trend < 0) &                 # Price is dropping/weak
            (flow_trend > 0) &                  # Money Flow is rising/strong
            (df['Synthetic_IV'] < df['Synthetic_IV'].rolling(100).mean()) # Low Volatility (Quiet accumulation)
        )
        
        # 2. INSTITUTIONAL DISTRIBUTION (The "Smart Money Sell")
        # Scenario: Price is rising, but Money Flow is dropping.
        # They are selling into the retail strength.
        df['Hidden_Distribution'] = (
            (price_trend > 0) &                 # Price is rising
            (flow_trend < 0) &                  # Money Flow is dropping
            (df['Vol_Z'] > 1.0)                 # Active volume
        )
        
        # 3. BULLISH LIQUIDITY SWEEP (The "Bear Trap")
        # Scenario: Price breaks a major support level (stops triggered), then instantly reverses.
        df['Bullish_Sweep'] = (
            (df['Low'] < df['Rolling_Min']) &           # Broke 50-period Low
            (df['Close'] > df['Open']) &                # Closed Green
            (df['Lower_Wick'] > c.min_wick_ratio * df['Body_Size']) & # Long Wick
            (df['Vol_Z'] > 2.0)                         # High Volume (Stop executions)
        )
        
        # 4. BEARISH LIQUIDITY SWEEP (The "Bull Trap")
        # Scenario: Price breaks resistance, lures breakout traders, then crashes.
        df['Bearish_Sweep'] = (
            (df['High'] > df['Rolling_Max']) &          # Broke 50-period High
            (df['Close'] < df['Open']) &                # Closed Red
            (df['Upper_Wick'] > c.min_wick_ratio * df['Body_Size']) &
            (df['Vol_Z'] > 2.0)
        )
        
        # 5. ICEBERG ABSORPTION
        # Scenario: Huge volume, Price barely moves. A massive wall is present.
        df['Iceberg'] = (
            (df['Vol_Z'] > c.iceberg_z_threshold) & 
            (df['Body_Size'] < (df['Avg_Range'] * 0.25)) & 
            (df['Candle_Range'] < df['Avg_Range'])
        )
        
        # 6. FEAR CAPITULATION (Crash Bottom)
        # Scenario: Massive Volume + High Negative Skew + Price Drop
        df['Capitulation'] = (
            (df['Vol_Z'] > 3.5) & 
            (df['Returns'] < -0.003) &
            (df['Sentiment_Skew'] < -1.0)  # Extreme Bearish Skew
        )
        
        return df

    def extract_examples(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Extract top examples for each pattern to validate.
        
        Args:
            df: DataFrame with pattern flags
            
        Returns:
            Dictionary mapping pattern names to example DataFrames
        """
        patterns = {}
        
        pattern_configs = {
            'Hidden_Accumulation': ('Smart_Money_Flow', False),
            'Hidden_Distribution': ('Vol_Z', False),
            'Bullish_Sweep': ('Vol_Z', False),
            'Bearish_Sweep': ('Vol_Z', False),
            'Iceberg': ('Vol_Z', False),
            'Capitulation': ('Vol_Z', False)
        }
        
        for pattern_name, (sort_col, ascending) in pattern_configs.items():
            if pattern_name in df.columns:
                pattern_df = df[df[pattern_name]].copy()
                if not pattern_df.empty and sort_col in pattern_df.columns:
                    pattern_df = pattern_df.sort_values(sort_col, ascending=ascending).head(10)
                patterns[pattern_name] = pattern_df
            else:
                patterns[pattern_name] = pd.DataFrame()
        
        return patterns

    def run_analysis(self, data_file: str, symbol: str, output_dir: str) -> bool:
        """
        Run the complete Smart Money analysis.
        
        Args:
            data_file: Path to raw OHLCV CSV file
            symbol: Stock symbol
            output_dir: Output directory for results
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("="*80)
        logger.info(f"🚀 Starting Smart Money Analysis for {symbol}")
        logger.info("="*80)
        
        # 1. Load Data
        try:
            logger.info(f"📂 Loading data from {data_file}...")
            # Try with index_col=0 first (common format)
            try:
                df = pd.read_csv(data_file, index_col=0, parse_dates=True)
            except Exception:
                # Fallback: read without index_col
                df = pd.read_csv(data_file, parse_dates=True)
            
            if df.empty:
                raise ValueError("CSV is empty")
            
            logger.info(f"   ✅ Loaded {len(df)} rows")
            logger.info(f"   Columns: {list(df.columns)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}", exc_info=True)
            return False
        
        # 2. Process
        try:
            logger.info("\n" + "="*80)
            logger.info("STEP 1: Calculating Smart Money Features")
            logger.info("="*80)
            logger.info("   Computing: Synthetic IV, OBV, Sentiment Skew, Liquidity Levels...")
            
            df = self.preprocess_data(df)
            logger.info("   ✅ Feature calculation complete")
            
            logger.info("\n" + "="*80)
            logger.info("STEP 2: Detecting Institutional Patterns")
            logger.info("="*80)
            logger.info("   Scanning for: Accumulation, Distribution, Sweeps, Icebergs...")
            
            df = self.detect_patterns(df)
            logger.info("   ✅ Pattern detection complete")
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}", exc_info=True)
            return False
        
        # 3. Save Results
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save Full Data with Features
            full_path = output_path / f'{symbol}_smart_money_data.csv'
            df.to_csv(full_path)
            logger.info(f"\n💾 Full dataset saved to: {full_path}")
            
            # Extract & Save Pattern Summaries
            examples = self.extract_examples(df)
            summary_stats = []
            
            logger.info("\n" + "="*80)
            logger.info("STEP 3: Pattern Summary")
            logger.info("="*80)
            
            for name, data in examples.items():
                # Count occurrences
                count = int(df[name].sum()) if name in df.columns else 0
                summary_stats.append({'Pattern': name, 'Count': count})
                
                if not data.empty:
                    logger.info(f"   👉 Found {count} signals for {name}")
                    # Save specific CSV for this pattern
                    # We include the 'Smart Money' columns for validation
                    cols = ['Close', 'Volume', 'Vol_Z', 'Synthetic_IV', 'Smart_Money_Flow', 'Sentiment_Skew']
                    valid_cols = [c for c in cols if c in data.columns]
                    
                    csv_path = output_path / f'{symbol}_{name.lower()}.csv'
                    data[valid_cols].to_csv(csv_path)
                else:
                    logger.info(f"   ⚠️  No strong signals for {name}")
            
            # Save Summary Stats
            summary_df = pd.DataFrame(summary_stats)
            summary_path = output_path / 'pattern_summary.csv'
            summary_df.to_csv(summary_path, index=False)
            logger.info(f"\n💾 Pattern summary saved to: {summary_path}")
            
            # Summary
            logger.info("\n" + "="*80)
            logger.info("✅ ANALYSIS COMPLETE")
            logger.info("="*80)
            logger.info(f"\n📁 Results saved in: {output_dir}/")
            logger.info(f"   - Full dataset: {symbol}_smart_money_data.csv")
            logger.info(f"   - Pattern summary: pattern_summary.csv")
            logger.info(f"   - Individual pattern CSVs: {len([k for k, v in examples.items() if not v.empty])} files")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}", exc_info=True)
            return False


# --- Backward Compatibility Functions ---
def run_simple_analysis(data_file: str, symbol: str, output_dir: str) -> bool:
    """
    Backward compatibility wrapper for the class-based implementation.
    
    Args:
        data_file: Path to raw OHLCV CSV file
        symbol: Stock symbol
        output_dir: Output directory
        
    Returns:
        True if successful, False otherwise
    """
    analyzer = SmartMoneyAnalyzer()
    return analyzer.run_analysis(data_file, symbol, output_dir)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Smart Money Intraday Analyzer - Detects institutional trading patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 simple_intraday_analysis.py RELIANCE.NS --data-file path/to/raw_data.csv
  python3 simple_intraday_analysis.py HDFCBANK.NS --data-file data.csv --output-dir results/
        """
    )
    
    parser.add_argument('symbol', help='Stock Symbol (e.g., RELIANCE.NS)')
    parser.add_argument('--data-file', required=True, help='Path to raw OHLCV CSV')
    parser.add_argument('--output-dir', help='Output directory (default: inferred from data-file path)')
    
    args = parser.parse_args()
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Try to infer from data_file path
        data_path = Path(args.data_file)
        base_dir = data_path.parent.parent
        output_dir = str(base_dir / "pattern_analysis" / "smart_money")
    
    # Create analyzer and run
    analyzer = SmartMoneyAnalyzer()
    success = analyzer.run_analysis(args.data_file, args.symbol, output_dir)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
