"""
Strategy Backtesting Tool

Backtests specific trading strategies using technical indicators.
Currently implements 3 cash-secured puts strategies for Indian stocks.

Usage:
    python3 backtest_strategies.py [stock_symbol] [--strategy N]
    
Examples:
    python3 backtest_strategies.py WIPRO.NS
    python3 backtest_strategies.py WIPRO.NS --strategy 1
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

OUTPUT_DIR = "output"
BASE_ANALYSIS_DIR = "analysis_results"


def get_ticker_analysis_dir(stock_symbol):
    """Get ticker-specific analysis directory."""
    ticker_dir = os.path.join(BASE_ANALYSIS_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def load_stock_data(stock_symbol):
    """Load stock analysis data."""
    file_path = os.path.join(OUTPUT_DIR, f"{stock_symbol}_analysis.csv")
    
    if not os.path.exists(file_path):
        print(f"❌ Analysis file not found: {file_path}")
        print(f"   Please run: python3 analyze_stock.py {stock_symbol}")
        return None
    
    try:
        print(f"🔄 Loading data for {stock_symbol}...")
        df = pd.read_csv(file_path, header=0, skiprows=[1, 2])
        first_col = df.columns[0]
        df = df.rename(columns={first_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        print(f"✅ Loaded {len(df)} days of data")
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None


def strategy_1_high_premium_low_risk(df):
    """
    Combo #1: "High Premium, Low Risk" Setup
    
    Rules:
    - Price is above slow EMA (trend_ema_slow) → stock in long-term uptrend
    - Price is near or slightly below fast EMA (trend_ema_fast) → small pullback
    - RSI between 35–45 → small dip but not heavy selling
    - BBW increases → volatility rising → premium increases
    """
    signals = pd.Series(0, index=df.index)
    
    # Check all conditions
    price_above_slow_ema = df['Close'] > df['trend_ema_slow']
    # Price near or slightly below fast EMA (within 3% range)
    price_near_fast_ema = (df['Close'] <= df['trend_ema_fast'] * 1.03) & (df['Close'] >= df['trend_ema_fast'] * 0.97)
    rsi_ok = (df['momentum_rsi'] >= 35) & (df['momentum_rsi'] <= 45)
    bbw_increasing = df['volatility_bbw'] > df['volatility_bbw'].shift(1)
    
    # All conditions must be true
    buy_signal = price_above_slow_ema & price_near_fast_ema & rsi_ok & bbw_increasing
    
    signals[buy_signal] = 1  # 1 = Sell Put (entry signal)
    
    return signals, "High Premium, Low Risk"


def strategy_2_oversold_reversal(df):
    """
    Combo #2: "Oversold Reversal" Setup
    
    Rules:
    - MACD histogram turning upward (trend_macd_diff increasing)
    - Stochastic RSI < 20 but curling upward
    - Williams %R < -80 but rising
    """
    signals = pd.Series(0, index=df.index)
    
    # MACD histogram turning upward
    macd_hist_rising = df['trend_macd_diff'] > df['trend_macd_diff'].shift(1)
    macd_hist_positive_trend = df['trend_macd_diff'] > df['trend_macd_diff'].shift(3)
    
    # Stochastic RSI < 20 but curling upward
    stoch_rsi_oversold = df['momentum_stoch_rsi'] < 20
    stoch_rsi_rising = df['momentum_stoch_rsi'] > df['momentum_stoch_rsi'].shift(1)
    
    # Williams %R < -80 but rising
    williams_oversold = df['momentum_wr'] < -80
    williams_rising = df['momentum_wr'] > df['momentum_wr'].shift(1)
    
    # All conditions
    buy_signal = macd_hist_rising & macd_hist_positive_trend & stoch_rsi_oversold & stoch_rsi_rising & williams_oversold & williams_rising
    
    signals[buy_signal] = 1
    
    return signals, "Oversold Reversal"


def strategy_3_premium_maximizer(df):
    """
    Combo #3: "Premium Maximizer" Setup
    
    Rules:
    - ATR high (above median) → high absolute volatility
    - BBW expanding → higher relative volatility
    - ADX < 25 → trend is weak → safer to sell puts
    - ROC stabilizing above 0% → momentum flattening out
    """
    signals = pd.Series(0, index=df.index)
    
    # ATR high (above median)
    atr_median = df['volatility_atr'].median()
    atr_high = df['volatility_atr'] > atr_median
    
    # BBW expanding
    bbw_expanding = df['volatility_bbw'] > df['volatility_bbw'].shift(1)
    
    # ADX < 25 (weak trend)
    adx_weak = df['trend_adx'] < 25
    
    # ROC stabilizing above 0% (between 0 and 5%)
    roc_stable = (df['momentum_roc'] >= 0) & (df['momentum_roc'] <= 5)
    
    # All conditions
    buy_signal = atr_high & bbw_expanding & adx_weak & roc_stable
    
    signals[buy_signal] = 1
    
    return signals, "Premium Maximizer"


def backtest_strategy(df, signals, strategy_name, initial_capital=100000):
    """
    Backtest a cash-secured puts strategy.
    
    For cash-secured puts:
    - When signal = 1, we "sell" a put (simulate by buying stock at strike price)
    - We hold until next signal or exit condition
    - Track returns
    """
    portfolio_value = initial_capital
    positions = []
    trades = []
    in_position = False
    entry_price = 0
    entry_date = None
    
    for date in df.index:
        signal = signals.loc[date]
        current_price = df.loc[date, 'Close']
        
        if signal == 1 and not in_position:
            # Enter position (sell put = buy stock at current price)
            entry_price = current_price
            entry_date = date
            in_position = True
            shares = portfolio_value / entry_price
            positions.append({
                'entry_date': date,
                'entry_price': entry_price,
                'shares': shares
            })
            
        elif in_position:
            # Check exit conditions
            # Exit after 30 days or if price moves significantly
            days_held = (date - entry_date).days
            
            # Exit conditions:
            # 1. Hold for 30 days (typical monthly option)
            # 2. Price moves up 5% (take profit)
            # 3. Price moves down 10% (stop loss)
            price_change_pct = ((current_price - entry_price) / entry_price) * 100
            
            should_exit = (days_held >= 30) or (price_change_pct >= 5) or (price_change_pct <= -10)
            
            if should_exit:
                # Exit position
                exit_price = current_price
                pnl_pct = price_change_pct
                pnl_absolute = (exit_price - entry_price) * shares
                portfolio_value = portfolio_value + pnl_absolute
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'shares': shares,
                    'pnl_pct': pnl_pct,
                    'pnl_absolute': pnl_absolute,
                    'days_held': days_held
                })
                
                in_position = False
                entry_price = 0
                entry_date = None
    
    # Close any remaining positions
    if in_position and len(positions) > 0:
        last_pos = positions[-1]
        exit_price = df.iloc[-1]['Close']
        pnl_pct = ((exit_price - last_pos['entry_price']) / last_pos['entry_price']) * 100
        pnl_absolute = (exit_price - last_pos['entry_price']) * last_pos['shares']
        portfolio_value = portfolio_value + pnl_absolute
        
        trades.append({
            'entry_date': last_pos['entry_date'],
            'exit_date': df.index[-1],
            'entry_price': last_pos['entry_price'],
            'exit_price': exit_price,
            'shares': last_pos['shares'],
            'pnl_pct': pnl_pct,
            'pnl_absolute': pnl_absolute,
            'days_held': (df.index[-1] - last_pos['entry_date']).days
        })
    
    # Calculate metrics
    total_return = ((portfolio_value - initial_capital) / initial_capital) * 100
    num_trades = len(trades)
    
    if num_trades > 0:
        winning_trades = [t for t in trades if t['pnl_pct'] > 0]
        win_rate = (len(winning_trades) / num_trades) * 100
        avg_return = np.mean([t['pnl_pct'] for t in trades])
        avg_days = np.mean([t['days_held'] for t in trades])
    else:
        win_rate = 0
        avg_return = 0
        avg_days = 0
    
    # Buy and hold comparison (annualized for long periods)
    total_days = (df.index[-1] - df.index[0]).days
    years = total_days / 365.25
    buy_hold_total = ((df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close']) * 100
    buy_hold_return = buy_hold_total  # Keep total return for comparison
    
    return {
        'strategy_name': strategy_name,
        'initial_capital': initial_capital,
        'final_value': portfolio_value,
        'total_return': total_return,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'avg_return_per_trade': avg_return,
        'avg_days_held': avg_days,
        'buy_hold_return': buy_hold_return,
        'trades': trades
    }


def print_results(results):
    """Print backtest results in a formatted way."""
    print("\n" + "="*80)
    print(f"📊 BACKTEST RESULTS: {results['strategy_name']}")
    print("="*80)
    
    print(f"\n💰 PERFORMANCE")
    print(f"   Initial Capital:     ₹{results['initial_capital']:>12,.2f}")
    print(f"   Final Portfolio:     ₹{results['final_value']:>12,.2f}")
    print(f"   Total Return:        {results['total_return']:>12.2f}%")
    
    print(f"\n📈 COMPARISON")
    print(f"   Buy-and-Hold:        {results['buy_hold_return']:>12.2f}%")
    difference = results['total_return'] - results['buy_hold_return']
    symbol = "✅" if difference > 0 else "❌"
    print(f"   Strategy vs Hold:    {difference:>12.2f}% {symbol}")
    
    print(f"\n📊 TRADE STATISTICS")
    print(f"   Number of Trades:    {results['num_trades']:>12}")
    print(f"   Win Rate:            {results['win_rate']:>12.2f}%")
    print(f"   Avg Return/Trade:    {results['avg_return_per_trade']:>12.2f}%")
    print(f"   Avg Days Held:       {results['avg_days_held']:>12.1f}")
    
    if results['trades']:
        print(f"\n🔄 RECENT TRADES (Last 5)")
        print("-"*80)
        recent_trades = results['trades'][-5:]
        for trade in recent_trades:
            pnl_symbol = "✅" if trade['pnl_pct'] > 0 else "❌"
            print(f"   {trade['entry_date'].date()} → {trade['exit_date'].date()}  "
                  f"Entry: ₹{trade['entry_price']:.2f}  Exit: ₹{trade['exit_price']:.2f}  "
                  f"Return: {trade['pnl_pct']:.2f}% {pnl_symbol}  ({trade['days_held']} days)")
    
    print("="*80)


def compare_strategies(all_results):
    """Compare multiple strategies side by side."""
    print("\n" + "="*80)
    print("🏆 STRATEGY COMPARISON")
    print("="*80)
    
    print(f"\n{'Strategy':<30} {'Return %':>12} {'Trades':>8} {'Win Rate %':>12} {'vs Buy-Hold':>12}")
    print("-"*80)
    
    for result in all_results:
        vs_hold = result['total_return'] - result['buy_hold_return']
        vs_symbol = "✅" if vs_hold > 0 else "❌"
        print(f"{result['strategy_name']:<30} {result['total_return']:>11.2f}% "
              f"{result['num_trades']:>8} {result['win_rate']:>11.2f}% "
              f"{vs_hold:>+11.2f}% {vs_symbol}")
    
    # Find best strategy
    best = max(all_results, key=lambda x: x['total_return'])
    print("\n" + "="*80)
    print(f"🥇 BEST STRATEGY: {best['strategy_name']} ({best['total_return']:.2f}% return)")
    print("="*80)


def main():
    """Main function."""
    print("\n" + "="*80)
    print("🎯 CASH-SECURED PUTS STRATEGY BACKTESTER")
    print("="*80)
    
    # Get stock symbol
    if len(sys.argv) > 1:
        stock_symbol = sys.argv[1].upper()
        if not stock_symbol.endswith('.NS'):
            stock_symbol += '.NS'
    else:
        stock_symbol = input("\nEnter stock symbol (e.g., WIPRO.NS): ").strip().upper()
        if not stock_symbol.endswith('.NS'):
            stock_symbol += '.NS'
    
    # Check which strategies to run
    strategy_num = None
    if '--strategy' in sys.argv:
        try:
            idx = sys.argv.index('--strategy')
            strategy_num = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            pass
    
    # Load data
    df = load_stock_data(stock_symbol)
    if df is None:
        return
    
    # Check required indicators
    required_indicators = [
        'trend_ema_fast', 'trend_ema_slow', 'momentum_rsi', 'volatility_bbw',
        'trend_macd_diff', 'momentum_stoch_rsi', 'momentum_wr',
        'volatility_atr', 'trend_adx', 'momentum_roc'
    ]
    
    missing = [ind for ind in required_indicators if ind not in df.columns]
    if missing:
        print(f"\n❌ Missing required indicators: {missing}")
        print("   Please ensure the analysis file has all technical indicators.")
        return
    
    print(f"\n✅ All required indicators found")
    
    # Define strategies
    strategies = [
        (strategy_1_high_premium_low_risk, "Strategy 1"),
        (strategy_2_oversold_reversal, "Strategy 2"),
        (strategy_3_premium_maximizer, "Strategy 3")
    ]
    
    # Run backtests
    all_results = []
    
    for i, (strategy_func, strategy_label) in enumerate(strategies, 1):
        if strategy_num is None or strategy_num == i:
            print(f"\n{'='*80}")
            print(f"🔄 Backtesting {strategy_label}: {strategy_func.__doc__.split(chr(10))[0]}")
            print(f"{'='*80}")
            
            signals, strategy_name = strategy_func(df)
            num_signals = signals.sum()
            print(f"   Found {num_signals} entry signals")
            
            if num_signals > 0:
                results = backtest_strategy(df, signals, strategy_name)
                print_results(results)
                all_results.append(results)
            else:
                print(f"   ⚠️  No signals generated for this strategy")
    
    # Compare strategies
    if len(all_results) > 1:
        compare_strategies(all_results)
    
    # Save results in ticker-specific directory
    if all_results:
        ticker_dir = get_ticker_analysis_dir(stock_symbol)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(ticker_dir, f"strategy_backtest_{timestamp}.csv")
        
        # Save summary
        summary_df = pd.DataFrame([{
            'Strategy': r['strategy_name'],
            'Total_Return_%': r['total_return'],
            'Num_Trades': r['num_trades'],
            'Win_Rate_%': r['win_rate'],
            'Avg_Return_%': r['avg_return_per_trade'],
            'vs_BuyHold_%': r['total_return'] - r['buy_hold_return']
        } for r in all_results])
        
        summary_df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        print(f"📁 All results organized in: {ticker_dir}/")


if __name__ == "__main__":
    main()

