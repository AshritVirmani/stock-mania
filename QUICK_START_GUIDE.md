# Quick Start Guide - Daily Usage

## 🚀 How to Use This System Tomorrow (and Every Day)

### Step 1: Update Stock Data (Get Latest Prices)

To get the most recent data including today's trading session:

```bash
python3 analyze_indian_stocks.py YOUR_STOCK.NS
```

**Examples:**
```bash
python3 analyze_indian_stocks.py GODREJPROP.NS
python3 analyze_indian_stocks.py WIPRO.NS RELIANCE.NS TCS.NS
```

This will:
- Fetch all historical data (including today if market was open)
- Calculate all 86 technical indicators
- Save to `output/YOUR_STOCK.NS_analysis.csv`

---

### Step 2: Run Full Analysis (One Command)

For comprehensive analysis including MCPT backtest:

```bash
python3 analyze_stock.py YOUR_STOCK.NS --all
```

**What this does:**
1. ✅ Correlation analysis (heatmaps)
2. ✅ Behavioral patterns (market regimes)
3. ✅ Similarity analysis (find similar days)
4. ✅ **Donchian MCPT backtest** (walk-forward, statistical significance)
5. ✅ Comprehensive HTML report

**Example:**
```bash
python3 analyze_stock.py GODREJPROP.NS --all
```

---

### Step 3: View Results

All results are organized in: `analysis_results/YOUR_STOCK.NS/`

**Key Files to Check:**

1. **`comprehensive_report.html`** - Open in browser for full analysis
2. **`donchian_mcpt_report.html`** - MCPT backtest results
3. **`donchian_actual_vs_permuted.png`** - Visual: Is strategy significant?
4. **`donchian_mcpt_summary.csv`** - Quick stats (p-value, returns)

---

## 📊 Quick Commands Reference

### Daily Workflow

```bash
# 1. Update data for your stocks
python3 analyze_indian_stocks.py GODREJPROP.NS WIPRO.NS

# 2. Run full analysis
python3 analyze_stock.py GODREJPROP.NS --all

# 3. Check results
open analysis_results/GODREJPROP.NS/comprehensive_report.html
open analysis_results/GODREJPROP.NS/donchian_mcpt_report.html
```

### Individual Analysis Tools

```bash
# Just correlation analysis
python3 analyze_correlations.py output/GODREJPROP.NS_analysis.csv

# Just behavioral patterns
python3 behavioral_patterns.py output/GODREJPROP.NS_analysis.csv

# Just Donchian MCPT backtest
python3 donchian_mcpt_backtest.py output/GODREJPROP.NS_analysis.csv

# Find similar days to a specific date
python3 find_similar_days.py 2025-11-14 output/GODREJPROP.NS_analysis.csv
```

---

## 🎯 What to Look For

### In Donchian MCPT Results:

1. **Average P-Value**:
   - **< 0.05** = Very significant (strong edge)
   - **0.05 - 0.10** = Significant (good edge)
   - **0.10 - 0.30** = Moderate significance (some edge)
   - **> 0.30** = Weak significance (may be luck)

2. **Actual vs Permuted Chart**:
   - Red line **clearly above** grey cluster = Strategy has real edge
   - Red line **in grey cluster** = Results might be luck

3. **Annualized Log Return**:
   - Positive = Strategy profitable
   - Compare to buy-and-hold for context

---

## 💡 Pro Tips

1. **Update data daily** before analysis to get latest indicators
2. **Use `--all` flag** for complete analysis including MCPT
3. **Check p-values** to assess statistical significance
4. **Compare multiple stocks** to find best opportunities
5. **Review walk-forward results** to see strategy performance over time

---

## 📁 File Locations

- **Input data**: `output/YOUR_STOCK.NS_analysis.csv`
- **All results**: `analysis_results/YOUR_STOCK.NS/`
- **Reports**: Open HTML files in your browser

---

## 🔄 Complete Daily Routine

```bash
# Morning routine (after market opens):
cd "/Users/av/Downloads/dev mode/ta"

# 1. Update data for stocks you're tracking
python3 analyze_indian_stocks.py GODREJPROP.NS WIPRO.NS RELIANCE.NS

# 2. Run full analysis
python3 analyze_stock.py GODREJPROP.NS --all

# 3. Review results
open analysis_results/GODREJPROP.NS/donchian_mcpt_report.html
```

---

## ❓ Quick Troubleshooting

**Problem**: "File not found"
- **Solution**: Run `python3 analyze_indian_stocks.py YOUR_STOCK.NS` first

**Problem**: "No data found"
- **Solution**: Check stock symbol format (must end with `.NS` for Indian stocks)

**Problem**: Analysis takes too long
- **Solution**: Use `--start-date 2020-01-01` to limit historical data

---

## 📞 Need Help?

- Check `ANALYSIS_GUIDE.md` for detailed documentation
- Check `DONCHIAN_STRATEGY_EXPLAINED.md` to understand the strategy
- Check `HOW_TO_READ_CORRELATION_HEATMAP.md` for interpretation guides

