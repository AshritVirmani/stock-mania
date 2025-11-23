# Dhan Data Workflow - Sequential Script Execution Guide

This document lists all Python scripts that work with raw Dhan API data, numbered in the order they should be executed.

## 📋 Prerequisites

- Dhan API credentials (Client ID and Access Token)
- Scrip Master CSV file (`api-scrip-master-detailed.csv`)
- Required Python libraries: `dhanhq`, `pandas`, `numpy`, `websocket-client`

---

## 🔢 Sequential Execution Order

### **STEP 1: Fetch Raw Daily Data**
**Script**: `legacy_scripts/complete_setup.py`  
**Purpose**: Fetches historical daily OHLCV data from Dhan API  
**Usage**:
```bash
python3 legacy_scripts/complete_setup.py SYMBOL.NS
# Example: python3 legacy_scripts/complete_setup.py RELIANCE.NS
```
**Output**: `analysis_results/{SYMBOL}/data/{SYMBOL}_analysis.csv`  
**Note**: This script has a toggle to choose between Dhan API and Yahoo Finance

---

### **STEP 2: Fetch Raw Intraday Data (1-minute or 5-minute)**
**Script**: `legacy_scripts/fetch_intraday_data.py`  
**Purpose**: Fetches 1-minute or 5-minute intraday OHLCV data from Dhan API  
**Usage**:
```bash
python3 legacy_scripts/fetch_intraday_data.py SYMBOL.NS --from-date 2020-01-01 --to-date 2024-12-31 --interval 1
# Example: python3 legacy_scripts/fetch_intraday_data.py RELIANCE.NS --from-date 2020-01-01 --to-date 2024-12-31 --interval 1
```
**Output**: `analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_raw.csv`  
**Note**: Automatically handles 90-day API limit by chunking requests

---

### **STEP 3: Simple Price-Volume Pattern Analysis (Raw Data)**
**Script**: `legacy_scripts/simple_intraday_analysis.py`  
**Purpose**: Analyzes raw OHLCV data to detect behavioral patterns using Z-scores  
**Usage**:
```bash
python3 legacy_scripts/simple_intraday_analysis.py SYMBOL.NS --data-file analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_raw.csv
# Example: python3 legacy_scripts/simple_intraday_analysis.py RELIANCE.NS --data-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_raw.csv
```
**Output**: 
- `analysis_results/{SYMBOL}/intraday_analysis/pattern_analysis/simple/processed_data.csv`
- Pattern CSVs: `panic_sells.csv`, `fomo_buys.csv`, `icebergs.csv`, `stop_hunts.csv`, etc.
**Detects**: Panic Sells, FOMO Buys, Iceberg/Absorption, Stop Hunts, Volume Divergences, Exhaustion Patterns, etc.

---

### **STEP 4: Calculate Technical Indicators (Optional)**
**Script**: `legacy_scripts/calculate_intraday_indicators.py`  
**Purpose**: Calculates 83+ TA indicators from raw intraday data  
**Usage**:
```bash
python3 legacy_scripts/calculate_intraday_indicators.py --data-file analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_raw.csv --output-file analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_indicators.csv
```
**Output**: `analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_indicators.csv`  
**Note**: Only needed if you want to analyze TA indicator accuracy

---

### **STEP 5: Analyze TA Indicator Accuracy (Requires Step 4)**
**Script**: `legacy_scripts/intraday_ta_accuracy_analysis.py`  
**Purpose**: Analyzes which TA indicators are most accurate for predicting next candle direction  
**Usage**:
```bash
python3 legacy_scripts/intraday_ta_accuracy_analysis.py SYMBOL.NS --from-date 2020-01-01 --to-date 2024-12-31 --interval 1
# OR if indicators already calculated:
python3 legacy_scripts/intraday_ta_accuracy_analysis.py SYMBOL.NS --data-file analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_indicators.csv
```
**Output**: 
- `analysis_results/{SYMBOL}/intraday_analysis/indicator_accuracy/indicator_rankings.csv`
- `analysis_results/{SYMBOL}/intraday_analysis/indicator_accuracy/indicator_rankings.json`
- Visualization charts

---

### **STEP 6: Comprehensive Pattern Discovery (Raw Data)**
**Script**: `legacy_scripts/intraday_pattern_discovery.py`  
**Purpose**: Orchestrates all pattern analyses (time, volume, price patterns) on raw data  
**Usage**:
```bash
python3 legacy_scripts/intraday_pattern_discovery.py SYMBOL.NS --data-file analysis_results/{SYMBOL}/intraday_analysis/data/{SYMBOL}_intraday_1min_raw.csv
# Example: python3 legacy_scripts/intraday_pattern_discovery.py RELIANCE.NS --data-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_raw.csv
```
**Output**: 
- Time patterns analysis
- Volume patterns analysis
- Price patterns analysis
- Comprehensive HTML report: `comprehensive_pattern_report.html`
**Note**: This script automatically runs `simple_intraday_analysis.py` first, then other pattern analyses

---

