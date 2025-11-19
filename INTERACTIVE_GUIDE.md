# 🚀 Interactive Backtesting Tool - User Guide

## Quick Start

```bash
python3 interactive_backtest.py
```

That's it! The tool will guide you through everything step-by-step.

---

## 📋 What It Does

The Interactive Backtester lets you:
- ✅ **Select stocks** from your analyzed data
- ✅ **Choose trading strategies** from a menu
- ✅ **Customize parameters** (like RSI thresholds)
- ✅ **See results** in an easy-to-read format
- ✅ **Save results** to CSV files
- ✅ **Test multiple strategies** without editing code

---

## 🎯 Step-by-Step Walkthrough

### Step 1: Select a Stock
```
📊 AVAILABLE STOCKS
  1. HDFCBANK.NS
  2. ICICIBANK.NS
  3. INFY.NS
  4. RELIANCE.NS
  5. TCS.NS
  0. Exit

Select a stock (enter number): 
```
- Just type the number (1-5) and press Enter
- The tool loads your stock's analysis data automatically

### Step 2: Choose a Strategy
```
🎯 TRADING STRATEGIES
  1. RSI Strategy (Buy oversold, Sell overbought)
  2. MACD Crossover Strategy
  3. Combined RSI + MACD Strategy
  4. Bollinger Bands Strategy
  5. Moving Average Crossover
  6. Custom Strategy (Advanced)
  0. Back to Stock Selection

Select a strategy (enter number):
```

**Strategy Descriptions:**

1. **RSI Strategy**
   - Buys when RSI < 30 (oversold)
   - Sells when RSI > 70 (overbought)
   - You can customize the thresholds

2. **MACD Crossover**
   - Buys when MACD line crosses above signal line
   - Sells when MACD line crosses below signal line
   - Good for trend following

3. **Combined RSI + MACD**
   - Uses both RSI and MACD signals
   - More conservative (requires confirmation)
   - Often better performance

4. **Bollinger Bands**
   - Buys when price touches lower band
   - Sells when price touches upper band
   - Mean reversion strategy

5. **Moving Average Crossover**
   - Buys when fast MA crosses above slow MA
   - Sells when fast MA crosses below slow MA
   - Classic trend following

6. **Custom Strategy** (Coming soon)
   - For advanced users who want to code their own

### Step 3: Set Parameters (if needed)

For RSI-based strategies, you'll see:
```
⚙️  RSI PARAMETERS
Enter RSI buy threshold (default 30): 
Enter RSI sell threshold (default 70): 
```
- Press Enter to use defaults (30/70)
- Or type custom values (e.g., 25/75 for more conservative)

### Step 4: Set Initial Capital
```
Enter initial capital (default ₹1,00,000): 
```
- Press Enter for ₹1,00,000
- Or type your own amount (e.g., `50000` or `₹2,00,000`)

### Step 5: View Results

You'll see a comprehensive results summary:
```
💰 FINANCIAL PERFORMANCE
   Initial Capital:     ₹  100,000.00
   Final Portfolio:     ₹  191,227.30
   Total Return:               91.23%

📊 COMPARISON
   Buy-and-Hold:               63.43%
   Strategy vs Hold:          +27.80% ✅

📉 RISK METRICS
   Number of Trades:             114
   Sharpe Ratio:                0.68
   Max Drawdown:              -35.09%
   Risk Rating:         Good ⭐⭐
```

**Understanding the Results:**

- **Total Return**: Your profit percentage
- **Strategy vs Hold**: How much better/worse than buy-and-hold
- **Sharpe Ratio**: Risk-adjusted returns
  - > 1.0 = Excellent ⭐⭐⭐
  - 0.5-1.0 = Good ⭐⭐
  - < 0.5 = Needs Improvement ⭐
- **Max Drawdown**: Worst peak-to-trough decline
- **Number of Trades**: How many buy/sell cycles

### Step 6: Save Results (Optional)
```
💾 Save results to CSV? (y/n): 
```
- Type `y` to save, `n` to skip
- File will be named: `backtest_STOCK_STRATEGY_TIMESTAMP.csv`

