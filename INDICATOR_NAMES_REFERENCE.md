# 📊 Technical Analysis Indicator Names Reference

## Where to Find Indicator Names

### 1. **README.md** (Complete List)
The main README file contains the complete list of all 43 indicators with descriptions:
- **Location**: `/Users/av/Downloads/dev mode/ta/README.md`
- **Lines**: 16-99
- Shows all indicators organized by category (Volume, Volatility, Trend, Momentum, Others)

### 2. **CSV Output Files** (Column Names)
Your analysis CSV files contain all indicator column names:
- **Location**: `output/HDFCBANK.NS_analysis.csv` (or any stock analysis file)
- **First row**: Contains all column names
- **Format**: `category_indicator` (e.g., `momentum_rsi`, `trend_macd`)

### 3. **Source Code Files**
Indicator classes and functions are defined in:
- `ta/volume.py` - Volume indicators
- `ta/volatility.py` - Volatility indicators  
- `ta/trend.py` - Trend indicators
- `ta/momentum.py` - Momentum indicators
- `ta/others.py` - Other indicators

---

## 📋 Complete Indicator List (As Column Names in CSV)

### Volume Indicators (9 indicators)
| CSV Column Name | Full Name | Description |
|----------------|-----------|-------------|
| `volume_adi` | Accumulation/Distribution Index | Money flow indicator |
| `volume_obv` | On-Balance Volume | Cumulative volume indicator |
| `volume_cmf` | Chaikin Money Flow | Money flow strength |
| `volume_fi` | Force Index | Price-volume momentum |
| `volume_em` | Ease of Movement | Price movement relative to volume |
| `volume_sma_em` | SMA Ease of Movement | Smoothed EoM |
| `volume_vpt` | Volume Price Trend | Volume-weighted price trend |
| `volume_vwap` | Volume Weighted Average Price | Average price weighted by volume |
| `volume_mfi` | Money Flow Index | Volume-weighted RSI |
| `volume_nvi` | Negative Volume Index | Smart money indicator |

### Volatility Indicators (4 indicators, multiple columns)
| CSV Column Name | Full Name | Description |
|----------------|-----------|-------------|
| `volatility_bbm` | Bollinger Bands Middle | 20-day moving average |
| `volatility_bbh` | Bollinger Bands High | Upper band |
| `volatility_bbl` | Bollinger Bands Low | Lower band |
| `volatility_bbw` | Bollinger Bands Width | Band width |
| `volatility_bbp` | Bollinger Bands % | Price position in bands |
| `volatility_bbhi` | BB High Indicator | Above upper band (0/1) |
| `volatility_bbli` | BB Low Indicator | Below lower band (0/1) |
| `volatility_kcc` | Keltner Channel Middle | Middle band |
| `volatility_kch` | Keltner Channel High | Upper band |
| `volatility_kcl` | Keltner Channel Low | Lower band |
| `volatility_kcw` | Keltner Channel Width | Band width |
| `volatility_kcp` | Keltner Channel % | Price position |
| `volatility_kchi` | KC High Indicator | Above upper (0/1) |
| `volatility_kcli` | KC Low Indicator | Below lower (0/1) |
| `volatility_dcl` | Donchian Channel Low | Lower band |
| `volatility_dch` | Donchian Channel High | Upper band |
| `volatility_dcm` | Donchian Channel Middle | Middle band |
| `volatility_dcw` | Donchian Channel Width | Band width |
| `volatility_dcp` | Donchian Channel % | Price position |
| `volatility_atr` | Average True Range | Volatility measure |
| `volatility_ui` | Ulcer Index | Downside volatility |

### Trend Indicators (15 indicators, multiple columns)
| CSV Column Name | Full Name | Description |
|----------------|-----------|-------------|
| `trend_macd` | MACD Line | Moving Average Convergence Divergence |
| `trend_macd_signal` | MACD Signal | Signal line |
| `trend_macd_diff` | MACD Histogram | MACD - Signal |
| `trend_sma_fast` | SMA Fast | 12-day Simple Moving Average |
| `trend_sma_slow` | SMA Slow | 26-day Simple Moving Average |
| `trend_ema_fast` | EMA Fast | 12-day Exponential Moving Average |
| `trend_ema_slow` | EMA Slow | 26-day Exponential Moving Average |
| `trend_vortex_ind_pos` | Vortex Indicator Positive | Positive trend strength |
| `trend_vortex_ind_neg` | Vortex Indicator Negative | Negative trend strength |
| `trend_vortex_ind_diff` | Vortex Indicator Diff | Difference |
| `trend_trix` | TRIX | Triple Exponential Average |
| `trend_mass_index` | Mass Index | Volatility indicator |
| `trend_dpo` | Detrended Price Oscillator | Price vs trend |
| `trend_kst` | KST Oscillator | Know Sure Thing |
| `trend_kst_sig` | KST Signal | Signal line |
| `trend_kst_diff` | KST Difference | KST - Signal |
| `trend_ichimoku_conv` | Ichimoku Conversion | Conversion line |
| `trend_ichimoku_base` | Ichimoku Base | Base line |
| `trend_ichimoku_a` | Ichimoku A | Leading span A |
| `trend_ichimoku_b` | Ichimoku B | Leading span B |
| `trend_stc` | Schaff Trend Cycle | Trend cycle indicator |
| `trend_adx` | ADX | Average Directional Index |
| `trend_adx_pos` | ADX Positive | Positive directional movement |
| `trend_adx_neg` | ADX Negative | Negative directional movement |
| `trend_cci` | Commodity Channel Index | Price deviation from average |
| `trend_visual_ichimoku_a` | Ichimoku Visual A | Visual leading span A |
| `trend_visual_ichimoku_b` | Ichimoku Visual B | Visual leading span B |
| `trend_aroon_up` | Aroon Up | Upward trend strength |
| `trend_aroon_down` | Aroon Down | Downward trend strength |
| `trend_aroon_ind` | Aroon Indicator | Combined Aroon |
| `trend_psar_up` | Parabolic SAR Up | Stop and reverse up |
| `trend_psar_down` | Parabolic SAR Down | Stop and reverse down |
| `trend_psar_up_indicator` | PSAR Up Indicator | Above PSAR (0/1) |
| `trend_psar_down_indicator` | PSAR Down Indicator | Below PSAR (0/1) |

