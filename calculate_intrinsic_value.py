"""
Intrinsic Value Calculator for Indian Stocks

A comprehensive valuation model that calculates intrinsic value using multiple methods:
1. Graham's Formula (Benjamin Graham)
2. Discounted Cash Flow (DCF) - Simplified
3. P/E Ratio Analysis
4. Price-to-Book (P/B) Analysis
5. PEG Ratio Analysis

Plus comprehensive Implied EPS Analysis for market expectations

Features:
- Automatic data validation and correction (dividend yield, debt-to-equity)
- Smart growth rate calculation from company data
- Multiple cash flow fallbacks (FCF → OCF → EPS proxy)
- Comprehensive implied EPS analysis
- Production-ready with robust error handling

Usage:
    python3 calculate_intrinsic_value.py TICKER.NS
    python3 calculate_intrinsic_value.py RELIANCE.NS TCS.NS INFY.NS

Version: 2.0 (Hedge Fund Grade)
- Sector-aware valuation (dynamic P/E and P/B by sector)
- Live risk-free rate fetching
- Special handling for Banks/Financials (DCF disabled, P/B focus)
- Modified Graham Formula for IT/Services companies
- Terminal value safety clamp
- Cyclical stock adjustments for Basic Materials
"""

import argparse
import sys
import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def fetch_risk_free_rate():
    """
    Fetch live India 10-Year Government Bond Yield.
    
    Returns:
        float: Risk-free rate (as decimal, e.g., 0.071 for 7.1%)
    """
    try:
        # Try to fetch India 10-Year Bond Yield
        # Common tickers: ^IGSEC (India Government Securities), or use generic proxy
        bond_tickers = ['^IGSEC', '^NSEI']  # Fallback options
        
        for ticker_symbol in bond_tickers:
            try:
                bond_ticker = yf.Ticker(ticker_symbol)
                hist = bond_ticker.history(period='5d')
                if not hist.empty and 'Close' in hist.columns:
                    # If it's a bond yield, it's typically already in percentage
                    yield_value = hist['Close'].iloc[-1]
                    # Convert to decimal if it appears to be in percentage (> 1)
                    if yield_value > 1:
                        risk_free = yield_value / 100
                    else:
                        risk_free = yield_value
                    # Sanity check: should be between 5% and 10% for India
                    if 0.05 <= risk_free <= 0.10:
                        print(f"   📈 Live Risk-Free Rate: {risk_free*100:.2f}% (from {ticker_symbol})")
                        return risk_free
            except:
                continue
        
        # Fallback: Use reasonable default for India (7.1%)
        print(f"   ⚠️  Using default Risk-Free Rate: 7.1% (could not fetch live data)")
        return 0.071
    except Exception as e:
        # Fallback to default
        print(f"   ⚠️  Using default Risk-Free Rate: 7.1% (error: {e})")
        return 0.071


def get_sector_benchmarks(sector, industry=None):
    """
    Return fair P/E and P/B based on sector norms for Indian market.
    
    Args:
        sector (str): Sector name
        industry (str, optional): Industry name for more specific classification
    
    Returns:
        tuple: (fair_pe, fair_pb) for the sector
    """
    # Sector-specific benchmarks for Indian market
    benchmarks = {
        'Technology': (25, 5.0),              # IT commands higher premiums (TCS, Infosys)
        'Consumer Defensive': (45, 12.0),      # FMCG is expensive (Nestle, HUL, Britannia)
        'Financial Services': (18, 3.0),       # Banks and NBFCs
        'Basic Materials': (10, 1.2),          # Commodities (Steel, Metals)
        'Industrials': (20, 3.0),              # Capital Goods (BHEL, L&T)
        'Energy': (12, 1.5),                   # Oil & Gas
        'Healthcare': (25, 4.0),               # Pharma
        'Consumer Cyclical': (20, 3.5),       # Retail, Auto
        'Communication Services': (18, 2.5),   # Telecom
        'Utilities': (15, 1.8),                # Power
        'Real Estate': (15, 2.0),              # Real Estate
    }
    
    # Industry-specific overrides (more granular)
    if industry:
        industry_lower = industry.lower()
        if 'bank' in industry_lower or 'financial' in industry_lower:
            # Private banks vs PSU banks
            if 'private' in industry_lower or 'hdfc' in industry_lower or 'icici' in industry_lower:
                return (20, 2.5)  # Private banks
            else:
                return (12, 1.2)  # PSU banks
        elif 'steel' in industry_lower or 'metal' in industry_lower:
            return (8, 1.0)  # Very cyclical, lower multiples
        elif 'fmcg' in industry_lower or 'consumer' in industry_lower:
            return (50, 15.0)  # Premium FMCG
    
    # Return sector benchmark or default conservative values
    return benchmarks.get(sector, (15, 1.5))


