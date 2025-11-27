"""
Intraday TA Analysis Pipeline - Orchestrator

A production-grade pipeline that manages data fetching, feature engineering,
and accuracy backtesting with smart caching and market-hour filtering.
"""

import os
import sys
import argparse
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

# Setup Project Path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Go up two levels: scripts/dhan -> scripts -> project root
LEGACY_SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "legacy"
sys.path.append(str(SCRIPT_DIR))
sys.path.append(str(LEGACY_SCRIPTS_DIR))

# Import Custom Modules (from same directory)
from fetch_intraday_data import fetch_intraday_dhan_data, save_intraday_data
from calculate_intraday_indicators import IntradayFeatureEngineer, save_intraday_indicators
from analyze_intraday_ta_accuracy import analyze_all_indicators, save_accuracy_results
from rank_intraday_indicators import generate_all_visualizations

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PipelineOrchestrator")


class AnalysisPipeline:
    """
    Production-grade pipeline for intraday TA analysis.
    Handles data fetching, feature engineering, and accuracy backtesting
    with smart caching and market-hour filtering.
    """
    
    def __init__(self, symbol: str, interval: str = '1'):
        """
        Initialize the analysis pipeline.
        
        Args:
            symbol: Stock symbol (e.g., 'HDFCBANK' or 'HDFCBANK.NS')
            interval: Time interval in minutes (default: '1')
        """
        self.symbol = symbol.upper().strip()
        if not self.symbol.endswith('.NS'):
            self.symbol += '.NS'
        self.interval = interval
        
        # Setup Paths
        self.base_dir = Path(PROJECT_ROOT) / "analysis_results" / self.symbol / "intraday_analysis"
        self.dirs = {
            'base': self.base_dir,
            'data': self.base_dir / 'data',
            'results': self.base_dir / 'results',
            'visualizations': self.base_dir / 'visualizations'
        }
        
        # Create directories
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def _filter_market_hours(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter data to only include market hours (09:15 to 15:30 IST).
        
        Args:
            df: DataFrame with datetime index
            
        Returns:
            Filtered DataFrame with only market hours data
        """
        if df is None or df.empty:
            return df
        
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning("Index is not DatetimeIndex, cannot filter market hours")
            return df
        
        # Filter to market hours: 09:15 to 15:30 IST
        # Using between_time which works on time component regardless of date
        try:
            filtered_df = df.between_time('09:15', '15:30')
            if len(filtered_df) < len(df):
                logger.info(f"   Filtered {len(df) - len(filtered_df)} rows outside market hours")
            return filtered_df
        except Exception as e:
            logger.warning(f"Could not filter market hours: {e}")
            return df

    def _validate_data(self, df: pd.DataFrame, stage: str) -> bool:
        """
        Validate data quality at each pipeline stage.
        
        Args:
            df: DataFrame to validate
            stage: Stage name for logging
            
        Returns:
            True if valid, False otherwise
        """
        if df is None or df.empty:
            logger.error(f"❌ {stage}: Data is None or empty")
            return False
        
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"❌ {stage}: Missing required columns: {missing_cols}")
            return False
        
        # Check for excessive NaN values
        nan_pct = df[required_cols].isna().sum().sum() / (len(df) * len(required_cols))
        if nan_pct > 0.1:  # More than 10% NaN
            logger.warning(f"⚠️  {stage}: High NaN percentage: {nan_pct*100:.1f}%")
        
        return True

    def run(self, from_date: str, to_date: str, force_download: bool = False) -> bool:
        """
        Execute the full analysis pipeline.
        
        Args:
            from_date: Start date in 'YYYY-MM-DD' format
            to_date: End date in 'YYYY-MM-DD' format
            force_download: If True, force re-download even if cached data exists
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("="*80)
        logger.info(f"🚀 STARTING PIPELINE: {self.symbol} ({self.interval}m)")
        logger.info(f"   Date Range: {from_date} to {to_date}")
        logger.info("="*80)

        # 1. DATA INGESTION
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Data Ingestion")
        logger.info("="*80)
        
        raw_file_path = self.dirs['data'] / f"{self.symbol}_intraday_{self.interval}min_raw.csv"
        df_raw = None

        if raw_file_path.exists() and not force_download:
            logger.info(f"📂 Found cached data: {raw_file_path.name}")
            try:
                df_raw = pd.read_csv(raw_file_path, index_col=0, parse_dates=True)
                logger.info(f"   ✅ Loaded {len(df_raw)} rows from cache")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load cached data: {e}. Fetching fresh data...")
                df_raw = None
        
        if df_raw is None or df_raw.empty or force_download:
            logger.info("📡 Fetching fresh data from API...")
            df_raw = fetch_intraday_dhan_data(self.symbol, from_date, to_date, self.interval)
            
            if df_raw is not None and not df_raw.empty:
                # Save raw data
                save_intraday_data(df_raw, self.symbol, self.interval, str(self.dirs['data']))
                logger.info(f"   ✅ Fetched and saved {len(df_raw)} rows")
            else:
                logger.error("❌ Failed to fetch data from API")
                return False
        
        if not self._validate_data(df_raw, "Data Ingestion"):
            return False

        # 2. FEATURE ENGINEERING
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Feature Engineering")
        logger.info("="*80)
        logger.info("   Calculating Technical Indicators & Smart Money Features...")
        
        try:
            engineer = IntradayFeatureEngineer()
            
            # Process the dataframe directly
            df_features = engineer._validate_data(df_raw.copy())
            if df_features is None:
                return False
            
            df_features = engineer.add_technical_indicators(df_features)
            df_features = engineer.add_smart_money_features(df_features)
            df_features = engineer.add_multi_timeframe_context(df_features)
            df_features = engineer.add_lag_features(df_features)
            
            # Filter Market Hours before Analysis (critical for accuracy)
            logger.info("   Filtering to market hours (09:15 - 15:30 IST)...")
            df_features = self._filter_market_hours(df_features)
            
            if not self._validate_data(df_features, "Feature Engineering"):
                return False
            
            # Save features
            feature_file = self.dirs['data'] / f"{self.symbol}_intraday_{self.interval}min_indicators.csv"
            df_features.to_csv(feature_file)
            logger.info(f"   ✅ Features generated: {len(df_features.columns)} columns, {len(df_features)} rows")
            
        except Exception as e:
            logger.error(f"❌ Feature Engineering Failed: {e}", exc_info=True)
            return False

        # 3. ACCURACY BACKTESTING
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Accuracy Backtesting")
        logger.info("="*80)
        logger.info("   Analyzing indicator accuracy (this may take a few minutes)...")
        
        try:
            results_df = analyze_all_indicators(df_features)
            
            if results_df is None or results_df.empty:
                logger.error("❌ Backtesting produced no results.")
                return False
                
            # Save accuracy results
            accuracy_file = save_accuracy_results(
                results_df, self.symbol, self.interval, str(self.dirs['results'])
            )
            logger.info(f"   ✅ Accuracy analysis complete: {len(results_df)} indicators analyzed")
            
        except Exception as e:
            logger.error(f"❌ Backtesting Failed: {e}", exc_info=True)
            return False

        # 4. VISUALIZATION & REPORTING
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Visualization & Reporting")
        logger.info("="*80)
        
        try:
            generate_all_visualizations(
                results_df, self.symbol, self.interval, str(self.dirs['visualizations'])
            )
            logger.info("   ✅ Visualizations generated")
        except Exception as e:
            logger.warning(f"⚠️  Visualization generation failed: {e}")
            # Don't fail the pipeline if visualization fails

        # 5. FINAL REPORT
        logger.info("\n" + "="*80)
        logger.info("✅ PIPELINE COMPLETE")
        logger.info("="*80)
        logger.info(f"\n📁 Results saved in: {self.dirs['base']}/")
        logger.info("\n📊 Key Files Generated:")
        logger.info(f"   ✅ Raw data: data/{self.symbol}_intraday_{self.interval}min_raw.csv")
        logger.info(f"   ✅ Features: data/{self.symbol}_intraday_{self.interval}min_indicators.csv")
        logger.info(f"   ✅ Accuracy results: results/indicator_accuracy_{self.interval}min.csv")
        logger.info(f"   ✅ Visualizations: visualizations/")
        
        # Show top 5 indicators
        if not results_df.empty and 'accuracy' in results_df.columns:
            logger.info("\n🏆 Top 5 Most Accurate Indicators:")
            top_5 = results_df.sort_values(by='accuracy', ascending=False).head(5)
            for idx, row in top_5.iterrows():
                accuracy_pct = row['accuracy'] * 100 if 'accuracy' in row else 0
                f1 = row.get('f1_score', 0)
                signals = int(row.get('total_signals', 0))
                indicator = row.get('indicator', idx)
                logger.info(f"   {indicator}: {accuracy_pct:.2f}% accuracy "
                           f"(F1: {f1:.3f}, Signals: {signals})")
        
        return True


# --- Backward Compatibility Functions ---
def get_output_directories(symbol: str) -> Dict[str, str]:
    """
    Backward compatibility wrapper for directory structure.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with directory paths as strings
    """
    pipeline = AnalysisPipeline(symbol)
    return {k: str(v) for k, v in pipeline.dirs.items()}


def run_intraday_analysis(symbol: str, from_date: str, to_date: str, interval: str = '1') -> bool:
    """
    Backward compatibility wrapper for the class-based implementation.
    
    Args:
        symbol: Stock symbol (e.g., 'HDFCBANK.NS')
        from_date: Start date in 'YYYY-MM-DD' format
        to_date: End date in 'YYYY-MM-DD' format
        interval: Interval in minutes (default: '1')
    
    Returns:
        True if successful, False otherwise
    """
    pipeline = AnalysisPipeline(symbol, interval)
    return pipeline.run(from_date, to_date, force_download=False)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Intraday TA Analysis Pipeline - Production-grade analysis with caching and market-hour filtering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze HDFCBANK for a specific date range
  python3 intraday_ta_accuracy_analysis.py HDFCBANK.NS --start 2025-11-01 --end 2025-11-20
  
  # Force re-download even if cached data exists
  python3 intraday_ta_accuracy_analysis.py RELIANCE.NS --start 2025-11-01 --end 2025-11-20 --force
  
  # Analyze with custom interval
  python3 intraday_ta_accuracy_analysis.py HDFCBANK.NS --start 2025-11-01 --end 2025-11-20 --interval 5
        """
    )
    
    parser.add_argument('symbol', help='Stock symbol (e.g., HDFCBANK or HDFCBANK.NS)')
    
    # Support both old and new argument formats
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--start', help='Start date (YYYY-MM-DD)')
    date_group.add_argument('--from-date', dest='start', help='Start date (YYYY-MM-DD) [deprecated, use --start]')
    
    date_group2 = parser.add_mutually_exclusive_group(required=True)
    date_group2.add_argument('--end', help='End date (YYYY-MM-DD)')
    date_group2.add_argument('--to-date', dest='end', help='End date (YYYY-MM-DD) [deprecated, use --end]')
    
    parser.add_argument('--interval', default='1', help='Interval in minutes (default: 1)')
    parser.add_argument('--force', action='store_true', help='Force re-download data (ignore cache)')
    
    args = parser.parse_args()
    
    # Validate symbol
    symbol = args.symbol.strip().upper()
    
    # Get date arguments (support both formats)
    start_date = args.start
    end_date = args.end
    
    # Validate dates
    try:
        from_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        to_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        if to_date_obj < from_date_obj:
            logger.error("❌ End date must be after start date.")
            sys.exit(1)
        
        days_diff = (to_date_obj - from_date_obj).days
        if days_diff > 90:
            logger.warning(f"⚠️  Date range is {days_diff} days. "
                         f"Large date ranges may take significant time to process.")
    except ValueError as e:
        logger.error(f"❌ Invalid date format: {e}")
        logger.error("   Dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    # Validate interval
    try:
        interval_int = int(args.interval)
        if interval_int < 1:
            logger.error("❌ Interval must be at least 1 minute.")
            sys.exit(1)
    except ValueError:
        logger.error("❌ Interval must be a valid integer.")
        sys.exit(1)
    
    # Run pipeline
    pipeline = AnalysisPipeline(symbol, args.interval)
    success = pipeline.run(start_date, end_date, force_download=args.force)
    
    if not success:
        logger.error("\n❌ Pipeline failed. Check logs for details.")
        sys.exit(1)
    
    logger.info("\n✅ Pipeline completed successfully!")


if __name__ == "__main__":
    main()
