# 💰 Intrinsic Value Calculator Guide

## Overview

This tool calculates the **intrinsic value** of stocks using multiple valuation methods to help you identify **undervalued stocks** (stocks trading below their true worth).

## 🎯 What is Intrinsic Value?

**Intrinsic value** is the true worth of a stock based on fundamental analysis, independent of its current market price. If a stock's intrinsic value is higher than its market price, it may be **undervalued** and represent a buying opportunity.

## 📊 Valuation Methods Used

The calculator uses **5 different valuation methods** to provide a comprehensive analysis:

### 1. **Graham's Formula** (Benjamin Graham)
- Formula: `IV = √(22.5 × EPS × Book Value)`
- Based on the legendary investor's preferred ratios (P/E of 15, P/B of 1.5)
- Best for: Value stocks with stable earnings

### 2. **DCF Model** (Discounted Cash Flow)
- Projects future free cash flows and discounts them to present value
- Uses 10-year projection with terminal value
- Best for: Companies with predictable cash flows

### 3. **P/E Based Valuation**
- Uses fair P/E ratio of 15 (can be adjusted for sector)
- Formula: `IV = EPS × Fair P/E`
- Best for: Comparing to market averages

### 4. **P/B Based Valuation**
- Uses fair Price-to-Book ratio of 1.5
- Formula: `IV = Book Value × Fair P/B`
- Best for: Asset-heavy companies

### 5. **PEG Based Valuation**
- Considers growth rate along with P/E
- Fair PEG = 1.0 (P/E should equal growth rate)
- Best for: Growth stocks

## 🚀 How to Use

### Basic Usage

```bash
# Analyze a single stock
python3 calculate_intrinsic_value.py RELIANCE.NS

# Analyze multiple stocks
python3 calculate_intrinsic_value.py TCS.NS INFY.NS HDFCBANK.NS
```

### Example Output

```
💰 INTRINSIC VALUE ANALYSIS: RELIANCE.NS
================================================================================

📊 Fetching fundamental data for RELIANCE.NS...
✅ Data fetched successfully

📈 Current Market Price: ₹2,450.00
📋 Company: Reliance Industries Limited
🏢 Sector: Energy
🏭 Industry: Oil & Gas Refining & Marketing

--------------------------------------------------------------------------------
🔍 CALCULATING INTRINSIC VALUE (Multiple Methods)
--------------------------------------------------------------------------------
1️⃣  Graham's Formula:        ₹2,850.00 (+16.3%)
2️⃣  DCF Model (10-year):      ₹2,720.00 (+11.0%)
3️⃣  P/E Based (Fair P/E=15):   ₹2,650.00 (+8.2%)
4️⃣  P/B Based (Fair P/B=1.5):  ₹2,600.00 (+6.1%)
5️⃣  PEG Based:                ₹2,750.00 (+12.2%)

--------------------------------------------------------------------------------
📊 SUMMARY
--------------------------------------------------------------------------------
Average Intrinsic Value:     ₹2,714.00
Current Market Price:        ₹2,450.00
Discount/Premium:            +10.8%

--------------------------------------------------------------------------------
🎯 VALUATION ASSESSMENT
--------------------------------------------------------------------------------
🟡 MODERATELY UNDERVALUED
Recommendation: Buy Opportunity
```

## 📈 Understanding the Results

### Discount/Premium Percentage

- **+20% or more**: 🟢 **SIGNIFICANTLY UNDERVALUED** - Strong buy opportunity
- **+10% to +20%**: 🟡 **MODERATELY UNDERVALUED** - Buy opportunity
- **-10% to +10%**: ⚪ **FAIRLY VALUED** - Hold
- **-20% to -10%**: 🟠 **MODERATELY OVERVALUED** - Caution
- **-20% or less**: 🔴 **SIGNIFICANTLY OVERVALUED** - Consider selling

### Key Metrics Explained

