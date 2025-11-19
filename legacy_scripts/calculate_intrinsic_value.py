"""
Intrinsic Value Calculator for Indian Stocks

This script calculates the intrinsic value of stocks using multiple valuation methods:
1. Graham's Formula (Benjamin Graham)
2. Discounted Cash Flow (DCF) - Simplified
3. P/E Ratio Analysis
4. Price-to-Book (P/B) Analysis
5. PEG Ratio Analysis

Usage:
    python3 calculate_intrinsic_value.py TICKER.NS
    python3 calculate_intrinsic_value.py RELIANCE.NS TCS.NS INFY.NS
"""

import argparse
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def fetch_fundamental_data(symbol):
    """
    Fetch fundamental data for a stock using yfinance.
    
    Args:
        symbol (str): Stock symbol (e.g., 'RELIANCE.NS')
    
    Returns:
        dict: Dictionary containing fundamental data
    """
    print(f"\n📊 Fetching fundamental data for {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get current price
        hist = ticker.history(period="1d")
        current_price = hist['Close'].iloc[-1] if not hist.empty else info.get('currentPrice', 0)
        
        # Get financial statements
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow = ticker.cashflow
        
        # Extract key metrics
        data = {
            'symbol': symbol,
            'current_price': current_price,
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            
            # Earnings & Profitability
            'trailing_pe': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'peg_ratio': info.get('pegRatio', None),
            'earnings_growth': info.get('earningsQuarterlyGrowth', None),
            'revenue_growth': info.get('revenueGrowth', None),
            'profit_margin': info.get('profitMargins', None),
            
            # Balance Sheet
            'book_value': info.get('bookValue', None),
            'price_to_book': info.get('priceToBook', None),
            'debt_to_equity': info.get('debtToEquity', None),
            'total_debt': info.get('totalDebt', None),
            'total_cash': info.get('totalCash', None),
            'total_assets': info.get('totalAssets', None),
            
            # Cash Flow
            'free_cashflow': info.get('freeCashflow', None),
            'operating_cashflow': info.get('operatingCashflow', None),
            
            # Dividends
            'dividend_yield': info.get('dividendYield', None),
            'payout_ratio': info.get('payoutRatio', None),
            
            # Market Metrics
            'market_cap': info.get('marketCap', None),
            'enterprise_value': info.get('enterpriseValue', None),
            'shares_outstanding': info.get('sharesOutstanding', None),
            
            # Growth Rates
            'earnings_growth_5y': info.get('earningsGrowth', None),
            'revenue_growth_5y': info.get('revenueGrowth', None),
            
            # Risk-free rate (using 10-year bond yield as proxy)
            'risk_free_rate': 0.07,  # 7% for Indian context (can be updated)
        }
        
        # Try to get EPS from financials if not in info
        if data['trailing_pe'] and data['current_price']:
            data['eps'] = data['current_price'] / data['trailing_pe']
        elif financials is not None and not financials.empty:
            try:
                net_income = financials.loc['Net Income'].iloc[0] if 'Net Income' in financials.index else None
                if net_income and data.get('shares_outstanding'):
                    data['eps'] = net_income / data['shares_outstanding']
            except:
                data['eps'] = None
        else:
            data['eps'] = None
        
        print(f"✅ Data fetched successfully")
        return data
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None


def calculate_graham_intrinsic_value(data):
    """
    Calculate intrinsic value using Benjamin Graham's formula.
    
    Formula: IV = sqrt(22.5 * EPS * BVPS)
    Where: 22.5 = 15 P/E * 1.5 P/B (Graham's preferred ratios)
    
    Args:
        data (dict): Fundamental data dictionary
    
    Returns:
        float: Intrinsic value
    """
    if not data.get('eps') or not data.get('book_value'):
        return None
    
    try:
        # Graham's formula: IV = sqrt(22.5 * EPS * BVPS)
        intrinsic_value = (22.5 * data['eps'] * data['book_value']) ** 0.5
        return intrinsic_value
    except:
        return None


def calculate_dcf_intrinsic_value(data, growth_rate=0.10, terminal_growth=0.03, years=10):
    """
    Calculate intrinsic value using simplified DCF model.
    
    Args:
        data (dict): Fundamental data dictionary
        growth_rate (float): Expected growth rate (default 10%)
        terminal_growth (float): Terminal growth rate (default 3%)
        years (int): Number of years to project
    
    Returns:
        float: Intrinsic value per share
    """
    if not data.get('free_cashflow') or not data.get('shares_outstanding'):
        return None
    
    try:
        fcf = data['free_cashflow']
        shares = data['shares_outstanding']
        fcf_per_share = fcf / shares
        
        # Discount rate (WACC approximation)
        # Risk-free rate + market risk premium
        discount_rate = data.get('risk_free_rate', 0.07) + 0.05  # 12% total
        
        # Project future cash flows
        pv_fcf = 0
        for year in range(1, years + 1):
            future_fcf = fcf_per_share * ((1 + growth_rate) ** year)
            pv_fcf += future_fcf / ((1 + discount_rate) ** year)
        
        # Terminal value
        terminal_fcf = fcf_per_share * ((1 + growth_rate) ** years) * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** years)
        
        intrinsic_value = pv_fcf + pv_terminal
        return intrinsic_value
    except Exception as e:
        return None


