# Why Are There So Many Negative Values in Technical Indicators?

## This is COMPLETELY NORMAL! ✅

Many technical indicators are **designed** to have negative values. They indicate **bearish signals, downward trends, or price declines**. Here's why:

---

## Indicators That Are **SUPPOSED** to Be Negative:

### 1. **Volume Indicators**

#### `volume_obv` (On-Balance Volume)
- **Negative = Selling pressure** (more volume on down days)
- **Positive = Buying pressure** (more volume on up days)
- **Example**: `-10,434,686` means cumulative selling volume exceeds buying volume

#### `volume_cmf` (Chaikin Money Flow)
- **Range**: -1 to +1
- **Negative = Money flowing out** (bearish)
- **Positive = Money flowing in** (bullish)
- **Example**: `-0.18` means 18% more selling pressure

#### `volume_fi` (Force Index)
- **Negative = Downward price pressure**
- **Positive = Upward price pressure**
- **Example**: `-14,373,072` means strong downward momentum

#### `volume_em` (Ease of Movement)
- **Negative = Price moving down easily** (low volume, price falling)
- **Positive = Price moving up easily**
- **Example**: `-1,349.65` means price is falling with relative ease

#### `volume_vpt` (Volume Price Trend)
- **Negative = Cumulative negative price-volume relationship**
- Shows when volume confirms price declines
- **Example**: `-115,689` means cumulative bearish volume-price trend

---

### 2. **Trend Indicators**

#### `trend_macd` (MACD Line)
- **Negative = Bearish momentum** (fast MA below slow MA)
- **Positive = Bullish momentum** (fast MA above slow MA)
- **Example**: `-1.54` means bearish trend

#### `trend_macd_diff` (MACD Histogram)
- **Negative = MACD below signal line** (bearish)
- **Positive = MACD above signal line** (bullish)
- **Example**: `-1.25` means bearish divergence

#### `trend_dpo` (Detrended Price Oscillator)
- **Negative = Price below trend**
- **Positive = Price above trend**
- **Example**: `-2.45` means price is below its trend

#### `trend_kst` (KST Oscillator)
- **Negative = Bearish momentum**
- **Positive = Bullish momentum**
- **Example**: `-179.46` means very bearish momentum

#### `trend_kst_diff` (KST Difference)
- **Negative = KST below signal** (bearish)
- **Example**: `-1.16` means bearish KST signal

#### `trend_cci` (Commodity Channel Index)
- **Range**: Typically -200 to +200
- **Negative = Below average price** (bearish)
- **Positive = Above average price** (bullish)
- **Example**: `-79.85` means price is below average

---

### 3. **Momentum Indicators**

#### `momentum_wr` (Williams %R)
- **ALWAYS NEGATIVE!** Range: -100 to 0
- **-100 to -80 = Oversold** (potential buy)
- **-20 to 0 = Overbought** (potential sell)
- **Example**: `-79.85` means oversold (bullish signal!)

#### `momentum_ao` (Awesome Oscillator)
- **Negative = Bearish momentum**
- **Positive = Bullish momentum**
- **Example**: `-39.27` means bearish momentum

#### `momentum_roc` (Rate of Change)
- **Negative = Price declining** (percentage change)
- **Positive = Price rising**
- **Example**: `-2.52%` means price dropped 2.52%

#### `momentum_tsi` (True Strength Index)
- **Negative = Bearish momentum**
- **Positive = Bullish momentum**
- **Example**: `-21.57` means bearish momentum

---

### 4. **Return Indicators**

#### `others_dr` (Daily Return)
- **Negative = Price went DOWN today**
- **Positive = Price went UP today**
- **Example**: `-2.73%` means stock dropped 2.73% today

#### `others_dlr` (Daily Log Return)
- **Negative = Logarithmic price decline**
- **Example**: `-2.77%` means log return of -2.77%

---

## What Negative Values Tell You:

### 🐻 **Bearish Signals** (Negative = Bad for buying)
- MACD negative = Downtrend
- Volume indicators negative = Selling pressure
- Returns negative = Price falling

### 🐂 **Bullish Signals** (Negative can be good!)
- Williams %R at -90 = **OVERSOLD** = Potential buy opportunity!
- RSI below 30 = **OVERSOLD** = Potential buy opportunity!

---

## Example from Your HDFC Data:

Looking at row 4 (2020-01-01):
- `trend_macd` = `-17.33` → **Bearish trend**
- `trend_kst` = `-179.46` → **Very bearish momentum**
- `momentum_wr` = `-79.85` → **Oversold** (potential buy signal!)
- `others_dr` = `0.0` → No change (first day)

Looking at row 6 (2020-01-03):
- `volume_obv` = `-1,044,686` → **Selling pressure**
- `volume_cmf` = `0.05` → Slight buying pressure
- `trend_macd` = `-0.15` → Slight bearish trend
- `others_dr` = `-1.43%` → **Price dropped 1.43%**

---

## Key Takeaway:

**Negative values are NOT errors!** They're telling you:
1. **When prices are falling** (returns, ROC)
2. **When selling pressure exists** (volume indicators)
3. **When trends are bearish** (MACD, KST)
4. **When stocks are oversold** (Williams %R, RSI)

These are **valuable signals** for trading decisions!

---

## Indicators That Should NOT Be Negative:

These should always be positive:
- `Close`, `High`, `Low`, `Open` (prices)
- `Volume` (trading volume)
- `momentum_rsi` (0-100 range)
- `volatility_bbm` (Bollinger middle band = price)
- Most moving averages (SMA, EMA)

If you see negative values in these, **then** there might be a data issue.

