# How to Run a Backtest - Step by Step Guide

## ✅ Quick Start

### Step 1: Run the Backtest
```bash
python3 backtest_example.py
```

That's it! The script will:
1. Load your HDFC bank analysis data
2. Create trading signals based on RSI and MACD indicators
3. Simulate trades
4. Calculate performance metrics
5. Save results to `backtest_results.csv`

---

## 📊 Understanding Your Results

### Your HDFC Backtest Results:
```
Initial Capital: $100,000.00
Final Portfolio Value: $191,227.30
Total Return: 91.23% ✅
Number of Trades: 114
Sharpe Ratio: 0.68
Maximum Drawdown: -35.09%

Buy-and-Hold Return: 63.43%
Strategy vs Buy-Hold: +27.80% ✅
```

### What These Numbers Mean:

1. **Total Return: 91.23%**
   - Your strategy turned $100,000 into $191,227
   - This is your profit over the entire period (2020-2025)

2. **Strategy vs Buy-Hold: +27.80%**
   - Buy-and-hold (just buying and holding) returned 63.43%
   - Your strategy beat buy-and-hold by 27.80%! 🎉

3. **Sharpe Ratio: 0.68**
   - Measures risk-adjusted returns
   - > 1.0 = Excellent
   - 0.5-1.0 = Good
   - < 0.5 = Needs improvement
   - Your 0.68 is decent but could be better

4. **Maximum Drawdown: -35.09%**
   - Worst peak-to-trough decline
   - Means at some point, your portfolio dropped 35% from a peak
   - Lower is better (less risk)

5. **Number of Trades: 114**
   - 99 buy signals + 155 sell signals = 114 completed trades
   - More trades = more transaction costs (not included in this simple backtest)

---

## 🔧 How the Strategy Works

The current strategy in `backtest_example.py` uses:

### BUY Signals:
- **RSI < 30** (oversold - stock is cheap, potential bounce)
- **OR MACD crosses above signal** (bullish momentum starting)

### SELL Signals:
- **RSI > 70** (overbought - stock is expensive)
- **OR MACD crosses below signal** (bearish momentum starting)

---

## 🎯 Customizing Your Strategy

Edit `backtest_example.py` to change the strategy:

### Example 1: Simple RSI Strategy
```python
# Buy when RSI < 30
buy_condition = df['momentum_rsi'] < 30
# Sell when RSI > 70
sell_condition = df['momentum_rsi'] > 70
```

### Example 2: Bollinger Bands Strategy
```python
# Buy when price touches lower band
buy_condition = df['Close'] <= df['volatility_bbl']
# Sell when price touches upper band
sell_condition = df['Close'] >= df['volatility_bbh']
```

### Example 3: Multiple Indicator Strategy
```python
# Buy when: RSI oversold AND price above 200-day MA
buy_condition = (df['momentum_rsi'] < 30) & (df['Close'] > df['trend_sma_slow'])
# Sell when: RSI overbought OR price below 200-day MA
sell_condition = (df['momentum_rsi'] > 70) | (df['Close'] < df['trend_sma_slow'])
```

---

## 📈 Testing Different Stocks

To test a different stock, change the filename:

```python
# In backtest_example.py, line 174:
df = pd.read_csv('output/RELIANCE.NS_analysis.csv', header=0, skiprows=[1, 2])
# or
df = pd.read_csv('output/TCS.NS_analysis.csv', header=0, skiprows=[1, 2])
```

---

## 📁 Output Files

After running the backtest, you'll get:

1. **`backtest_results.csv`**
   - Contains: Date, Close price, Signals, RSI, MACD, Portfolio value, Returns
   - Use this to analyze when trades happened
   - Open in Excel/Google Sheets to visualize

2. **Console Output**
   - Summary statistics printed to terminal

---

## 🚀 Next Steps

1. **Try Different Strategies**
   - Modify the buy/sell conditions
   - Test different indicator combinations

2. **Add More Metrics**
   - Win rate (how many trades were profitable)
   - Average profit per trade
   - Transaction costs
   - Slippage

3. **Test Multiple Stocks**
   - Create a loop to test all 5 stocks
   - Compare which strategies work best for which stocks

4. **Visualize Results**
   - Plot portfolio value over time
   - Show buy/sell points on price chart
   - Compare with buy-and-hold

---

## ⚠️ Important Notes

1. **No Transaction Costs**: This simple backtest doesn't include:
   - Brokerage fees
   - Taxes
   - Slippage (difference between expected and actual price)

2. **Past Performance ≠ Future Results**: 
   - Backtesting shows what WOULD have happened
   - Real trading may have different results

3. **Overfitting Risk**:
   - Don't optimize too much for past data
   - Test on out-of-sample data

---

## 💡 Pro Tips

1. **Start Simple**: Test one indicator at a time
2. **Compare Strategies**: Always compare with buy-and-hold
3. **Check Drawdowns**: High returns with huge drawdowns = risky
4. **Test Multiple Periods**: Try different date ranges
5. **Paper Trade First**: Test with real-time data before using real money

---

## 🎓 Learning More

- Read the code in `backtest_example.py` to understand how it works
- Experiment with different indicators from your analysis files
- Research technical analysis strategies online
- Consider using professional backtesting libraries (Backtrader, Zipline)

Happy Backtesting! 📊🚀

