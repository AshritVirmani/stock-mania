# Dhan API Scripts

This directory contains all scripts specifically designed to work with Dhan API data for intraday analysis.

## Script Organization

### Main Workflow Scripts (Numbered)

- **00_complete_setup_dhan.py** - Complete orchestrator that runs all Dhan intraday analysis steps
- **01_fetch_intraday_data.py** - Fetches 1-minute or 5-minute intraday OHLCV data from Dhan API
- **02_simple_intraday_analysis.py** - Smart Money pattern analysis (Synthetic IV, OBV, Sentiment Skew)
- **03_calculate_intraday_indicators.py** - Calculates technical indicators + Smart Money features
- **04_intraday_ta_accuracy_analysis.py** - Analyzes TA indicator accuracy with market-hour filtering
- **05_intraday_pattern_discovery.py** - Comprehensive pattern discovery with parallel processing
- **06_fetch_options_data.py** - Fetches historical options data (requires v2 API access)
- **07_market_depth_websocket.py** - Real-time market depth streaming (during market hours)

### Supporting Scripts (Utility)

- **analyze_intraday_time_patterns.py** - Time-based pattern analysis (hourly, day-of-week)
- **analyze_intraday_volume_patterns.py** - Volume pattern analysis
- **analyze_intraday_price_patterns.py** - Price pattern analysis
- **analyze_indicator_combinations.py** - Indicator combination analysis
- **analyze_intraday_ta_accuracy.py** - Core TA accuracy analysis engine
- **generate_intraday_pattern_report.py** - Generates comprehensive HTML reports
- **rank_intraday_indicators.py** - Ranks and visualizes indicator performance

## Quick Start

### Complete Workflow (Recommended)

```bash
# Run complete Dhan API intraday analysis
python3 dhan_scripts/00_complete_setup_dhan.py SYMBOL.NS \
    --start 2024-11-01 --end 2024-11-24 --interval 1
```

### Individual Steps

```bash
# Step 1: Fetch intraday data
python3 dhan_scripts/01_fetch_intraday_data.py SYMBOL.NS \
    --start 2024-11-01 --end 2024-11-24 --interval 1

# Step 2: Smart Money analysis
python3 dhan_scripts/02_simple_intraday_analysis.py SYMBOL.NS \
    --data-file analysis_results/SYMBOL/intraday_analysis/data/SYMBOL_intraday_1min_raw.csv

# Step 3: Calculate indicators
python3 dhan_scripts/03_calculate_intraday_indicators.py \
    --input-file analysis_results/SYMBOL/intraday_analysis/data/SYMBOL_intraday_1min_raw.csv \
    --symbol SYMBOL.NS

# Step 4: TA accuracy analysis
python3 dhan_scripts/04_intraday_ta_accuracy_analysis.py SYMBOL.NS \
    --start 2024-11-01 --end 2024-11-24 --interval 1

# Step 5: Pattern discovery
python3 dhan_scripts/05_intraday_pattern_discovery.py SYMBOL.NS \
    --data-file analysis_results/SYMBOL/intraday_analysis/data/SYMBOL_intraday_1min_raw.csv
```

## Features

- **Smart Caching**: Reuses cached data to avoid redundant API calls
- **Market Hours Filtering**: Automatically filters to 09:15-15:30 IST
- **Parallel Processing**: Pattern discovery runs analyses in parallel
- **Error Resilience**: Continues execution even if individual steps fail
- **Comprehensive Reporting**: Generates HTML reports with all findings

## Dependencies

All scripts depend on `legacy_scripts/complete_setup.py` for:
- `ScripMaster` class
- `DhanDataExtractor` class
- Dhan API configuration (CLIENT_ID, ACCESS_TOKEN, SCRIP_MASTER_PATH)

## Output Structure

```
analysis_results/{SYMBOL}/intraday_analysis/
├── data/
│   ├── {SYMBOL}_intraday_1min_raw.csv
│   ├── {SYMBOL}_intraday_1min_indicators.csv
│   └── {SYMBOL}_intraday_1min_features.csv
├── results/
│   └── indicator_accuracy_1min.csv
├── visualizations/
│   └── (charts and plots)
└── pattern_analysis/
    ├── smart_money/
    ├── time_patterns/
    ├── volume_patterns/
    ├── price_patterns/
    └── comprehensive_pattern_report.html
```