def calculate_pe_based_intrinsic_value(data, fair_pe=15):
    """
    Calculate intrinsic value based on fair P/E ratio.
    
    Args:
        data (dict): Fundamental data dictionary
        fair_pe (float): Fair P/E ratio (default 15, can be adjusted based on sector)
    
    Returns:
        float: Intrinsic value
    """
    if not data.get('eps'):
        return None
    
    try:
        intrinsic_value = data['eps'] * fair_pe
        return intrinsic_value
    except:
        return None


def calculate_pb_based_intrinsic_value(data, fair_pb=1.5):
    """
    Calculate intrinsic value based on fair P/B ratio.
    
    Args:
        data (dict): Fundamental data dictionary
        fair_pb (float): Fair P/B ratio (default 1.5)
    
    Returns:
        float: Intrinsic value
    """
    if not data.get('book_value'):
        return None
    
    try:
        intrinsic_value = data['book_value'] * fair_pb
        return intrinsic_value
    except:
        return None


def calculate_peg_based_intrinsic_value(data):
    """
    Calculate intrinsic value using PEG ratio.
    Fair PEG is typically 1.0
    
    Args:
        data (dict): Fundamental data dictionary
    
    Returns:
        float: Intrinsic value
    """
    if not data.get('trailing_pe') or not data.get('earnings_growth_5y'):
        return None
    
    try:
        # If PEG is available, use it directly
        if data.get('peg_ratio'):
            # Fair P/E = Fair PEG (1.0) * Growth Rate
            growth = data.get('earnings_growth_5y', 0.10)
            if growth and growth > 0:
                fair_pe = 1.0 * growth * 100  # Convert to percentage
                if data.get('eps'):
                    return data['eps'] * fair_pe
        return None
    except:
        return None


