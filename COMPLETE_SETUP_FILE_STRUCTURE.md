# Complete Setup File Structure Diagram

## Overview
When you run `python3 legacy_scripts/complete_setup.py TICKER.NS`, the script creates a ticker-specific folder with organized subdirectories and generates all analysis files in a clean, clutter-free structure.

---

## Input
```
Command: python3 legacy_scripts/complete_setup.py WOCKPHARMA.NS
```

---

## Execution Flow & File Creation

### Step 1: Data Fetching & Indicators
**Script:** `analyze_indian_stocks.py`
**Action:** Fetches historical data from Yahoo Finance, calculates 86 technical indicators
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    └── data/
        └── WOCKPHARMA.NS_analysis.csv  ← Main data file (OHLCV + 86 indicators)
```

---

### Step 2: Benjamin Oreo Valuation
**Script:** `calculate_intrinsic_value.py`
**Action:** Calculates intrinsic value using 6 valuation methods (Graham, DCF, P/E, P/B, PEG, Implied EPS)
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    │   └── WOCKPHARMA.NS_analysis.csv (from Step 1)
    └── valuation/
        └── intrinsic_value.json  ← Valuation results with all methods
```

---

### Step 3: Correlation Analysis
**Script:** `analyze_correlations.py`
**Input:** `data/WOCKPHARMA.NS_analysis.csv`
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    │   └── WOCKPHARMA.NS_analysis.csv
    ├── valuation/
    │   └── intrinsic_value.json (from Step 2)
    └── analysis/
        ├── correlation_matrix.csv  ← Full correlation matrix
        └── correlation_heatmap.png  ← Filtered heatmap (significant correlations only)
```

---

### Step 4: Behavioral Pattern Analysis (Market Regimes)
**Script:** `behavioral_patterns.py`
**Input:** `data/WOCKPHARMA.NS_analysis.csv`
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    ├── valuation/
    └── analysis/
        ├── correlation_matrix.csv (from Step 3)
        ├── correlation_heatmap.png
        ├── data_with_regimes.csv  ← Data with regime labels (K-Means clusters)
        └── market_regimes_plot.png  ← Regime visualization over time
```

---

### Step 5: Red Light Regime Identification
**Script:** `identify_red_light_regime.py`
**Input:** `analysis/data_with_regimes.csv`
**Action:** Identifies worst-performing regime (prints to console, no new file)

---

### Step 6: Similarity Analysis
**Script:** `find_similar_days.py`
**Input:** `data/WOCKPHARMA.NS_analysis.csv` + latest date from `analysis/data_with_regimes.csv`
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    ├── valuation/
    └── analysis/
        ├── ... (previous files)
        └── similar_days_latest.csv  ← Similar days for latest date (no date suffix)
```

---

### Step 7: Standard Donchian MCPT Backtest
**Script:** `donchian_mcpt_backtest.py`
**Input:** `data/WOCKPHARMA.NS_analysis.csv`
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    ├── valuation/
    ├── analysis/
    └── backtests/
        └── standard/
            ├── results.csv  ← Detailed walk-forward results
            ├── summary.csv  ← Quick summary metrics
            ├── report.html  ← Comprehensive HTML report
            └── equity_curve.png  ← Performance visualization
```

**Note:** If data < 3 years, runs `simple_backtest_for_new_stocks.py` instead (creates different files)

---

### Step 8: Enhanced Donchian MCPT Backtest
**Script:** `donchian_enhanced_backtest.py`
**Input:** `data/WOCKPHARMA.NS_analysis.csv` + `analysis/data_with_regimes.csv`
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    ├── valuation/
    ├── analysis/
    └── backtests/
        ├── standard/ (from Step 7)
        └── enhanced/
            ├── results.csv  ← Enhanced strategy results
            └── summary.csv  ← Enhanced strategy summary
```

**Note:** Only runs if data >= 3 years (requires walk-forward)

---

### Step 9: Drawdown Analysis
**Script:** `analyze_drawdowns.py`
**Input:** `backtests/standard/results.csv` + `analysis/data_with_regimes.csv`
**Action:** Analyzes drawdowns by regime (prints to console, may create additional files)

---

### Step 10: Strategy Comparison
**Script:** `compare_backtests.py`
**Input:** Reads from `backtests/standard/` and `backtests/enhanced/`
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    ├── valuation/
    ├── analysis/
    ├── backtests/
    └── reports/
        └── backtest_comparison.csv  ← Standard vs Enhanced comparison
```

---

