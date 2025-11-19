"""
Simple Backtesting Example using Technical Analysis Indicators

This demonstrates how to use the TA library indicators to create trading signals
and backtest a simple strategy.

NOTE: This is a SIMPLE backtest example (RSI/MACD strategy).
For more advanced backtesting with statistical significance testing, see:
- donchian_mcpt_backtest.py (Standard Donchian with MCPT)
- donchian_enhanced_backtest.py (Enhanced Donchian with regime filtering)

This example is useful for:
- Learning how to create trading signals
- Understanding basic backtesting concepts
- Quick strategy testing

For production/robust backtesting, use the Donchian MCPT backtests instead.
"""

import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.utils import dropna


def create_trading_signals(df):
    """
    Create buy/sell signals based on technical indicators.
    
    Example Strategy: 
    - BUY when: RSI < 30 (oversold) AND MACD crosses above signal
    - SELL when: RSI > 70 (overbought) OR MACD crosses below signal
    """
    df = df.copy()
    
    # Initialize signal column
    df['signal'] = 0  # 0 = hold, 1 = buy, -1 = sell
    df['position'] = 0  # Track current position (1 = long, 0 = no position)
    
    # Strategy 1: RSI-based signals
    # Buy when RSI < 30 (oversold)
    buy_condition_1 = df['momentum_rsi'] < 30
    
    # Sell when RSI > 70 (overbought)
    sell_condition_1 = df['momentum_rsi'] > 70
    
    # Strategy 2: MACD crossover
    # Buy when MACD crosses above signal line
    df['macd_cross_above'] = (
        (df['trend_macd'] > df['trend_macd_signal']) & 
        (df['trend_macd'].shift(1) <= df['trend_macd_signal'].shift(1))
    )
    
    # Sell when MACD crosses below signal line
    df['macd_cross_below'] = (
        (df['trend_macd'] < df['trend_macd_signal']) & 
        (df['trend_macd'].shift(1) >= df['trend_macd_signal'].shift(1))
    )
    
    # Combined strategy: Buy on RSI oversold OR MACD bullish crossover
    df.loc[buy_condition_1 | df['macd_cross_above'], 'signal'] = 1
    
    # Sell on RSI overbought OR MACD bearish crossover
    df.loc[sell_condition_1 | df['macd_cross_below'], 'signal'] = -1
    
    return df