def is_financial_company(sector, industry):
    """
    Check if company is a bank or financial services company.
    
    Args:
        sector (str): Sector name
        industry (str): Industry name
    
    Returns:
        bool: True if financial company
    """
    financial_keywords = ['bank', 'financial', 'nbfc', 'finance', 'credit', 'lending']
    sector_lower = (sector or '').lower()
    industry_lower = (industry or '').lower()
    
    return (any(keyword in sector_lower for keyword in financial_keywords) or
            any(keyword in industry_lower for keyword in financial_keywords))


def is_asset_light_company(sector, industry):
    """
    Check if company is asset-light (IT, Services, Software).
    These companies have low book value, so standard Graham formula doesn't work well.
    
    Args:
        sector (str): Sector name
        industry (str): Industry name
    
    Returns:
        bool: True if asset-light company
    """
    asset_light_keywords = ['technology', 'software', 'it services', 'consulting', 'services']
    sector_lower = (sector or '').lower()
    industry_lower = (industry or '').lower()
    
    return (any(keyword in sector_lower for keyword in asset_light_keywords) or
            any(keyword in industry_lower for keyword in asset_light_keywords))


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
            'dividend_yield_raw': info.get('dividendYield', None),
            'dividend_rate': info.get('dividendRate', None),  # Annual dividend per share
            'payout_ratio': info.get('payoutRatio', None),
            
            # Market Metrics
            'market_cap': info.get('marketCap', None),
            'enterprise_value': info.get('enterpriseValue', None),
            'shares_outstanding': info.get('sharesOutstanding', None),
            
            # Growth Rates
            'earnings_growth_5y': info.get('earningsGrowth', None),
            'revenue_growth_5y': info.get('revenueGrowth', None),
        }
        
        # Fetch live risk-free rate
        data['risk_free_rate'] = fetch_risk_free_rate()
        
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
        
        # Fix dividend yield calculation (handle Indian dividend declarations)
        # Indian companies declare dividends as % of Face Value (₹10), not market price
        # Validate and recalculate if needed
        dividend_yield = data.get('dividend_yield_raw')
        if dividend_yield is not None:
            # Check if dividend yield is unreasonably high (>10% is suspicious)
            if dividend_yield > 0.10:  # More than 10%
                print(f"⚠️  Warning: Dividend yield seems high ({dividend_yield*100:.2f}%)")
                print(f"   This might be a data error. Recalculating from dividend rate...")
                
                # Try to recalculate from dividend rate
                if data.get('dividend_rate') and current_price > 0:
                    dividend_yield = data['dividend_rate'] / current_price
                    print(f"   Recalculated dividend yield: {dividend_yield*100:.2f}%")
                else:
                    # If still suspicious, cap it at reasonable level or set to None
                    print(f"   Using capped value of 5% for safety")
                    dividend_yield = min(dividend_yield, 0.05)
        
        data['dividend_yield'] = dividend_yield
        
        # Fix debt-to-equity ratio (handle percentage vs ratio)
        # Some data sources provide debt-to-equity as percentage (e.g., 37.71) instead of ratio (0.3771)
        # Normal debt-to-equity ratios are typically 0.0 to 3.0, rarely above 5.0
        debt_to_equity = data.get('debt_to_equity')
        if debt_to_equity is not None:
            # If debt-to-equity > 10, it's likely a percentage that needs conversion
            if debt_to_equity > 10:
                original_value = debt_to_equity
                debt_to_equity = debt_to_equity / 100
                print(f"⚠️  Warning: Debt-to-Equity appears to be percentage ({original_value:.2f}%)")
                print(f"   Converted to ratio: {debt_to_equity:.2f}")
            # Also check for suspiciously high ratios (even after conversion)
            elif debt_to_equity > 5.0:
                print(f"⚠️  Warning: Very high Debt-to-Equity ratio ({debt_to_equity:.2f})")
                print(f"   This may indicate high financial risk")
        
        data['debt_to_equity'] = debt_to_equity
        
        # Validate and fix other suspicious values
        if data.get('trailing_pe') and data['trailing_pe'] < 0:
            print(f"⚠️  Warning: Negative P/E ratio detected, setting to None")
            data['trailing_pe'] = None
        
        if data.get('free_cashflow') and data['free_cashflow'] < 0:
            print(f"⚠️  Warning: Negative Free Cash Flow detected")
            print(f"   This may affect DCF valuation accuracy")
        
        print(f"✅ Data fetched successfully")
        return data
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None


