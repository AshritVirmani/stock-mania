"""
Interactive Backtesting Tool
User-friendly interface for testing trading strategies on Indian stocks
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from ta import add_all_ta_features
from ta.utils import dropna


class InteractiveBacktester:
    def __init__(self):
        self.output_dir = "output"
        self.available_stocks = []
        self.df = None
        self.results = None
        
    def scan_available_stocks(self):
        """Scan output directory for available stock analysis files"""
        if not os.path.exists(self.output_dir):
            print(f"❌ Output directory '{self.output_dir}' not found!")
            print("   Please run analyze_indian_stocks.py first to generate analysis files.")
            return []
        
        files = [f for f in os.listdir(self.output_dir) if f.endswith('_analysis.csv')]
        stocks = [f.replace('_analysis.csv', '') for f in files]
        self.available_stocks = sorted(stocks)
        return self.available_stocks
    
    def load_stock_data(self, stock_symbol):
        """Load stock analysis data from CSV"""
        filepath = os.path.join(self.output_dir, f"{stock_symbol}_analysis.csv")
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        try:
            df = pd.read_csv(filepath, header=0, skiprows=[1, 2])
            first_col = df.columns[0]
            df = df.rename(columns={first_col: 'Date'})
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
            # Ensure required columns exist
            required_cols = ['Close', 'momentum_rsi', 'trend_macd', 'trend_macd_signal']
            missing = [col for col in required_cols if col not in df.columns]
            
            if missing:
                print(f"❌ Missing required columns: {missing}")
                return None
            
            self.df = df
            print(f"✅ Loaded {len(df)} days of data for {stock_symbol}")
            print(f"   Date range: {df.index.min().date()} to {df.index.max().date()}")
            return df
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def display_stock_menu(self):
        """Display menu for stock selection"""
        stocks = self.scan_available_stocks()
        
        if not stocks:
            return None
        
        print("\n" + "="*60)
        print("📊 AVAILABLE STOCKS")
        print("="*60)
        for i, stock in enumerate(stocks, 1):
            print(f"  {i}. {stock}")
        print(f"  0. Exit")
        print("="*60)
        
        while True:
            try:
                choice = input("\nSelect a stock (enter number): ").strip()
                if choice == '0':
                    return None
                idx = int(choice) - 1
                if 0 <= idx < len(stocks):
                    return stocks[idx]
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n\nExiting...")
                return None
    
    def display_strategy_menu(self):
        """Display menu for strategy selection"""
        print("\n" + "="*60)
        print("🎯 TRADING STRATEGIES")
        print("="*60)
        print("  1. RSI Strategy (Buy oversold, Sell overbought)")
        print("  2. MACD Crossover Strategy")
        print("  3. Combined RSI + MACD Strategy")
        print("  4. Bollinger Bands Strategy")
        print("  5. Moving Average Crossover")
        print("  6. Custom Strategy (Advanced)")
        print("  0. Back to Stock Selection")
        print("="*60)
        
        while True:
            try:
                choice = input("\nSelect a strategy (enter number): ").strip()
                if choice == '0':
                    return None
                if choice in ['1', '2', '3', '4', '5', '6']:
                    return choice
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n\nExiting...")
                return None
    
    def get_rsi_parameters(self):
        """Get RSI threshold parameters from user"""
        print("\n" + "-"*60)
        print("⚙️  RSI PARAMETERS")
        print("-"*60)
        print("RSI ranges from 0-100:")
        print("  - Below 30 = Oversold (potential buy)")
        print("  - Above 70 = Overbought (potential sell)")
        
        while True:
            try:
                buy_threshold = input("\nEnter RSI buy threshold (default 30): ").strip()
                buy_threshold = int(buy_threshold) if buy_threshold else 30
                
                sell_threshold = input("Enter RSI sell threshold (default 70): ").strip()
                sell_threshold = int(sell_threshold) if sell_threshold else 70
                
                if 0 <= buy_threshold < sell_threshold <= 100:
                    return buy_threshold, sell_threshold
                else:
                    print("❌ Invalid values. Buy threshold must be < Sell threshold (0-100)")
            except ValueError:
                print("❌ Please enter valid numbers.")
    
    def create_rsi_strategy(self, df, buy_threshold=30, sell_threshold=70):
        """RSI-based trading strategy"""
        df = df.copy()
        df['signal'] = 0
        
        df.loc[df['momentum_rsi'] < buy_threshold, 'signal'] = 1  # Buy
        df.loc[df['momentum_rsi'] > sell_threshold, 'signal'] = -1  # Sell
        
        return df
    
    def create_macd_strategy(self, df):
        """MACD crossover strategy"""
        df = df.copy()
        df['signal'] = 0
        
        # Buy when MACD crosses above signal
        df['macd_cross_above'] = (
            (df['trend_macd'] > df['trend_macd_signal']) & 
            (df['trend_macd'].shift(1) <= df['trend_macd_signal'].shift(1))
        )
        
        # Sell when MACD crosses below signal
        df['macd_cross_below'] = (
            (df['trend_macd'] < df['trend_macd_signal']) & 
            (df['trend_macd'].shift(1) >= df['trend_macd_signal'].shift(1))
        )
        
        df.loc[df['macd_cross_above'], 'signal'] = 1
        df.loc[df['macd_cross_below'], 'signal'] = -1
        
        return df
    
    def create_combined_strategy(self, df, rsi_buy=30, rsi_sell=70):
        """Combined RSI + MACD strategy"""
        df = df.copy()
        df['signal'] = 0
        
        # RSI conditions
        rsi_buy_cond = df['momentum_rsi'] < rsi_buy
        rsi_sell_cond = df['momentum_rsi'] > rsi_sell
        
        # MACD conditions
        macd_cross_above = (
            (df['trend_macd'] > df['trend_macd_signal']) & 
            (df['trend_macd'].shift(1) <= df['trend_macd_signal'].shift(1))
        )
        macd_cross_below = (
            (df['trend_macd'] < df['trend_macd_signal']) & 
            (df['trend_macd'].shift(1) >= df['trend_macd_signal'].shift(1))
        )
        
        # Buy: RSI oversold OR MACD bullish crossover
        df.loc[rsi_buy_cond | macd_cross_above, 'signal'] = 1
        
        # Sell: RSI overbought OR MACD bearish crossover
        df.loc[rsi_sell_cond | macd_cross_below, 'signal'] = -1
        
        return df
    
    def create_bollinger_strategy(self, df):
        """Bollinger Bands strategy"""
        df = df.copy()
        df['signal'] = 0
        
        # Buy when price touches lower band (oversold)
        df.loc[df['Close'] <= df['volatility_bbl'], 'signal'] = 1
        
        # Sell when price touches upper band (overbought)
        df.loc[df['Close'] >= df['volatility_bbh'], 'signal'] = -1
        
        return df
    
    def create_ma_crossover_strategy(self, df):
        """Moving Average Crossover strategy"""
        df = df.copy()
        df['signal'] = 0
        
        # Buy when fast MA crosses above slow MA
        df['ma_cross_above'] = (
            (df['trend_ema_fast'] > df['trend_ema_slow']) & 
            (df['trend_ema_fast'].shift(1) <= df['trend_ema_slow'].shift(1))
        )
        
        # Sell when fast MA crosses below slow MA
        df['ma_cross_below'] = (
            (df['trend_ema_fast'] < df['trend_ema_slow']) & 
            (df['trend_ema_fast'].shift(1) >= df['trend_ema_slow'].shift(1))
        )
        
        df.loc[df['ma_cross_above'], 'signal'] = 1
        df.loc[df['ma_cross_below'], 'signal'] = -1
        
        return df
    
    def run_backtest(self, df, initial_capital=100000):
        """Run backtest simulation"""
        capital = initial_capital
        shares = 0
        trades = []
        
        df['capital'] = initial_capital
        df['shares'] = 0
        df['portfolio_value'] = initial_capital
        df['returns'] = 0.0
        
        for i in range(1, len(df)):
            current_price = df.iloc[i]['Close']
            signal = df.iloc[i]['signal']
            prev_portfolio_value = df.iloc[i-1]['portfolio_value']
            
            # Execute buy signal
            if signal == 1 and shares == 0:
                shares = capital / current_price
                capital = 0
                trades.append({
                    'date': df.index[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares
                })
            
            # Execute sell signal
            elif signal == -1 and shares > 0:
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
            
            df.iloc[i, df.columns.get_loc('capital')] = capital
            df.iloc[i, df.columns.get_loc('shares')] = shares
            df.iloc[i, df.columns.get_loc('portfolio_value')] = portfolio_value
            
            # Calculate daily returns
            if prev_portfolio_value > 0:
                df.iloc[i, df.columns.get_loc('returns')] = (
                    (portfolio_value - prev_portfolio_value) / prev_portfolio_value
                )
        
        # Calculate metrics
        final_value = df.iloc[-1]['portfolio_value']
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        returns_series = df['returns'].dropna()
        if len(returns_series) > 0:
            sharpe_ratio = (returns_series.mean() / returns_series.std()) * np.sqrt(252) if returns_series.std() > 0 else 0
            max_drawdown = ((df['portfolio_value'] / df['portfolio_value'].expanding().max()) - 1).min() * 100
        else:
            sharpe_ratio = 0
            max_drawdown = 0
        
        buy_hold_return = ((df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close']) * 100
        
        results = {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'num_trades': len(trades),
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'buy_hold_return': buy_hold_return,
            'trades': trades,
            'df': df
        }
        
        self.results = results
        return results
    
    def display_results(self, results, strategy_name):
        """Display backtest results in a user-friendly format"""
        print("\n" + "="*70)
        print(f"📈 BACKTEST RESULTS - {strategy_name}")
        print("="*70)
        print(f"\n💰 FINANCIAL PERFORMANCE")
        print(f"   Initial Capital:     ₹{results['initial_capital']:>12,.2f}")
        print(f"   Final Portfolio:     ₹{results['final_value']:>12,.2f}")
        print(f"   Total Return:        {results['total_return']:>12.2f}%")
        
        print(f"\n📊 COMPARISON")
        print(f"   Buy-and-Hold:        {results['buy_hold_return']:>12.2f}%")
        difference = results['total_return'] - results['buy_hold_return']
        symbol = "✅" if difference > 0 else "❌"
        print(f"   Strategy vs Hold:    {difference:>12.2f}% {symbol}")
        
        print(f"\n📉 RISK METRICS")
        print(f"   Number of Trades:    {results['num_trades']:>12}")
        print(f"   Sharpe Ratio:        {results['sharpe_ratio']:>12.2f}")
        print(f"   Max Drawdown:        {results['max_drawdown']:>12.2f}%")
        
        # Sharpe ratio interpretation
        if results['sharpe_ratio'] > 1.0:
            sharpe_rating = "Excellent ⭐⭐⭐"
        elif results['sharpe_ratio'] > 0.5:
            sharpe_rating = "Good ⭐⭐"
        else:
            sharpe_rating = "Needs Improvement ⭐"
        print(f"   Risk Rating:         {sharpe_rating}")
        
        print("="*70)
        
        # Show recent trades
        if results['trades']:
            print(f"\n🔄 RECENT TRADES (Last 5)")
            print("-"*70)
            recent_trades = results['trades'][-5:]
            for trade in recent_trades:
                action_symbol = "🟢 BUY" if trade['action'] == 'BUY' else "🔴 SELL"
                print(f"   {trade['date'].date()}  {action_symbol:8}  @ ₹{trade['price']:>8.2f}  ({trade['shares']:.2f} shares)")
    
    def save_results(self, stock_symbol, strategy_name):
        """Save backtest results to CSV"""
        if self.results is None:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_{stock_symbol}_{strategy_name.replace(' ', '_')}_{timestamp}.csv"
        
        # Save key columns
        save_cols = ['Close', 'signal', 'momentum_rsi', 'trend_macd', 
                     'trend_macd_signal', 'portfolio_value', 'returns']
        available_cols = [col for col in save_cols if col in self.results['df'].columns]
        
        self.results['df'][available_cols].to_csv(filename)
        print(f"\n💾 Results saved to: {filename}")
    
    def run_interactive(self):
        """Main interactive loop"""
        print("\n" + "="*70)
        print("🚀 INTERACTIVE BACKTESTING TOOL")
        print("="*70)
        print("Test trading strategies on Indian stocks using technical indicators")
        print("="*70)
        
        while True:
            # Step 1: Select Stock
            stock_symbol = self.display_stock_menu()
            if stock_symbol is None:
                print("\n👋 Thank you for using Interactive Backtester!")
                break
            
            # Load stock data
            df = self.load_stock_data(stock_symbol)
            if df is None:
                continue
            
            # Step 2: Select Strategy
            strategy_choice = self.display_strategy_menu()
            if strategy_choice is None:
                continue
            
            # Step 3: Apply Strategy
            strategy_name = ""
            if strategy_choice == '1':
                strategy_name = "RSI Strategy"
                rsi_buy, rsi_sell = self.get_rsi_parameters()
                df = self.create_rsi_strategy(df, rsi_buy, rsi_sell)
                
            elif strategy_choice == '2':
                strategy_name = "MACD Crossover"
                df = self.create_macd_strategy(df)
                
            elif strategy_choice == '3':
                strategy_name = "Combined RSI + MACD"
                rsi_buy, rsi_sell = self.get_rsi_parameters()
                df = self.create_combined_strategy(df, rsi_buy, rsi_sell)
                
            elif strategy_choice == '4':
                strategy_name = "Bollinger Bands"
                df = self.create_bollinger_strategy(df)
                
            elif strategy_choice == '5':
                strategy_name = "Moving Average Crossover"
                df = self.create_ma_crossover_strategy(df)
                
            elif strategy_choice == '6':
                print("\n⚠️  Custom strategy feature coming soon!")
                print("   For now, please edit backtest_example.py directly.")
                continue
            
            # Count signals
            buy_signals = (df['signal'] == 1).sum()
            sell_signals = (df['signal'] == -1).sum()
            print(f"\n📊 Strategy Signals Generated:")
            print(f"   Buy signals:  {buy_signals}")
            print(f"   Sell signals: {sell_signals}")
            
            # Step 4: Get initial capital
            print("\n" + "-"*60)
            try:
                capital_input = input("Enter initial capital (default ₹1,00,000): ").strip()
                # Remove ₹, $, and commas for parsing
                capital_input_clean = capital_input.replace('₹', '').replace('$', '').replace(',', '').replace(' ', '')
                initial_capital = float(capital_input_clean) if capital_input_clean else 100000
            except ValueError:
                print("❌ Invalid input. Using default ₹1,00,000")
                initial_capital = 100000
            
            # Step 5: Run Backtest
            print("\n⏳ Running backtest...")
            results = self.run_backtest(df, initial_capital)
            
            # Step 6: Display Results
            self.display_results(results, strategy_name)
            
            # Step 7: Save Results
            save = input("\n💾 Save results to CSV? (y/n): ").strip().lower()
            if save == 'y':
                self.save_results(stock_symbol, strategy_name)
            
            # Step 8: Continue?
            print("\n" + "-"*60)
            continue_choice = input("Test another strategy? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 Thank you for using Interactive Backtester!")
                break


def main():
    """Main entry point"""
    backtester = InteractiveBacktester()
    try:
        backtester.run_interactive()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting... Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

