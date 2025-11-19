"""
Unified Stock Analysis Tool

This is the main entry point for all analysis and visualization features.
Run this script to perform comprehensive technical analysis on your stocks.

Usage:
    python3 analyze_stock.py [stock_symbol] [--all]
    
Examples:
    python3 analyze_stock.py                    # Interactive menu
    python3 analyze_stock.py RELIANCE.NS       # Basic analysis (correlations, regimes, report)
    python3 analyze_stock.py RELIANCE.NS --all  # Full analysis with all features:
                                                #   - Correlation analysis
                                                #   - Behavioral patterns (market regimes)
                                                #   - Similarity analysis
                                                #   - Donchian MCPT backtest (walk-forward, statistical significance)
                                                #   - Comprehensive HTML report
"""

import os
import sys
import subprocess

OUTPUT_DIR = "output"
BASE_ANALYSIS_DIR = "analysis_results"


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def find_available_stocks():
    """Find all available stock analysis files."""
    if not os.path.exists(OUTPUT_DIR):
        return []
    files = [f.replace('_analysis.csv', '') for f in os.listdir(OUTPUT_DIR) 
             if f.endswith('_analysis.csv')]
    return sorted(files)


def ensure_analysis_exists(stock_symbol):
    """Check if analysis file exists, if not, generate it."""
    analysis_file = os.path.join(OUTPUT_DIR, f"{stock_symbol}_analysis.csv")
    
    if os.path.exists(analysis_file):
        return True
    
    print(f"\n⚠️  Analysis file not found for {stock_symbol}")
    print(f"   Generating analysis file now...")
    print(f"   (This may take a few minutes for stocks with long histories)\n")
    
    try:
        subprocess.run(['python3', 'analyze_indian_stocks.py', stock_symbol], 
                      check=True)
        
        # Check if file was created
        if os.path.exists(analysis_file):
            print(f"\n✅ Analysis file generated successfully!")
            return True
        else:
            print(f"\n❌ Failed to generate analysis file")
            return False
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error generating analysis: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Analysis generation cancelled by user")
        return False


def run_analysis(stock_symbol, run_all=False):
    """Run analysis for a given stock."""
    print(f"\n{'='*70}")
    print(f"📊 ANALYZING: {stock_symbol}")
    print(f"{'='*70}\n")
    
    # Ensure analysis file exists
    if not ensure_analysis_exists(stock_symbol):
        return False
    
    analysis_file = os.path.join(OUTPUT_DIR, f"{stock_symbol}_analysis.csv")
    
    # Step 1: Correlation Analysis
    print("1️⃣  Running correlation analysis...")
    try:
        subprocess.run(['python3', 'analyze_correlations.py', analysis_file], 
                      check=True, capture_output=True)
        print("   ✅ Correlation analysis complete")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Correlation analysis failed: {e}")
    
    # Step 2: Behavioral Pattern Analysis
    print("\n2️⃣  Running behavioral pattern analysis...")
    try:
        subprocess.run(['python3', 'behavioral_patterns.py', analysis_file], 
                      check=True, capture_output=True)
        print("   ✅ Behavioral pattern analysis complete")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Behavioral pattern analysis failed: {e}")
    
    # Step 3: Similarity Analysis (for latest date)
    if run_all:
        print("\n3️⃣  Running similarity analysis...")
        try:
            # Get latest date from regime data
            ticker_dir = get_ticker_analysis_dir(stock_symbol)
            regime_file = os.path.join(ticker_dir, "data_with_regimes.csv")
            if os.path.exists(regime_file):
                import pandas as pd
                df = pd.read_csv(regime_file, index_col=0, parse_dates=True)
                latest_date = df.index.max().strftime('%Y-%m-%d')
                subprocess.run(['python3', 'find_similar_days.py', latest_date, analysis_file], 
                             check=True, capture_output=True)
                print(f"   ✅ Similarity analysis complete for {latest_date}")
        except Exception as e:
            print(f"   ⚠️  Similarity analysis failed: {e}")
    
    # Step 4: Donchian MCPT Backtest (Standard)
    if run_all:
        print("\n4️⃣  Running Donchian MCPT backtest (standard)...")
        try:
            subprocess.run(['python3', 'donchian_mcpt_backtest.py', analysis_file], 
                         check=True, capture_output=True)
            print("   ✅ Donchian MCPT backtest complete")
            print("      - Walk-forward MCPT results")
            print("      - Actual vs Permuted strategy comparison")
            print("      - Statistical significance analysis")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Donchian MCPT backtest failed: {e}")
    
    # Step 4b: Enhanced Donchian MCPT Backtest (with regime filtering and pattern exits)
    if run_all:
        print("\n4️⃣b Running Enhanced Donchian MCPT backtest...")
        print("   (Regime filtering + Pattern-matching exits)")
        try:
            subprocess.run(['python3', 'donchian_enhanced_backtest.py', analysis_file], 
                         check=True, capture_output=True)
            print("   ✅ Enhanced Donchian MCPT backtest complete")
            print("      - Regime-filtered signals (only trade in trending markets)")
            print("      - Pattern-matching early exits")
            print("      - Walk-forward MCPT results")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Enhanced Donchian MCPT backtest failed: {e}")
    
    # Step 5: Generate Report
    print("\n5️⃣  Generating comprehensive report...")
    try:
        subprocess.run(['python3', 'generate_analysis_report.py', stock_symbol], 
                      check=True, capture_output=True)
        print("   ✅ Report generated")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Report generation failed: {e}")
    
    ticker_dir = get_ticker_analysis_dir(stock_symbol)
    
    print(f"\n{'='*70}")
    print(f"✅ ANALYSIS COMPLETE FOR {stock_symbol}")
    print(f"{'='*70}")
    print(f"\n📁 All results organized in: {ticker_dir}/")
    print(f"   - Correlation heatmap: correlation_heatmap_full.png")
    print(f"   - Market regimes plot: market_regimes_plot.png")
    print(f"   - Comprehensive report: comprehensive_report.html")
    print(f"   - Regime data: data_with_regimes.csv")
    print(f"   - Correlation matrix: correlation_matrix.csv")
    if run_all:
        print(f"   - Donchian MCPT report: donchian_mcpt_report.html")
        print(f"   - Donchian walk-forward results: donchian_walkforward_results.csv")
        print(f"   - Donchian actual vs permuted: donchian_actual_vs_permuted.png")
        print(f"   - Enhanced Donchian summary: donchian_enhanced_mcpt_summary.csv")
        print(f"   - Enhanced Donchian results: donchian_enhanced_walkforward_results.csv")
    print(f"\n💡 To create interactive dashboards, run: python3 visualize_indicators.py")
    
    return True