def calculate_graham_intrinsic_value(data):
    """
    Calculate intrinsic value using Benjamin Graham's formula.
    
    For traditional companies: IV = sqrt(22.5 * EPS * BVPS)
    For asset-light companies (IT/Services): IV = EPS * (8.5 + 2g)
    Where: g is the growth rate
    
    Args:
        data (dict): Fundamental data dictionary
    
    Returns:
        float: Intrinsic value
    """
    if not data.get('eps'):
        return None
    
    try:
        sector = data.get('sector', '')
        industry = data.get('industry', '')
        
        # Use Modified Graham Formula for asset-light companies
        if is_asset_light_company(sector, industry):
            # Modified Graham: V = EPS * (8.5 + 2g)
            # Get growth rate
            growth_rate = None
            if data.get('earnings_growth_5y') and data['earnings_growth_5y'] > 0:
                growth_rate = min(data['earnings_growth_5y'], 0.30)  # Cap at 30%
            elif data.get('revenue_growth_5y') and data['revenue_growth_5y'] > 0:
                growth_rate = min(data['revenue_growth_5y'], 0.25)
            elif data.get('earnings_growth') and data['earnings_growth'] > 0:
                growth_rate = min(data['earnings_growth'], 0.20)
            
            if growth_rate and growth_rate > 0:
                # Convert growth rate to percentage for formula
                g_percentage = growth_rate * 100
                # Use conservative base of 7 instead of 8.5 for Indian context
                intrinsic_value = data['eps'] * (7 + 2 * g_percentage)
                # Cap the multiplier at reasonable level (max P/E of 25)
                max_multiplier = 25
                if (7 + 2 * g_percentage) > max_multiplier:
                    intrinsic_value = data['eps'] * max_multiplier
                return intrinsic_value
            else:
                # Fallback: Use conservative P/E of 15 if no growth data
                return data['eps'] * 15
        
        # Standard Graham Formula for traditional companies
        if not data.get('book_value'):
            return None
        
        # Graham's formula: IV = sqrt(22.5 * EPS * BVPS)
        intrinsic_value = (22.5 * data['eps'] * data['book_value']) ** 0.5
        return intrinsic_value
    except Exception as e:
        return None


