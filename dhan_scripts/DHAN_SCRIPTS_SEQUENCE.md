# Dhan Scripts - Sequential Execution Order

All scripts that work with raw Dhan API data, organized similar to legacy_scripts structure.

## Main Workflow Scripts

### 00_complete_setup_dhan.py
**Complete Orchestrator** - Runs all Dhan intraday analysis steps in sequence
- Purpose: One-command complete workflow
- Command: `python3 dhan_scripts/00_complete_setup_dhan.py SYMBOL.NS --start YYYY-MM-DD --end YYYY-MM-DD`
- Output: Complete analysis results in `analysis_results/{SYMBOL}/intraday_analysis/`

### 01_fetch_intraday_data.py
**Step 1: Fetch Raw Intraday Data**
- Purpose: Fetches 1-minute or 5-minute intraday OHLCV data from Dhan API
- Command: `python3 dhan_scripts/01_fetch_intraday_data.py SYMBOL.NS --start YYYY-MM-DD --end YYYY-MM-DD --interval 1`
- Output: `analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_raw.csv`
- Features: Automatically handles 90-day API limit by chunking

### 02_simple_intraday_analysis.py
**Step 2: Smart Money Pattern Analysis**
- Purpose: Detects institutional patterns using Smart Money features (Synthetic IV, OBV, Sentiment Skew)
- Command: `python3 dhan_scripts/02_simple_intraday_analysis.py SYMBOL.NS --data-file path/to/raw_data.csv`
- Output: Smart Money patterns (Accumulation, Distribution, Sweeps, Icebergs, Capitulation)
- Features: Professional-grade institutional footprint detection

### 03_calculate_intraday_indicators.py
**Step 3: Feature Engineering**
- Purpose: Calculates technical indicators + Smart Money features + multi-timeframe context
- Command: `python3 dhan_scripts/03_calculate_intraday_indicators.py --input-file path/to/raw_data.csv --symbol SYMBOL.NS`
- Output: `{SYMBOL}_intraday_1min_indicators.csv` (with 28+ indicators)
- Features: RSI, MACD, ATR, VWAP, Bollinger Bands, plus Smart Money features

### 04_intraday_ta_accuracy_analysis.py
**Step 4: TA Indicator Accuracy Analysis**
- Purpose: Analyzes which TA indicators are most accurate for next candle prediction
- Command: `python3 dhan_scripts/04_intraday_ta_accuracy_analysis.py SYMBOL.NS --start YYYY-MM-DD --end YYYY-MM-DD --interval 1`
- Output: Accuracy rankings, visualizations, and reports
- Features: Market hours filtering (09:15-15:30 IST), smart caching

### 05_intraday_pattern_discovery.py
**Step 5: Comprehensive Pattern Discovery**
- Purpose: Orchestrates all pattern analyses with parallel processing
- Command: `python3 dhan_scripts/05_intraday_pattern_discovery.py SYMBOL.NS --data-file path/to/raw_data.csv`
- Output: Time patterns, volume patterns, price patterns, comprehensive HTML report
- Features: Parallel execution, Smart Money feature injection, error isolation

### 06_fetch_options_data.py
**Step 6: Options Data (Optional)**
- Purpose: Fetches historical expired options data with OI and IV
- Command: `python3 dhan_scripts/06_fetch_options_data.py NIFTY --strike-type ATM --option-type CE ...`
- Note: Requires v2 API access token with proper permissions

### 07_market_depth_websocket.py
**Step 7: Real-Time Market Depth (Market Hours Only)**
- Purpose: Streams real-time 20-level or 200-level market depth via WebSocket
- Command: `python3 dhan_scripts/07_market_depth_websocket.py --level 20 --instruments NSE_EQ:15083 --duration 60`
- Note: Only works during NSE market hours (9:15 AM - 3:30 PM IST, Mon-Fri)

## Supporting Scripts

These are called automatically by the main scripts:

- **analyze_intraday_time_patterns.py** - Time-based pattern analysis (called by Step 5)
- **analyze_intraday_volume_patterns.py** - Volume pattern analysis (called by Step 5)
- **analyze_intraday_price_patterns.py** - Price pattern analysis (called by Step 5)
- **analyze_indicator_combinations.py** - Indicator combination analysis (called by Step 5)
- **analyze_intraday_ta_accuracy.py** - Core TA accuracy engine (called by Step 4)
- **generate_intraday_pattern_report.py** - HTML report generation (called by Step 5)
- **rank_intraday_indicators.py** - Indicator ranking and visualization (called by Step 4)

## Quick Start

### Recommended: Complete Workflow

```bash
# Run everything in one command
python3 dhan_scripts/00_complete_setup_dhan.py HCLTECH.NS \
    --start 2024-11-01 --end 2024-11-24 --interval 1
```

This will:
1. Fetch intraday data from Dhan API
2. Run Smart Money analysis
3. Calculate all indicators
4. Analyze TA accuracy
5. Discover patterns
6. Generate comprehensive reports

### Individual Steps (Advanced)

If you want to run steps individually:

```bash
# 1. Fetch data
python3 dhan_scripts/01_fetch_intraday_data.py SYMBOL.NS \
    --start 2024-11-01 --end 2024-11-24 --interval 1

# 2. Smart Money analysis
python3 dhan_scripts/02_simple_intraday_analysis.py SYMBOL.NS \
    --data-file analysis_results/SYMBOL/intraday_analysis/data/SYMBOL_intraday_1min_raw.csv

# 3. Calculate indicators
python3 dhan_scripts/03_calculate_intraday_indicators.py \
    --input-file analysis_results/SYMBOL/intraday_analysis/data/SYMBOL_intraday_1min_raw.csv \
    --symbol SYMBOL.NS

# 4. TA accuracy
python3 dhan_scripts/04_intraday_ta_accuracy_analysis.py SYMBOL.NS \
    --start 2024-11-01 --end 2024-11-24 --interval 1

# 5. Pattern discovery
python3 dhan_scripts/05_intraday_pattern_discovery.py SYMBOL.NS \
    --data-file analysis_results/SYMBOL/intraday_analysis/data/SYMBOL_intraday_1min_raw.csv
```

## Key Features

- **Smart Caching**: Reuses cached data to avoid redundant API calls
- **Market Hours Filtering**: Automatically filters to 09:15-15:30 IST
- **Parallel Processing**: Pattern discovery runs analyses in parallel
- **Error Resilience**: Continues execution even if individual steps fail
- **Comprehensive Reporting**: Generates HTML reports with all findings

## Dependencies

All scripts depend on `legacy_scripts/complete_setup.py` for:
- `ScripMaster` class (symbol lookup)
- `DhanDataExtractor` class (data fetching)
- Dhan API configuration (CLIENT_ID, ACCESS_TOKEN, SCRIP_MASTER_PATH)

