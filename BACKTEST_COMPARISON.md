# Backtest Tools Comparison

## Overview

You have **three different backtesting tools** in this repository, each serving different purposes:

## 1. `backtest_example.py` - Simple Learning Example

**Purpose**: Educational example for learning basic backtesting concepts

**Strategy**: RSI + MACD crossover signals
- **BUY**: RSI < 30 (oversold) OR MACD crosses above signal
- **SELL**: RSI > 70 (overbought) OR MACD crosses below signal

**Features**:
- ✅ Simple, easy to understand
- ✅ Good for learning
- ✅ Quick testing
- ❌ No statistical significance testing
- ❌ No walk-forward analysis
- ❌ No regime filtering

**Usage**:
```bash
# Default: HDFCBANK.NS
python3 backtest_example.py

# Custom stock
python3 backtest_example.py GODREJPROP.NS
```

**Output**: 
- Console summary (returns, Sharpe ratio, drawdown)
- `backtest_results.csv` (detailed daily results)

**Best For**: Learning, quick strategy ideas, simple testing

---

## 2. `donchian_mcpt_backtest.py` - Standard Donchian with MCPT

**Purpose**: Robust backtesting with statistical significance testing

**Strategy**: Donchian Channel Breakout
- **BUY**: Price breaks above N-day high
- **SELL**: Price breaks below N-day low
- **Optimization**: Finds best lookback period (12-170 days) based on profit factor

**Features**:
- ✅ Walk-forward analysis (avoids overfitting)
- ✅ Monte Carlo Permutation Test (MCPT) for statistical significance
- ✅ P-value calculation (is strategy better than random?)
- ✅ Visualizations (equity curve, p-value distribution)
- ✅ HTML report
- ❌ No regime filtering
- ❌ No pattern-matching exits

**Usage**:
```bash
python3 donchian_mcpt_backtest.py output/GODREJPROP.NS_analysis.csv
```

**Output**:
- `donchian_walkforward_results.csv` (detailed results)
- `donchian_walkforward_results_readable_summary.csv` (readable version)
- `donchian_mcpt_summary.csv` (quick summary)
- `donchian_mcpt_report.html` (comprehensive report)
- `donchian_equity_curve.png` (visualization)
- `donchian_actual_vs_permuted.png` (statistical significance)

**Best For**: Production backtesting, statistical validation, robust testing

---

## 3. `donchian_enhanced_backtest.py` - Enhanced Donchian with Filters

**Purpose**: Advanced Donchian strategy with market regime awareness

**Strategy**: Donchian Channel Breakout + Enhancements
- **Base**: Same as standard Donchian
- **+ Regime Filtering**: Only trades in trending markets (bullish/bearish)
- **+ Pattern Exits**: Early exit based on similar historical days

**Features**:
- ✅ All features from standard Donchian MCPT
- ✅ Behavioral regime filtering (avoids choppy markets)
- ✅ Pattern-matching exit logic (uses historical analogues)
- ✅ More conservative (fewer trades, potentially better risk-adjusted returns)
- ❌ May filter out profitable trades (too conservative)

**Usage**:
```bash
# Prerequisites: Run behavioral pattern analysis first
python3 behavioral_patterns.py output/GODREJPROP.NS_analysis.csv

# Then run enhanced backtest
python3 donchian_enhanced_backtest.py output/GODREJPROP.NS_analysis.csv
```

**Output**:
- `donchian_enhanced_walkforward_results.csv` (detailed results)
- `donchian_enhanced_walkforward_results_readable_summary.csv` (readable version)
- `donchian_enhanced_mcpt_summary.csv` (quick summary)

**Best For**: Risk-aware trading, avoiding choppy markets, advanced strategies

---

## Quick Comparison Table

| Feature | `backtest_example.py` | `donchian_mcpt_backtest.py` | `donchian_enhanced_backtest.py` |
|---------|----------------------|----------------------------|--------------------------------|
| **Complexity** | Simple | Medium | Advanced |
| **Strategy** | RSI/MACD | Donchian Breakout | Donchian + Filters |
| **Walk-Forward** | ❌ | ✅ | ✅ |
| **Statistical Testing** | ❌ | ✅ (MCPT) | ✅ (MCPT) |
| **Regime Filtering** | ❌ | ❌ | ✅ |
| **Pattern Exits** | ❌ | ❌ | ✅ |
| **Visualizations** | ❌ | ✅ | ❌ |
| **HTML Report** | ❌ | ✅ | ❌ |
| **Best For** | Learning | Production | Risk-Aware |

---

## Which One Should You Use?

### For Learning:
→ Use `backtest_example.py`
- Simple to understand
- Easy to modify
- Good for experimenting

### For Serious Backtesting:
→ Use `donchian_mcpt_backtest.py`
- Statistical validation
- Walk-forward testing
- Comprehensive reports

### For Advanced Strategies:
→ Use `donchian_enhanced_backtest.py`
- Market regime awareness
- Pattern-based exits
- More sophisticated risk management

---

## Running All Three

You can compare all three approaches:

```bash
# 1. Simple example
python3 backtest_example.py GODREJPROP.NS

# 2. Standard Donchian
python3 donchian_mcpt_backtest.py output/GODREJPROP.NS_analysis.csv

# 3. Enhanced Donchian
python3 behavioral_patterns.py output/GODREJPROP.NS_analysis.csv  # First!
python3 donchian_enhanced_backtest.py output/GODREJPROP.NS_analysis.csv

# 4. Compare results
python3 compare_backtests.py GODREJPROP.NS
```

---

## Notes

- **`backtest_example.py`** is still functional and useful for learning
- It's simpler than the Donchian backtests but serves a different purpose
- The Donchian backtests are more robust for production use
- All three tools can coexist - use the right tool for the right job!

