# 📊 Stock Analysis Tools - Quick Reference

## 🚀 Start Here

**One command to run everything:**
```bash
python3 analyze_stock.py
```

**What happens:**
1. Tool asks if you want to select from existing stocks OR enter a new ticker symbol
2. If you enter a new ticker, it automatically generates the analysis file first
3. Then runs all analyses:
   - ✅ Correlation analysis (which indicators move together)
   - ✅ Behavioral patterns (market regimes)
   - ✅ Similar days finder (historical patterns)
   - ✅ Comprehensive HTML report

**Example:**
```bash
python3 analyze_stock.py
# Select option 2: Enter new ticker symbol
# Enter: WIPRO.NS
# Tool automatically generates analysis and runs all features!
```

---

## 📋 All Available Tools

| Tool | Purpose | Command |
|------|---------|---------|
| **Main Tool** | Run all analyses | `python3 analyze_stock.py` |
| **Strategy Backtest** | Test trading strategies | `python3 backtest_strategies.py STOCK` |
| Correlation | Find indicator relationships | `python3 analyze_correlations.py output/STOCK.csv` |
| Patterns | Identify market regimes | `python3 behavioral_patterns.py output/STOCK.csv` |
| Similar Days | Find historical patterns | `python3 find_similar_days.py DATE output/STOCK.csv` |
| Dashboard | Interactive visualizations | `python3 visualize_indicators.py` |
| Report | Generate HTML report | `python3 generate_analysis_report.py STOCK` |

---

## 📁 Where Everything Goes

```
output/                    → Stock analysis CSV files
analysis_results/          → All analysis outputs (organized by ticker)
  ├── WIPRO.NS/           → All WIPRO results
  │   ├── correlation_heatmap.png
  │   ├── correlation_matrix.csv
  │   ├── market_regimes_plot.png
  │   ├── data_with_regimes.csv
  │   ├── comprehensive_report.html
  │   ├── strategy_backtest_*.csv
  │   ├── similar_days_*.csv
  │   └── dashboards/     → Interactive HTML files
  ├── RELIANCE.NS/        → All RELIANCE results
  └── HDFCBANK.NS/        → All HDFCBANK results
```

**Each stock has its own folder - no clutter!** ✨

---

## 🎯 Common Tasks

### Analyze a stock completely:
```bash
python3 analyze_stock.py RELIANCE.NS --all
```

### Find days similar to today:
```bash
python3 find_similar_days.py 2024-01-15 output/RELIANCE.NS_analysis.csv
```

### Create custom visualization:
```bash
python3 visualize_indicators.py
# Then follow the menu
```

### View everything in one report:
```bash
python3 generate_analysis_report.py RELIANCE.NS
# Open: analysis_results/RELIANCE.NS_comprehensive_report.html
```

---

## 📖 Full Documentation

See `ANALYSIS_GUIDE.md` for detailed explanations of each tool.

---

**That's it! Start with `python3 analyze_stock.py` and explore from there.** 🎉

