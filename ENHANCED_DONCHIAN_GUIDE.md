# Enhanced Donchian Strategy Guide

## Overview

The Enhanced Donchian Strategy improves upon the basic Donchian breakout strategy by incorporating two key enhancements:

1. **Behavioral Regime Filtering** - Only trades in trending markets (bullish/bearish), avoiding choppy/sideways markets
2. **Pattern-Matching Exit Logic** - Uses historical analogues to exit early when similar days had negative returns

## How It Works

### 1. Regime Filtering

**Problem**: The basic Donchian strategy struggles in sideways/choppy markets where momentum reverses quickly, leading to whipsaw losses.

**Solution**: Filter trades based on market regime:
- **Bullish Regimes** (Cluster 1): Only allow LONG signals
- **Bearish Regimes** (Cluster 4): Only allow SHORT signals (if enabled)
- **Choppy/Consolidation Regimes** (Cluster 0, 3): Block all signals

**Implementation**:
- Loads `data_with_regimes.csv` from behavioral pattern analysis
- Identifies which regimes have positive mean returns (bullish) vs negative (bearish) vs low absolute returns (choppy)
- Filters Donchian signals to only allow trades in appropriate regimes

**Result**: Avoids whipsaw losses during consolidation periods, potentially improving Sharpe Ratio.

### 2. Pattern-Matching Exit Logic

**Problem**: The basic Donchian exit waits for the opposite signal, which can sometimes give back a lot of profit.

**Solution**: Use pattern matching to analyze similar historical days:
- For each day we hold a position, find the top 5 most similar historical days
- Calculate the average 5-day return of those similar days
- If the average return is negative (below threshold, default -1%), exit early

**Implementation**:
- Uses the `PatternMatcher` from `find_similar_days.py`
- Normalizes all 86 indicators and finds days with similar indicator profiles
- Analyzes subsequent price performance of similar days
- Exits position early if historical analogues suggest poor performance ahead

**Result**: Proactive risk management and optimized exit timing based on historical patterns.

## Usage

### Running the Enhanced Backtest

```bash
# Run enhanced Donchian backtest for a stock
python3 donchian_enhanced_backtest.py output/WIPRO.NS_analysis.csv
```

### Prerequisites

The enhanced strategy requires:
1. **Analysis file**: `output/YOUR_STOCK.NS_analysis.csv` (with all 86 indicators)
2. **Regime data**: `analysis_results/YOUR_STOCK.NS/data_with_regimes.csv` (from behavioral pattern analysis)

**To generate prerequisites**:
```bash
# Step 1: Generate analysis file
python3 analyze_indian_stocks.py WIPRO.NS

# Step 2: Run behavioral pattern analysis (generates regime data)
python3 behavioral_patterns.py output/WIPRO.NS_analysis.csv

# Step 3: Run enhanced Donchian backtest
python3 donchian_enhanced_backtest.py output/WIPRO.NS_analysis.csv
```

### Running via Unified Tool

The enhanced Donchian backtest is automatically included when running full analysis:

```bash
python3 analyze_stock.py WIPRO.NS --all
```

This will run:
- Standard Donchian MCPT backtest
- **Enhanced Donchian MCPT backtest** (with regime filtering and pattern exits)

## Output Files

Results are saved in `analysis_results/YOUR_STOCK.NS/`:

1. **`donchian_enhanced_walkforward_results.csv`** - Detailed walk-forward results
2. **`donchian_enhanced_mcpt_summary.csv`** - Summary statistics including:
   - Total and annualized log returns
   - Average p-value (statistical significance)
   - Number of walk-forward periods
   - Status of regime filtering and pattern exit features

## Comparing Standard vs Enhanced

### Standard Donchian Strategy
- Trades on all Donchian breakout signals
- Exits only when opposite signal occurs
- No market regime awareness
- No pattern-based exit logic

### Enhanced Donchian Strategy
- **Regime Filtering**: Only trades in trending markets
- **Pattern Exits**: Early exit based on similar historical days
- **Better Risk Management**: Avoids choppy markets and uses historical analogues

