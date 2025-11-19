# 📊 How to Read Correlation Heatmaps

## Quick Guide

### Understanding the Colors

- **🔴 Dark Red** = Strong **positive** correlation (close to +1.0)
  - Indicators move **together** in the same direction
  - Example: When RSI goes up, Stochastic RSI also goes up
  
- **🔵 Dark Blue** = Strong **negative** correlation (close to -1.0)
  - Indicators move in **opposite** directions
  - Example: When price goes up, Williams %R goes down
  
- **⚪ White/Light Gray** = Weak or **no** correlation (close to 0.0)
  - Indicators are **independent** - no relationship
  - Example: Volume indicators vs momentum indicators might be unrelated

- **🔴 Red Diagonal Line** = Self-correlation (always 1.0)
  - Each indicator is perfectly correlated with itself
  - This is **normal** and expected - ignore it!

---

## 📐 How to Read the Grid

### Finding a Specific Correlation

1. **Pick an indicator on the LEFT (vertical axis)**
   - Example: `momentum_rsi`

2. **Pick an indicator on the BOTTOM (horizontal axis)**
   - Example: `trend_macd`

3. **Find where they intersect**
   - The color at that intersection shows their correlation
   - Red = move together, Blue = move opposite, White = no relationship

### Example:
```
Looking at RSI (left) vs MACD (bottom):
- Red square = RSI and MACD move together (both bullish/bearish)
- Blue square = RSI and MACD move opposite (one bullish, one bearish)
- White = No clear relationship
```

---

## 🎯 What to Look For

### 1. **Red Clusters** (Positive Correlations)
- **What it means:** Groups of indicators that move together
- **Why it matters:** These indicators are **redundant** - you don't need all of them
- **Example:** If RSI, Stochastic RSI, and Williams %R are all red together, they're measuring similar things

### 2. **Blue Squares** (Negative Correlations)
- **What it means:** Indicators that move in opposite directions
- **Why it matters:** Good for **confirmation** - when one is bullish, the other is bearish
- **Example:** Price vs Volatility often have negative correlation

### 3. **White Areas** (No Correlation)
- **What it means:** Independent indicators
- **Why it matters:** These are **unique** - each adds different information
- **Example:** Volume indicators vs Price indicators might be independent

---

## 🔍 Practical Examples

### Example 1: Finding Redundant Indicators
```
If you see:
- momentum_rsi ↔ momentum_stoch_rsi = Dark Red (0.95)
- momentum_rsi ↔ momentum_wr = Dark Red (0.90)

This means:
✅ RSI, Stochastic RSI, and Williams %R are all measuring momentum
❌ You don't need all three - they're redundant
💡 Pick ONE and use it
```

### Example 2: Finding Complementary Indicators
```
If you see:
- trend_macd ↔ volatility_atr = White (0.15)
- trend_macd ↔ volume_obv = White (0.20)

This means:
✅ MACD, ATR, and OBV are independent
💡 Use them together for better analysis
💡 Each adds unique information
```

### Example 3: Finding Confirmation Signals
```
If you see:
- momentum_rsi ↔ trend_macd = Dark Red (0.85)

This means:
✅ When RSI is bullish, MACD is also bullish
💡 Both confirm the same trend
💡 Stronger signal when both agree
```

---

## 📊 Reading the Filtered Heatmap

The **filtered heatmap** (`correlation_heatmap_filtered_0.7.png`) shows only significant correlations (≥ 0.7).

### Why Use the Filtered Version?

- ✅ **Easier to read** - only shows important relationships
- ✅ **Less clutter** - white areas are hidden
- ✅ **Focus on patterns** - see which indicators group together
- ✅ **Faster analysis** - don't waste time on weak correlations

### What the Filtered Version Shows:

- **Red squares** = Strong positive relationships (≥ 0.7)
- **Blue squares** = Strong negative relationships (≤ -0.7)
- **White areas** = Hidden (correlations < 0.7)

---

## 🎓 Step-by-Step Reading Guide

### Step 1: Identify Indicator Groups
Look for **red clusters** - groups of indicators that are all red together.

