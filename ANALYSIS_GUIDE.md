# 📊 Stock Analysis & Visualization Guide

## Quick Start

### Option 1: Unified Tool (Recommended)
```bash
python3 analyze_stock.py
```
This will show an interactive menu to select a stock and run all analyses.

### Option 2: Individual Tools
Each tool can be run independently for specific needs.

---

## 🛠️ Available Tools

### 1. **Main Analysis Tool** (`analyze_stock.py`)
**What it does:** Runs all analyses in one go - correlation, behavioral patterns, similarity, and generates a report. **Automatically generates analysis files if they don't exist!**

**Usage:**
```bash
python3 analyze_stock.py                    # Interactive menu - can enter new ticker
python3 analyze_stock.py RELIANCE.NS       # Analyze specific stock
python3 analyze_stock.py RELIANCE.NS --all # Full analysis with similarity
```

**Interactive Features:**
- Option 1: Select from existing stocks
- Option 2: **Enter new ticker symbol** - automatically generates analysis first!
- Tool automatically adds `.NS` suffix for Indian stocks

**Output:**
- Correlation heatmap (PNG)
- Market regimes plot (PNG)
- Comprehensive HTML report
- All saved in `analysis_results/` folder

---

### 2. **Correlation Analysis** (`analyze_correlations.py`)
**What it does:** Finds relationships between all 86 indicators.

**Usage:**
```bash
python3 analyze_correlations.py output/RELIANCE.NS_analysis.csv
```

**Output:**
- Correlation heatmap image
- CSV file with full correlation matrix
- List of highly correlated indicator pairs

---

### 3. **Behavioral Patterns** (`behavioral_patterns.py`)
**What it does:** Identifies market regimes (bull, bear, sideways) using clustering.

**Usage:**
```bash
python3 behavioral_patterns.py output/RELIANCE.NS_analysis.csv
python3 behavioral_patterns.py output/RELIANCE.NS_analysis.csv --clusters=5
```

**Output:**
- Market regimes plot showing price with regime colors
- CSV file with regime labels for each day
- Summary statistics for each regime

---

### 4. **Similar Days Finder** (`find_similar_days.py`)
**What it does:** Finds historical days with similar indicator patterns.

**Usage:**
```bash
python3 find_similar_days.py 2024-01-15 output/RELIANCE.NS_analysis.csv
```

**Output:**
- CSV file with top 10 similar days
- Shows subsequent price performance for each similar day

---

### 5. **Interactive Dashboard** (`visualize_indicators.py`)
**What it does:** Creates interactive HTML dashboards to explore indicator relationships.

**Usage:**
```bash
python3 visualize_indicators.py
```
Follow the interactive menu to:
1. Select a stock
2. Choose X-axis indicator
3. Choose Y-axis indicator
4. Dashboard is saved as HTML

**Output:**
- Interactive HTML file in `analysis_results/dashboards/`
- Scatter plot colored by market regime
- Hover to see dates and values

---

### 6. **Report Generator** (`generate_analysis_report.py`)
**What it does:** Creates a comprehensive HTML report combining all analyses.

**Usage:**
```bash
python3 generate_analysis_report.py RELIANCE.NS
```

**Output:**
- Single HTML file with all visualizations and summaries
- Self-contained (images embedded)
- Easy to share or view in browser

---

## 📁 File Organization

