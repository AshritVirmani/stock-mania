# What Does the Donchian Breakout Strategy Do?

## Simple Explanation

The **Donchian Breakout Strategy** is a **trend-following** system that tries to catch big price moves by identifying when prices "break out" of recent trading ranges.

---

## How It Works (Step by Step)

### 1. **Calculates Two Price Bands**

For each day, it looks back at the last N days (e.g., 20 days) and finds:
- **Upper Band** = Highest price in the last 20 days
- **Lower Band** = Lowest price in the last 20 days

**Example with 20-day lookback:**
```
Day 1-20: Prices range from ₹100 to ₹120
  → Upper Band = ₹120 (highest)
  → Lower Band = ₹100 (lowest)
```

### 2. **Generates Trading Signals**

The strategy watches the current price relative to these bands:

- **🟢 BUY Signal (+1)**: When current price **breaks ABOVE** the upper band
  - Meaning: Price is making a new high (strong upward momentum)
  - Action: Go LONG (buy and hold)

- **🔴 SELL Signal (-1)**: When current price **breaks BELOW** the lower band
  - Meaning: Price is making a new low (strong downward momentum)
  - Action: Go SHORT (sell and hold short position)

- **⚪ HOLD (0)**: When price is **between** the bands
  - Meaning: Price is in a range, no clear trend
  - Action: Keep current position (don't change)

### 3. **Holds Position Until Next Signal**

Once you get a signal, you hold that position (long or short) until the opposite signal appears.

---

## Visual Example

```
Price Chart with Donchian Channels (20-day lookback):

Price
  ↑
₹120 ──────────────────────────────── Upper Band
     │                                │
₹110 │        ⚪ HOLD                 │
     │     (price between bands)      │
₹100 ──────────────────────────────── Lower Band
     │                                │
  Day 1                              Day 20

When price breaks above ₹120 → 🟢 BUY
When price breaks below ₹100 → 🔴 SELL
```

---

## Real Example from Your Data

From the test run above:

```
Date: 2010-04-28
- Close Price: ₹221.33
- Upper Band: ₹236.16
- Lower Band: ₹221.82
- Price broke BELOW lower band (₹221.33 < ₹221.82)
→ 🔴 SELL Signal generated
```

---

## Why It Works (The Theory)

1. **Momentum**: When price breaks above recent highs, it often continues upward (momentum)
2. **Trend Following**: It catches the start of new trends
3. **Breakout Trading**: Many profitable moves start with breakouts from ranges

---

## The "Optimization" Part

The strategy has **one parameter**: the **lookback period** (N days).

**What optimization does:**
- Tests different lookback periods (12 to 169 days)
- For each period, calculates how profitable it would have been
- Picks the lookback period with the **highest profit factor**

**Example:**
- 20-day lookback → Profit Factor = 1.2
- 50-day lookback → Profit Factor = 1.8 ← **BEST**
- 100-day lookback → Profit Factor = 1.5

**Result**: Use 50-day lookback for this stock/period

---

## What the MCPT Tests

The Monte Carlo Permutation Test asks:
- **"Is this strategy's success due to real edge, or just luck?"**

**How:**
1. Takes the **same signals** (same buy/sell timing)
2. **Shuffles the returns** (randomizes what actually happened)
3. Tests if random returns would perform as well

**If red line (real strategy) is above grey lines (random):**
→ Strategy has **real predictive power**, not just luck

**If red line is in grey cluster:**
→ Results might just be **random chance**

---

## Summary

**Donchian Strategy = "Buy new highs, sell new lows"**

- **Simple**: Just two bands (high and low)
- **Trend-following**: Catches momentum moves
- **Systematic**: No emotions, just rules
- **Optimized**: Finds best lookback period for each stock
- **Tested**: MCPT validates if it's real edge or luck

---

## When It Works Best

✅ **Works well in:**
- Trending markets (strong up or down moves)
- Volatile stocks with clear breakouts
- Stocks with momentum characteristics

❌ **May struggle in:**
- Sideways/ranging markets (lots of false breakouts)
- Very choppy price action
- Low volatility stocks

---

## Key Takeaway

The Donchian strategy is like saying:
- **"If price makes a new 20-day high, buy - momentum is strong"**
- **"If price makes a new 20-day low, sell - momentum is weak"**

It's a simple but powerful trend-following system that has been used by professional traders for decades!

