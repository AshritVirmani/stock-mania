"""
Advanced Intraday Pattern Discovery - Orchestrator

A multi-threaded discovery engine that:
1. Injects "Smart Money" features (Synthetic IV, Flow, Skew) into raw data.
2. Executes Time, Volume, and Price analysis in parallel.
3. Aggregates findings into a comprehensive institutional report.
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add script directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Go up two levels: scripts/dhan -> scripts -> project root
LEGACY_SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "legacy"
sys.path.append(str(SCRIPT_DIR))
sys.path.append(str(LEGACY_SCRIPTS_DIR))

# Import Analysis Modules (from same directory)
# (Using try-except to handle potentially missing modules gracefully)
try:
    from analyze_intraday_time_patterns import analyze_time_patterns
    from analyze_intraday_volume_patterns import analyze_volume_patterns
    from analyze_intraday_price_patterns import analyze_price_patterns
    from analyze_indicator_combinations import analyze_combinations
    from generate_intraday_pattern_report import generate_report
    from analyze_algo_trading_patterns import analyze_algo_patterns
    # Import the enhanced analyzer we built earlier
    from simple_intraday_analysis import SmartMoneyAnalyzer, run_simple_analysis
    SMART_MONEY_AVAILABLE = True
    ALGO_ANALYSIS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️  Some analysis modules are missing: {e}")
    SMART_MONEY_AVAILABLE = False
    ALGO_ANALYSIS_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PatternOrchestrator")


class PatternDiscoveryOrchestrator:
    """
    Advanced pattern discovery orchestrator with parallel processing
    and Smart Money feature injection.
    """
    
    def __init__(self, symbol: str, data_file: str, output_base_dir: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            symbol: Stock symbol
            data_file: Path to input data CSV file
            output_base_dir: Custom output directory (optional)
        """
        self.symbol = symbol.upper().strip()
        self.data_file = Path(data_file)
        
        # Determine Output Directory
        if output_base_dir:
            self.base_dir = Path(output_base_dir)
        else:
            # Default: ../pattern_analysis/ relative to data file
            self.base_dir = self.data_file.parent.parent / "pattern_analysis"
            
        self.dirs = {
            'root': self.base_dir,
            'smart_money': self.base_dir / 'smart_money',
            'time': self.base_dir / 'time_patterns',
            'volume': self.base_dir / 'volume_patterns',
            'price': self.base_dir / 'price_patterns',
            'indicators': self.base_dir / 'indicator_combinations',
            'simple': self.base_dir / 'simple'
        }
        
        # Create directories
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Injects Institutional Features (Synthetic IV, Smart Money Flow) 
        if they are missing from the input data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with Smart Money features added
        """
        required_features = ['Synthetic_IV', 'Smart_Money_Flow', 'Sentiment_Skew']
        
        if all(col in df.columns for col in required_features):
            logger.info("✅ Input data already contains Smart Money features.")
            return df

        logger.info("⚡ Injecting Smart Money Features (Synthetic IV, OBV, Skew)...")
        try:
            # 1. Synthetic IV (Parkinson Volatility)
            if 'High' in df.columns and 'Low' in df.columns:
                const = 1.0 / (4.0 * np.log(2.0))
                log_hl = np.log(df['High'] / df['Low']).replace(0, 0.00001)
                df['Parkinson_Var'] = (log_hl ** 2).rolling(30).sum() * const
                df['Synthetic_IV'] = np.sqrt(df['Parkinson_Var']) * 100
                logger.info("   ✅ Synthetic IV calculated")
            
            # 2. Smart Money Flow (Detrended OBV)
            if 'Close' in df.columns and 'Volume' in df.columns:
                obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                df['Smart_Money_Flow'] = obv - obv.rolling(200).mean()
                logger.info("   ✅ Smart Money Flow calculated")
            
            # 3. Sentiment Skew
            if 'Close' in df.columns:
                returns = df['Close'].pct_change()
                df['Sentiment_Skew'] = returns.rolling(60).skew()
                logger.info("   ✅ Sentiment Skew calculated")
                
            logger.info("   ✅ All Smart Money features injected successfully.")
            
            # Save enriched data for inspection
            enriched_path = self.dirs['smart_money'] / f"{self.symbol}_enriched_data.csv"
            df.to_csv(enriched_path)
            logger.info(f"   💾 Enriched data saved to: {enriched_path}")
            
        except Exception as e:
            logger.error(f"⚠️  Feature injection failed: {e}. Proceeding with raw data.", exc_info=True)
            
        return df

    def run_analysis_step(self, func, name: str, df: pd.DataFrame, output_dir: Path) -> tuple:
        """
        Wrapper to run a single analysis step safely with error isolation.
        
        Args:
            func: Analysis function to execute
            name: Name of the analysis step
            df: DataFrame to analyze
            output_dir: Output directory path
            
        Returns:
            Tuple of (name, success, result)
        """
        try:
            logger.info(f"▶️  Starting {name}...")
            # Some functions might return a path, others boolean, or None
            result = func(df, self.symbol, str(output_dir))
            logger.info(f"✅ {name} Completed.")
            return name, True, result
        except Exception as e:
            logger.error(f"❌ {name} Failed: {e}", exc_info=True)
            return name, False, str(e)

    def run(self, use_raw_data: bool = True) -> bool:
        """
        Execute the full pattern discovery pipeline.
        
        Args:
            use_raw_data: If True, run simple analysis on raw data
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("="*80)
        logger.info(f"🔎 STARTING DISCOVERY ENGINE: {self.symbol}")
        logger.info("="*80)

        # 1. Load Data
        if not self.data_file.exists():
            logger.error(f"❌ File not found: {self.data_file}")
            return False

        logger.info(f"📂 Loading data from {self.data_file}...")
        try:
            df = pd.read_csv(self.data_file, index_col=0, parse_dates=True)
            logger.info(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return False

        # 2. Enrich Data (The "Value Add")
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Data Enrichment")
        logger.info("="*80)
        df = self.enrich_data(df)

        # 3. Simple Pattern Analysis (if raw data)
        simple_analysis_dir = None
        if use_raw_data:
            logger.info("\n" + "="*80)
            logger.info("STEP 2: Simple Pattern Analysis")
            logger.info("="*80)
            try:
                if SMART_MONEY_AVAILABLE:
                    run_simple_analysis(str(self.data_file), self.symbol, str(self.dirs['simple']))
                    simple_analysis_dir = str(self.dirs['simple'])
                    logger.info("   ✅ Simple analysis completed")
                else:
                    logger.warning("   ⚠️  Smart Money analyzer not available, skipping simple analysis")
            except Exception as e:
                logger.error(f"   ❌ Simple analysis failed: {e}")

        # 4. Parallel Execution of Independent Modules
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Parallel Pattern Analysis")
        logger.info("="*80)
        logger.info("   Running Time, Volume, and Price analysis in parallel...")
        
        results = {}
        tasks = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Schedule tasks
            tasks.append(executor.submit(
                self.run_analysis_step, 
                analyze_time_patterns, 
                "Time Analysis", 
                df, 
                self.dirs['time']
            ))
            tasks.append(executor.submit(
                self.run_analysis_step, 
                analyze_volume_patterns, 
                "Volume Analysis", 
                df, 
                self.dirs['volume']
            ))
            tasks.append(executor.submit(
                self.run_analysis_step, 
                analyze_price_patterns, 
                "Price Analysis", 
                df, 
                self.dirs['price']
            ))
            
            # Wait for completion and collect results
            for future in as_completed(tasks):
                name, success, output = future.result()
                results[name] = {"success": success, "output": str(output) if output else None}

        # 4.5. Algo Trading Pattern Analysis
        logger.info("\n" + "="*80)
        logger.info("STEP 4.5: Algo Trading Pattern Analysis")
        logger.info("="*80)
        
        algo_dir = self.dirs['root'] / "algo_patterns"
        algo_dir.mkdir(exist_ok=True)
        
        # Find iceberg file
        iceberg_file = None
        if simple_analysis_dir:
            iceberg_file = Path(simple_analysis_dir) / f"{self.symbol}_iceberg.csv"
            if not iceberg_file.exists():
                iceberg_file = None
        
        if ALGO_ANALYSIS_AVAILABLE:
            try:
                logger.info("▶️  Starting Algo Trading Analysis...")
                analyze_algo_patterns(df, self.symbol, str(algo_dir), iceberg_file=str(iceberg_file) if iceberg_file else None)
                results["Algo Trading"] = {"success": True, "output": str(algo_dir)}
                logger.info("   ✅ Algo trading analysis completed")
            except Exception as e:
                logger.error(f"   ❌ Algo trading analysis failed: {e}")
                results["Algo Trading"] = {"success": False, "output": str(e)}
        else:
            logger.warning("   ⚠️  Algo trading analysis module not available")
            results["Algo Trading"] = {"success": False, "output": "Module not available"}
        
        # 5. Sequential Execution (Dependent Modules)
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Institutional & Indicator Analysis")
        logger.info("="*80)
        
        # Smart Money Analysis (Uses enriched data)
        try:
            logger.info("▶️  Starting Institutional Footprint Analysis...")
            if SMART_MONEY_AVAILABLE and 'SmartMoneyAnalyzer' in globals():
                analyzer = SmartMoneyAnalyzer()
                analyzer.run_analysis(str(self.data_file), self.symbol, str(self.dirs['smart_money']))
                results["Smart Money"] = {"success": True, "output": str(self.dirs['smart_money'])}
                logger.info("   ✅ Institutional analysis completed")
            else:
                logger.warning("   ⚠️  Smart Money analyzer not available")
                results["Smart Money"] = {"success": False, "output": "Module not available"}
        except Exception as e:
            logger.error(f"❌ Smart Money Analysis Failed: {e}")
            results["Smart Money"] = {"success": False, "output": str(e)}

        # Indicator Combinations (Only if indicators exist)
        indicator_cols = [c for c in df.columns if any(x in c.lower() for x in ['rsi', 'macd', 'bb', 'sma', 'ema', 'atr'])]
        if len(indicator_cols) > 5:
            logger.info(f"   Found {len(indicator_cols)} indicator columns. Running combination analysis...")
            name, success, output = self.run_analysis_step(
                analyze_combinations, 
                "Indicator Combinations", 
                df, 
                self.dirs['indicators']
            )
            results[name] = {"success": success, "output": str(output) if output else None}
        else:
            logger.info("   ⚠️  No indicator columns found. Skipping indicator combination analysis.")
            results["Indicator Combinations"] = {"success": False, "output": "Insufficient indicators"}

        # 6. Generate Report
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Report Generation")
        logger.info("="*80)
        
        report_path = None
        try:
            report_path = generate_report(
                self.symbol, 
                str(self.dirs['root']), 
                str(self.dirs['root']), 
                simple_analysis_dir
            )
            logger.info(f"   ✅ Report generated: {report_path}")
            results["Report"] = {"success": True, "output": str(report_path)}
        except Exception as e:
            logger.error(f"   ❌ Report generation failed: {e}")
            results["Report"] = {"success": False, "output": str(e)}

        # 7. Save Execution Summary
        summary_path = self.dirs['root'] / "discovery_summary.json"
        summary_data = {
            "symbol": self.symbol,
            "timestamp": datetime.now().isoformat(),
            "data_file": str(self.data_file),
            "results": results,
            "summary": {
                "total_steps": len(results),
                "successful": sum(1 for r in results.values() if r.get("success", False)),
                "failed": sum(1 for r in results.values() if not r.get("success", False))
            }
        }
        
        try:
            with open(summary_path, 'w') as f:
                json.dump(summary_data, f, indent=4, default=str)
            logger.info(f"   💾 Summary saved to: {summary_path}")
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to save summary: {e}")

        # Final Report
        logger.info("\n" + "="*80)
        logger.info("✅ DISCOVERY COMPLETE")
        logger.info("="*80)
        logger.info(f"\n📁 Results saved in: {self.dirs['root']}/")
        logger.info(f"\n📊 Execution Summary:")
        logger.info(f"   Total Steps: {summary_data['summary']['total_steps']}")
        logger.info(f"   Successful: {summary_data['summary']['successful']}")
        logger.info(f"   Failed: {summary_data['summary']['failed']}")
        
        if report_path:
            logger.info(f"\n📄 Report available at: {report_path}")
        
        return summary_data['summary']['successful'] > 0


# --- Backward Compatibility Functions ---
def run_pattern_discovery(symbol: str, data_file: str, use_raw_data: bool = True) -> bool:
    """
    Backward compatibility wrapper for the class-based implementation.
    
    Args:
        symbol: Stock symbol
        data_file: Path to input data CSV (raw OHLCV or indicators)
        use_raw_data: If True, expects raw OHLCV data and runs simple analysis first
    
    Returns:
        True if successful, False otherwise
    """
    orchestrator = PatternDiscoveryOrchestrator(symbol, data_file)
    return orchestrator.run(use_raw_data=use_raw_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Advanced Intraday Pattern Discovery - Multi-threaded with Smart Money features',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover patterns from raw data
  python3 intraday_pattern_discovery.py RELIANCE.NS --data-file data/RELIANCE.NS_intraday_1min_raw.csv
  
  # Discover patterns from indicator data
  python3 intraday_pattern_discovery.py HDFCBANK.NS --data-file data/HDFCBANK.NS_indicators.csv --use-indicators
  
  # Custom output directory
  python3 intraday_pattern_discovery.py TCS.NS --data-file data/TCS.csv --output-dir custom_output/
        """
    )
    parser.add_argument('symbol', help='Stock Symbol (e.g. RELIANCE.NS)')
    parser.add_argument('--data-file', required=True, help='Path to CSV data')
    parser.add_argument('--output-dir', help='Custom output directory')
    parser.add_argument('--use-raw-data', action='store_true', default=True, 
                       help='Treat input as raw OHLCV data (default: True)')
    parser.add_argument('--use-indicators', action='store_true', 
                       help='Treat input as indicators data (overrides --use-raw-data)')
    
    args = parser.parse_args()
    
    use_raw = args.use_raw_data and not args.use_indicators
    
    orchestrator = PatternDiscoveryOrchestrator(
        symbol=args.symbol,
        data_file=args.data_file,
        output_base_dir=args.output_dir
    )
    
    success = orchestrator.run(use_raw_data=use_raw)
    
    if not success:
        logger.error("\n❌ Pattern discovery completed with errors. Check logs for details.")
        sys.exit(1)
    
    logger.info("\n✅ Pattern discovery completed successfully!")