```
ta/
├── analyze_stock.py              # 🎯 START HERE - Main unified tool
├── analyze_correlations.py       # Correlation analysis
├── behavioral_patterns.py        # Market regime identification
├── find_similar_days.py          # Pattern matching
├── visualize_indicators.py       # Interactive dashboards
├── generate_analysis_report.py   # Comprehensive reports
│
├── output/                       # Stock analysis CSV files
│   ├── RELIANCE.NS_analysis.csv
│   ├── HDFCBANK.NS_analysis.csv
│   └── ...
│
└── analysis_results/             # All analysis outputs (organized by ticker)
    ├── WIPRO.NS/                 # All WIPRO results in one folder
    │   ├── correlation_heatmap.png
    │   ├── correlation_matrix.csv
    │   ├── market_regimes_plot.png
    │   ├── data_with_regimes.csv
    │   ├── comprehensive_report.html
    │   ├── strategy_backtest_*.csv
    │   ├── similar_days_*.csv
    │   └── dashboards/
    │       └── *.html
    ├── RELIANCE.NS/              # All RELIANCE results
    └── HDFCBANK.NS/              # All HDFCBANK results
```

**Each stock has its own organized folder - easy to find and manage!** ✨

---

## 🎯 Typical Workflow

### For Quick Analysis:
```bash
# 1. Generate stock data (if not done)
python3 analyze_indian_stocks.py RELIANCE.NS

# 2. Run all analyses
python3 analyze_stock.py RELIANCE.NS --all

# 3. View the report
open analysis_results/RELIANCE.NS_comprehensive_report.html
```

### For Deep Dive:
```bash
# 1. Correlation analysis
python3 analyze_correlations.py output/RELIANCE.NS_analysis.csv

# 2. Behavioral patterns
python3 behavioral_patterns.py output/RELIANCE.NS_analysis.csv

# 3. Find similar days to a specific date
python3 find_similar_days.py 2024-01-15 output/RELIANCE.NS_analysis.csv

# 4. Create custom interactive dashboard
python3 visualize_indicators.py

# 5. Generate final report
python3 generate_analysis_report.py RELIANCE.NS
```

---

## 💡 What Each Analysis Tells You

### Correlation Analysis
- **Shows:** Which indicators move together
- **Use for:** Understanding redundant indicators, finding indicator groups
- **Example:** RSI and Stochastic RSI are highly correlated (both measure momentum)

### Behavioral Patterns
- **Shows:** Different market regimes (bull, bear, sideways)
- **Use for:** Understanding market cycles, identifying regime changes
- **Example:** Regime 2 might be "bull market" with high returns and low volatility

### Similar Days
- **Shows:** Historical days with similar indicator patterns
- **Use for:** Predicting future price movements based on past patterns
- **Example:** "Today looks like 2020-03-15, which was followed by a 10% gain"

### Interactive Dashboards
- **Shows:** Relationship between any two indicators
- **Use for:** Exploring data visually, finding patterns
- **Example:** Plot RSI vs MACD to see their relationship

---

## 🔧 Troubleshooting

### "File not found" errors
- Make sure you've run `analyze_indian_stocks.py` first to generate the analysis CSV files

### "Regime file not found"
- Run `behavioral_patterns.py` first to generate regime data

### "Similarity file not found"
- Run `find_similar_days.py` for the date you need, or use `--all` flag in `analyze_stock.py`

### Scripts are slow
- Use `--tail=1000` in `analyze_correlations.py` to analyze only recent data
- Reduce number of clusters in `behavioral_patterns.py` with `--clusters=3`

---

## 📚 Next Steps

1. **Start with the unified tool:** `python3 analyze_stock.py`
2. **Explore the HTML report** to see all findings
3. **Create custom dashboards** for specific indicator pairs
4. **Use similar days** to inform trading decisions
5. **Compare multiple stocks** by running analysis on each

---

## 🎓 Understanding the Results

- **Correlation > 0.95:** Indicators are nearly identical (redundant)
- **Correlation 0.7-0.95:** Strong relationship (useful for confirmation)
- **Correlation < 0.3:** Weak relationship (independent indicators)

- **Regime with high returns:** Bull market conditions
- **Regime with high volatility:** Uncertain/volatile market
- **Regime with negative returns:** Bear market conditions

- **Similar days with consistent outcomes:** Pattern is predictive
- **Similar days with mixed outcomes:** Pattern is not reliable

---

**Happy Analyzing! 📈**