### **STEP 7: Fetch Options Data (Optional - Requires v2 API Access)**
**Script**: `legacy_scripts/fetch_options_data.py`  
**Purpose**: Fetches historical expired options data with OI and IV  
**Usage**:
```bash
python3 legacy_scripts/fetch_options_data.py NIFTY --strike-type ATM --option-type CE --from-date 2024-01-01 --to-date 2024-01-31 --instrument OPTIDX --expiry-flag MONTH --expiry-code 1 --interval 1
```
**Output**: `{SYMBOL}_{OPTION_TYPE}_{STRIKE_TYPE}_options_{FROM_DATE}_to_{TO_DATE}.csv`  
**Note**: Requires v2 API access token. Currently returns 401 (authentication issue)

---

### **STEP 8: Real-Time Market Depth (During Market Hours)**
**Script**: `legacy_scripts/market_depth_websocket.py`  
**Purpose**: Streams real-time 20-level or 200-level market depth data via WebSocket  
**Usage**:
```bash
# 20-level depth (up to 50 instruments)
python3 legacy_scripts/market_depth_websocket.py --level 20 --instruments NSE_EQ:2 NSE_EQ:2885 --duration 60 --output-dir market_depth_data

# 200-level depth (1 instrument)
python3 legacy_scripts/market_depth_websocket.py --level 200 --instruments NSE_EQ:2 --duration 60 --output-dir market_depth_data
```
**Output**: CSV files with bid/ask depth data  
**Note**: Only works during market hours (9:15 AM - 3:30 PM IST, Mon-Fri)

---

## 📊 Complete Workflow Example

### For Intraday Analysis (Raw Data Focus):

```bash
# 1. Fetch raw intraday data
python3 legacy_scripts/fetch_intraday_data.py RELIANCE.NS \
    --from-date 2020-01-01 \
    --to-date 2024-12-31 \
    --interval 1

# 2. Simple pattern analysis (works on raw data)
python3 legacy_scripts/simple_intraday_analysis.py RELIANCE.NS \
    --data-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_raw.csv

# 3. Comprehensive pattern discovery (includes simple analysis)
python3 legacy_scripts/intraday_pattern_discovery.py RELIANCE.NS \
    --data-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_raw.csv
```

### For TA Indicator Analysis (Requires Indicators):

```bash
# 1. Fetch raw intraday data
python3 legacy_scripts/fetch_intraday_data.py RELIANCE.NS \
    --from-date 2020-01-01 \
    --to-date 2024-12-31 \
    --interval 1

# 2. Calculate indicators
python3 legacy_scripts/calculate_intraday_indicators.py \
    --data-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_raw.csv \
    --output-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_indicators.csv

# 3. Analyze indicator accuracy
python3 legacy_scripts/intraday_ta_accuracy_analysis.py RELIANCE.NS \
    --data-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_indicators.csv
```

---

## 🔄 Script Dependencies

```
STEP 1 (complete_setup.py)
    └─> Fetches daily data (optional, can use Yahoo Finance)

STEP 2 (fetch_intraday_data.py)
    └─> Fetches raw intraday OHLCV data
        ├─> STEP 3 (simple_intraday_analysis.py) - Works on raw data
        ├─> STEP 4 (calculate_intraday_indicators.py) - Optional, adds indicators
        │   └─> STEP 5 (intraday_ta_accuracy_analysis.py) - Requires indicators
        └─> STEP 6 (intraday_pattern_discovery.py) - Works on raw data, includes STEP 3

STEP 7 (fetch_options_data.py) - Independent, requires v2 API
STEP 8 (market_depth_websocket.py) - Independent, real-time during market hours
```

---

## 📁 Output Directory Structure

```
analysis_results/
└── {SYMBOL}/
    ├── data/
    │   └── {SYMBOL}_analysis.csv (daily data)
    └── intraday_analysis/
        ├── data/
        │   ├── {SYMBOL}_intraday_1min_raw.csv
        │   └── {SYMBOL}_intraday_1min_indicators.csv (if calculated)
        ├── pattern_analysis/
        │   ├── simple/
        │   │   ├── processed_data.csv
        │   │   ├── panic_sells.csv
        │   │   ├── fomo_buys.csv
        │   │   └── ... (other patterns)
        │   ├── time_patterns/
        │   ├── volume_patterns/
        │   ├── price_patterns/
        │   └── comprehensive_pattern_report.html
        └── indicator_accuracy/ (if Step 5 executed)
```

---

## ⚠️ Important Notes

1. **Raw Data Focus**: Steps 3 and 6 work directly on raw OHLCV data without requiring indicators
2. **Market Hours**: Step 8 (market depth) only works during NSE market hours (9:15 AM - 3:30 PM IST)
3. **API Limits**: Step 2 automatically handles 90-day API limit by chunking requests
4. **Options Data**: Step 7 requires v2 API access (currently has authentication issues)
5. **Daily Data**: Step 1 is optional if you only need intraday analysis

---

## 🚀 Quick Start (Minimal Workflow)

For quick analysis on raw data only:

```bash
# Fetch and analyze in one go
python3 legacy_scripts/fetch_intraday_data.py RELIANCE.NS --from-date 2020-01-01 --to-date 2024-12-31 --interval 1
python3 legacy_scripts/intraday_pattern_discovery.py RELIANCE.NS --data-file analysis_results/RELIANCE.NS/intraday_analysis/data/RELIANCE.NS_intraday_1min_raw.csv
```

This will:
1. Fetch raw intraday data
2. Run simple pattern analysis
3. Run comprehensive pattern discovery
4. Generate HTML report