### Expected Improvements

1. **Higher Sharpe Ratio**: Avoiding choppy markets reduces whipsaw losses
2. **Better Exit Timing**: Pattern matching helps exit before giving back profits
3. **Reduced Drawdowns**: Regime filtering prevents trades in unfavorable conditions

## Configuration

### Regime Filtering Thresholds

In `donchian_enhanced.py`, the `identify_trending_regimes` function uses:
- **Bullish**: Mean daily return > 0.1% (0.001)
- **Bearish**: Mean daily return < -0.1% (-0.001)
- **Choppy**: Absolute mean return ≤ 0.1% (0.001)

You can adjust these thresholds in the function if needed.

### Pattern Exit Threshold

In `get_pattern_exit_signal`, the default threshold is **-1.0%**:
- If average 5-day return of similar days < -1%, exit early
- You can adjust this threshold based on your risk tolerance

### Enable/Disable Features

The enhanced backtest automatically detects available data:
- If `data_with_regimes.csv` exists → Regime filtering enabled
- If analysis file exists → Pattern matching enabled
- If either is missing, that feature is disabled (with a warning)

## Example Workflow

```bash
# 1. Generate initial analysis
python3 analyze_indian_stocks.py WIPRO.NS

# 2. Run behavioral pattern analysis (for regime data)
python3 behavioral_patterns.py output/WIPRO.NS_analysis.csv

# 3. Run enhanced Donchian backtest
python3 donchian_enhanced_backtest.py output/WIPRO.NS_analysis.csv

# 4. Compare results
# Check: analysis_results/WIPRO.NS/donchian_enhanced_mcpt_summary.csv
# Compare with: analysis_results/WIPRO.NS/donchian_mcpt_summary.csv
```

## Understanding the Results

### Summary Metrics

- **Total Log Return**: Cumulative return across all walk-forward periods
- **Annualized Log Return**: Annualized version of total return
- **Average P-Value**: Statistical significance (lower = more significant)
- **Regime Filtering**: Shows if regime filtering was enabled
- **Pattern Exit**: Shows if pattern matching exits were enabled

### Interpreting P-Values

- **p < 0.05**: Strategy is statistically significant (95% confidence)
- **p < 0.01**: Very significant (99% confidence)
- **p > 0.05**: Not statistically significant (could be random)

### Comparing Strategies

Compare the enhanced strategy with the standard Donchian:
1. Check if Sharpe Ratio improved (higher is better)
2. Check if p-value decreased (more significant)
3. Check if drawdowns reduced (lower is better)
4. Check if win rate improved (higher is better)

## Troubleshooting

### "Regime data not found"
- Run `behavioral_patterns.py` first to generate `data_with_regimes.csv`

### "Pattern matching setup failed"
- Ensure the analysis file has all 86 indicators
- Check that `find_similar_days.py` dependencies are installed

### "No results produced"
- Check that you have enough historical data (at least 2-3 years)
- Verify the analysis file is correctly formatted

## Technical Details

### Regime Identification

Regimes are identified using K-Means clustering on normalized indicator data:
- 5 clusters by default (configurable)
- Each cluster represents a distinct market regime
- Regimes are characterized by mean returns and volatility

### Pattern Matching

Pattern matching uses:
- **Euclidean distance** on normalized indicators
- **MinMaxScaler** for normalization
- **Top 5 similar days** for exit decisions
- **5-day forward returns** for outcome analysis

### Walk-Forward Framework

The enhanced strategy uses the same walk-forward framework as the standard Donchian:
- **Training Period**: 2 years (730 days)
- **Testing Period**: 6 months (183 days)
- **MCPT Iterations**: 1000 permutations per test period

## References

- **Donchian Strategy**: `donchian_strategy.py`
- **Behavioral Patterns**: `behavioral_patterns.py`
- **Pattern Matching**: `find_similar_days.py`
- **Walk-Forward MCPT**: `walkforward_mcpt.py`

