# 📁 File Organization Guide

## New Organized Structure

All analysis results are now organized by stock ticker in separate folders:

```
analysis_results/
├── WIPRO.NS/
│   ├── correlation_heatmap.png
│   ├── correlation_matrix.csv
│   ├── market_regimes_plot.png
│   ├── data_with_regimes.csv
│   ├── comprehensive_report.html
│   ├── strategy_backtest_TIMESTAMP.csv
│   ├── similar_days_2024-01-15.csv
│   └── dashboards/
│       ├── momentum_rsi_vs_trend_macd.html
│       └── ...
│
├── RELIANCE.NS/
│   ├── correlation_heatmap.png
│   ├── correlation_matrix.csv
│   ├── market_regimes_plot.png
│   ├── data_with_regimes.csv
│   ├── comprehensive_report.html
│   └── ...
│
├── HDFCBANK.NS/
│   └── ...
│
└── TCS.NS/
    └── ...
```

## Benefits

✅ **No Clutter** - Each stock has its own folder  
✅ **Easy to Find** - All results for a stock in one place  
✅ **Clean Structure** - Organized and professional  
✅ **Easy Cleanup** - Delete a ticker folder to remove all its results  

## File Naming Convention

All files use simple, descriptive names (no ticker prefix needed since they're in ticker folders):

- `correlation_heatmap.png` - Correlation visualization
- `correlation_matrix.csv` - Full correlation data
- `market_regimes_plot.png` - Market regime visualization
- `data_with_regimes.csv` - Data with regime labels
- `comprehensive_report.html` - Full analysis report
- `strategy_backtest_TIMESTAMP.csv` - Strategy backtest results
- `similar_days_DATE.csv` - Similar days analysis
- `dashboards/` - Interactive HTML dashboards

## Accessing Results

### View All Results for a Stock:
```bash
ls analysis_results/WIPRO.NS/
```

### Open Report:
```bash
open analysis_results/WIPRO.NS/comprehensive_report.html
```

### View Dashboards:
```bash
ls analysis_results/WIPRO.NS/dashboards/
```

## Migration Note

If you have old results in the root `analysis_results/` folder, they'll still work, but new results will be organized by ticker. You can manually move old files to their respective ticker folders if needed.

---

**Everything is now organized and easy to navigate! 📁✨**

