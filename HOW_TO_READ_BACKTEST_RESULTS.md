# How to Read Donchian Backtest Results

## Problem: CSV Files Are Hard to Read in Excel

The walk-forward results CSV files contain Python array data (`permuted_returns`) that Excel can't display properly. The arrays look like long strings with `np.float64(...)` values, making the file hard to read.

## Solution: Use the Readable Summary Tool

I've created a tool that extracts the important information and creates a clean, readable summary:

```bash
python3 read_results_summary.py analysis_results/GODREJPROP.NS/donchian_enhanced_walkforward_results.csv
```

This creates: `donchian_enhanced_walkforward_results_readable_summary.csv`

## Understanding the Columns

### Main Columns (Easy to Read)

1. **`train_start`** / **`train_end`**: The date range used to **train/optimize** the strategy
   - Example: `2010-01-05` to `2012-01-04` (2 years of training data)

2. **`test_start`** / **`test_end`**: The date range used to **test** the strategy (out-of-sample)
   - Example: `2012-01-05` to `2012-07-04` (6 months of testing)
   - This is the period where we actually trade and measure performance

3. **`best_lookback`**: The optimal Donchian lookback period found during training
   - Example: `54` means using 54-day high/low for breakout signals
   - This was optimized on the training data

4. **`actual_returns`**: The **log return** achieved by the strategy during the test period
   - Example: `0.1644` = 16.44% return (log scale)
   - Positive = profit, Negative = loss
   - This is the **actual performance** of the strategy

5. **`p_value`**: Statistical significance of the strategy's performance
   - **0.0** = Highly significant (very unlikely to be random)
   - **< 0.05** = Significant (95% confidence)
   - **> 0.05** = Not significant (could be random luck)
   - **1.0** = No trades or completely random

6. **`permuted_returns_mean`**: Average return of 1000 random strategies
   - This is what we compare against to see if our strategy is better than random

7. **`permuted_returns_std`**: Standard deviation of random strategies
   - Shows how much random strategies vary

8. **`cumulative_return`**: Running total of all returns
   - Shows how the strategy performed over time
   - Final value = total return across all periods

9. **`is_significant`**: True/False - whether p-value < 0.05
   - Quick way to see which periods were statistically significant

## What the Results Mean

### For GODREJPROP.NS Enhanced Strategy:

- **Total Cumulative Return**: 8.39 (839% total return)
- **Average Return per Period**: 0.31 (31% per 6-month period)
- **Significant Periods**: 21 out of 27 (78% were statistically significant)
- **Best Period**: Dec 2021 - Jun 2022 (97.5% return, p=0.0 = highly significant)
- **Worst Periods**: Several periods with 0% return (no trades due to regime filtering)

## Interpreting the Data

### Good Signs ✅

1. **Low P-Values** (especially 0.0): Strategy is statistically significant
2. **Consistent Positive Returns**: Strategy works across multiple periods
3. **High Cumulative Return**: Overall strategy is profitable
4. **Many Significant Periods**: Strategy isn't just lucky

### Warning Signs ⚠️

1. **High P-Values** (> 0.05): Results might be random
2. **Many Zero Returns**: Strategy might be too conservative (missing trades)
3. **High Volatility** (large std dev): Unpredictable performance
4. **Negative Returns**: Strategy losing money in some periods

## Comparing Standard vs Enhanced

To see if the enhancements helped:

```bash
# Standard Donchian
python3 read_results_summary.py analysis_results/GODREJPROP.NS/donchian_walkforward_results.csv

# Enhanced Donchian (with regime filtering + pattern exits)
python3 read_results_summary.py analysis_results/GODREJPROP.NS/donchian_enhanced_walkforward_results.csv
```

Compare:
- **Total Cumulative Return**: Higher is better
- **Average P-Value**: Lower is better (more significant)
- **Significant Periods**: More is better
- **Average Return per Period**: Higher is better

## Quick Reference

| Column | What It Means | Good Value |
|--------|---------------|------------|
| `actual_returns` | Strategy return | Positive, high |
| `p_value` | Statistical significance | < 0.05 (lower is better) |
| `best_lookback` | Optimal parameter | Varies (12-170) |
| `cumulative_return` | Total return so far | Increasing over time |
| `is_significant` | Is it significant? | True |

## Example: Reading a Row

```
train_start: 2021-06-24
train_end: 2021-12-22
test_start: 2021-12-23
test_end: 2022-06-22
best_lookback: 22
actual_returns: 0.9753
p_value: 0.0
```

**Translation:**
- Trained on data from June 2021 to December 2021
- Tested from December 2021 to June 2022
- Used 22-day Donchian lookback (optimized during training)
- Achieved 97.5% return during test period
- P-value of 0.0 = **highly statistically significant** (not random)

## Tips for Excel Users

1. **Use the readable summary CSV** instead of the raw results
2. **Filter by `is_significant`** to see only statistically significant periods
3. **Sort by `actual_returns`** to find best/worst periods
4. **Create a chart** of `cumulative_return` to visualize performance over time
5. **Ignore the `permuted_returns` columns** - they're just for statistical analysis

## Need More Help?

- See `ENHANCED_DONCHIAN_GUIDE.md` for strategy details
- See `DONCHIAN_STRATEGY_EXPLAINED.md` for how the strategy works
- Check the summary CSV files for pre-calculated statistics

