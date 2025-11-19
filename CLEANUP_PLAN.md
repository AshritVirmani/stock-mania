# Repository Cleanup Plan

## Files Essential for Complete Setup

### Root Level (Keep)
- `calculate_intrinsic_value.py` - Used by complete_setup
- `find_undervalued_stocks.py` - Standalone utility
- `ta/` - Core library (required)
- `setup.py` - Package setup
- `requirements*.txt` - Dependencies
- `README.md` - Main documentation
- `COMPLETE_SETUP_FILE_STRUCTURE.md` - Setup documentation
- `COMPLETE_SETUP_GUIDE.md` - Setup guide
- `INTRINSIC_VALUE_GUIDE.md` - Valuation guide
- `VALUATION_FIXES.md` - Valuation documentation

### legacy_scripts/ (Keep - Used by complete_setup)
- `complete_setup.py` - Main orchestrator
- `analyze_indian_stocks.py` - Step 1
- `analyze_correlations.py` - Step 3
- `behavioral_patterns.py` - Step 4
- `identify_red_light_regime.py` - Step 5
- `find_similar_days.py` - Step 6
- `walkforward_mcpt.py` - Imported by complete_setup
- `donchian_mcpt_backtest.py` - Step 7
- `donchian_enhanced_backtest.py` - Step 8
- `simple_backtest_for_new_stocks.py` - Fallback
- `analyze_drawdowns.py` - Step 9
- `compare_backtests.py` - Step 10
- `generate_analysis_report.py` - Step 11

## Files to Remove (Not Used by Complete Setup)

### Root Level - Old Results/Output
- `output/` directory - Old output location
- `analysis_results/` - Keep structure, but remove old flat files:
  - `RELIANCE.NS_*.csv`, `RELIANCE.NS_*.png`, `RELIANCE.NS_*.html` (flat files)
  - `HDFCBANK.NS_*.csv`, `HDFCBANK.NS_*.png` (flat files)
  - `WIPRO.NS_*.csv`, `WIPRO.NS_*.png`, `WIPRO.NS_*.html` (flat files)
  - `VMM.NS_*.csv`, `VMM.NS_*.png`, `VMM.NS_*.html` (flat files)
  - `backtest_INFY.NS_*.csv` (old backtest files)
  - `backtest_results.csv` (old file)
  - `full_indicator_correlation_matrix.csv` (old file)
  - `analysis_results/dashboards/` (if not used)

### Root Level - Old Analysis Folders
- `correlation_analysis/` - Old location
- `behavioral_analysis/` - Old location
- `similarity_analysis/` - Old location
- `interactive_visualizations/` - Not used by complete_setup
- `stock_analysis/` - If not used

### Root Level - Examples/Test/Build
- `examples_to_use/` - Examples not needed for production
- `test/` - Test files (optional, can keep for development)
- `build/` - Build artifacts
- `ta.egg-info/` - Build artifacts
- `docs/` - Documentation build (if not needed)

### Root Level - Redundant Guides
- `BENJAMIN_OREO_README.md` - Can remove (branding removed)
- `ANALYSIS_GUIDE.md` - Redundant with COMPLETE_SETUP_GUIDE
- `BACKTEST_COMPARISON.md` - Redundant
- `DONCHIAN_STRATEGY_EXPLAINED.md` - Redundant
- `ENHANCED_DONCHIAN_GUIDE.md` - Redundant
- `HISTORICAL_DATA_GUIDE.md` - Redundant
- `HOW_TO_BACKTEST.md` - Redundant
- `HOW_TO_READ_BACKTEST_RESULTS.md` - Redundant
- `HOW_TO_READ_CORRELATION_HEATMAP.md` - Redundant
- `INDICATOR_NAMES_REFERENCE.md` - Maybe keep if useful
- `INTERACTIVE_GUIDE.md` - Not used by complete_setup
- `LOOKAHEAD_BIAS_FIX.md` - Redundant
- `MDD_REDUCTION_GUIDE.md` - Redundant
- `ORGANIZATION_GUIDE.md` - Redundant
- `QUICK_START_GUIDE.md` - Redundant with COMPLETE_SETUP_GUIDE
- `README_ANALYSIS.md` - Redundant
- `README_INTERACTIVE.md` - Redundant
- `STRATEGY_BACKTEST_GUIDE.md` - Redundant
- `WHAT_DONCHIAN_DOES.md` - Redundant
- `WHICH_APPROACH_BETTER.md` - Redundant
- `explain_negative_values.md` - Redundant

### legacy_scripts/ - Unused Scripts
- `analyze_stock.py` - Not used by complete_setup
- `backtest_example.py` - Example file
- `backtest_strategies.py` - Not used by complete_setup
- `donchian_enhanced.py` - Not used (enhanced_backtest.py is used)
- `donchian_simple_summary.py` - Utility, maybe keep
- `donchian_strategy.py` - Not used
- `interactive_backtest.py` - Not used by complete_setup
- `list_indicators.py` - Utility, maybe keep
- `read_results_summary.py` - Utility, maybe keep
- `visualize_indicators.py` - Not used by complete_setup
- `calculate_intrinsic_value.py` (in legacy_scripts) - Duplicate, root version is used
- `find_undervalued_stocks.py` (in legacy_scripts) - Duplicate, root version is used

### Root Level - Config Files (Keep Essential)
- `LICENSE` - Keep
- `MANIFEST` - Keep if needed
- `Makefile` - Keep if used
- `pylintrc` - Keep if used
- `setup.cfg` - Keep if used
- `RELEASE.md` - Maybe remove
- `requirements_viz.txt` - Remove if not needed
- `requirements-core.txt` - Keep
- `requirements-coverage.txt` - Remove if not needed
- `requirements-doc.txt` - Remove if not needed
- `requirements-play.txt` - Keep (has yfinance)
- `requirements-test.txt` - Remove if not needed
- `requirements.txt` - Keep (main requirements)

## Summary

**Keep:**
- Core library (`ta/`)
- Essential scripts for complete_setup
- Main documentation (README, COMPLETE_SETUP guides)
- Setup files (setup.py, requirements.txt)
- License

**Remove:**
- Old analysis results (flat files in analysis_results/)
- Old output directories
- Redundant guide files
- Example/test files (optional)
- Build artifacts
- Unused legacy scripts
- Duplicate files

