# Maximum Drawdown (MDD) Reduction Guide

## Current Situation

You have a Donchian strategy with:
- **Total Return**: 142.89%
- **Maximum Drawdown**: 18.82% ⚠️

**Goal**: Reduce MDD while maintaining returns.

## Good News: Both Solutions Are Already Implemented! ✅

The Enhanced Donchian strategy (`donchian_enhanced_backtest.py`) already includes:

1. ✅ **Regime Filtering** (Option 1) - Filters out dangerous market regimes
2. ✅ **Pattern-Based Early Exits** (Option 2) - Exits early based on similar historical patterns

## Step 1: Identify Dangerous Regimes

First, analyze which market regimes are associated with your worst drawdown periods:

```bash
python3 analyze_drawdowns.py \
  analysis_results/GODREJPROP.NS/donchian_walkforward_results.csv \
  analysis_results/GODREJPROP.NS/data_with_regimes.csv
```

This will:
- Identify worst performing periods (bottom 25% by default)
- Map them to market regimes
- Identify which regimes are "dangerous" (appear in >50% of worst periods)
- Simulate MDD reduction by filtering those regimes

**Example Output:**
```
⚠️  Dangerous Regimes (appear in >50% of worst periods):
   Regime 3: AVOID trading in this regime
   Regime 4: AVOID trading in this regime

📊 MDD Comparison:
   Original Strategy:
      Maximum Drawdown: -18.82%
   Filtered Strategy (excluding regimes [3, 4]):
      Maximum Drawdown: -12.45%
   MDD Reduction: 6.37%
```

## Step 2: Choose Your Approach

### Option 1: Regime Filtering (Recommended First)

**Pros:**
- Simple to implement (already done!)
- Prevents entering trades in dangerous conditions
- Reduces whipsaw losses

**Cons:**
- May miss some profitable trades
- Requires regime data to be available

**How to Use:**

The Enhanced Donchian already does this! Just run:

```bash
# Make sure regime data exists
python3 behavioral_patterns.py output/GODREJPROP.NS_analysis.csv

# Run enhanced backtest (regime filtering is automatic)
python3 donchian_enhanced_backtest.py output/GODREJPROP.NS_analysis.csv
```

The enhanced strategy will:
1. Identify trending regimes (bullish/bearish) vs choppy regimes
2. Only allow trades in trending regimes
3. Block trades in choppy/consolidation regimes

**Customization:**

To filter specific dangerous regimes, edit `donchian_enhanced.py`:

```python
# In identify_trending_regimes(), adjust thresholds:
bullish_regimes = regime_returns[regime_returns > 0.001].index.tolist()  # > 0.1% daily
bearish_regimes = regime_returns[regime_returns < -0.001].index.tolist()  # < -0.1% daily
choppy_regimes = regime_returns[abs(regime_returns) <= 0.001].index.tolist()  # Low absolute return

# Or manually specify dangerous regimes:
dangerous_regimes = [3, 4]  # From your analysis
choppy_regimes = dangerous_regimes  # Add to choppy list
```

### Option 2: Pattern-Based Early Exit (Advanced)

**Pros:**
- More dynamic (exits based on current conditions)
- Can protect profits during adverse patterns
- Uses historical analogues

**Cons:**
- More complex
- Requires full indicator data
- May exit too early in some cases

**How to Use:**

The Enhanced Donchian already includes this! It's enabled by default when you run:

```bash
python3 donchian_enhanced_backtest.py output/GODREJPROP.NS_analysis.csv
```

**How It Works:**

1. When you enter a trade, the system records the current indicator "fingerprint"
2. Each day the trade is open, it finds the top 5 most similar historical days
3. If those similar days had negative average 5-day returns (< -1%), it exits early
4. This protects capital before losses accumulate

**Customization:**

Edit `donchian_enhanced.py`:

```python
# In get_pattern_exit_signal(), adjust threshold:
threshold = -1.0  # Exit if similar days averaged < -1% return
# Make it more aggressive:
threshold = -0.5  # Exit if similar days averaged < -0.5% return
# Or more conservative:
threshold = -2.0  # Exit if similar days averaged < -2% return
```

## Step 3: Compare Results

After running the enhanced backtest, compare with the standard:

```bash
# Standard Donchian
python3 donchian_mcpt_backtest.py output/GODREJPROP.NS_analysis.csv

# Enhanced Donchian (with both features)
python3 donchian_enhanced_backtest.py output/GODREJPROP.NS_analysis.csv

# Compare
python3 compare_backtests.py GODREJPROP.NS
```

**What to Look For:**

✅ **Good Result:**
- MDD reduced (e.g., from -18.82% to -12%)
- Returns maintained (e.g., still > 100%)
- Sharpe Ratio improved

⚠️ **Needs Adjustment:**
- MDD reduced but returns dropped too much
- Try adjusting regime thresholds or pattern exit threshold
- Or use only one feature (regime OR pattern, not both)

## Step 4: Fine-Tuning

### If MDD Still Too High:

1. **More Aggressive Regime Filtering:**
   - Lower the threshold for "choppy" regimes
   - Filter more regimes

2. **More Aggressive Pattern Exits:**
   - Lower the threshold (e.g., -0.5% instead of -1%)
   - Check more similar days (e.g., top 10 instead of top 5)

3. **Combine Both:**
   - Use regime filtering to avoid bad entries
   - Use pattern exits to protect during trades

### If Returns Drop Too Much:

1. **Less Aggressive Filtering:**
   - Raise the threshold for "choppy" regimes
   - Filter fewer regimes

2. **Less Aggressive Pattern Exits:**
   - Raise the threshold (e.g., -2% instead of -1%)
   - Check fewer similar days (e.g., top 3 instead of top 5)

3. **Use Only One Feature:**
   - Try regime filtering alone
   - Or pattern exits alone
   - See which works better

## Recommended Workflow

1. **Run Drawdown Analysis:**
   ```bash
   python3 analyze_drawdowns.py \
     analysis_results/GODREJPROP.NS/donchian_walkforward_results.csv \
     analysis_results/GODREJPROP.NS/data_with_regimes.csv
   ```

2. **Run Enhanced Backtest:**
   ```bash
   python3 donchian_enhanced_backtest.py output/GODREJPROP.NS_analysis.csv
   ```

3. **Compare Results:**
   ```bash
   python3 compare_backtests.py GODREJPROP.NS
   ```

4. **Fine-Tune if Needed:**
   - Adjust thresholds in `donchian_enhanced.py`
   - Re-run and compare

## Expected Results

With proper tuning, you should see:

- **MDD Reduction**: 30-50% reduction (e.g., from -18.82% to -10% to -12%)
- **Return Preservation**: 80-95% of original returns maintained
- **Sharpe Ratio**: Improved (better risk-adjusted returns)

## Summary

✅ **Both solutions are already implemented** in the Enhanced Donchian strategy
✅ **Start with regime filtering** (simpler, more predictable)
✅ **Add pattern exits** if MDD still too high
✅ **Fine-tune thresholds** based on your risk tolerance

The Enhanced Donchian strategy is designed exactly for this use case - reducing MDD while maintaining returns!