### Momentum Indicators (11 indicators, multiple columns)
| CSV Column Name | Full Name | Description |
|----------------|-----------|-------------|
| `momentum_rsi` | Relative Strength Index | Momentum oscillator (0-100) |
| `momentum_stoch_rsi` | Stochastic RSI | Stochastic of RSI |
| `momentum_stoch_rsi_k` | StochRSI K | %K line |
| `momentum_stoch_rsi_d` | StochRSI D | %D line |
| `momentum_tsi` | True Strength Index | Momentum with double smoothing |
| `momentum_uo` | Ultimate Oscillator | Multi-timeframe momentum |
| `momentum_stoch` | Stochastic Oscillator | %K line |
| `momentum_stoch_signal` | Stochastic Signal | %D signal line |
| `momentum_wr` | Williams %R | Momentum oscillator (-100 to 0) |
| `momentum_ao` | Awesome Oscillator | Momentum using median price |
| `momentum_roc` | Rate of Change | Price change percentage |
| `momentum_ppo` | Percentage Price Oscillator | MACD as percentage |
| `momentum_ppo_signal` | PPO Signal | Signal line |
| `momentum_ppo_hist` | PPO Histogram | PPO - Signal |
| `momentum_pvo` | Percentage Volume Oscillator | Volume MACD as percentage |
| `momentum_pvo_signal` | PVO Signal | Signal line |
| `momentum_pvo_hist` | PVO Histogram | PVO - Signal |
| `momentum_kama` | KAMA | Kaufman's Adaptive Moving Average |

### Other Indicators (3 indicators)
| CSV Column Name | Full Name | Description |
|----------------|-----------|-------------|
| `others_dr` | Daily Return | Daily price change % |
| `others_dlr` | Daily Log Return | Logarithmic daily return |
| `others_cr` | Cumulative Return | Total return from start |

---

## 🔍 Quick Ways to See All Indicators

### Method 1: Check CSV Header
```bash
head -1 output/HDFCBANK.NS_analysis.csv
```
Shows all column names (indicators) in your analysis file.

### Method 2: Python Code
```python
import pandas as pd
df = pd.read_csv('output/HDFCBANK.NS_analysis.csv', skiprows=2, nrows=1)
print(list(df.columns))
```

### Method 3: Read README.md
```bash
cat README.md | grep -A 100 "The library has implemented"
```

---

## 📝 Indicator Naming Convention

All indicators follow this pattern:
```
category_indicator
```

**Categories:**
- `volume_` - Volume-based indicators
- `volatility_` - Volatility indicators
- `trend_` - Trend indicators
- `momentum_` - Momentum indicators
- `others_` - Other indicators

**Examples:**
- `momentum_rsi` = RSI (momentum category)
- `trend_macd` = MACD (trend category)
- `volatility_bbm` = Bollinger Bands Middle (volatility category)

---

## 🎯 Most Commonly Used Indicators

### For Trading Signals:
- `momentum_rsi` - RSI (most popular)
- `trend_macd` - MACD line
- `trend_macd_signal` - MACD signal
- `trend_macd_diff` - MACD histogram
- `volatility_bbh` - Bollinger upper band
- `volatility_bbl` - Bollinger lower band
- `trend_ema_fast` - Fast EMA
- `trend_ema_slow` - Slow EMA
- `momentum_wr` - Williams %R

### For Analysis:
- `trend_adx` - Trend strength
- `volatility_atr` - Volatility measure
- `volume_obv` - Volume trend
- `volume_cmf` - Money flow
- `trend_cci` - Commodity Channel Index

---

## 📚 Full Documentation

For detailed information about each indicator:
- **Online Docs**: https://technical-analysis-library-in-python.readthedocs.io/en/latest/
- **README.md**: Complete list with links
- **Source Code**: See implementation in `ta/` folder

---

## 💡 Using Indicators in Your Code

### Access in DataFrame:
```python
df['momentum_rsi']  # RSI values
df['trend_macd']    # MACD values
df['volatility_bbh'] # Bollinger upper band
```

### In Backtesting:
```python
# Buy when RSI < 30
buy_signal = df['momentum_rsi'] < 30

# Sell when price > Bollinger upper band
sell_signal = df['Close'] > df['volatility_bbh']
```

---

**Total: 43 indicators generating 85+ columns in your CSV files!**