def calculate_dcf_intrinsic_value(data, growth_rate=None, terminal_growth=0.03, years=10):
    """
    Calculate intrinsic value using simplified DCF model.
    
    NOTE: DCF is NOT suitable for Banks/Financials. Use P/B or DDM instead.
    
    Args:
        data (dict): Fundamental data dictionary
        growth_rate (float): Expected growth rate (auto-calculated if None)
        terminal_growth (float): Terminal growth rate (default 3%)
        years (int): Number of years to project
    
    Returns:
        float: Intrinsic value per share, or None if not applicable (e.g., for banks)
    """
    # Skip DCF for financial companies
    sector = data.get('sector', '')
    industry = data.get('industry', '')
    if is_financial_company(sector, industry):
        print(f"   ⚠️  DCF not suitable for {sector}/{industry}. Using P/B focus instead.")
        return None
    # Try to get FCF first, fallback to operating cash flow or EPS-based proxy
    fcf = data.get('free_cashflow')
    operating_cf = data.get('operating_cashflow')
    shares = data.get('shares_outstanding')
    
    if not shares:
        return None
    
    # Use FCF if available and positive, otherwise try operating CF
    if fcf and fcf > 0:
        fcf_per_share = fcf / shares
        cash_flow_type = "Free Cash Flow"
    elif operating_cf and operating_cf > 0:
        # Use operating cash flow as proxy (less ideal but better than nothing)
        fcf_per_share = operating_cf / shares
        cash_flow_type = "Operating Cash Flow (proxy)"
        print(f"   ⚠️  Using Operating CF as FCF proxy (FCF unavailable)")
    elif data.get('eps'):
        # Last resort: Use EPS as cash flow proxy (assumes earnings = cash flow)
        # This is not ideal but provides a rough estimate
        fcf_per_share = data['eps'] * 0.8  # Assume 80% of earnings is cash
        cash_flow_type = "EPS-based proxy (80% of earnings)"
        print(f"   ⚠️  Using EPS-based cash flow proxy (FCF unavailable)")
    else:
        return None
    
    try:
        # Auto-calculate growth rate if not provided
        if growth_rate is None:
            # Use revenue growth if available, otherwise earnings growth
            if data.get('revenue_growth_5y') and data['revenue_growth_5y'] > 0:
                growth_rate = min(data['revenue_growth_5y'], 0.20)  # Cap at 20%
            elif data.get('earnings_growth_5y') and data['earnings_growth_5y'] > 0:
                growth_rate = min(data['earnings_growth_5y'], 0.20)
            elif data.get('revenue_growth') and data['revenue_growth'] > 0:
                growth_rate = min(data['revenue_growth'], 0.15)  # Cap at 15% for quarterly
            else:
                growth_rate = 0.10  # Default 10%
        
        # Ensure growth rate is reasonable (0% to 20%)
        growth_rate = max(0.0, min(growth_rate, 0.20))
        
        # Discount rate (WACC approximation)
        # Risk-free rate + market risk premium
        risk_free = data.get('risk_free_rate', 0.071)
        discount_rate = risk_free + 0.05  # 5% market risk premium
        
        # For cyclical or high-risk stocks, adjust discount rate
        if data.get('debt_to_equity') and data['debt_to_equity'] > 1.5:
            discount_rate += 0.02  # Add 2% for high debt
            print(f"   ⚠️  Adjusted discount rate for high debt: {discount_rate*100:.1f}%")
        
        # CRITICAL FIX: Terminal growth safety clamp
        # Terminal growth should never exceed risk-free rate
        # If discount rate is close to terminal growth, denominator becomes tiny
        terminal_growth = min(terminal_growth, risk_free - 0.01)  # Keep at least 1% spread
        
        # Additional safety: Ensure discount_rate > terminal_growth
        if discount_rate <= terminal_growth:
            terminal_growth = discount_rate - 0.01
            print(f"   ⚠️  Adjusted terminal growth to {terminal_growth*100:.1f}% for safety")
        
        # Project future cash flows
        pv_fcf = 0
        for year in range(1, years + 1):
            future_fcf = fcf_per_share * ((1 + growth_rate) ** year)
            pv_fcf += future_fcf / ((1 + discount_rate) ** year)
        
        # Terminal value (with safety check)
        terminal_fcf = fcf_per_share * ((1 + growth_rate) ** years) * (1 + terminal_growth)
        denominator = discount_rate - terminal_growth
        if denominator <= 0:
            print(f"   ❌ DCF calculation error: Invalid discount/terminal growth spread")
            return None
        terminal_value = terminal_fcf / denominator
        pv_terminal = terminal_value / ((1 + discount_rate) ** years)
        
        intrinsic_value = pv_fcf + pv_terminal
        
        # Add note about assumptions
        if cash_flow_type != "Free Cash Flow":
            print(f"   📝 DCF assumptions: {cash_flow_type}, Growth: {growth_rate*100:.1f}%, Discount: {discount_rate*100:.1f}%")
        
        return intrinsic_value
    except Exception as e:
        print(f"   ❌ DCF calculation error: {e}")
        return None


