"""
Find Undervalued Stocks - Batch Analysis

This script analyzes multiple stocks and identifies which ones are trading
below their intrinsic value (undervalued stocks).

Usage:
    python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS INFY.NS
    python3 find_undervalued_stocks.py --min-discount 10
"""

import argparse
import sys
from calculate_intrinsic_value import analyze_valuation


def find_undervalued_stocks(stocks, min_discount=10):
    """
    Analyze multiple stocks and find undervalued ones.
    
    Args:
        stocks (list): List of stock symbols
        min_discount (float): Minimum discount percentage to consider undervalued
    
    Returns:
        list: List of undervalued stocks with their details
    """
    print("\n" + "="*80)
    print(f"🔍 SCREENING {len(stocks)} STOCKS FOR UNDERVALUED OPPORTUNITIES")
    print("="*80)
    print(f"Minimum discount threshold: {min_discount}%")
    print("="*80)
    
    results = []
    undervalued = []
    
    for i, symbol in enumerate(stocks, 1):
        symbol = symbol.strip().upper()
        
        # Ensure .NS suffix for Indian stocks
        if not symbol.endswith('.NS'):
            symbol = symbol + '.NS'
        
        print(f"\n[{i}/{len(stocks)}] Analyzing {symbol}...")
        result = analyze_valuation(symbol)
        
        if result:
            results.append(result)
            if result['discount_premium_pct'] >= min_discount:
                undervalued.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("📊 ANALYSIS SUMMARY")
    print("="*80)
    
    if not results:
        print("❌ No results to display")
        return []
    
    # Sort by discount (highest first)
    results.sort(key=lambda x: x['discount_premium_pct'], reverse=True)
    
    print(f"\n{'Stock':<20} {'Price':<12} {'Intrinsic Value':<18} {'Discount/Premium':<20} {'Status':<25}")
    print("-"*95)
    
    for r in results:
        status = "🟢 UNDERVALUED" if r['discount_premium_pct'] >= min_discount else \
                 "⚪ FAIR/OVER" if r['discount_premium_pct'] >= -10 else "🔴 OVERVALUED"
        
        print(f"{r['symbol']:<20} ₹{r['current_price']:<10.2f} ₹{r['average_intrinsic_value']:<17.2f} "
              f"{r['discount_premium_pct']:>+6.1f}%{'':<12} {status:<25}")
    
    # Undervalued stocks
    if undervalued:
        print("\n" + "="*80)
        print(f"✅ FOUND {len(undervalued)} UNDERVALUED STOCKS (≥{min_discount}% discount)")
        print("="*80)
        
        undervalued.sort(key=lambda x: x['discount_premium_pct'], reverse=True)
        
        for i, stock in enumerate(undervalued, 1):
            print(f"\n{i}. {stock['symbol']}")
            print(f"   Current Price:        ₹{stock['current_price']:.2f}")
            print(f"   Intrinsic Value:      ₹{stock['average_intrinsic_value']:.2f}")
            print(f"   Discount:             {stock['discount_premium_pct']:+.1f}%")
            print(f"   Assessment:           {stock['assessment']}")
        
        print("\n" + "="*80)
        print("💡 NEXT STEPS")
        print("="*80)
        print("For each undervalued stock, consider:")
        print("  1. Run technical analysis: python3 analyze_indian_stocks.py <TICKER>")
        print("  2. Check backtest results: python3 complete_setup.py <TICKER>")
        print("  3. Review financial health and fundamentals")
        print("  4. Consider your risk tolerance and investment goals")
    else:
        print(f"\n⚠️  No stocks found with ≥{min_discount}% discount to intrinsic value")
        print("   Consider:")
        print("   - Lowering the discount threshold (--min-discount)")
        print("   - Analyzing more stocks")
        print("   - Current market may be fairly valued or overvalued")
    
    return undervalued


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Find undervalued stocks by comparing market price to intrinsic value",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze specific stocks
  python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS INFY.NS
  
  # Find stocks with at least 15% discount
  python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS --min-discount 15
  
  # Analyze popular Indian stocks
  python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS \\
    ICICIBANK.NS WIPRO.NS HCLTECH.NS BHARTIARTL.NS ITC.NS SBIN.NS
        """
    )
    parser.add_argument('stocks', nargs='+', help='Stock symbols to analyze')
    parser.add_argument('--min-discount', type=float, default=10.0,
                        help='Minimum discount percentage to consider undervalued (default: 10.0)')
    args = parser.parse_args()
    
    find_undervalued_stocks(args.stocks, args.min_discount)


if __name__ == "__main__":
    main()