- **P/E Ratio**: Price-to-Earnings ratio. Lower is generally better (but depends on growth)
- **P/B Ratio**: Price-to-Book ratio. < 1.0 means trading below book value
- **PEG Ratio**: P/E divided by growth rate. < 1.0 is considered good
- **EPS**: Earnings Per Share - company's profit per share
- **Book Value**: Net asset value per share
- **Debt-to-Equity**: Financial leverage. Lower is generally safer

## ⚠️ Important Notes

### Limitations

1. **Data Availability**: Some stocks may not have complete fundamental data
2. **Assumptions**: Models use standard assumptions (e.g., 7% risk-free rate, 15 P/E)
3. **Market Context**: Intrinsic value doesn't account for market sentiment or short-term factors
4. **Sector Differences**: Different sectors have different typical ratios

### Best Practices

1. **Use Multiple Methods**: Don't rely on a single valuation method
2. **Compare to Peers**: Check how the stock compares to its sector/industry
3. **Consider Growth**: High-growth stocks may justify higher valuations
4. **Check Financial Health**: Look at debt levels, profit margins, cash flow
5. **Combine with Technical Analysis**: Use this with your existing technical indicators

## 🔄 Integration with Existing Tools

You can combine intrinsic value analysis with your existing tools:

```bash
# Step 1: Calculate intrinsic value
python3 calculate_intrinsic_value.py RELIANCE.NS

# Step 2: Run technical analysis
python3 analyze_indian_stocks.py RELIANCE.NS

# Step 3: Run complete setup (includes backtesting)
python3 complete_setup.py RELIANCE.NS
```

## 💡 Investment Strategy

### Value Investing Approach

1. **Find Undervalued Stocks**: Look for stocks with 10%+ discount to intrinsic value
2. **Check Fundamentals**: Ensure good financial health (low debt, good margins)
3. **Verify with Technicals**: Use your technical analysis to find good entry points
4. **Diversify**: Don't put all money in one stock
5. **Be Patient**: Value investing is a long-term strategy

### Example Workflow

```bash
# 1. Screen for undervalued stocks
python3 calculate_intrinsic_value.py RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS

# 2. For undervalued stocks, run technical analysis
python3 complete_setup.py RELIANCE.NS  # If RELIANCE is undervalued

# 3. Review backtest results and make investment decision
```

## 🎓 Learning More

### Understanding Valuation Methods

- **Graham's Formula**: Based on "The Intelligent Investor" by Benjamin Graham
- **DCF**: Most comprehensive but requires accurate cash flow projections
- **P/E Analysis**: Simple but effective for comparing similar companies
- **P/B Analysis**: Useful for asset-heavy businesses (banks, real estate)
- **PEG Ratio**: Combines value and growth considerations

### Further Reading

- "The Intelligent Investor" by Benjamin Graham
- "Security Analysis" by Benjamin Graham & David Dodd
- "A Random Walk Down Wall Street" by Burton Malkiel

## ❓ Troubleshooting

### "Insufficient data to calculate intrinsic value"

**Cause**: Missing EPS, Book Value, or Free Cash Flow data

**Solutions**:
- Some stocks (especially new listings) may not have complete data
- Try checking the stock on Yahoo Finance directly
- The stock may be too new or have limited financial history

### "Could not fetch data"

**Cause**: Invalid symbol or network issues

**Solutions**:
- Verify the symbol format (e.g., `RELIANCE.NS` for Indian stocks)
- Check your internet connection
- Try again later (Yahoo Finance may have rate limits)

## 📝 Example: Finding Undervalued Stocks

```bash
# Analyze a portfolio of stocks
python3 calculate_intrinsic_value.py \
  RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS ICICIBANK.NS \
  WIPRO.NS HCLTECH.NS BHARTIARTL.NS ITC.NS SBIN.NS

# Look for stocks with +10% or higher discount
# These are your potential buy candidates
```

---

**Remember**: Intrinsic value is a guide, not a guarantee. Always do your own research and consider your risk tolerance before investing! 📊💰