def analyze_valuation(symbol):
    """
    Perform complete intrinsic value analysis for a stock.
    
    Args:
        symbol (str): Stock symbol
    """
    print("\n" + "="*80)
    print(f"💰 INTRINSIC VALUE ANALYSIS: {symbol}")
    print("="*80)
    
    # Fetch data
    data = fetch_fundamental_data(symbol)
    if not data:
        print(f"❌ Could not fetch data for {symbol}")
        return None
    
    current_price = data['current_price']
    
    print(f"\n📈 Current Market Price: ₹{current_price:.2f}")
    print(f"📋 Company: {data.get('name', 'N/A')}")
    print(f"🏢 Sector: {data.get('sector', 'N/A')}")
    print(f"🏭 Industry: {data.get('industry', 'N/A')}")
    
    # Calculate intrinsic values using different methods
    print("\n" + "-"*80)
    print("🔍 CALCULATING INTRINSIC VALUE (Multiple Methods)")
    print("-"*80)
    
    results = {}
    
    # 1. Graham's Formula
    graham_iv = calculate_graham_intrinsic_value(data)
    if graham_iv:
        results['Graham Formula'] = graham_iv
        discount = ((graham_iv - current_price) / current_price) * 100
        print(f"1️⃣  Graham's Formula:        ₹{graham_iv:.2f} ({discount:+.1f}%)")
    
    # 2. DCF Model
    dcf_iv = calculate_dcf_intrinsic_value(data)
    if dcf_iv:
        results['DCF Model'] = dcf_iv
        discount = ((dcf_iv - current_price) / current_price) * 100
        print(f"2️⃣  DCF Model (10-year):      ₹{dcf_iv:.2f} ({discount:+.1f}%)")
    
    # 3. P/E Based
    pe_iv = calculate_pe_based_intrinsic_value(data)
    if pe_iv:
        results['P/E Based (Fair P/E=15)'] = pe_iv
        discount = ((pe_iv - current_price) / current_price) * 100
        print(f"3️⃣  P/E Based (Fair P/E=15):   ₹{pe_iv:.2f} ({discount:+.1f}%)")
    
    # 4. P/B Based
    pb_iv = calculate_pb_based_intrinsic_value(data)
    if pb_iv:
        results['P/B Based (Fair P/B=1.5)'] = pb_iv
        discount = ((pb_iv - current_price) / current_price) * 100
        print(f"4️⃣  P/B Based (Fair P/B=1.5):  ₹{pb_iv:.2f} ({discount:+.1f}%)")
    
    # 5. PEG Based
    peg_iv = calculate_peg_based_intrinsic_value(data)
    if peg_iv:
        results['PEG Based'] = peg_iv
        discount = ((peg_iv - current_price) / current_price) * 100
        print(f"5️⃣  PEG Based:                ₹{peg_iv:.2f} ({discount:+.1f}%)")
    
    if not results:
        print("⚠️  Insufficient data to calculate intrinsic value")
        print("   Required: EPS, Book Value, or Free Cash Flow")
        return None
    
    # Calculate average intrinsic value
    avg_iv = sum(results.values()) / len(results)
    discount_to_avg = ((avg_iv - current_price) / current_price) * 100
    
    print("\n" + "-"*80)
    print("📊 SUMMARY")
    print("-"*80)
    print(f"Average Intrinsic Value:     ₹{avg_iv:.2f}")
    print(f"Current Market Price:        ₹{current_price:.2f}")
    print(f"Discount/Premium:            {discount_to_avg:+.1f}%")
    
    # Valuation assessment
    print("\n" + "-"*80)
    print("🎯 VALUATION ASSESSMENT")
    print("-"*80)
    
    if discount_to_avg > 20:
        assessment = "🟢 SIGNIFICANTLY UNDERVALUED"
        recommendation = "Strong Buy Opportunity"
    elif discount_to_avg > 10:
        assessment = "🟡 MODERATELY UNDERVALUED"
        recommendation = "Buy Opportunity"
    elif discount_to_avg > -10:
        assessment = "⚪ FAIRLY VALUED"
        recommendation = "Hold"
    elif discount_to_avg > -20:
        assessment = "🟠 MODERATELY OVERVALUED"
        recommendation = "Caution"
    else:
        assessment = "🔴 SIGNIFICANTLY OVERVALUED"
        recommendation = "Consider Selling"
    
    print(f"{assessment}")
    print(f"Recommendation: {recommendation}")
    
    # Key metrics
    print("\n" + "-"*80)
    print("📋 KEY METRICS")
    print("-"*80)
    if data.get('trailing_pe'):
        print(f"Trailing P/E:                {data['trailing_pe']:.2f}")
    if data.get('forward_pe'):
        print(f"Forward P/E:                 {data['forward_pe']:.2f}")
    if data.get('price_to_book'):
        print(f"Price-to-Book:               {data['price_to_book']:.2f}")
    if data.get('peg_ratio'):
        print(f"PEG Ratio:                   {data['peg_ratio']:.2f} (Fair = 1.0)")
    if data.get('eps'):
        print(f"EPS:                         ₹{data['eps']:.2f}")
    if data.get('book_value'):
        print(f"Book Value per Share:        ₹{data['book_value']:.2f}")
    if data.get('dividend_yield'):
        print(f"Dividend Yield:              {data['dividend_yield']*100:.2f}%")
    if data.get('profit_margin'):
        print(f"Profit Margin:               {data['profit_margin']*100:.2f}%")
    if data.get('debt_to_equity'):
        print(f"Debt-to-Equity:              {data['debt_to_equity']:.2f}")
    
    return {
        'symbol': symbol,
        'current_price': current_price,
        'average_intrinsic_value': avg_iv,
        'discount_premium_pct': discount_to_avg,
        'assessment': assessment,
        'results': results
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Calculate intrinsic value for Indian stocks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 calculate_intrinsic_value.py RELIANCE.NS
  python3 calculate_intrinsic_value.py TCS.NS INFY.NS HDFCBANK.NS
        """
    )
    parser.add_argument('stocks', nargs='+', help='Stock symbols (e.g., RELIANCE.NS TCS.NS)')
    args = parser.parse_args()
    
    results = []
    
    for symbol in args.stocks:
        symbol = symbol.strip().upper()
        
        # Ensure .NS suffix for Indian stocks
        if not symbol.endswith('.NS'):
            print(f"⚠️  Adding .NS suffix for Indian stock")
            symbol = symbol + '.NS'
        
        result = analyze_valuation(symbol)
        if result:
            results.append(result)
        
        print("\n" + "="*80 + "\n")
    
    # Summary table if multiple stocks
    if len(results) > 1:
        print("\n" + "="*80)
        print("📊 COMPARISON SUMMARY")
        print("="*80)
        print(f"{'Stock':<20} {'Price':<12} {'Intrinsic Value':<18} {'Discount/Premium':<20} {'Assessment':<30}")
        print("-"*100)
        for r in results:
            print(f"{r['symbol']:<20} ₹{r['current_price']:<10.2f} ₹{r['average_intrinsic_value']:<17.2f} "
                  f"{r['discount_premium_pct']:>+6.1f}%{'':<12} {r['assessment']:<30}")
        
        # Find most undervalued
        most_undervalued = max(results, key=lambda x: x['discount_premium_pct'])
        print(f"\n🏆 Most Undervalued: {most_undervalued['symbol']} "
              f"({most_undervalued['discount_premium_pct']:+.1f}%)")


if __name__ == "__main__":
    main()

