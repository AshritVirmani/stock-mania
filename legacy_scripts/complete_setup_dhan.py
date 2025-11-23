"""
Complete Dhan API Intraday Setup - Standalone Workflow

A comprehensive workflow that runs all Dhan API intraday analysis scripts in sequence:
1. Fetch intraday data from Dhan API
2. Smart Money pattern analysis
3. Feature engineering (indicators + Smart Money features)
4. TA accuracy analysis
5. Pattern discovery
6. Comprehensive reporting

Usage:
    python3 complete_setup_dhan.py SYMBOL.NS --start 2024-11-01 --end 2024-11-24 --interval 1
    python3 complete_setup_dhan.py ADANIPORTS.NS --start 2024-11-01 --end 2024-11-24
"""

import os
import sys
import argparse
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(SCRIPT_DIR))

# Import modules
from fetch_intraday_data import DhanIntradayFetcher, fetch_intraday_dhan_data
from simple_intraday_analysis import SmartMoneyAnalyzer, run_simple_analysis
from calculate_intraday_indicators import IntradayFeatureEngineer
from intraday_ta_accuracy_analysis import AnalysisPipeline
from intraday_pattern_discovery import PatternDiscoveryOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DhanCompleteSetup")


class DhanCompleteSetup:
    """
    Complete workflow for Dhan API intraday analysis.
    Orchestrates all intraday analysis scripts in proper sequence.
    """
    
    def __init__(self, symbol: str, interval: str = '1'):
        """
        Initialize the complete setup workflow.
        
        Args:
            symbol: Stock symbol (e.g., 'ADANIPORTS.NS')
            interval: Time interval in minutes (default: '1')
        """
        self.symbol = symbol.upper().strip()
        if not self.symbol.endswith('.NS'):
            self.symbol += '.NS'
        self.interval = interval
        
        # Setup directories
        self.base_dir = Path(PROJECT_ROOT) / "analysis_results" / self.symbol / "intraday_analysis"
        self.dirs = {
            'base': self.base_dir,
            'data': self.base_dir / 'data',
            'results': self.base_dir / 'results',
            'visualizations': self.base_dir / 'visualizations',
            'pattern_analysis': self.base_dir / 'pattern_analysis'
        }
        
        # Create directories
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)
    
    def step1_fetch_data(self, from_date: str, to_date: str, force_download: bool = False) -> Optional[pd.DataFrame]:
        """
        Step 1: Fetch intraday data from Dhan API.
        
        Args:
            from_date: Start date in 'YYYY-MM-DD' format
            to_date: End date in 'YYYY-MM-DD' format
            force_download: Force re-download even if cached
            
        Returns:
            DataFrame with raw OHLCV data or None if fails
        """
        logger.info("="*80)
        logger.info("STEP 1: Fetching Intraday Data from Dhan API")
        logger.info("="*80)
        
        raw_file = self.dirs['data'] / f"{self.symbol}_intraday_{self.interval}min_raw.csv"
        alt_file = self.dirs['data'] / f"{self.symbol}_intraday_{self.interval}min.csv"  # Fetcher saves without _raw
        
        # Check cache (try both naming conventions)
        cache_file = raw_file if raw_file.exists() else (alt_file if alt_file.exists() else None)
        if cache_file and not force_download:
            logger.info(f"📂 Found cached data: {cache_file.name}")
            try:
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                logger.info(f"   ✅ Loaded {len(df)} rows from cache")
                # Ensure it's saved with _raw suffix for consistency
                if cache_file != raw_file:
                    df.to_csv(raw_file)
                    logger.info(f"   📝 Saved as {raw_file.name} for consistency")
                return df
            except Exception as e:
                logger.warning(f"⚠️  Failed to load cache: {e}. Fetching fresh data...")
        
        # Fetch from Dhan API
        logger.info("📡 Fetching data from Dhan API...")
        try:
            fetcher = DhanIntradayFetcher()
            df = fetcher.fetch_data(self.symbol, from_date, to_date, self.interval)
            
            if df is None or df.empty:
                logger.error("❌ Failed to fetch data from Dhan API")
                return None
            
            # Save raw data (with _raw suffix to match expected format by other scripts)
            # The fetcher.save_to_csv saves without _raw, so we save directly
            df.to_csv(raw_file)
            logger.info(f"   ✅ Fetched and saved {len(df)} rows to {raw_file.name}")
            logger.info(f"   Date range: {df.index.min()} to {df.index.max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Data fetch failed: {e}", exc_info=True)
            return None
    
    def step2_smart_money_analysis(self, data_file: str) -> bool:
        """
        Step 2: Run Smart Money pattern analysis.
        
        Args:
            data_file: Path to raw data CSV file
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Smart Money Pattern Analysis")
        logger.info("="*80)
        
        try:
            analyzer = SmartMoneyAnalyzer()
            success = analyzer.run_analysis(
                data_file, 
                self.symbol, 
                str(self.dirs['pattern_analysis'] / 'smart_money')
            )
            
            if success:
                logger.info("   ✅ Smart Money analysis completed")
            else:
                logger.warning("   ⚠️  Smart Money analysis had issues")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Smart Money analysis failed: {e}", exc_info=True)
            return False
    
    def step3_feature_engineering(self, data_file: str) -> Optional[str]:
        """
        Step 3: Calculate technical indicators and Smart Money features.
        
        Args:
            data_file: Path to raw data CSV file
            
        Returns:
            Path to features file or None if fails
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Feature Engineering")
        logger.info("="*80)
        logger.info("   Calculating Technical Indicators + Smart Money Features...")
        
        try:
            engineer = IntradayFeatureEngineer()
            features_file = engineer.generate_features(
                data_file,
                output_dir=str(self.dirs['data']),
                symbol=self.symbol
            )
            
            if features_file:
                logger.info(f"   ✅ Features saved to: {features_file}")
                return features_file
            else:
                logger.error("   ❌ Feature engineering failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ Feature engineering failed: {e}", exc_info=True)
            return None
    
    def step4_ta_accuracy(self, from_date: str, to_date: str, force_download: bool = False) -> bool:
        """
        Step 4: Analyze TA indicator accuracy.
        
        Args:
            from_date: Start date in 'YYYY-MM-DD' format
            to_date: End date in 'YYYY-MM-DD' format
            force_download: Force re-download data
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 4: TA Indicator Accuracy Analysis")
        logger.info("="*80)
        
        try:
            pipeline = AnalysisPipeline(self.symbol, self.interval)
            success = pipeline.run(from_date, to_date, force_download=force_download)
            
            if success:
                logger.info("   ✅ TA accuracy analysis completed")
            else:
                logger.warning("   ⚠️  TA accuracy analysis had issues")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ TA accuracy analysis failed: {e}", exc_info=True)
            return False
    
    def step5_pattern_discovery(self, data_file: str) -> bool:
        """
        Step 5: Comprehensive pattern discovery.
        
        Args:
            data_file: Path to raw data CSV file
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Comprehensive Pattern Discovery")
        logger.info("="*80)
        
        try:
            orchestrator = PatternDiscoveryOrchestrator(
                symbol=self.symbol,
                data_file=data_file,
                output_base_dir=str(self.dirs['pattern_analysis'])
            )
            success = orchestrator.run(use_raw_data=True)
            
            if success:
                logger.info("   ✅ Pattern discovery completed")
                # Check if HTML report was generated
                report_files = list(self.dirs['pattern_analysis'].glob("**/*.html"))
                if report_files:
                    logger.info(f"   📄 Pattern report(s) generated: {len(report_files)} file(s)")
                    for rf in report_files:
                        logger.info(f"      - {rf.relative_to(self.dirs['base'])}")
                else:
                    logger.warning("   ⚠️  No HTML report found (may need to check pattern_analysis directory)")
            else:
                logger.warning("   ⚠️  Pattern discovery had issues")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Pattern discovery failed: {e}", exc_info=True)
            return False
    
    def run_complete_workflow(self, from_date: str, to_date: str, force_download: bool = False) -> bool:
        """
        Run the complete Dhan API intraday workflow.
        
        Args:
            from_date: Start date in 'YYYY-MM-DD' format
            to_date: End date in 'YYYY-MM-DD' format
            force_download: Force re-download data
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("="*80)
        logger.info(f"🚀 COMPLETE DHAN API INTRADAY SETUP: {self.symbol}")
        logger.info("="*80)
        logger.info(f"   Date Range: {from_date} to {to_date}")
        logger.info(f"   Interval: {self.interval} minute(s)")
        logger.info("="*80)
        
        results = {}
        
        # Step 1: Fetch Data
        df_raw = self.step1_fetch_data(from_date, to_date, force_download)
        if df_raw is None or df_raw.empty:
            logger.error("❌ Workflow failed at Step 1: Data fetch")
            return False
        
        # Ensure raw file path is correct (already handled in step1)
        raw_file = str(self.dirs['data'] / f"{self.symbol}_intraday_{self.interval}min_raw.csv")
        results['data_fetch'] = True
        
        # Step 2: Smart Money Analysis
        results['smart_money'] = self.step2_smart_money_analysis(raw_file)
        
        # Step 3: Feature Engineering
        features_file = self.step3_feature_engineering(raw_file)
        results['feature_engineering'] = features_file is not None
        
        # Step 4: TA Accuracy Analysis (uses pipeline which handles its own data fetch)
        results['ta_accuracy'] = self.step4_ta_accuracy(from_date, to_date, force_download=False)
        
        # Step 5: Pattern Discovery
        results['pattern_discovery'] = self.step5_pattern_discovery(raw_file)
        
        # Final Summary
        logger.info("\n" + "="*80)
        logger.info("✅ WORKFLOW COMPLETE")
        logger.info("="*80)
        logger.info(f"\n📊 Execution Summary:")
        logger.info(f"   ✅ Data Fetch: {'Success' if results.get('data_fetch') else 'Failed'}")
        logger.info(f"   {'✅' if results.get('smart_money') else '⚠️ '} Smart Money Analysis: {'Success' if results.get('smart_money') else 'Issues'}")
        logger.info(f"   {'✅' if results.get('feature_engineering') else '❌'} Feature Engineering: {'Success' if results.get('feature_engineering') else 'Failed'}")
        logger.info(f"   {'✅' if results.get('ta_accuracy') else '⚠️ '} TA Accuracy Analysis: {'Success' if results.get('ta_accuracy') else 'Issues'}")
        logger.info(f"   {'✅' if results.get('pattern_discovery') else '⚠️ '} Pattern Discovery: {'Success' if results.get('pattern_discovery') else 'Issues'}")
        
        logger.info(f"\n📁 Results saved in: {self.dirs['base']}/")
        logger.info(f"   - Raw data: data/{self.symbol}_intraday_{self.interval}min_raw.csv")
        logger.info(f"   - Features: data/{self.symbol}_intraday_{self.interval}min_indicators.csv")
        logger.info(f"   - Smart Money: pattern_analysis/smart_money/")
        logger.info(f"   - TA Accuracy: results/")
        logger.info(f"   - Pattern Discovery: pattern_analysis/")
        
        # Count successful steps
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        
        return successful >= 3  # At least 3 steps should succeed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Complete Dhan API Intraday Setup - Standalone Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow for ADANIPORTS
  python3 complete_setup_dhan.py ADANIPORTS.NS --start 2024-11-01 --end 2024-11-24
  
  # Run with 5-minute interval
  python3 complete_setup_dhan.py RELIANCE.NS --start 2024-11-01 --end 2024-11-24 --interval 5
  
  # Force re-download data
  python3 complete_setup_dhan.py HDFCBANK.NS --start 2024-11-01 --end 2024-11-24 --force
        """
    )
    
    parser.add_argument('symbol', help='Stock symbol (e.g., ADANIPORTS.NS)')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--interval', default='1', help='Interval in minutes (default: 1)')
    parser.add_argument('--force', action='store_true', help='Force re-download data (ignore cache)')
    
    args = parser.parse_args()
    
    # Validate dates
    try:
        from_date_obj = datetime.strptime(args.start, '%Y-%m-%d')
        to_date_obj = datetime.strptime(args.end, '%Y-%m-%d')
        
        if to_date_obj < from_date_obj:
            logger.error("❌ End date must be after start date.")
            sys.exit(1)
        
        days_diff = (to_date_obj - from_date_obj).days
        if days_diff > 90:
            logger.warning(f"⚠️  Date range is {days_diff} days. Dhan API allows max 90 days per request.")
            logger.warning(f"   The fetcher will automatically chunk the requests.")
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
    
    # Run workflow
    setup = DhanCompleteSetup(args.symbol, args.interval)
    success = setup.run_complete_workflow(
        args.start, 
        args.end, 
        force_download=args.force
    )
    
    if not success:
        logger.error("\n❌ Workflow completed with errors. Check logs for details.")
        sys.exit(1)
    
    logger.info("\n✅ Complete Dhan API workflow finished successfully!")


if __name__ == "__main__":
    main()