**Example:**
```
You might see a cluster:
- trend_ema_fast
- trend_ema_slow
- trend_sma_fast
- trend_sma_slow
- volatility_bbm
- volume_vwap

All red together = They all measure similar trend/price levels
```

### Step 2: Find Unique Indicators
Look for indicators with **mostly white** around them.

**Example:**
```
momentum_rsi might have:
- Some red with other momentum indicators
- Mostly white with trend/volatility indicators

This means RSI is unique for momentum analysis
```

### Step 3: Identify Opposites
Look for **blue squares** - indicators that move opposite.

**Example:**
```
trend_vortex_ind_pos ↔ trend_vortex_ind_neg = Dark Blue

This makes sense - positive and negative vortex move opposite!
```

### Step 4: Build Your Strategy
Use this knowledge to:
- **Remove redundant indicators** (pick one from each red cluster)
- **Combine unique indicators** (use indicators from different groups)
- **Find confirmations** (use indicators that correlate well)

---

## 💡 Practical Applications

### For Strategy Building:

1. **Don't use redundant indicators**
   - If RSI and Stochastic RSI are 0.95 correlated, pick one
   - Using both doesn't add value

2. **Combine independent indicators**
   - Use indicators from different groups
   - Example: RSI (momentum) + MACD (trend) + ATR (volatility)

3. **Look for confirmations**
   - When multiple indicators agree (all red together), stronger signal
   - Example: RSI + MACD + OBV all bullish = strong buy signal

### For Understanding Relationships:

- **High positive correlation (0.8-1.0):** Indicators measure similar things
- **High negative correlation (-0.8 to -1.0):** Indicators are opposites
- **Low correlation (-0.3 to 0.3):** Indicators are independent

---

## 🔧 Tips for Better Reading

### 1. Zoom In
- The heatmap is large - zoom in to see specific areas
- Focus on one section at a time

### 2. Use the CSV File
- Open `correlation_matrix.csv` in Excel
- Search for specific indicators
- Sort by correlation value

### 3. Look for Patterns
- **Diagonal patterns** = indicators in same category
- **Blocks of red** = indicator groups
- **Scattered blue** = opposite relationships

### 4. Compare Stocks
- Run correlation analysis on multiple stocks
- Compare which indicators correlate differently
- Some relationships are stock-specific

---

## 📋 Common Questions

### Q: Why is the diagonal all red?
**A:** Each indicator is perfectly correlated with itself (1.0). This is normal - ignore it!

### Q: What's a "good" correlation?
**A:** 
- **> 0.7** = Strong relationship (useful for confirmation)
- **0.3-0.7** = Moderate relationship
- **< 0.3** = Weak relationship (independent)

### Q: Should I avoid highly correlated indicators?
**A:** 
- **For analysis:** Yes - they're redundant
- **For confirmation:** No - use them together for stronger signals

### Q: What if two indicators are -0.9 correlated?
**A:** They move in opposite directions. This is useful for:
- Confirming reversals
- Finding divergences
- Understanding market dynamics

---

## 🎯 Quick Reference

| Color | Correlation | Meaning | Use Case |
|-------|-------------|---------|----------|
| 🔴 Dark Red | +0.8 to +1.0 | Strong positive | Confirmation signals |
| 🟠 Light Red | +0.5 to +0.8 | Moderate positive | Supporting evidence |
| ⚪ White | -0.3 to +0.3 | No correlation | Independent indicators |
| 🟦 Light Blue | -0.5 to -0.8 | Moderate negative | Divergence signals |
| 🔵 Dark Blue | -0.8 to -1.0 | Strong negative | Opposite movements |

---

## 🚀 Next Steps

1. **Open the filtered heatmap** - easier to read
2. **Identify indicator groups** - find red clusters
3. **Pick unique indicators** - one from each group
4. **Build your strategy** - combine independent indicators
5. **Test it** - use the backtesting tools!

---

**Remember:** The heatmap shows **relationships**, not **causation**. Just because two indicators correlate doesn't mean one causes the other!

