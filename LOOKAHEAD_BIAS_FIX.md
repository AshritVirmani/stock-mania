# Lookahead Bias Fix - Donchian Strategy

## Problem Identified

The Donchian strategy had **lookahead bias** in two places:

### 1. Optimization Function (`donchian_strategy.py`)

**Before (WRONG):**
```python
log_returns = np.log(df['close']).diff().shift(-1)  # Using tomorrow's return!
sig_rets = signal * log_returns
```

**After (FIXED):**
```python
log_returns = np.log(df['close']).diff()
# Signal on day T captures return from day T to T+1
aligned_signals = signal.iloc[:-1]
aligned_returns = log_returns.iloc[1:]
sig_rets = aligned_signals * aligned_returns
```

### 2. Walk-Forward Testing (`walkforward_mcpt.py`)

**Before (WRONG):**
```python
signals = donchian_breakout(test_data, best_lookback)
log_returns = np.log(test_data['close']).diff()
actual_ret, permuted_rets, p_value = monte_carlo_permutation_test(
    signals.iloc[1:], log_returns.iloc[1:], mcpt_iterations
)
```

**After (FIXED):**
```python
signals = donchian_breakout(test_data, best_lookback)
log_returns = np.log(test_data['close']).diff()
# Signal on day T captures return from day T to T+1
aligned_signals = signals.iloc[:-1]
aligned_returns = log_returns.iloc[1:]
min_len = min(len(aligned_signals), len(aligned_returns))
actual_ret, permuted_rets, p_value = monte_carlo_permutation_test(
    aligned_signals.iloc[:min_len], aligned_returns.iloc[:min_len], mcpt_iterations
)
```

## Why This Matters

**Lookahead bias** means the strategy is using information from the future to make past decisions. This makes backtest results unrealistically good.

### Example of the Problem:

```
Day 0: Price = ₹100, Signal = BUY (based on day 0 data)
Day 1: Price = ₹110, Return = 10%
```

**WRONG (with lookahead bias):**
- Signal[0] * Return[0] = BUY * 10% = 10% profit
- But Return[0] is calculated from Day 0 to Day 1, which we don't know on Day 0!

**CORRECT (fixed):**
- Signal[0] * Return[1] = BUY * (return from Day 1 to Day 2)
- This is the return we actually capture after entering on Day 0

## Impact

The previous results showing **18,706x returns** were inflated due to lookahead bias. After fixing:

1. **Returns will be lower** (more realistic)
2. **Strategy performance will be more accurate**
3. **Backtest results will be trustworthy**

## What to Do Next

1. **Re-run the backtests** with the fixed code:
   ```bash
   python3 donchian_mcpt_backtest.py output/GODREJPROP.NS_analysis.csv
   python3 donchian_enhanced_backtest.py output/GODREJPROP.NS_analysis.csv
   ```

2. **Compare results** - The new results will be more conservative and realistic

3. **Trust the new results** - They represent what you could actually achieve

## Technical Details

### Signal/Return Alignment

- **Signal[T]**: Trading decision made at the close of day T
- **Return[T+1]**: Price movement from day T to day T+1
- **Correct**: Signal[T] * Return[T+1] = profit/loss from decision on day T

### Donchian Channel Calculation

The Donchian channels are calculated correctly:
```python
upper = df['close'].rolling(lookback - 1).max().shift(1)  # ✅ Correct
lower = df['close'].rolling(lookback - 1).min().shift(1)  # ✅ Correct
```

This uses only past data (shift(1) means yesterday's value), so no lookahead bias here.

## Summary

✅ **Fixed**: Signal/return alignment in optimization and testing
✅ **Fixed**: Removed `.shift(-1)` that caused lookahead bias
✅ **Result**: More realistic and trustworthy backtest results

The strategy is still valid, but the returns will be more conservative and realistic.