def calculate_pe_based_intrinsic_value(data, fair_pe=15, use_cyclical_adjustment=True):
    """
    Calculate intrinsic value based on fair P/E ratio.
    
    For cyclical stocks (Basic Materials), compares current P/E to historical median.
    
    Args:
        data (dict): Fundamental data dictionary
        fair_pe (float): Fair P/E ratio (default 15, can be adjusted based on sector)
        use_cyclical_adjustment (bool): Apply cyclical stock logic for Basic Materials
    
    Returns:
        float: Intrinsic value
    """
    if not data.get('eps'):
        return None
    
    try:
        # Cyclical stock adjustment for Basic Materials
        if use_cyclical_adjustment and data.get('sector') == 'Basic Materials':
            current_pe = data.get('trailing_pe')
            if current_pe and current_pe > 0:
                # For cyclical stocks, low P/E often means "top of cycle" (sell signal)
                # High P/E means "bottom of cycle" (buy signal)
                # Use a conservative approach: if current P/E is very low, be cautious
                if current_pe < fair_pe * 0.7:  # Current P/E is 30% below fair
                    print(f"   ⚠️  Cyclical stock: Current P/E ({current_pe:.1f}) is low.")
                    print(f"      This may indicate top of cycle. Using conservative valuation.")
                    # Use slightly lower fair P/E for safety
                    fair_pe = fair_pe * 0.9
        
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
    Fair PEG is typically 1.0, so Fair P/E = Growth Rate (as percentage)
    
    Formula: IV = EPS × (Growth Rate × 100)
    Where Growth Rate is the earnings growth rate
    
    Args:
        data (dict): Fundamental data dictionary
    
    Returns:
        float: Intrinsic value
    """
    if not data.get('eps'):
        return None
    
    try:
        # Get growth rate - prefer 5-year earnings growth, fallback to revenue growth
        growth_rate = None
        
        # Try 5-year earnings growth first
        if data.get('earnings_growth_5y') and data['earnings_growth_5y'] > 0:
            growth_rate = data['earnings_growth_5y']
        # Fallback to 5-year revenue growth
        elif data.get('revenue_growth_5y') and data['revenue_growth_5y'] > 0:
            growth_rate = data['revenue_growth_5y']
        # Fallback to quarterly earnings growth
        elif data.get('earnings_growth') and data['earnings_growth'] > 0:
            growth_rate = data['earnings_growth']
        # Fallback to quarterly revenue growth
        elif data.get('revenue_growth') and data['revenue_growth'] > 0:
            growth_rate = data['revenue_growth']
        
        # If we have a growth rate, calculate fair P/E
        if growth_rate and growth_rate > 0:
            # Cap growth rate at 30% for reasonable P/E
            growth_rate = min(growth_rate, 0.30)
            # Fair P/E = Growth Rate × 100 (convert to percentage)
            # For PEG = 1.0, P/E should equal growth rate percentage
            fair_pe = growth_rate * 100
            # Cap fair P/E at 30 for safety
            fair_pe = min(fair_pe, 30)
            intrinsic_value = data['eps'] * fair_pe
            return intrinsic_value
        
        return None
    except Exception as e:
        return None


def calculate_implied_eps(data, pe_ratios=[10, 15, 20, 25, 30]):
    """
    Calculate Implied EPS - what EPS would justify the current market price
    at different P/E ratios.
    
    Formula: Implied EPS = Current Price / P/E Ratio
    
    Args:
        data (dict): Fundamental data dictionary
        pe_ratios (list): List of P/E ratios to calculate implied EPS for
    
    Returns:
        dict: Dictionary with P/E ratios as keys and implied EPS as values
    """
    current_price = data.get('current_price')
    if not current_price or current_price <= 0:
        return None
    
    implied_eps_dict = {}
    for pe in pe_ratios:
        implied_eps = current_price / pe
        implied_eps_dict[pe] = implied_eps
    
    return implied_eps_dict


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
    sector = data.get('sector', 'N/A')
    industry = data.get('industry', 'N/A')
    
    print(f"\n📈 Current Market Price: ₹{current_price:.2f}")
    print(f"📋 Company: {data.get('name', 'N/A')}")
    print(f"🏢 Sector: {sector}")
    print(f"🏭 Industry: {industry}")
    
    # Get sector-specific benchmarks
    fair_pe, fair_pb = get_sector_benchmarks(sector, industry)
    print(f"\nℹ️  Using Sector Benchmarks: Fair P/E={fair_pe}, Fair P/B={fair_pb}")
    
    # Special note for financial companies
    if is_financial_company(sector, industry):
        print(f"   📌 Financial Company: DCF disabled, focusing on P/B and P/E analysis")
    
    # Calculate intrinsic values using different methods
    print("\n" + "-"*80)
    print("🔍 CALCULATING INTRINSIC VALUE (Multiple Methods)")
    print("-"*80)
    
    results = {}
    
    # 1. Graham's Formula (or Modified Graham for IT/Services)
    graham_iv = calculate_graham_intrinsic_value(data)
    if graham_iv:
        method_name = "Modified Graham" if is_asset_light_company(sector, industry) else "Graham Formula"
        results[f'{method_name}'] = graham_iv
        discount = ((graham_iv - current_price) / current_price) * 100
        print(f"1️⃣  {method_name}:        ₹{graham_iv:.2f} ({discount:+.1f}%)")
    
    # 2. DCF Model (skipped for financials)
    dcf_iv = calculate_dcf_intrinsic_value(data)
    if dcf_iv:
        results['DCF Model (10-year)'] = dcf_iv
        discount = ((dcf_iv - current_price) / current_price) * 100
        print(f"2️⃣  DCF Model (10-year):      ₹{dcf_iv:.2f} ({discount:+.1f}%)")
    
    # 3. P/E Based (with sector-specific fair P/E)
    pe_iv = calculate_pe_based_intrinsic_value(data, fair_pe=fair_pe)
    if pe_iv:
        results[f'P/E Based (Fair P/E={fair_pe})'] = pe_iv
        discount = ((pe_iv - current_price) / current_price) * 100
        print(f"3️⃣  P/E Based (Fair P/E={fair_pe}):   ₹{pe_iv:.2f} ({discount:+.1f}%)")
    
    # 4. P/B Based (with sector-specific fair P/B, especially important for financials)
    pb_iv = calculate_pb_based_intrinsic_value(data, fair_pb=fair_pb)
    if pb_iv:
        results[f'P/B Based (Fair P/B={fair_pb})'] = pb_iv
        discount = ((pb_iv - current_price) / current_price) * 100
        print(f"4️⃣  P/B Based (Fair P/B={fair_pb}):  ₹{pb_iv:.2f} ({discount:+.1f}%)")
        # For financial companies, emphasize P/B
        if is_financial_company(sector, industry):
            print(f"      ⭐ Primary valuation method for {sector}")
    
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
    
    # Market expectations note
    if discount_to_avg < -20:
        print("\n💡 Note: Market may be pricing in future growth/margin expansion")
        print("   Consider: Earnings growth trajectory, sector trends, competitive position")
    
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
        print(f"Current EPS:                 ₹{data['eps']:.2f}")
    if data.get('book_value'):
        print(f"Book Value per Share:        ₹{data['book_value']:.2f}")
    if data.get('dividend_yield') is not None:
        div_yield = data['dividend_yield']
        if div_yield > 0.10:
            print(f"Dividend Yield:              {div_yield*100:.2f}% ⚠️ (Please verify)")
        else:
            print(f"Dividend Yield:              {div_yield*100:.2f}%")
    if data.get('profit_margin'):
        print(f"Profit Margin:               {data['profit_margin']*100:.2f}%")
    if data.get('debt_to_equity'):
        print(f"Debt-to-Equity:              {data['debt_to_equity']:.2f}")
    
    # Implied EPS calculation
    implied_eps = calculate_implied_eps(data)
    if implied_eps:
        print("\n" + "-"*80)
        print("💡 IMPLIED EPS ANALYSIS")
        print("-"*80)
        print("What EPS would justify the current price at different P/E ratios?")
        print(f"\n{'P/E Ratio':<15} {'Implied EPS':<20} {'vs Current EPS':<25} {'Gap':<15}")
        print("-"*75)
        
        current_eps = data.get('eps')
        for pe in sorted(implied_eps.keys()):
            implied = implied_eps[pe]
            if current_eps:
                gap = implied - current_eps
                gap_pct = (gap / current_eps) * 100 if current_eps > 0 else 0
                vs_current = f"₹{current_eps:.2f}"
                gap_str = f"{gap:+.2f} ({gap_pct:+.1f}%)"
            else:
                vs_current = "N/A"
                gap_str = "N/A"
            
            # Highlight if implied EPS is close to current EPS
            marker = ""
            if current_eps and abs(implied - current_eps) / current_eps < 0.10:
                marker = " ⭐"
            
            print(f"P/E {pe:<10} ₹{implied:<18.2f} {vs_current:<24} {gap_str:<14}{marker}")
        
        # Show what P/E the current EPS implies
        if current_eps and current_eps > 0:
            implied_pe = current_price / current_eps
            print(f"\n📊 Current EPS (₹{current_eps:.2f}) implies P/E of {implied_pe:.2f}")
            
            # Compare to trailing P/E if available
            if data.get('trailing_pe'):
                diff = implied_pe - data['trailing_pe']
                if abs(diff) > 0.1:
                    print(f"   (Trailing P/E: {data['trailing_pe']:.2f}, Difference: {diff:+.2f})")
        
        # Interpretation
        print("\n💭 Interpretation:")
        if current_eps:
            # Find closest P/E ratio
            closest_pe = min(implied_eps.keys(), key=lambda x: abs(implied_eps[x] - current_eps))
            if abs(implied_eps[closest_pe] - current_eps) / current_eps < 0.10:
                print(f"   Market is pricing the stock at approximately P/E {closest_pe}")
            else:
                # Find what P/E would match current EPS
                matching_pe = current_price / current_eps
                if matching_pe < 10:
                    print(f"   Market expects very high earnings growth (P/E {matching_pe:.1f})")
                elif matching_pe > 30:
                    print(f"   Market is pricing at premium P/E {matching_pe:.1f} (growth expectations)")
                else:
                    print(f"   Market is pricing at P/E {matching_pe:.1f}")
        else:
            print("   Use Implied EPS to understand market expectations")
    
    result_dict = {
        'symbol': symbol,
        'current_price': current_price,
        'average_intrinsic_value': avg_iv,
        'discount_premium_pct': discount_to_avg,
        'assessment': assessment,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to valuation directory
    save_valuation_results(result_dict, symbol)
    
    return result_dict


def get_valuation_dir(stock_symbol):
    """Get valuation subdirectory for Benjamin Oreo results."""
    base_dir = os.path.join("analysis_results", stock_symbol)
    valuation_dir = os.path.join(base_dir, "valuation")
    if not os.path.exists(valuation_dir):
        os.makedirs(valuation_dir)
    return valuation_dir


def save_valuation_results(result_dict, stock_symbol):
    """Save valuation results as JSON to valuation/ directory."""
    try:
        valuation_dir = get_valuation_dir(stock_symbol)
        output_path = os.path.join(valuation_dir, "intrinsic_value.json")
        
        # Convert results to JSON-serializable format
        json_dict = {
            'symbol': result_dict['symbol'],
            'current_price': float(result_dict['current_price']),
            'average_intrinsic_value': float(result_dict['average_intrinsic_value']),
            'discount_premium_pct': float(result_dict['discount_premium_pct']),
            'assessment': result_dict['assessment'],
            'timestamp': result_dict['timestamp'],
            'valuation_methods': {}
        }
        
        # Convert results dictionary to JSON-serializable format
        for method, value in result_dict['results'].items():
            if value is not None:
                json_dict['valuation_methods'][method] = float(value)
        
        with open(output_path, 'w') as f:
            json.dump(json_dict, f, indent=2)
        
        print(f"\n💾 Valuation results saved to: {output_path}")
    except Exception as e:
        print(f"⚠️  Could not save valuation results: {e}")


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

