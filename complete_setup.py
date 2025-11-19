"""
Complete Setup for New Ticker

This script runs the complete analysis workflow for a new stock ticker:
1. Fetch data and calculate all 86 indicators
2. Correlation analysis
3. Behavioral pattern analysis (market regimes)
4. Similarity analysis
5. Standard Donchian MCPT backtest
6. Enhanced Donchian MCPT backtest (with Red Light filtering + pattern exits)
7. Drawdown analysis
8. Comparison and summary

Usage:
    python3 complete_setup.py TICKER.NS
    python3 complete_setup.py TCS.NS
"""

import os
import sys
import subprocess
import pandas as pd

OUTPUT_DIR = "output"
BASE_ANALYSIS_DIR = "analysis_results"


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def run_complete_setup(stock_symbol):
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
    
    try:
        result = subprocess.run(
            ['python3', 'analyze_indian_stocks.py', stock_symbol],
            check=True,
            capture_output=False
        )
        analysis_file = os.path.join(OUTPUT_DIR, f"{stock_symbol}_analysis.csv")
        
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
    
    # Step 2: Correlation Analysis
    print("\n" + "="*80)
    print("STEP 2: Correlation Analysis")
    print("="*80)
    try:
        subprocess.run(
            ['python3', 'analyze_correlations.py', analysis_file],
            check=True,
            capture_output=True
        )
        print("✅ Correlation analysis complete")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Correlation analysis failed: {e}")
    
    # Step 3: Behavioral Pattern Analysis
    print("\n" + "="*80)
    print("STEP 3: Behavioral Pattern Analysis (Market Regimes)")
    print("="*80)
    print("🔍 Identifying market regimes (this may take a few minutes)...")
    try:
        subprocess.run(
            ['python3', 'behavioral_patterns.py', analysis_file],
            check=True,
            capture_output=True
        )
        print("✅ Behavioral pattern analysis complete")
        print("   - Market regimes identified")
        print("   - Regime data saved")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Behavioral pattern analysis failed: {e}")
        print("   ⚠️  Enhanced Donchian will run without regime filtering")
    
    # Step 4: Identify Red Light Regime
    print("\n" + "="*80)
    print("STEP 4: Identifying Red Light Regime")
    print("="*80)
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    regime_file = os.path.join(ticker_dir, "data_with_regimes.csv")
    
    if os.path.exists(regime_file):
        try:
            subprocess.run(
                ['python3', 'identify_red_light_regime.py', regime_file],
                check=True,
                capture_output=False
            )
        except Exception as e:
            print(f"⚠️  Red Light identification failed: {e}")
    else:
        print("⚠️  Regime data not found. Skipping Red Light identification.")
    
    # Step 5: Similarity Analysis
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
                ['python3', 'find_similar_days.py', latest_date, analysis_file],
                check=True,
                capture_output=True
            )
            print(f"✅ Similarity analysis complete for {latest_date}")
        except Exception as e:
            print(f"⚠️  Similarity analysis failed: {e}")
    else:
        print("⚠️  Regime data not found. Skipping similarity analysis.")
    
    # Step 6: Standard Donchian MCPT Backtest
    print("\n" + "="*80)
    print("STEP 6: Standard Donchian MCPT Backtest")
    print("="*80)
    
    # Check data requirements first
    try:
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
                        ['python3', 'simple_backtest_for_new_stocks.py', analysis_file],
                        check=True,
                        capture_output=False
                    )
                    print("✅ Simple backtest complete")
                except Exception as e:
                    print(f"⚠️  Simple backtest failed: {e}")
                print(f"\n   → Walk-forward analysis requires ~3 years of data")
                print(f"   → Other analyses (correlation, regimes) are still available")
            else:
                print("📊 Running walk-forward analysis with Monte Carlo Permutation Test...")
                result = subprocess.run(
                    ['python3', 'donchian_mcpt_backtest.py', analysis_file],
                    check=True,
                    capture_output=False
                )
                print("✅ Standard Donchian MCPT backtest complete")
        else:
            print("⚠️  Could not load data. Skipping Donchian backtest.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Standard Donchian backtest failed: {e}")
    except Exception as e:
        print(f"⚠️  Error checking data requirements: {e}")
    
    # Step 7: Enhanced Donchian MCPT Backtest
    print("\n" + "="*80)
    print("STEP 7: Enhanced Donchian MCPT Backtest")
    print("="*80)
    
    # Check data requirements first
    try:
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
                    ['python3', 'donchian_enhanced_backtest.py', analysis_file],
                    check=True,
                    capture_output=False
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
    walkforward_file = os.path.join(ticker_dir, "donchian_walkforward_results.csv")
    if os.path.exists(walkforward_file) and os.path.exists(regime_file):
        try:
            subprocess.run(
                ['python3', 'analyze_drawdowns.py', walkforward_file, regime_file],
                check=True,
                capture_output=False
            )
        except Exception as e:
            print(f"⚠️  Drawdown analysis failed: {e}")
    else:
        print("⚠️  Required files not found. Skipping drawdown analysis.")
    
    # Step 9: Comparison
    print("\n" + "="*80)
    print("STEP 9: Strategy Comparison")
    print("="*80)
    try:
        subprocess.run(
            ['python3', 'compare_backtests.py', stock_symbol],
            check=True,
            capture_output=False
        )
    except Exception as e:
        print(f"⚠️  Comparison failed: {e}")
    
    # Step 10: Generate Comprehensive Report
    print("\n" + "="*80)
    print("STEP 10: Generating Comprehensive Report")
    print("="*80)
    try:
        subprocess.run(
            ['python3', 'generate_analysis_report.py', stock_symbol],
            check=True,
            capture_output=True
        )
        print("✅ Comprehensive report generated")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Report generation failed: {e}")
    
    # Final Summary
    print("\n" + "="*80)
    print("✅ COMPLETE SETUP FINISHED FOR {stock_symbol}")
    print("="*80)
    
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    print(f"\n📁 All results saved in: {ticker_dir}/")
    print("\n📊 Key Files Generated:")
    print(f"   ✅ Analysis data: output/{stock_symbol}_analysis.csv")
    print(f"   ✅ Correlation heatmap: {ticker_dir}/correlation_heatmap_full.png")
    print(f"   ✅ Market regimes: {ticker_dir}/market_regimes_plot.png")
    print(f"   ✅ Regime data: {ticker_dir}/data_with_regimes.csv")
    print(f"   ✅ Standard Donchian results: {ticker_dir}/donchian_walkforward_results_readable_summary.csv")
    print(f"   ✅ Enhanced Donchian results: {ticker_dir}/donchian_enhanced_walkforward_results_readable_summary.csv")
    print(f"   ✅ Comprehensive report: {ticker_dir}/comprehensive_report.html")
    print(f"   ✅ Strategy comparison: {ticker_dir}/backtest_comparison.csv")
    
    print("\n💡 Quick Commands:")
    print(f"   # View simple summary:")
    print(f"   python3 donchian_simple_summary.py {ticker_dir}/donchian_walkforward_results.csv")
    print(f"   python3 donchian_simple_summary.py {ticker_dir}/donchian_enhanced_walkforward_results.csv")
    print(f"   # View comprehensive report:")
    print(f"   open {ticker_dir}/comprehensive_report.html")
    
    return True


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 complete_setup.py TICKER.NS")
        print("\nExample:")
        print("  python3 complete_setup.py TCS.NS")
        print("  python3 complete_setup.py RELIANCE.NS")
        print("  python3 complete_setup.py INFY.NS")
        print("\nThis will run the complete analysis workflow:")
        print("  1. Fetch data and calculate indicators")
        print("  2. Correlation analysis")
        print("  3. Behavioral pattern analysis")
        print("  4. Similarity analysis")
        print("  5. Standard Donchian MCPT backtest")
        print("  6. Enhanced Donchian MCPT backtest")
        print("  7. Drawdown analysis")
        print("  8. Strategy comparison")
        print("  9. Comprehensive report")
        return
    
    stock_symbol = sys.argv[1].strip().upper()
    
    # Ensure .NS suffix for Indian stocks
    if not stock_symbol.endswith('.NS'):
        print(f"⚠️  Adding .NS suffix for Indian stock")
        stock_symbol = stock_symbol + '.NS'
    
    run_complete_setup(stock_symbol)


if __name__ == "__main__":
    main()