def backtest_strategy(df, initial_capital=100000):
    """
    Simulate trading based on signals and calculate returns.
    
    Args:
        df: DataFrame with 'Close', 'signal', and indicator columns
        initial_capital: Starting capital in currency units
    
    Returns:
        DataFrame with backtest results and performance metrics
    """
    df = df.copy()
    
    # Initialize tracking variables
    capital = float(initial_capital)
    shares = 0.0
    df['capital'] = float(initial_capital)
    df['shares'] = 0.0
    df['portfolio_value'] = float(initial_capital)
    df['returns'] = 0.0
    
    # Track trades
    trades = []
    
    for i in range(1, len(df)):
        current_price = df.iloc[i]['Close']
        signal = df.iloc[i]['signal']
        prev_portfolio_value = df.iloc[i-1]['portfolio_value']
        
        # Execute buy signal
        if signal == 1 and shares == 0:  # Buy only if not already holding
            shares = capital / current_price
            capital = 0
            trades.append({
                'date': df.index[i],
                'action': 'BUY',
                'price': current_price,
                'shares': shares
            })
        
        # Execute sell signal
        elif signal == -1 and shares > 0:  # Sell only if holding
            capital = shares * current_price
            trades.append({
                'date': df.index[i],
                'action': 'SELL',
                'price': current_price,
                'shares': shares
            })
            shares = 0
        
        # Update portfolio value
        if shares > 0:
            portfolio_value = shares * current_price
        else:
            portfolio_value = capital
        
        df.iloc[i, df.columns.get_loc('capital')] = float(capital)
        df.iloc[i, df.columns.get_loc('shares')] = float(shares)
        df.iloc[i, df.columns.get_loc('portfolio_value')] = float(portfolio_value)
        
        # Calculate daily returns
        if prev_portfolio_value > 0:
            df.iloc[i, df.columns.get_loc('returns')] = (
                (portfolio_value - prev_portfolio_value) / prev_portfolio_value
            )
    
    # Final portfolio value
    final_value = df.iloc[-1]['portfolio_value']
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    
    # Calculate metrics
    returns_series = df['returns'].dropna()
    
    if len(returns_series) > 0:
        sharpe_ratio = (returns_series.mean() / returns_series.std()) * np.sqrt(252) if returns_series.std() > 0 else 0
        max_drawdown = ((df['portfolio_value'] / df['portfolio_value'].expanding().max()) - 1).min() * 100
    else:
        sharpe_ratio = 0
        max_drawdown = 0
    
    # Print results
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    print(f"Initial Capital: ₹{initial_capital:,.2f}")
    print(f"Final Portfolio Value: ₹{final_value:,.2f}")
    print(f"Total Return: {total_return:.2f}%")
    print(f"Number of Trades: {len(trades)}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Maximum Drawdown: {max_drawdown:.2f}%")
    print("="*60)
    
    # Compare with buy-and-hold
    buy_hold_return = ((df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close']) * 100
    print(f"\nBuy-and-Hold Return: {buy_hold_return:.2f}%")
    print(f"Strategy vs Buy-Hold: {total_return - buy_hold_return:.2f}%")
    
    return df, trades


def example_backtest():
    """
    Example: Load stock data, add indicators, create signals, and backtest.
    """
    # Load your analyzed stock data (from analyze_indian_stocks.py output)
    # Or load fresh data and add indicators
    print("Loading stock data...")
    
    # For this example, we'll assume you have a CSV file
    # In practice, you'd load from your output directory or fetch fresh data
    import sys
    stock_file = 'output/HDFCBANK.NS_analysis.csv'
    if len(sys.argv) > 1:
        stock_file = sys.argv[1]
        if not stock_file.startswith('output/'):
            stock_file = f'output/{stock_file}_analysis.csv'
    
    try:
        # The CSV has a multi-row header structure
        # Row 1: Column names (Price, Close, High, etc.) - but first column is actually dates
        # Row 2: Ticker info
        # Row 3: "Date" label
        # Row 4+: Actual data
        df = pd.read_csv(stock_file, header=0, skiprows=[1, 2])
        # The first column is actually dates, rename it
        first_col = df.columns[0]
        df = df.rename(columns={first_col: 'Date'})
        # Set Date as index
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        print(f"Loaded {len(df)} rows of data")
        print(f"Date range: {df.index.min()} to {df.index.max()}")
        print(f"Sample columns: {list(df.columns[:5])}")
    except FileNotFoundError:
        print("ERROR: Please run analyze_indian_stocks.py first to generate analysis files")
        print("Or modify this script to fetch data directly using yfinance")
        return
    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Ensure we have the required columns
    required_cols = ['Close', 'momentum_rsi', 'trend_macd', 'trend_macd_signal']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        print("Make sure the data has been processed with add_all_ta_features()")
        return
    
    # Create trading signals
    print("\nCreating trading signals...")
    df = create_trading_signals(df)
    
    # Count signals
    buy_signals = (df['signal'] == 1).sum()
    sell_signals = (df['signal'] == -1).sum()
    print(f"Buy signals: {buy_signals}")
    print(f"Sell signals: {sell_signals}")
    
    # Run backtest
    print("\nRunning backtest...")
    df_results, trades = backtest_strategy(df, initial_capital=100000)
    
    # Save results
    output_file = 'backtest_results.csv'
    df_results[['Close', 'signal', 'momentum_rsi', 'trend_macd', 
                'trend_macd_signal', 'portfolio_value', 'returns']].to_csv(output_file)
    print(f"\nResults saved to {output_file}")
    
    return df_results, trades


if __name__ == "__main__":
    example_backtest()