### Step 7: Test Another Strategy
```
Test another strategy? (y/n): 
```
- Type `y` to test another strategy on the same stock
- Type `n` to exit or select a different stock

---

## 💡 Tips for Best Results

### 1. **Start with Combined Strategy**
   - Strategy #3 (RSI + MACD) often performs best
   - Uses multiple indicators for confirmation

### 2. **Compare Strategies**
   - Test the same stock with different strategies
   - See which works best for that stock

### 3. **Check Sharpe Ratio**
   - Higher is better (risk-adjusted returns)
   - A strategy with 50% return but Sharpe 0.3 is risky
   - A strategy with 30% return but Sharpe 1.2 is better

### 4. **Watch Max Drawdown**
   - Lower is better (less risk)
   - -50% drawdown means you lost half your money at worst point
   - Can you handle that psychologically?

### 5. **Number of Trades**
   - More trades = more transaction costs (not included)
   - Fewer trades = less active management needed

---

## 🎨 Example Workflow

```
1. Run: python3 interactive_backtest.py

2. Select: 1 (HDFCBANK.NS)

3. Select: 3 (Combined RSI + MACD)

4. Parameters: Press Enter (use defaults 30/70)

5. Capital: Press Enter (use ₹1,00,000)

6. View Results: See performance metrics

7. Save: y (save to CSV)

8. Continue: y (test another strategy)

9. Select: 4 (Bollinger Bands)

10. Compare results with previous strategy
```

---

## 🔧 Troubleshooting

### "Output directory not found"
- **Solution**: Run `analyze_indian_stocks.py` first to generate analysis files

### "Missing required columns"
- **Solution**: Make sure you ran the full analysis (all indicators)

### "No stocks available"
- **Solution**: Check that `output/` folder has `*_analysis.csv` files

### Keyboard Interrupt (Ctrl+C)
- Just press Ctrl+C anytime to exit gracefully

---

## 📊 Understanding the Output

### Recent Trades Section
Shows the last 5 trades:
```
🔄 RECENT TRADES (Last 5)
   2025-01-09  🟢 BUY     @ ₹  822.78  (134.54 shares)
   2025-03-24  🔴 SELL    @ ₹  888.00  (134.54 shares)
```
- 🟢 = Buy signal
- 🔴 = Sell signal
- Shows date, action, price, and shares

### Performance Indicators
- ✅ = Strategy beat buy-and-hold
- ❌ = Strategy underperformed buy-and-hold
- ⭐ = Risk rating (more stars = better)

---

## 🚀 Advanced Usage

### Testing Multiple Stocks
1. Run the tool
2. Test strategy on Stock A
3. Exit and run again
4. Test same strategy on Stock B
5. Compare results

### Parameter Optimization
1. Test with default RSI (30/70)
2. Test with conservative RSI (25/75)
3. Test with aggressive RSI (35/65)
4. See which performs best

### Strategy Comparison
1. Test Strategy #1 (RSI only)
2. Test Strategy #3 (RSI + MACD)
3. Compare Sharpe ratios and returns
4. Choose the best one

---

## 📝 Notes

- **No Transaction Costs**: This backtest doesn't include brokerage fees
- **Past Performance**: Results show what WOULD have happened, not future guarantees
- **Paper Trading**: Test with real-time data before using real money
- **Multiple Timeframes**: Results are for the entire date range (2020-2025)

---

## 🎓 Next Steps

1. **Experiment**: Try different strategies on different stocks
2. **Learn**: Understand why some strategies work better
3. **Optimize**: Fine-tune parameters for your risk tolerance
4. **Visualize**: Open CSV files in Excel to see charts
5. **Paper Trade**: Test strategies with real-time data

---

## 💬 Quick Reference

| Command | Action |
|---------|--------|
| `python3 interactive_backtest.py` | Start the tool |
| `1-5` | Select stock |
| `1-6` | Select strategy |
| `Enter` | Use default value |
| `y/n` | Yes/No prompts |
| `Ctrl+C` | Exit anytime |

---

**Happy Backtesting! 📈🚀**