### Step 11: Comprehensive Report
**Script:** `generate_analysis_report.py`
**Input:** Reads all files from ticker directory
**Creates:**
```
analysis_results/
└── WOCKPHARMA.NS/
    ├── data/
    ├── valuation/
    ├── analysis/
    ├── backtests/
    └── reports/
        ├── backtest_comparison.csv (from Step 10)
        └── comprehensive_report.html  ← All analyses in one HTML report
```

---

## Final Directory Structure

After complete setup finishes, the directory structure looks like:

```
analysis_results/
└── WOCKPHARMA.NS/
    │
    ├── data/
    │   └── WOCKPHARMA.NS_analysis.csv
    │
    ├── valuation/
    │   └── intrinsic_value.json
    │
    ├── analysis/
    │   ├── correlation_matrix.csv
    │   ├── correlation_heatmap.png
    │   ├── data_with_regimes.csv
    │   ├── market_regimes_plot.png
    │   └── similar_days_latest.csv
    │
    ├── backtests/
    │   ├── standard/
    │   │   ├── results.csv
    │   │   ├── summary.csv
    │   │   ├── report.html
    │   │   └── equity_curve.png
    │   └── enhanced/
    │       ├── results.csv
    │       └── summary.csv
    │
    └── reports/
        ├── backtest_comparison.csv
        └── comprehensive_report.html
```

---

## File Dependencies Flow

```
data/WOCKPHARMA.NS_analysis.csv
    │
    ├─→ calculate_intrinsic_value.py
    │   └─→ valuation/intrinsic_value.json
    │
    ├─→ analyze_correlations.py
    │   └─→ analysis/correlation_matrix.csv, analysis/correlation_heatmap.png
    │
    ├─→ behavioral_patterns.py
    │   └─→ analysis/data_with_regimes.csv, analysis/market_regimes_plot.png
    │       │
    │       ├─→ identify_red_light_regime.py (reads, no output)
    │       │
    │       └─→ find_similar_days.py (uses latest date)
    │           └─→ analysis/similar_days_latest.csv
    │
    ├─→ donchian_mcpt_backtest.py
    │   └─→ backtests/standard/results.csv, summary.csv, report.html, equity_curve.png
    │       │
    │       └─→ analyze_drawdowns.py (reads walkforward + regimes)
    │
    └─→ donchian_enhanced_backtest.py (uses analysis + regimes)
        └─→ backtests/enhanced/results.csv, summary.csv
            │
            └─→ compare_backtests.py (reads both summaries)
                └─→ reports/backtest_comparison.csv
                    │
                    └─→ generate_analysis_report.py (reads all files)
                        └─→ reports/comprehensive_report.html
```

---

## Key Points

1. **Organized Subdirectories:** Files are organized by function (data, valuation, analysis, backtests, reports)
2. **Clean Structure:** Reduced from ~18 files in root to ~12 files in organized folders
3. **Benjamin Oreo Integration:** Intrinsic value calculation is now part of the complete workflow
4. **Sequential Dependencies:** Later steps depend on earlier step outputs
5. **Main Data File:** `data/{TICKER}_analysis.csv` is the foundation for all analyses
6. **Regime Data:** `analysis/data_with_regimes.csv` enables enhanced strategies
7. **Final Report:** `reports/comprehensive_report.html` aggregates everything

---

## File Count Summary

After complete setup, you typically get:
- **1** main data file (in `data/`)
- **1** valuation file (in `valuation/`)
- **5** analysis files (in `analysis/`)
- **4** standard backtest files (in `backtests/standard/`)
- **2** enhanced backtest files (in `backtests/enhanced/`)
- **2** report files (in `reports/`)
- **Total: ~15 files** organized in 5 subdirectories (33% reduction from previous structure)

---

## Benefits of New Structure

1. **Reduced Clutter:** Files organized into logical subdirectories instead of single flat folder
2. **Easier Navigation:** Find files quickly by category (data, analysis, backtests, etc.)
3. **Better Maintenance:** Clear separation of concerns
4. **Cleaner Names:** Simplified filenames (results.csv instead of donchian_walkforward_results.csv)
5. **Benjamin Oreo Integration:** Valuation now part of standard workflow
6. **Backward Compatibility:** Scripts check new paths first, fallback to old paths

---

## Notes

- If stock has < 3 years of data, walk-forward backtests are skipped
- Some scripts may create additional intermediate files
- All paths are relative to project root
- Old files in root `analysis_results/{TICKER}/` are still supported for backward compatibility
- Valuation results are saved as JSON for easy programmatic access
