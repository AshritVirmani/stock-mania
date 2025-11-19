# 🎯 Cash-Secured Puts Strategy Backtesting Guide

## Quick Start

```bash
python3 backtest_strategies.py WIPRO.NS
```

This will backtest all 3 cash-secured puts strategies and show you which performs best.

---

## 📊 Available Strategies

### Strategy 1: "High Premium, Low Risk"
**Best for:** Income traders seeking safe premium collection

**Indicators:**
- `trend_ema_fast` (30-day EMA)
- `trend_ema_slow` (31-day EMA) 
- `momentum_rsi` (10-period RSI)
- `volatility_bbw` (Bollinger Band Width)

**Entry Conditions:**
- Price above slow EMA (uptrend)
- Price near fast EMA (small pullback)
- RSI between 35-45 (moderate dip)
- BBW increasing (volatility rising = higher premiums)

---

### Strategy 2: "Oversold Reversal"
**Best for:** Buying stocks at discounts

**Indicators:**
- `trend_macd_diff` (MACD Histogram)
- `momentum_stoch_rsi` (Stochastic RSI)
- `momentum_wr` (Williams %R)

**Entry Conditions:**
- MACD histogram turning upward
- Stochastic RSI < 20 but rising
- Williams %R < -80 but rising

**Perfect when:** You want assignment to get shares at a bargain

---

### Strategy 3: "Premium Maximizer"
**Best for:** Maximum premium per risk

**Indicators:**
- `volatility_atr` (Average True Range)
- `volatility_bbw` (Bollinger Band Width)
- `trend_adx` (Average Directional Index)
- `momentum_roc` (Rate of Change)

**Entry Conditions:**
- ATR above median (high volatility)
- BBW expanding (increasing volatility)
- ADX < 25 (weak trend = less directional risk)
- ROC between 0-5% (momentum stabilizing)

**Best for:** Monthly option income sellers

---

## 🚀 Usage

### Backtest All Strategies
```bash
python3 backtest_strategies.py WIPRO.NS
```

### Backtest Specific Strategy
```bash
python3 backtest_strategies.py WIPRO.NS --strategy 1
python3 backtest_strategies.py WIPRO.NS --strategy 2
python3 backtest_strategies.py WIPRO.NS --strategy 3
```

### Interactive Mode
```bash
python3 backtest_strategies.py
# Then enter stock symbol when prompted
```

---

## 📈 Understanding Results

### Performance Metrics

- **Total Return:** Overall profit/loss percentage
- **Buy-and-Hold:** What you'd get by just holding the stock
- **Strategy vs Hold:** How much better/worse than buy-and-hold
- **Win Rate:** Percentage of profitable trades
- **Avg Return/Trade:** Average profit per trade
- **Avg Days Held:** Average holding period

### Trade Details

Each trade shows:
- Entry and exit dates
- Entry and exit prices
- Return percentage
- Days held
- ✅ = Profitable trade
- ❌ = Losing trade

---

## 💡 Strategy Comparison

After running all strategies, you'll see a comparison table showing:
- Which strategy has the highest return
- Which has the best win rate
- Which beats buy-and-hold

The best strategy is highlighted with 🥇

---

## ⚙️ How It Works

### Cash-Secured Puts Simulation

The backtester simulates selling cash-secured puts by:
1. **Entry Signal:** When all conditions are met, "sell" a put (simulate by buying stock)
2. **Hold Period:** Hold position for up to 30 days (typical monthly option)
3. **Exit Conditions:**
   - Hold for 30 days (option expiry)
   - Price moves up 5% (take profit)
   - Price moves down 10% (stop loss)

### Why This Approach?

- Selling puts = obligation to buy at strike price
- If assigned, you own the stock
- This simulation assumes you'd buy at current price when signal triggers
- Tracks if that would have been profitable

---

## 📁 Output Files

Results are saved to:
```
analysis_results/WIPRO.NS_strategy_backtest_TIMESTAMP.csv
```

Contains summary of all strategies tested with key metrics.

---

## 🔧 Customization

To modify strategies, edit the strategy functions in `backtest_strategies.py`:

- `strategy_1_high_premium_low_risk()` - Strategy 1 logic
- `strategy_2_oversold_reversal()` - Strategy 2 logic  
- `strategy_3_premium_maximizer()` - Strategy 3 logic

Adjust entry conditions, exit rules, or add new strategies!

---

## 📊 Example Output

```
🏆 STRATEGY COMPARISON
================================================================================
Strategy                      Return %    Trades  Win Rate %  vs Buy-Hold
--------------------------------------------------------------------------------
High Premium, Low Risk           12.45%       45      62.22%      +5.23% ✅
Oversold Reversal                 8.32%       52      55.77%      +1.10% ✅
Premium Maximizer                15.67%       38      65.79%      +8.45% ✅

================================================================================
🥇 BEST STRATEGY: Premium Maximizer (15.67% return)
================================================================================
```

---

## ⚠️ Important Notes

1. **Past Performance ≠ Future Results**
   - Backtests show historical performance
   - Market conditions change
   - Use as a guide, not a guarantee

2. **Assumptions:**
   - No transaction costs included
   - No slippage
   - Perfect execution at signal prices
   - Real trading may differ

3. **Cash-Secured Puts:**
   - Requires capital to secure the put
   - Risk of assignment
   - This simulation simplifies the process

---

## 🎓 Next Steps

1. **Test on Multiple Stocks:** Run backtests on different stocks to see which strategies work best for each
2. **Adjust Parameters:** Modify entry/exit conditions to optimize
3. **Paper Trade:** Test strategies with real-time data before using real money
4. **Combine Strategies:** Use multiple strategies together for diversification

---

**Happy Backtesting! 📈💰**

