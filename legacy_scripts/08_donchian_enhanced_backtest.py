"""
Enhanced Donchian MCPT Backtest (Hedge Fund Grade Strategy Validator)

This script backtests the enhanced Donchian strategy with:
1. Behavioral regime filtering (only trade in trending markets)
2. Pattern-matching exit logic (early exit based on similar historical days)
3. Strategy Validation: Compares "Blind Trend Following" vs "Regime-Aware" to prove Alpha
4. Transaction cost analysis
5. Auto-detection of Red Light (Crash) Regime
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Environment, FileSystemLoader
from walkforward_mcpt import load_stock_data, monte_carlo_permutation_test
from donchian_enhanced import donchian_enhanced, identify_trending_regimes
from donchian_strategy import optimize_donchian, donchian_breakout
import sys
import os
import importlib.util
# Add current directory to path for local imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import PatternMatcher from 06_find_similar_days.py
find_similar_days_path = os.path.join(script_dir, '06_find_similar_days.py')
spec = importlib.util.spec_from_file_location("find_similar_days", find_similar_days_path)
find_similar_days = importlib.util.module_from_spec(spec)
spec.loader.exec_module(find_similar_days)
PatternMatcher = find_similar_days.PatternMatcher

# Import from 04_behavioral_patterns.py
behavioral_patterns_path = os.path.join(script_dir, '04_behavioral_patterns.py')
spec = importlib.util.spec_from_file_location("behavioral_patterns", behavioral_patterns_path)
behavioral_patterns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(behavioral_patterns)
load_analysis_data = behavioral_patterns.load_analysis_data
get_indicator_columns = behavioral_patterns.get_indicator_columns
from tqdm import tqdm

BASE_OUTPUT_DIR = "analysis_results"
DEFAULT_STOCK_FILE = "output/RELIANCE.NS_analysis.csv"
TRAIN_PERIOD_DAYS = 365 * 2
TEST_PERIOD_DAYS = 365 // 2
MCPT_ITERATIONS = 1000
TRANSACTION_COST_BPS = 0.0010  # 10 bps (0.10%) per trade


def get_ticker_output_dir(stock_symbol):
    """Get ticker-specific output directory."""
    ticker_dir = os.path.join(BASE_OUTPUT_DIR, stock_symbol)
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    return ticker_dir


def get_backtests_dir(stock_symbol, strategy="enhanced"):
    """Get backtests subdirectory for strategy results."""
    backtests_dir = os.path.join(get_ticker_output_dir(stock_symbol), "backtests", strategy)
    if not os.path.exists(backtests_dir):
        os.makedirs(backtests_dir)
    return backtests_dir


def get_analysis_dir(stock_symbol):
    """Get analysis subdirectory for correlation, regimes, similarity."""
    analysis_dir = os.path.join(get_ticker_output_dir(stock_symbol), "analysis")
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    return analysis_dir


def auto_detect_red_light_regime(regime_data_path):
    """
    Auto-detects the Red Light (Crash) Regime by finding the regime with worst average return.
    
    Returns:
        int or None: The regime ID with worst performance, or None if data unavailable
    """
    if not os.path.exists(regime_data_path):
        return None
    
    try:
        df = pd.read_csv(regime_data_path, index_col=0, parse_dates=True)
        
        # Handle different column name cases
        close_col = None
        for col in ['Close', 'close', 'CLOSE']:
            if col in df.columns:
                close_col = col
                break
        
        if close_col is None:
            return None
        
        # Calculate returns by regime
        df['returns'] = df[close_col].pct_change()
        regime_stats = df.groupby('regime')['returns'].mean()
        
        if len(regime_stats) == 0:
            return None
        
        red_light_regime = regime_stats.idxmin()
        return red_light_regime
    except Exception as e:
        print(f"⚠️  Could not auto-detect red light regime: {e}")
        return None


def calculate_metrics(returns_series):
    """
    Hedge Fund Performance Metrics.
    
    Returns:
        tuple: (total_return, sharpe_ratio, max_drawdown, volatility)
    """
    total_ret = returns_series.sum()
    mean_ret = returns_series.mean()
    vol = returns_series.std() * np.sqrt(252)
    sharpe = (mean_ret * 252) / vol if vol > 0 else 0
    
    # Max Drawdown
    cum = returns_series.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    max_dd = dd.min()
    
    return total_ret, sharpe, max_dd, vol


class EnhancedWalkForwardAnalysis:
    """
    Walk-forward analysis with enhanced Donchian strategy.
    Now includes comparison between blind and filtered strategies.
    """
    def __init__(self, data, train_period_days, test_period_days, 
                 use_regime_filter=True, use_pattern_exit=True,
                 analysis_file_path=None, regime_data_path=None,
                 compare_blind=True, red_light_regime=None):
        self.data = data
        self.train_period = pd.Timedelta(days=train_period_days)
        self.test_period = pd.Timedelta(days=test_period_days)
        self.use_regime_filter = use_regime_filter
        self.use_pattern_exit = use_pattern_exit
        self.compare_blind = compare_blind
        self.red_light_regime = red_light_regime
        self.results = []
        self.regime_data_path = regime_data_path
        self.analysis_file_path = analysis_file_path
        
        # Initialize pattern matcher and normalized data if needed
        self.pattern_matcher = None
        self.df_normalized = None
        self.df_full = None
        
        # Load regime data if available for comparison
        self.regime_df = None
        if self.regime_data_path and os.path.exists(self.regime_data_path):
            try:
                self.regime_df = pd.read_csv(self.regime_data_path, index_col=0, parse_dates=True)
            except Exception as e:
                print(f"⚠️  Could not load regime data: {e}")
        
        if self.use_pattern_exit and self.analysis_file_path:
            self._setup_pattern_matching()
    
    def _setup_pattern_matching(self):
        """Load and prepare indicator data for pattern matching."""
        try:
            print("🔄 Loading indicator data for pattern matching...")
            self.df_full = load_analysis_data(self.analysis_file_path)
            if self.df_full is None:
                print("⚠️  Could not load analysis data. Pattern matching disabled.")
                self.use_pattern_exit = False
                return
            
            # Get indicator columns
            df_indicators = get_indicator_columns(self.df_full)
            
            # Initialize pattern matcher and normalize
            self.pattern_matcher = PatternMatcher()
            self.df_normalized = self.pattern_matcher.fit_and_transform(df_indicators)
            
            # Ensure df_full has proper column names for pattern matching
            # Standardize to lowercase for consistency
            if 'Close' in self.df_full.columns:
                self.df_full.columns = [col.lower() if col in ['Open', 'High', 'Low', 'Close', 'Volume'] else col 
                                       for col in self.df_full.columns]
            
            print("✅ Pattern matching setup complete")
        except Exception as e:
            print(f"⚠️  Pattern matching setup failed: {e}")
            self.use_pattern_exit = False

    def run(self, mcpt_iterations=1000):
        """Execute enhanced walk-forward analysis."""
        start_date = self.data.index.min()
        end_date = self.data.index.max()
        current_date = start_date + self.train_period
        
        total_days = (end_date - current_date).days
        pbar = tqdm(total=total_days, desc="Enhanced Walk-Forward Analysis")
        
        while current_date + self.test_period <= end_date:
            train_start = current_date - self.train_period
            train_end = current_date - pd.Timedelta(days=1)
            test_start = current_date
            test_end = current_date + self.test_period - pd.Timedelta(days=1)
            
            # Training phase
            train_data = self.data.loc[train_start:train_end]
            if train_data.empty:
                current_date += self.test_period
                pbar.update(self.test_period.days)
                continue
            
            # Optimize lookback period
            best_lookback, _ = optimize_donchian(train_data)
            
            # Testing phase
            test_data = self.data.loc[test_start:test_end]
            if test_data.empty:
                current_date += self.test_period
                pbar.update(self.test_period.days)
                continue
            
            # Generate enhanced signals
            # Prepare full OHLC data for pattern matching (use lowercase column names)
            df_full_ohlc = None
            if self.df_full is not None:
                ohlc_cols = ['open', 'high', 'low', 'close', 'volume']
                available_cols = [col for col in ohlc_cols if col in self.df_full.columns]
                if available_cols:
                    df_full_ohlc = self.df_full[available_cols]
            
            signals_filtered = donchian_enhanced(
                test_data, 
                best_lookback,
                regime_data_path=self.regime_data_path if self.use_regime_filter else None,
                use_pattern_exit=self.use_pattern_exit,
                pattern_matcher=self.pattern_matcher,
                df_normalized=self.df_normalized,
                df_full=df_full_ohlc,
                allow_bearish=True,
                pattern_exit_threshold=-2.0,
                num_similar_days=10,
                filter_red_light=True
            )
            
            # Generate blind signals for comparison
            signals_blind = None
            if self.compare_blind:
                signals_blind = donchian_breakout(test_data, best_lookback)
            
            log_returns = np.log(test_data['close']).diff()
            
            # MCPT - Align signals and returns correctly to avoid lookahead bias
            aligned_signals_filtered = signals_filtered.iloc[:-1].reset_index(drop=True)
            aligned_returns = log_returns.iloc[1:].reset_index(drop=True)
            min_len = min(len(aligned_signals_filtered), len(aligned_returns))
            aligned_signals_filtered = aligned_signals_filtered.iloc[:min_len]
            aligned_returns = aligned_returns.iloc[:min_len]
            
            # Drop any NaN values
            valid_mask = ~(aligned_returns.isna() | aligned_signals_filtered.isna())
            aligned_signals_filtered = aligned_signals_filtered[valid_mask]
            aligned_returns = aligned_returns[valid_mask]
            
            # Calculate filtered strategy returns with transaction costs
            if len(aligned_signals_filtered) > 0 and len(aligned_returns) > 0:
                # Calculate trades (position changes)
                trades_filtered = pd.Series(aligned_signals_filtered).diff().abs().fillna(0)
                ret_filtered_raw = aligned_signals_filtered * aligned_returns
                ret_filtered_net = ret_filtered_raw - (trades_filtered * TRANSACTION_COST_BPS)
                actual_ret_filtered = ret_filtered_net.sum()
                
                # MCPT on filtered strategy
                actual_ret, permuted_rets, p_value = monte_carlo_permutation_test(
                    aligned_signals_filtered, aligned_returns, mcpt_iterations
                )
            else:
                actual_ret_filtered = 0.0
                actual_ret = 0.0
                permuted_rets = [0.0] * mcpt_iterations
                p_value = 1.0
                trades_filtered = pd.Series([0])
            
            # Calculate blind strategy returns for comparison
            actual_ret_blind = 0.0
            trades_blind = 0
            if self.compare_blind and signals_blind is not None:
                aligned_signals_blind = signals_blind.iloc[:-1].reset_index(drop=True)
                aligned_signals_blind = aligned_signals_blind.iloc[:min_len]
                aligned_signals_blind = aligned_signals_blind[valid_mask]
                
                if len(aligned_signals_blind) > 0:
                    trades_blind_series = pd.Series(aligned_signals_blind).diff().abs().fillna(0)
                    ret_blind_raw = aligned_signals_blind * aligned_returns
                    ret_blind_net = ret_blind_raw - (trades_blind_series * TRANSACTION_COST_BPS)
                    actual_ret_blind = ret_blind_net.sum()
                    trades_blind = trades_blind_series.sum()
            
            # Store results
            self.results.append({
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'best_lookback': best_lookback,
                'actual_returns': actual_ret_filtered,  # Net returns with costs
                'actual_returns_blind': actual_ret_blind,  # Blind strategy for comparison
                'p_value': p_value,
                'permuted_returns_mean': np.mean(permuted_rets),
                'permuted_returns_std': np.std(permuted_rets),
                'permuted_returns': permuted_rets,
                'trades_filtered': trades_filtered.sum() if isinstance(trades_filtered, pd.Series) else 0,
                'trades_blind': trades_blind,
            })
            
            current_date += self.test_period
            pbar.update(self.test_period.days)
        
        pbar.close()
        return pd.DataFrame(self.results)


def plot_strategy_comparison(results_df, output_path, stock_symbol, red_light_regime=None):
    """
    The 'Money Shot' Chart: Compares Blind vs Regime-Filtered Strategy.
    Shows the value of regime filtering.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')
    
    # Sort by test_end date
    results_df = results_df.sort_values('test_end').copy()
    
    # Calculate cumulative returns
    results_df['cum_returns_filtered'] = results_df['actual_returns'].cumsum()
    results_df['cum_returns_blind'] = results_df['actual_returns_blind'].cumsum()
    
    # Plot both strategies
    ax.plot(results_df['test_end'], results_df['cum_returns_blind'], 
            label='Blind Trend Following', color='gray', linewidth=2, alpha=0.7)
    ax.plot(results_df['test_end'], results_df['cum_returns_filtered'], 
            label='Regime-Aware Strategy', color='#00ff00', linewidth=3, zorder=10)
    
    # Highlight red light periods if regime data available
    if red_light_regime is not None:
        # Note: This is a simplified visualization - in full implementation,
        # you'd load the regime data and highlight specific dates
        ax.text(0.02, 0.98, f'Red Light Regime: {red_light_regime} (Avoided)', 
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='red', alpha=0.2))
    
    ax.set_title(f'The Value of Context: {stock_symbol}\n(Green Line avoids trading during Red Zones)', 
                 fontsize=16, fontweight='bold')
    ax.set_xlabel('Test Period End Date', fontsize=12)
    ax.set_ylabel('Cumulative Log Return', fontsize=12)
    ax.legend(loc='upper left', frameon=True, framealpha=0.9, facecolor='white')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_equity_curve(results_df, output_path):
    """Plots the cumulative returns for the enhanced strategy."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 7))
    
    results_df = results_df.sort_values('test_end')
    results_df['cumulative_returns'] = results_df['actual_returns'].cumsum()
    
    ax.plot(results_df['test_end'], results_df['cumulative_returns'], 
            marker='o', linestyle='-', linewidth=2, color='#1f77b4', 
            label='Enhanced Strategy Equity (Log)')
    
    ax.set_title('Enhanced Donchian Strategy Performance', fontsize=16, fontweight='bold')
    ax.set_xlabel('Test Period End Date', fontsize=12)
    ax.set_ylabel('Cumulative Log Returns', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def generate_html_report(summary_df, comparison_df, results_df, stock_symbol, output_dir):
    """Generates a comprehensive HTML report with strategy comparison."""
    env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
    
    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Strategy Validator Report: {{ stock_symbol }}</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0 auto; max-width: 1200px; padding: 20px; background-color: #f9f9f9; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .summary-table { border-collapse: collapse; width: 100%; font-size: 14px; }
            .summary-table th, .summary-table td { border: 1px solid #e0e0e0; padding: 12px; text-align: left; }
            .summary-table th { background-color: #f2f6fc; font-weight: 600; color: #2c3e50; }
            .comparison-table { border-collapse: collapse; width: 100%; font-size: 14px; margin-top: 20px; }
            .comparison-table th, .comparison-table td { border: 1px solid #e0e0e0; padding: 12px; text-align: center; }
            .comparison-table th { background-color: #e8f4f8; font-weight: 600; }
            .plot-container { text-align: center; margin: 20px 0; }
            img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
            .caption { font-style: italic; color: #666; margin-top: 8px; }
            .metric-box { background-color: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; }
            .winner { background-color: #d4edda; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Strategy Validator Report: {{ stock_symbol }}</h1>
        
        <div class="container">
            <h2>Executive Summary</h2>
            {{ summary_table }}
            <div class="metric-box">
                <strong>Methodology:</strong> Walk-Forward Optimization ({{ train_days }} day train / {{ test_days }} day test).
                <br>
                <strong>Validation:</strong> Monte Carlo Permutation Test ({{ mcpt_iter }} iterations per period).
                <br>
                <strong>Transaction Costs:</strong> {{ transaction_cost }} bps per trade.
            </div>
        </div>
        
        <div class="container">
            <h2>Strategy Comparison: Blind vs Regime-Aware</h2>
            {{ comparison_table }}
            <div class="caption">This comparison proves whether regime filtering adds value or is just over-fitting.</div>
        </div>
        
        <div class="container">
            <h2>1. Strategy Comparison (The "Money Plot")</h2>
            <div class="plot-container">
                <img src="strategy_comparison.png" alt="Strategy Comparison">
                <div class="caption">Green line = Regime-Aware Strategy. Gray line = Blind Trend Following. If Green beats Gray, regime filtering adds Alpha.</div>
            </div>
        </div>
        
        <div class="container">
            <h2>2. Enhanced Strategy Equity Curve</h2>
            <div class="plot-container">
                <img src="equity_curve.png" alt="Equity Curve">
                <div class="caption">Cumulative Log Returns over the entire test history.</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = env.from_string(template_str)
    
    summary_table_html = summary_df.to_html(classes='summary-table', index=False)
    comparison_table_html = comparison_df.to_html(classes='comparison-table', index=False)
    
    html_content = template.render(
        stock_symbol=stock_symbol,
        summary_table=summary_table_html,
        comparison_table=comparison_table_html,
        train_days=TRAIN_PERIOD_DAYS,
        test_days=TEST_PERIOD_DAYS,
        mcpt_iter=MCPT_ITERATIONS,
        transaction_cost=TRANSACTION_COST_BPS * 10000  # Convert to bps
    )
    
    report_path = os.path.join(output_dir, "strategy_validator_report.html")
    with open(report_path, 'w') as f:
        f.write(html_content)
    print(f"📄 Professional HTML report generated at: {report_path}")


def main():
    """Main function for enhanced Donchian backtest."""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print(f"⚠️  No file path provided. Using default: {DEFAULT_STOCK_FILE}")
        file_path = DEFAULT_STOCK_FILE
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return
    
    stock_symbol = os.path.basename(file_path).replace('_analysis.csv', '').replace('.csv', '')
    output_dir = get_backtests_dir(stock_symbol, "enhanced")
    
    # Try to find regime data in analysis directory
    analysis_dir = get_analysis_dir(stock_symbol)
    regime_path = os.path.join(analysis_dir, "data_with_regimes.csv")
    
    print(f"🔄 Loading OHLCV data for {stock_symbol}...")
    ohlc_data = load_stock_data(file_path)
    if ohlc_data is None:
        return
    
    print(f"✅ OHLCV data loaded successfully. Shape: {ohlc_data.shape}")
    
    # Check if regime data exists and auto-detect red light regime
    use_regime_filter = os.path.exists(regime_path)
    red_light_regime = None
    
    if use_regime_filter:
        print("🛑 Auto-detecting Red Light (Crash) Regime...")
        red_light_regime = auto_detect_red_light_regime(regime_path)
        if red_light_regime is not None:
            print(f"   ✅ Detected Red Light Regime: {red_light_regime}")
        else:
            print("   ⚠️  Could not auto-detect red light regime")
    else:
        print("⚠️  Regime data not found. Run behavioral_patterns.py first for regime filtering.")
        print("   Continuing without regime filtering...")
    
    # Check if analysis file exists for pattern matching
    use_pattern_exit = os.path.exists(file_path)
    
    if not use_pattern_exit:
        print("⚠️  Analysis file not found. Pattern matching exits will be disabled.")
    
    print("\n🚀 Starting Enhanced Walk-Forward Analysis with MCPT...")
    print(f"   - Regime filtering: {'✅ Enabled' if use_regime_filter else '❌ Disabled'}")
    print(f"   - Pattern-matching exits: {'✅ Enabled' if use_pattern_exit else '❌ Disabled'}")
    print(f"   - Strategy comparison: ✅ Enabled (Blind vs Regime-Aware)")
    print(f"   - Transaction costs: {TRANSACTION_COST_BPS * 10000:.0f} bps per trade")
    
    wf_analyzer = EnhancedWalkForwardAnalysis(
        data=ohlc_data,
        train_period_days=TRAIN_PERIOD_DAYS,
        test_period_days=TEST_PERIOD_DAYS,
        use_regime_filter=use_regime_filter,
        use_pattern_exit=use_pattern_exit,
        analysis_file_path=file_path if use_pattern_exit else None,
        regime_data_path=regime_path if use_regime_filter else None,
        compare_blind=True,
        red_light_regime=red_light_regime
    )
    
    results_df = wf_analyzer.run(mcpt_iterations=MCPT_ITERATIONS)
    
    if results_df.empty:
        print("❌ Analysis produced no results.")
        return
    
    # Analyze results
    print("\n📊 Analyzing results...")
    
    # Enhanced strategy metrics
    total_log_return_filtered = results_df['actual_returns'].sum()
    total_p_value = results_df['p_value'].mean()
    total_trades_filtered = results_df['trades_filtered'].sum()
    
    # Blind strategy metrics
    total_log_return_blind = results_df['actual_returns_blind'].sum()
    total_trades_blind = results_df['trades_blind'].sum()
    
    total_days = (results_df['test_end'].max() - results_df['test_start'].min()).days
    annualized_return_filtered = (total_log_return_filtered / (total_days / 365.25)) if total_days > 0 else 0
    annualized_return_blind = (total_log_return_blind / (total_days / 365.25)) if total_days > 0 else 0
    
    # Calculate additional metrics
    ret_filtered_series = results_df['actual_returns']
    ret_blind_series = results_df['actual_returns_blind']
    
    tot_filt, sh_filt, mdd_filt, vol_filt = calculate_metrics(ret_filtered_series)
    tot_blind, sh_blind, mdd_blind, vol_blind = calculate_metrics(ret_blind_series)
    
    # Value added by regime filtering
    value_added = total_log_return_filtered - total_log_return_blind
    
    summary = {
        'Stock': stock_symbol,
        'Strategy': 'Enhanced Donchian (Regime Filtered + Pattern Exit)',
        'Total Log Return': f"{total_log_return_filtered:.4f}",
        'Annualized Return': f"{annualized_return_filtered:.2%}",
        'Average P-Value': f"{total_p_value:.4f}",
        'Num Walk-Forward Periods': len(results_df),
        'Regime Filtering': '✅ Enabled' if use_regime_filter else '❌ Disabled',
        'Pattern Exit': '✅ Enabled' if use_pattern_exit else '❌ Disabled',
    }
    
    summary_df = pd.DataFrame([summary])
    
    # Comparison table
    comparison_data = {
        'Metric': ['Total Return', 'Annualized Return', 'Sharpe Ratio', 'Max Drawdown', 'Volatility', 'Total Trades'],
        'Blind Trend Following': [
            f"{tot_blind:.4f}",
            f"{annualized_return_blind:.2%}",
            f"{sh_blind:.2f}",
            f"{mdd_blind:.2%}",
            f"{vol_blind:.2%}",
            f"{total_trades_blind:.0f}"
        ],
        'Regime-Aware Strategy': [
            f"{tot_filt:.4f}",
            f"{annualized_return_filtered:.2%}",
            f"{sh_filt:.2f}",
            f"{mdd_filt:.2%}",
            f"{vol_filt:.2%}",
            f"{total_trades_filtered:.0f}"
        ],
        'Value Added': [
            f"{value_added:.4f}",
            f"{(annualized_return_filtered - annualized_return_blind):.2%}",
            f"{(sh_filt - sh_blind):.2f}",
            f"{(mdd_filt - mdd_blind):.2%}",
            f"{(vol_filt - vol_blind):.2%}",
            f"{(total_trades_filtered - total_trades_blind):.0f}"
        ]
    }
    comparison_df = pd.DataFrame(comparison_data)
    
    print("\n" + "="*80)
    print("📈 HEDGE FUND GRADE STRATEGY VALIDATOR")
    print("="*80)
    print("\n📊 STRATEGY COMPARISON:")
    print("-" * 80)
    print(f"{'METRIC':<20} | {'BLIND TREND':<15} | {'REGIME FILTERED':<15} | {'VALUE ADDED':<15}")
    print("-" * 80)
    print(f"{'Total Return':<20} | {tot_blind:>15.4f} | {tot_filt:>15.4f} | {value_added:>15.4f}")
    print(f"{'Annualized Return':<20} | {annualized_return_blind:>15.2%} | {annualized_return_filtered:>15.2%} | {(annualized_return_filtered - annualized_return_blind):>15.2%}")
    print(f"{'Sharpe Ratio':<20} | {sh_blind:>15.2f} | {sh_filt:>15.2f} | {(sh_filt - sh_blind):>15.2f}")
    print(f"{'Max Drawdown':<20} | {mdd_blind:>15.2%} | {mdd_filt:>15.2%} | {(mdd_filt - mdd_blind):>15.2%}")
    print(f"{'Volatility':<20} | {vol_blind:>15.2%} | {vol_filt:>15.2%} | {(vol_filt - vol_blind):>15.2%}")
    print(f"{'Total Trades':<20} | {total_trades_blind:>15.0f} | {total_trades_filtered:>15.0f} | {(total_trades_filtered - total_trades_blind):>15.0f}")
    print("="*80)
    
    if value_added > 0:
        print(f"\n✅ REGIME FILTERING ADDS VALUE: +{value_added:.4f} log return ({annualized_return_filtered - annualized_return_blind:.2%} annualized)")
    else:
        print(f"\n⚠️  REGIME FILTERING DOES NOT ADD VALUE: {value_added:.4f} log return")
    
    print("\n" + "="*80)
    print("📈 ENHANCED STRATEGY SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))
    print("="*80)
    
    # Save results
    output_path = os.path.join(output_dir, "results.csv")
    summary_path = os.path.join(output_dir, "summary.csv")
    comparison_path = os.path.join(output_dir, "comparison.csv")
    
    results_df.to_csv(output_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    comparison_df.to_csv(comparison_path, index=False)
    
    print(f"\n💾 Results saved to: {output_path}")
    print(f"💾 Summary saved to: {summary_path}")
    print(f"💾 Comparison saved to: {comparison_path}")
    
    # Generate visualizations
    print("\n🎨 Generating visualizations...")
    
    # Strategy comparison plot
    comparison_plot_path = os.path.join(output_dir, "strategy_comparison.png")
    plot_strategy_comparison(results_df, comparison_plot_path, stock_symbol, red_light_regime)
    print(f"📊 Strategy comparison plot saved to: {comparison_plot_path}")
    
    # Equity curve
    equity_curve_path = os.path.join(output_dir, "equity_curve.png")
    plot_equity_curve(results_df, equity_curve_path)
    print(f"📈 Equity curve plot saved to: {equity_curve_path}")
    
    # Generate HTML report
    generate_html_report(summary_df, comparison_df, results_df, stock_symbol, output_dir)
    
    # Print simple summary (easy to read format)
    try:
        from donchian_simple_summary import print_simple_summary
        print_simple_summary(output_path, initial_capital=100000)
    except Exception as e:
        print(f"⚠️  Could not generate simple summary: {e}")
    
    print(f"\n✅ Enhanced analysis complete for {stock_symbol}.")


if __name__ == "__main__":
    main()

