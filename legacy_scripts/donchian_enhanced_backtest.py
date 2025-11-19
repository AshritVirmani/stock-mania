"""
Enhanced Donchian MCPT Backtest

This script backtests the enhanced Donchian strategy with:
1. Behavioral regime filtering (only trade in trending markets)
2. Pattern-matching exit logic (early exit based on similar historical days)
"""

import os
import sys
import pandas as pd
import numpy as np
from walkforward_mcpt import load_stock_data, monte_carlo_permutation_test
from donchian_enhanced import donchian_enhanced, identify_trending_regimes
from donchian_strategy import optimize_donchian
from find_similar_days import PatternMatcher
from behavioral_patterns import load_analysis_data, get_indicator_columns, normalize_indicators
from tqdm import tqdm

BASE_OUTPUT_DIR = "analysis_results"
DEFAULT_STOCK_FILE = "output/RELIANCE.NS_analysis.csv"
TRAIN_PERIOD_DAYS = 365 * 2
TEST_PERIOD_DAYS = 365 // 2
MCPT_ITERATIONS = 1000


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


class EnhancedWalkForwardAnalysis:
    """
    Walk-forward analysis with enhanced Donchian strategy.
    """
    def __init__(self, data, train_period_days, test_period_days, 
                 use_regime_filter=True, use_pattern_exit=True,
                 analysis_file_path=None, regime_data_path=None):
        self.data = data
        self.train_period = pd.Timedelta(days=train_period_days)
        self.test_period = pd.Timedelta(days=test_period_days)
        self.use_regime_filter = use_regime_filter
        self.use_pattern_exit = use_pattern_exit
        self.results = []
        self.regime_data_path = regime_data_path
        self.analysis_file_path = analysis_file_path
        
        # Initialize pattern matcher and normalized data if needed
        self.pattern_matcher = None
        self.df_normalized = None
        self.df_full = None
        
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
            
            signals = donchian_enhanced(
                test_data, 
                best_lookback,
                regime_data_path=self.regime_data_path if self.use_regime_filter else None,
                use_pattern_exit=self.use_pattern_exit,
                pattern_matcher=self.pattern_matcher,
                df_normalized=self.df_normalized,
                df_full=df_full_ohlc,
                allow_bearish=True,
                pattern_exit_threshold=-2.0,  # Exit if similar days averaged < -2% (as per user request)
                num_similar_days=10,  # Check top 10 similar days (as per user request)
                filter_red_light=True  # Filter out Red Light (worst-performing) regimes
            )
            
            log_returns = np.log(test_data['close']).diff()
            
            # MCPT - Align signals and returns correctly to avoid lookahead bias
            # Signal on day T should capture return from day T to T+1
            aligned_signals = signals.iloc[:-1].reset_index(drop=True)
            aligned_returns = log_returns.iloc[1:].reset_index(drop=True)
            min_len = min(len(aligned_signals), len(aligned_returns))
            aligned_signals = aligned_signals.iloc[:min_len]
            aligned_returns = aligned_returns.iloc[:min_len]
            
            # Drop any NaN values
            valid_mask = ~(aligned_returns.isna() | aligned_signals.isna())
            aligned_signals = aligned_signals[valid_mask]
            aligned_returns = aligned_returns[valid_mask]
            
            if len(aligned_signals) == 0 or len(aligned_returns) == 0:
                actual_ret = 0.0
                permuted_rets = [0.0] * mcpt_iterations
                p_value = 1.0
            else:
                actual_ret, permuted_rets, p_value = monte_carlo_permutation_test(
                    aligned_signals, aligned_returns, mcpt_iterations
                )
            
            # Store results
            self.results.append({
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'best_lookback': best_lookback,
                'actual_returns': actual_ret,
                'p_value': p_value,
                'permuted_returns_mean': np.mean(permuted_rets),
                'permuted_returns_std': np.std(permuted_rets),
                'permuted_returns': permuted_rets,
            })
            
            current_date += self.test_period
            pbar.update(self.test_period.days)
        
        pbar.close()
        return pd.DataFrame(self.results)


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
    
    # Check if regime data exists (already set above)
    use_regime_filter = os.path.exists(regime_path)
    
    if not use_regime_filter:
        print("⚠️  Regime data not found. Run behavioral_patterns.py first for regime filtering.")
        print("   Continuing without regime filtering...")
    
    # Check if analysis file exists for pattern matching
    use_pattern_exit = os.path.exists(file_path)
    
    if not use_pattern_exit:
        print("⚠️  Analysis file not found. Pattern matching exits will be disabled.")
    
    print("\n🚀 Starting Enhanced Walk-Forward Analysis with MCPT...")
    print(f"   - Regime filtering: {'✅ Enabled' if use_regime_filter else '❌ Disabled'}")
    print(f"   - Pattern-matching exits: {'✅ Enabled' if use_pattern_exit else '❌ Disabled'}")
    
    wf_analyzer = EnhancedWalkForwardAnalysis(
        data=ohlc_data,
        train_period_days=TRAIN_PERIOD_DAYS,
        test_period_days=TEST_PERIOD_DAYS,
        use_regime_filter=use_regime_filter,
        use_pattern_exit=use_pattern_exit,
        analysis_file_path=file_path if use_pattern_exit else None,
        regime_data_path=regime_path if use_regime_filter else None
    )
    
    results_df = wf_analyzer.run(mcpt_iterations=MCPT_ITERATIONS)
    
    if results_df.empty:
        print("❌ Analysis produced no results.")
        return
    
    # Analyze results
    print("\n📊 Analyzing results...")
    total_log_return = results_df['actual_returns'].sum()
    total_p_value = results_df['p_value'].mean()
    
    total_days = (results_df['test_end'].max() - results_df['test_start'].min()).days
    annualized_return = (total_log_return / (total_days / 365.25)) if total_days > 0 else 0
    
    summary = {
        'Stock': stock_symbol,
        'Strategy': 'Enhanced Donchian (Regime Filtered + Pattern Exit)',
        'Total Log Return': f"{total_log_return:.4f}",
        'Annualized Log Return': f"{annualized_return:.4f}",
        'Average P-Value': f"{total_p_value:.4f}",
        'Num Walk-Forward Periods': len(results_df),
        'Regime Filtering': '✅ Enabled' if use_regime_filter else '❌ Disabled',
        'Pattern Exit': '✅ Enabled' if use_pattern_exit else '❌ Disabled',
    }
    
    summary_df = pd.DataFrame([summary])
    
    print("\n" + "="*80)
    print("📈 ENHANCED DONCHIAN STRATEGY - WALK-FORWARD MCPT SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))
    print("="*80)
    
    # Save results
    output_path = os.path.join(output_dir, "results.csv")
    summary_path = os.path.join(output_dir, "summary.csv")
    
    results_df.to_csv(output_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    
    print(f"\n💾 Results saved to: {output_path}")
    print(f"💾 Summary saved to: {summary_path}")
    
    # Print simple summary (easy to read format)
    try:
        from donchian_simple_summary import print_simple_summary
        print_simple_summary(output_path, initial_capital=100000)
    except Exception as e:
        print(f"⚠️  Could not generate simple summary: {e}")
    
    print(f"\n✅ Enhanced analysis complete for {stock_symbol}.")


if __name__ == "__main__":
    main()

