# 💰 Intrinsic Value Analysis Guide

## Overview

This guide explains how to calculate intrinsic value for stocks and identify undervalued opportunities. Intrinsic value represents the "true" worth of a stock based on fundamental analysis, helping you determine if a stock is trading below or above its fair value.

## 🚀 Quick Start

### Calculate Intrinsic Value for a Single Stock

```bash
python3 calculate_intrinsic_value.py RELIANCE.NS
```

### Calculate for Multiple Stocks

```bash
python3 calculate_intrinsic_value.py RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS
```

### Find Undervalued Stocks (Batch Analysis)

```bash
# Find stocks with at least 10% discount (default)
python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS INFY.NS

# Find stocks with at least 15% discount
python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS INFY.NS --min-discount 15
```

---

## 📊 Valuation Methods Used

The script calculates intrinsic value using **5 different methods** and averages them:

### 1. **Graham's Formula** (Benjamin Graham)
- Formula: `IV = √(22.5 × EPS × Book Value per Share)`
- Based on Warren Buffett's mentor's approach
- Assumes fair P/E of 15 and P/B of 1.5

### 2. **Discounted Cash Flow (DCF) Model**
- Projects future free cash flows for 10 years
- Uses discount rate (WACC approximation) of ~12%
- Includes terminal value calculation
- Most sophisticated method

### 3. **P/E Ratio Analysis**
- Assumes fair P/E ratio of 15
- Formula: `IV = EPS × 15`
- Can be adjusted based on sector averages

### 4. **Price-to-Book (P/B) Analysis**
- Assumes fair P/B ratio of 1.5
- Formula: `IV = Book Value × 1.5`
- Useful for asset-heavy companies

### 5. **PEG Ratio Analysis**
- Considers growth rate
- Fair PEG = 1.0
- Formula: `Fair P/E = Growth Rate × 100`

---

## 📈 Understanding the Results

### Output Example

```
💰 INTRINSIC VALUE ANALYSIS: RELIANCE.NS
================================================================================

📈 Current Market Price: ₹2,450.00
📋 Company: Reliance Industries Limited
🏢 Sector: Energy
🏭 Industry: Oil & Gas Refining & Marketing

🔍 CALCULATING INTRINSIC VALUE (Multiple Methods)
--------------------------------------------------------------------------------
1️⃣  Graham's Formula:        ₹2,680.50 (+9.4%)
2️⃣  DCF Model (10-year):      ₹2,750.20 (+12.3%)
3️⃣  P/E Based (Fair P/E=15):   ₹2,600.00 (+6.1%)
4️⃣  P/B Based (Fair P/B=1.5):  ₹2,550.00 (+4.1%)
5️⃣  PEG Based:                ₹2,720.00 (+11.0%)

📊 SUMMARY
--------------------------------------------------------------------------------
Average Intrinsic Value:     ₹2,660.14
Current Market Price:        ₹2,450.00
Discount/Premium:            +8.6%

🎯 VALUATION ASSESSMENT
--------------------------------------------------------------------------------
🟡 MODERATELY UNDERVALUED
Recommendation: Buy Opportunity

💡 IMPLIED EPS ANALYSIS
--------------------------------------------------------------------------------
What EPS would justify the current price at different P/E ratios?

P/E Ratio      Implied EPS         vs Current EPS            Gap             
---------------------------------------------------------------------------
P/E 10         ₹245.00             ₹132.00                   +113.00 (+85.6%)
P/E 15         ₹163.33             ₹132.00                   +31.33 (+23.7%)
P/E 20         ₹122.50             ₹132.00                   -9.50 (-7.2%) ⭐
P/E 25         ₹98.00              ₹132.00                   -34.00 (-25.8%)
P/E 30         ₹81.67              ₹132.00                   -50.33 (-38.1%)

📊 Current EPS (₹132.00) implies P/E of 18.56
   (Trailing P/E: 18.56, Difference: +0.00)

💭 Interpretation:
   Market is pricing the stock at approximately P/E 20
```

### Interpretation

- **Positive % (e.g., +8.6%)**: Stock is **UNDERVALUED** - trading below intrinsic value
- **Negative % (e.g., -5.2%)**: Stock is **OVERVALUED** - trading above intrinsic value
- **Near 0%**: Stock is **FAIRLY VALUED**

### Assessment Levels

- **🟢 SIGNIFICANTLY UNDERVALUED** (>20% discount): Strong Buy Opportunity
- **🟡 MODERATELY UNDERVALUED** (10-20% discount): Buy Opportunity
- **⚪ FAIRLY VALUED** (-10% to +10%): Hold
- **🟠 MODERATELY OVERVALUED** (-10% to -20%): Caution
- **🔴 SIGNIFICANTLY OVERVALUED** (<-20% premium): Consider Selling

---

## 🔍 Finding Undervalued Stocks

### Example: Screen Multiple Stocks

```bash
python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS \
  ICICIBANK.NS WIPRO.NS HCLTECH.NS BHARTIARTL.NS ITC.NS SBIN.NS
```

This will:
1. Analyze all stocks
2. Calculate intrinsic value for each
3. Show which ones are undervalued
4. Rank them by discount percentage

### Output Example

