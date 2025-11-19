"""
Complete Setup for New Ticker

This script runs the complete analysis workflow for a new stock ticker:
1. Fetch data and calculate all 86 indicators
2. Intrinsic value calculation
3. Correlation analysis
4. Behavioral pattern analysis (market regimes)
5. Similarity analysis
6. Standard Donchian MCPT backtest
7. Enhanced Donchian MCPT backtest (with Red Light filtering + pattern exits)
8. Drawdown analysis
9. Strategy comparison & regime risk analysis
10. Comprehensive report
11. Whale calendar (macro + micro strategy)
12. Professional whale chart (Bloomberg-style deep dive)
13. Final dashboard (Alpha Deck - Portfolio Manager's Monitor)

Usage:
    python3 complete_setup.py TICKER.NS
    python3 complete_setup.py TCS.NS
"""

import os
import sys
import subprocess
import pandas as pd

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

BASE_ANALYSIS_DIR = os.path.join(PROJECT_ROOT, "analysis_results")


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_data_dir(stock_symbol):
    """Get data subdirectory for main analysis CSV."""
    data_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory for correlation, regimes, similarity."""
    analysis_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "analysis")
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    return analysis_dir


def get_backtests_dir(stock_symbol, strategy="standard"):
    """Get backtests subdirectory for strategy results."""
    backtests_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "backtests", strategy)
    if not os.path.exists(backtests_dir):
        os.makedirs(backtests_dir)
    return backtests_dir


def get_valuation_dir(stock_symbol):
    """Get valuation subdirectory for intrinsic value results."""
    valuation_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "valuation")
    if not os.path.exists(valuation_dir):
        os.makedirs(valuation_dir)
    return valuation_dir


def get_reports_dir(stock_symbol):
    """Get reports subdirectory for final reports."""
    reports_dir = os.path.join(get_ticker_analysis_dir(stock_symbol), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir


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
            ['python3', os.path.join(SCRIPT_DIR, '01_analyze_indian_stocks.py'), stock_symbol],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        data_dir = get_data_dir(stock_symbol)
        analysis_file = os.path.join(data_dir, f"{stock_symbol}_analysis.csv")
        
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
    
    # Step 2: Intrinsic Value Calculation
    print("\n" + "="*80)
    print("STEP 2: Intrinsic Value Calculation")
    print("="*80)
    print("💰 Calculating intrinsic value using multiple valuation methods...")
    print("   (Output will be displayed and saved to valuation folder)\n")
    try:
        # Use the calculate_intrinsic_value.py from project root (not legacy_scripts)
        calc_script = os.path.join(PROJECT_ROOT, 'calculate_intrinsic_value.py')
        valuation_dir = get_valuation_dir(stock_symbol)
        output_file = os.path.join(valuation_dir, "valuation_output.txt")
        
        # Run the script and capture output while displaying it
        result = subprocess.run(
            ['python3', calc_script, stock_symbol],
            check=True,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Display the output
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Save output to text file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n--- ERRORS/WARNINGS ---\n")
                f.write(result.stderr)
        
        print(f"\n✅ Intrinsic value calculation complete")
        print(f"   - Intrinsic value calculated using 5 methods (Graham, DCF, P/E, P/B, PEG)")
        print(f"   - Results saved to valuation/intrinsic_value.json")
        print(f"   - Terminal output saved to valuation/valuation_output.txt")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Intrinsic value calculation failed: {e}")
        if hasattr(e, 'stdout') and e.stdout:
            print(e.stdout)
        if hasattr(e, 'stderr') and e.stderr:
            print(e.stderr, file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Intrinsic value calculation error: {e}")
    
    # Step 3: Correlation Analysis
    print("\n" + "="*80)
    print("STEP 3: Correlation Analysis")
    print("="*80)
    try:
        subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '03_analyze_correlations.py'), analysis_file],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT
        )
        print("✅ Correlation analysis complete")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Correlation analysis failed: {e}")
    
    # Step 4: Behavioral Pattern Analysis
    print("\n" + "="*80)
    print("STEP 4: Behavioral Pattern Analysis (Market Regimes)")
    print("="*80)
    print("🔍 Identifying market regimes (this may take a few minutes)...")
    try:
        subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '04_behavioral_patterns.py'), analysis_file],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT
        )
        print("✅ Behavioral pattern analysis complete")
        print("   - Market regimes identified")
        print("   - Regime data saved")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Behavioral pattern analysis failed: {e}")
        print("   ⚠️  Enhanced Donchian will run without regime filtering")
    
    # Step 5: Identify Red Light Regime
    print("\n" + "="*80)
    print("STEP 4: Identifying Red Light Regime")
    print("="*80)
    analysis_dir = get_analysis_dir(stock_symbol)
    regime_file = os.path.join(analysis_dir, "data_with_regimes.csv")
    
    if os.path.exists(regime_file):
        try:
            subprocess.run(
                ['python3', os.path.join(SCRIPT_DIR, '05_identify_red_light_regime.py'), regime_file],
                check=True,
                capture_output=False,
                cwd=PROJECT_ROOT
            )
        except Exception as e:
            print(f"⚠️  Red Light identification failed: {e}")
    else:
        print("⚠️  Regime data not found. Skipping Red Light identification.")
    
    # Step 6: Similarity Analysis
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
                ['python3', os.path.join(SCRIPT_DIR, '06_find_similar_days.py'), analysis_file, '--date', latest_date],
                check=True,
                capture_output=True,
                cwd=PROJECT_ROOT
            )
            print(f"✅ Similarity analysis complete for {latest_date}")
        except Exception as e:
            print(f"⚠️  Similarity analysis failed: {e}")
    else:
        print("⚠️  Regime data not found. Skipping similarity analysis.")
    
    # Step 7: Standard Donchian MCPT Backtest
    print("\n" + "="*80)
    print("STEP 6: Standard Donchian MCPT Backtest")
    print("="*80)
    
    # Check data requirements first
    try:
        sys.path.insert(0, SCRIPT_DIR)
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
                        ['python3', os.path.join(SCRIPT_DIR, '07a_simple_backtest_for_new_stocks.py'), analysis_file],
                        check=True,
                        capture_output=False,
                        cwd=PROJECT_ROOT
                    )
                    print("✅ Simple backtest complete")
                except Exception as e:
                    print(f"⚠️  Simple backtest failed: {e}")
                print(f"\n   → Walk-forward analysis requires ~3 years of data")
                print(f"   → Other analyses (correlation, regimes) are still available")
            else:
                print("📊 Running walk-forward analysis with Monte Carlo Permutation Test...")
                result = subprocess.run(
                    ['python3', os.path.join(SCRIPT_DIR, '07b_donchian_mcpt_backtest.py'), analysis_file],
                    check=True,
                    capture_output=False,
                    cwd=PROJECT_ROOT
                )
                print("✅ Standard Donchian MCPT backtest complete")
        else:
            print("⚠️  Could not load data. Skipping Donchian backtest.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Standard Donchian backtest failed: {e}")
    except Exception as e:
        print(f"⚠️  Error checking data requirements: {e}")
    
    # Step 8: Enhanced Donchian MCPT Backtest
    print("\n" + "="*80)
    print("STEP 7: Enhanced Donchian MCPT Backtest")
    print("="*80)
    
    # Check data requirements first
    try:
        sys.path.insert(0, SCRIPT_DIR)
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
                    ['python3', os.path.join(SCRIPT_DIR, '08_donchian_enhanced_backtest.py'), analysis_file],
                    check=True,
                    capture_output=False,
                    cwd=PROJECT_ROOT
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
    backtests_standard_dir = get_backtests_dir(stock_symbol, "standard")
    walkforward_file = os.path.join(backtests_standard_dir, "results.csv")
    if os.path.exists(walkforward_file) and os.path.exists(regime_file):
        try:
            subprocess.run(
                ['python3', os.path.join(SCRIPT_DIR, '09_analyze_drawdowns.py'), walkforward_file, regime_file],
                check=True,
                capture_output=False,
                cwd=PROJECT_ROOT
            )
            print("✅ Drawdown analysis complete")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Drawdown analysis failed: {e}")
        except Exception as e:
            print(f"⚠️  Drawdown analysis error: {e}")
    else:
        print("⚠️  Required files not found. Skipping drawdown analysis.")
        if not os.path.exists(walkforward_file):
            print(f"   Missing: {walkforward_file}")
        if not os.path.exists(regime_file):
            print(f"   Missing: {regime_file}")
    
    # Step 9: Strategy Comparison & Regime Risk Analysis
    print("\n" + "="*80)
    print("STEP 9: Strategy Comparison & Regime Risk Analysis")
    print("="*80)
    print("📊 Comparing strategies and performing Bayesian regime risk analysis...")
    print("   (This includes probabilistic regime audit and filtering simulation)")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '10_compare_backtests.py'), stock_symbol],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Strategy comparison and regime risk analysis complete")
        print("   - Standard vs Enhanced strategy comparison")
        print("   - Bayesian regime risk analysis (if regime data available)")
        print("   - Filter impact equity curve generated")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Strategy comparison failed: {e}")
        print("   → This step can run independently later if needed")
    except Exception as e:
        print(f"⚠️  Strategy comparison error: {e}")
        print("   → This step can run independently later if needed")
    
    # Step 10: Generate Comprehensive Report
    print("\n" + "="*80)
    print("STEP 10: Generating Comprehensive Report")
    print("="*80)
    try:
        subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '11_generate_analysis_report.py'), stock_symbol],
            check=True,
            capture_output=True,
            cwd=PROJECT_ROOT
        )
        print("✅ Comprehensive report generated")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Report generation failed: {e}")
    
    # Step 11: Generate Whale Calendar
    print("\n" + "="*80)
    print("STEP 11: Generating Whale Calendar (Macro + Micro Strategy)")
    print("="*80)
    print("📅 Generating complete strategy calendar with regime filtering...")
    print("   - Whale signals (volume, spread, CLV analysis)")
    print("   - Regime-aware filtering (Regime 3 = blocked, Regime 1 = high conviction)")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '12_whale_calendar.py'), analysis_file],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Whale calendar generated")
        print("   - Combines whale buy signals with regime data")
        print("   - Regime 3 (Crash) signals are blocked (⛔)")
        print("   - Regime 1 (Rally) signals get gold star (⭐)")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Whale calendar generation failed: {e}")
        print("   → This step can run independently later if needed")
    except Exception as e:
        print(f"⚠️  Whale calendar error: {e}")
        print("   → This step can run independently later if needed")
    
    # Step 12: Generate Professional Whale Chart
    print("\n" + "="*80)
    print("STEP 12: Generating Professional Whale Chart (Bloomberg-Style)")
    print("="*80)
    print("📊 Generating Bloomberg-style candlestick chart with whale signals...")
    print("   - Professional candlestick visualization")
    print("   - Whale signals overlaid on price action")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '14_whale_hunter_pro.py'), analysis_file],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Professional whale chart generated")
        print("   - Bloomberg-style candlestick chart")
        print("   - Whale signals (Ignition, Stealth, Trap) overlaid")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Professional whale chart generation failed: {e}")
        print("   → This step can run independently later if needed")
        print("   → Note: Requires mplfinance library (pip install mplfinance)")
    except Exception as e:
        print(f"⚠️  Professional whale chart error: {e}")
        print("   → This step can run independently later if needed")
    
    # Step 13: Generate Final Dashboard (Alpha Deck)
    print("\n" + "="*80)
    print("STEP 13: Generating Final Dashboard (Alpha Deck)")
    print("="*80)
    print("🏛️  Assembling Portfolio Manager's Monitor...")
    print("   - Unified dashboard combining all analyses")
    print("   - Strategy validation, whale signals, regimes, forecasts")
    try:
        result = subprocess.run(
            ['python3', os.path.join(SCRIPT_DIR, '13_generate_final_dashboard.py'), stock_symbol],
            check=True,
            capture_output=False,
            cwd=PROJECT_ROOT
        )
        print("✅ Final dashboard (Alpha Deck) generated")
        print("   - Portfolio Manager's unified view")
        print("   - All PhD-grade artifacts in one place")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Final dashboard generation failed: {e}")
        print("   → This step can run independently later if needed")
    except Exception as e:
        print(f"⚠️  Final dashboard error: {e}")
        print("   → This step can run independently later if needed")
    
    # Final Summary
    print("\n" + "="*80)
    print(f"✅ COMPLETE SETUP FINISHED FOR {stock_symbol}")
    print("="*80)
    
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    print(f"\n📁 All results saved in: {ticker_dir}/")
    print("\n📊 Key Files Generated:")
    print(f"   ✅ Analysis data: data/{stock_symbol}_analysis.csv")
    print(f"   ✅ Valuation: valuation/intrinsic_value.json")
    print(f"   ✅ Valuation output: valuation/valuation_output.txt")
    print(f"   ✅ Correlation heatmap: analysis/correlation_heatmap.png")
    print(f"   ✅ Market regimes: analysis/market_regimes_plot.png")
    print(f"   ✅ Regime data: analysis/data_with_regimes.csv")
    print(f"   ✅ Standard Donchian: backtests/standard/results.csv")
    print(f"   ✅ Enhanced Donchian: backtests/enhanced/results.csv")
    print(f"   ✅ Strategy comparison: reports/backtest_comparison.csv")
    print(f"   ✅ Filter impact curve: reports/filter_impact_equity_curve.png")
    print(f"   ✅ Comprehensive report: reports/comprehensive_report.html")
    print(f"   ✅ Whale calendar: analysis/complete_whale_calendar.html")
    print(f"   ✅ Professional whale chart: analysis/whale_entry_map_pro.png")
    print(f"   ✅ Alpha Deck dashboard: {stock_symbol}_Alpha_Deck.html")
    
    print("\n💡 Quick Commands:")
    print(f"   # View simple summary:")
    print(f"   python3 donchian_simple_summary.py {ticker_dir}/backtests/standard/results.csv")
    print(f"   python3 donchian_simple_summary.py {ticker_dir}/backtests/enhanced/results.csv")
    print(f"   # View comprehensive report:")
    print(f"   open {ticker_dir}/reports/comprehensive_report.html")
    
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
        print("  2. Intrinsic value calculation")
        print("  3. Correlation analysis")
        print("  4. Behavioral pattern analysis")
        print("  5. Similarity analysis")
        print("  6. Standard Donchian MCPT backtest")
        print("  7. Enhanced Donchian MCPT backtest")
        print("  8. Drawdown analysis")
        print("  9. Strategy comparison & regime risk analysis")
        print("  10. Comprehensive report")
        print("  11. Whale calendar (macro + micro strategy)")
        print("  12. Professional whale chart (Bloomberg-style)")
        print("  13. Final dashboard (Alpha Deck)")
        return
    
    stock_symbol = sys.argv[1].strip().upper()
    
    # Ensure .NS suffix for Indian stocks
    if not stock_symbol.endswith('.NS'):
        print(f"⚠️  Adding .NS suffix for Indian stock")
        stock_symbol = stock_symbol + '.NS'
    
    run_complete_setup(stock_symbol)


if __name__ == "__main__":
    main()

