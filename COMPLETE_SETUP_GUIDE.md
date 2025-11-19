# Complete Setup Guide - New Ticker

## One-Command Complete Analysis

Run the complete analysis workflow for any new ticker with a single command:

```bash
python3 complete_setup.py TICKER.NS
```

**Example:**
```bash
python3 complete_setup.py TCS.NS
python3 complete_setup.py RELIANCE.NS
python3 complete_setup.py INFY.NS
```

## What It Does (Automated)

The `complete_setup.py` script runs the entire analysis pipeline:

### Step 1: Data Fetching & Indicators
- Fetches all historical data from listing date
- Calculates all 86 technical indicators
- Saves to `output/TICKER.NS_analysis.csv`

### Step 2: Correlation Analysis
- Analyzes correlations between all 86 indicators
- Generates correlation heatmaps (full and filtered)
- Saves correlation matrix

### Step 3: Behavioral Pattern Analysis
- Identifies market regimes using K-Means clustering
- Analyzes regime characteristics
- Saves regime data for filtering

### Step 4: Red Light Regime Identification
- Identifies worst-performing regime (Red Light)
- Shows which regime to avoid for MDD reduction

### Step 5: Similarity Analysis
- Finds similar historical days using pattern matching
- Analyzes subsequent price performance
- Enables pattern-based exits

### Step 6: Standard Donchian MCPT Backtest
- Walk-forward optimization and testing
- Monte Carlo Permutation Test for statistical significance
- Generates visualizations and HTML report

### Step 7: Enhanced Donchian MCPT Backtest
- **Red Light regime filtering** (avoids worst-performing regimes)
- **Pattern-based early exits** (-2.0% threshold, 10 similar days)
- Walk-forward MCPT with enhanced features

### Step 8: Drawdown Analysis
- Analyzes which regimes cause drawdowns
- Simulates MDD reduction from filtering
- Provides recommendations

### Step 9: Strategy Comparison
- Compares Standard vs Enhanced Donchian
- Shows MDD reduction and return impact
- Side-by-side comparison

### Step 10: Comprehensive Report
- Generates HTML report with all analyses
- Includes visualizations and insights
- One-stop summary document

## Output Files

All results are organized in: `analysis_results/TICKER.NS/`

### Analysis Data
- `output/TICKER.NS_analysis.csv` - Full data with all 86 indicators

### Correlation Analysis
- `correlation_heatmap_full.png` - Full correlation matrix
- `correlation_heatmap_filtered_0.7.png` - Significant correlations only
- `correlation_matrix.csv` - Raw correlation data

### Behavioral Patterns
- `market_regimes_plot.png` - Regimes over time
- `data_with_regimes.csv` - Full data with regime labels
- `regime_analysis_summary.csv` - Regime characteristics

### Similarity Analysis
- `similar_days_euclidean_YYYY-MM-DD.csv` - Similar days for latest date

### Standard Donchian Backtest
- `donchian_walkforward_results.csv` - Detailed results
- `donchian_walkforward_results_readable_summary.csv` - Easy-to-read summary
- `donchian_mcpt_summary.csv` - Quick summary
- `donchian_mcpt_report.html` - Comprehensive HTML report
- `donchian_equity_curve.png` - Performance visualization
- `donchian_actual_vs_permuted.png` - Statistical significance

### Enhanced Donchian Backtest
- `donchian_enhanced_walkforward_results.csv` - Detailed results
- `donchian_enhanced_walkforward_results_readable_summary.csv` - Easy-to-read summary
- `donchian_enhanced_mcpt_summary.csv` - Quick summary

### Analysis & Comparison
- `backtest_comparison.csv` - Standard vs Enhanced comparison
- `comprehensive_report.html` - All analyses in one report

## Quick View Results

After setup completes, view results:

```bash
# View simple summaries (easy to read)
python3 donchian_simple_summary.py analysis_results/TCS.NS/donchian_walkforward_results.csv
python3 donchian_simple_summary.py analysis_results/TCS.NS/donchian_enhanced_walkforward_results.csv

# View comprehensive report
open analysis_results/TCS.NS/comprehensive_report.html

# View comparison
cat analysis_results/TCS.NS/backtest_comparison.csv
```

## Expected Time

- **Data Fetching**: 1-5 minutes (depending on history length)
- **Correlation Analysis**: 30 seconds - 2 minutes
- **Behavioral Patterns**: 1-3 minutes
- **Similarity Analysis**: 30 seconds - 1 minute
- **Standard Donchian Backtest**: 5-15 minutes
- **Enhanced Donchian Backtest**: 10-20 minutes (includes pattern matching)
- **Total**: ~20-45 minutes for complete setup

## What to Check After Setup

1. **Red Light Regime**: Check which regime was identified as worst
2. **MDD Reduction**: Compare Enhanced vs Standard MDD
3. **Returns**: Ensure Enhanced maintains or improves returns
4. **Statistical Significance**: Check p-values (< 0.05 is good)

## Troubleshooting

### "Regime data not found"
- Behavioral pattern analysis may have failed
- Enhanced Donchian will run without regime filtering
- Re-run: `python3 behavioral_patterns.py output/TICKER.NS_analysis.csv`

### "Pattern matching failed"
- Enhanced Donchian will run without pattern exits
- This is okay - regime filtering still works

### "No results produced"
- Check that you have enough historical data (at least 2-3 years)
- Verify the analysis file was created correctly

## Next Steps After Setup

1. **Review Results**: Check the comprehensive report
2. **Compare Strategies**: See which performs better
3. **Fine-Tune**: Adjust thresholds if needed
4. **Monitor**: Re-run periodically to update with new data

## Summary

✅ **One command** runs everything
✅ **Automated workflow** - no manual steps
✅ **Complete analysis** - all features included
✅ **Organized results** - everything in one directory

Just run: `python3 complete_setup.py TICKER.NS` and wait for completion!