```
📊 ANALYSIS SUMMARY
================================================================================

Stock                Price        Intrinsic Value    Discount/Premium    Status                    
---------------------------------------------------------------------------------------------------
RELIANCE.NS         ₹2,450.00    ₹2,660.14          +8.6%              🟢 UNDERVALUED
TCS.NS              ₹3,200.00    ₹3,100.00          -3.1%              ⚪ FAIR/OVER
INFY.NS             ₹1,450.00    ₹1,680.00          +15.9%             🟢 UNDERVALUED

✅ FOUND 2 UNDERVALUED STOCKS (≥10% discount)
================================================================================

1. INFY.NS
   Current Price:        ₹1,450.00
   Intrinsic Value:      ₹1,680.00
   Discount:             +15.9%
   Assessment:           🟡 MODERATELY UNDERVALUED
```

---

## ⚠️ Important Notes

### Limitations

1. **Data Availability**: Some stocks may not have complete fundamental data
   - Missing EPS, Book Value, or Free Cash Flow will skip certain methods
   - Script will still work with available data

2. **Market Conditions**: Intrinsic value is a theoretical estimate
   - Market can remain irrational longer than you can remain solvent
   - Use as one tool in your investment decision, not the only tool

3. **Sector Variations**: Default ratios (P/E=15, P/B=1.5) are general
   - Tech stocks may have higher P/E ratios
   - Banks may have different P/B ratios
   - Consider sector-specific adjustments

4. **Growth Assumptions**: DCF model uses default 10% growth rate
   - May not reflect actual company growth
   - Adjust based on company-specific analysis

### Best Practices

1. **Combine with Technical Analysis**
   ```bash
   # After finding undervalued stock, run technical analysis
   python3 analyze_stock.py INFY.NS
   ```

2. **Check Multiple Timeframes**: Intrinsic value changes over time
   - Re-run analysis periodically
   - Track changes in valuation

3. **Consider Other Factors**:
   - Management quality
   - Competitive position
   - Industry trends
   - Economic conditions

4. **Diversification**: Don't put all money in one "undervalued" stock
   - Spread risk across multiple opportunities
   - Consider portfolio allocation

---

## 📋 Key Metrics Explained

### P/E Ratio (Price-to-Earnings)
- **What it is**: Stock price divided by earnings per share
- **Lower is better**: Indicates cheaper valuation
- **Fair range**: 10-20 for most stocks (varies by sector)

### P/B Ratio (Price-to-Book)
- **What it is**: Stock price divided by book value per share
- **Lower is better**: Indicates trading closer to asset value
- **Fair range**: 1.0-2.0 for most stocks

### PEG Ratio (Price/Earnings to Growth)
- **What it is**: P/E ratio divided by earnings growth rate
- **Lower is better**: Indicates better value relative to growth
- **Fair value**: 1.0 (P/E should equal growth rate)

### Debt-to-Equity
- **What it is**: Total debt divided by shareholder equity
- **Lower is better**: Less financial risk
- **Fair range**: < 1.0 for most companies

### Free Cash Flow
- **What it is**: Cash generated after capital expenditures
- **Higher is better**: More cash available for growth/dividends
- **Used in**: DCF valuation model

### Implied EPS
- **What it is**: The earnings per share that would justify the current market price at different P/E ratios
- **Formula**: `Implied EPS = Current Price / P/E Ratio`
- **Use case**: Understand what earnings the market is expecting
- **Example**: If stock trades at ₹1,000 and P/E 20, Implied EPS = ₹50
  - If current EPS is ₹40, market expects 25% earnings growth
  - If current EPS is ₹60, stock may be overvalued

---

## 🎯 Example Workflow

### Step 1: Find Undervalued Stocks
```bash
python3 find_undervalued_stocks.py RELIANCE.NS TCS.NS INFY.NS --min-discount 10
```

### Step 2: Analyze Top Candidates
```bash
# Get detailed intrinsic value analysis
python3 calculate_intrinsic_value.py INFY.NS

# Run technical analysis
python3 analyze_stock.py INFY.NS
```

### Step 3: Make Investment Decision
- Review intrinsic value assessment
- Check technical indicators
- Consider risk tolerance
- Make informed decision

---

## 🔧 Troubleshooting

### Error: "Could not fetch data"
- **Cause**: Stock symbol may be incorrect or data unavailable
- **Solution**: Verify symbol format (e.g., `RELIANCE.NS` for Indian stocks)

### Error: "Insufficient data to calculate intrinsic value"
- **Cause**: Missing fundamental data (EPS, Book Value, etc.)
- **Solution**: Stock may be too new or data not available via yfinance

### Results seem incorrect
- **Cause**: Market data may be stale or company fundamentals changed
- **Solution**: Re-run analysis, check company's latest financial reports

---

## 📚 Additional Resources

- **Benjamin Graham's "The Intelligent Investor"**: Classic book on value investing
- **Warren Buffett's Letters**: Learn from the master of value investing
- **Company Annual Reports**: Get detailed fundamental data
- **Sector Analysis**: Understand industry-specific valuation metrics

---

## 💡 Pro Tips

1. **Margin of Safety**: Look for stocks with 20%+ discount for safety buffer
2. **Regular Updates**: Re-run analysis quarterly as fundamentals change
3. **Compare Peers**: Compare intrinsic value across similar companies
4. **Track Changes**: Monitor how discount/premium changes over time
5. **Combine Methods**: Use both fundamental (intrinsic value) and technical analysis

---

**Happy Value Investing! 🚀**

