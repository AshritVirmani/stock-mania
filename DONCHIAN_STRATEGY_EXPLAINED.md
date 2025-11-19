# What is the "Optimized Strategy" in the MCPT?

## The Strategy: Donchian Breakout

The **Donchian Breakout Strategy** is a trend-following trading system that:

1. **Calculates two bands (channels)** around the price:
   - **Upper Band** = Highest price over the last N days
   - **Lower Band** = Lowest price over the last N days
   - N is called the "lookback period"

2. **Generates trading signals**:
   - **BUY Signal (+1)**: When current price breaks **above** the Upper Band
   - **SELL Signal (-1)**: When current price breaks **below** the Lower Band
   - **HOLD (0)**: When price is between the bands

3. **Trades based on signals**:
   - When signal = +1: Go LONG (buy and hold)
   - When signal = -1: Go SHORT (sell and hold short position)
   - The position is held until the next signal

## What Does "Optimized" Mean?

The strategy has **one parameter**: the **lookback period** (N days).

### Optimization Process:

1. **On Training Data** (e.g., first 2 years):
   - Test lookback periods from 12 to 169 days
   - For each lookback, calculate the **Profit Factor**:
     - Profit Factor = (Sum of winning trades) / (Sum of losing trades)
   - Pick the lookback period with the **highest profit factor**

2. **Example**:
   - Lookback = 20 days → Profit Factor = 1.2
   - Lookback = 50 days → Profit Factor = 1.8
   - Lookback = 78 days → Profit Factor = 1.77 ← **BEST**
   - **Result**: Use lookback = 78 days for this period

3. **On Test Data** (next 6 months):
   - Use the optimized lookback period (e.g., 78 days)
   - Generate signals and calculate returns
   - This is the **"Real Optimized Strategy"** (red line)

## What Are the "Permuted Strategies" (Grey Lines)?

The permuted strategies are **the same strategy** but with a crucial difference:

- **Same lookback period** (e.g., 78 days)
- **Same signals** (same buy/sell timing)
- **BUT**: The returns are **randomly shuffled**

### Why Shuffle Returns?

Shuffling returns breaks the relationship between:
- When the strategy says "BUY" 
- What actually happened to the price

This tests: **"What if the strategy was just luck?"**

If the strategy has real edge:
- **Real Strategy** (red): Signals match actual price movements → High returns
- **Permuted Strategies** (grey): Signals don't match shuffled returns → Low returns (~0)

## Visual Interpretation

In the graph:

- **Red Line**: Your optimized Donchian strategy with real signal-return relationships
- **Grey Lines**: Same strategy but with shuffled returns (testing if it's just luck)
- **White/Dark Grey Line**: Average of all permuted strategies

**If red line is above grey cluster** → Strategy has real edge (not just luck)
**If red line is in grey cluster** → Strategy might just be luck

## Summary

**"Real Optimized Strategy"** = Donchian Breakout with the best lookback period found through optimization, using real price data

**"Permuted Strategies"** = Same strategy, same signals, but returns are shuffled to test if results are due to luck or real predictive power

The outperformance shows that the Donchian breakout signals have **genuine predictive power** for WIPRO.NS stock, not just random luck!

