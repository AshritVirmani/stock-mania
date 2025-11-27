# Scripts Directory

This directory contains all executable Python scripts, organized by purpose.

## 📂 Structure

```
scripts/
├── analysis/      # Analysis and reporting scripts
├── dhan/         # Dhan API integration scripts
├── legacy/       # Legacy workflow scripts
└── utils/        # Utility scripts
```

## 🔧 Usage

### Legacy Workflow (Complete Analysis)
```bash
# Run complete analysis for a ticker
python3 scripts/legacy/complete_setup.py TICKER.NS

# Individual steps
python3 scripts/legacy/01_analyze_indian_stocks.py TICKER.NS
python3 scripts/legacy/04_behavioral_patterns.py data_file.csv
```

### Dhan API Workflow
```bash
# Complete Dhan setup
python3 scripts/dhan/00_complete_setup_dhan.py TICKER.NS

# Individual steps
python3 scripts/dhan/01_fetch_intraday_data.py TICKER.NS
python3 scripts/dhan/02_simple_intraday_analysis.py TICKER.NS
```

### Utilities
```bash
# Calculate intrinsic value
python3 scripts/utils/calculate_intrinsic_value.py TICKER.NS

# Find undervalued stocks
python3 scripts/utils/find_undervalued_stocks.py
```

## 📋 Script Categories

### `legacy/`
Original workflow scripts for complete stock analysis:
- `complete_setup.py` - Main entry point for full analysis
- `01_analyze_indian_stocks.py` - Data fetching and indicators
- `04_behavioral_patterns.py` - Market regime analysis
- `07a_simple_backtest_for_new_stocks.py` - Backtesting
- And more...

### `dhan/`
Dhan API integration and intraday analysis:
- `00_complete_setup_dhan.py` - Complete Dhan workflow
- `01_fetch_intraday_data.py` - Fetch intraday data
- `02_simple_intraday_analysis.py` - Intraday pattern analysis
- And more...

### `utils/`
Utility scripts for various tasks:
- `calculate_intrinsic_value.py` - Stock valuation
- `find_undervalued_stocks.py` - Stock screening

### `analysis/`
Analysis and reporting scripts (currently empty, for future use)

## 🔗 Related Documentation

- See `docs/COMPLETE_SETUP_GUIDE.md` for detailed workflow
- See `docs/DHAN_DATA_WORKFLOW.md` for Dhan API workflow
- See `docs/PROJECT_STRUCTURE.md` for overall project structure