def main():
    """Main function with interactive menu."""
    print("\n" + "="*70)
    print("🚀 UNIFIED STOCK ANALYSIS TOOL")
    print("="*70)
    print("Comprehensive technical analysis and visualization")
    print("="*70)
    
    # Check if stock symbol provided as argument
    stock_symbol = None
    run_all = False
    
    if len(sys.argv) > 1:
        if '--all' in sys.argv:
            run_all = True
            sys.argv.remove('--all')
        if len(sys.argv) > 1:
            stock_symbol = sys.argv[1]
    
    # If no stock provided, show menu or ask for input
    if not stock_symbol:
        available_stocks = find_available_stocks()
        
        print("\n" + "="*70)
        print("SELECT ANALYSIS OPTION")
        print("="*70)
        print("  1. Select from existing stocks")
        print("  2. Enter new ticker symbol")
        print("  0. Exit")
        print("="*70)
        
        try:
            option = input("\nSelect option (1/2/0): ").strip()
            
            if option == '0':
                print("👋 Goodbye!")
                return
            elif option == '2':
                # Ask for ticker symbol
                print("\n" + "-"*70)
                print("ENTER TICKER SYMBOL")
                print("-"*70)
                print("Format: TICKER.NS (e.g., RELIANCE.NS, TCS.NS, HDFCBANK.NS)")
                print("For Indian stocks, add .NS suffix")
                print("-"*70)
                stock_symbol = input("\nEnter ticker symbol: ").strip().upper()
                
                if not stock_symbol:
                    print("❌ No ticker symbol provided. Exiting.")
                    return
                
                # Ensure .NS suffix for Indian stocks
                if not stock_symbol.endswith('.NS'):
                    print(f"⚠️  Adding .NS suffix for Indian stock")
                    stock_symbol = stock_symbol + '.NS'
                    
            elif option == '1':
                # Show existing stocks menu
                if not available_stocks:
                    print("\n❌ No stock analysis files found!")
                    print("   Switching to option 2: Enter new ticker symbol\n")
                    option = '2'
                    stock_symbol = input("Enter ticker symbol: ").strip().upper()
                    if not stock_symbol.endswith('.NS'):
                        stock_symbol = stock_symbol + '.NS'
                else:
                    print("\n📊 Available Stocks:")
                    print("-" * 70)
                    for i, stock in enumerate(available_stocks, 1):
                        print(f"  {i}. {stock}")
                    print("  0. Back")
                    print("-" * 70)
                    
                    choice = input("\nSelect a stock (enter number): ").strip()
                    if choice == '0':
                        return
                    stock_symbol = available_stocks[int(choice) - 1]
            else:
                print("❌ Invalid option. Exiting.")
                return
                
        except (ValueError, IndexError, KeyboardInterrupt):
            print("\n❌ Invalid selection. Exiting.")
            return
    
    # Run analysis
    run_analysis(stock_symbol, run_all)


if __name__ == "__main__":
    main()

