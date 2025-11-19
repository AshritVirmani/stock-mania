import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from donchian_strategy import optimize_donchian, donchian_breakout

def load_stock_data(file_path):
    """
    Loads and preprocesses stock data from a CSV file.
    Renames columns to lowercase for consistency.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path, header=0, skiprows=[1, 2])
        first_col = df.columns[0]
        df = df.rename(columns={first_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # Standardize column names to lowercase
        df.columns = [col.lower() for col in df.columns]
        
        # Ensure required OHLC columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError("Missing one or more required OHLCV columns.")
            
        return df[required_cols]
    except Exception as e:
        print(f"❌ Error loading or parsing data: {e}")
        return None

def monte_carlo_permutation_test(signals, returns, iterations=1000):
    """
    Performs a Monte Carlo permutation test to determine the statistical significance
    of a trading strategy's performance.

    Args:
        signals (pd.Series): The trading signals (1, -1, 0).
        returns (pd.Series): The log returns of the asset.
        iterations (int): The number of permutation iterations to run.

    Returns:
        tuple: A tuple containing the actual strategy returns, a list of permuted
               returns, and the calculated p-value.
    """
    actual_returns = (signals * returns).cumsum().iloc[-1]
    
    permuted_returns_list = []
    shuffled_returns = returns.copy()

    for _ in range(iterations):
        # Shuffle the returns to break any real correlation with signals
        np.random.shuffle(shuffled_returns.values)
        permuted_strategy_returns = (signals * shuffled_returns).cumsum().iloc[-1]
        permuted_returns_list.append(permuted_strategy_returns)
        
    # p-value is the probability that a random strategy would outperform the actual strategy
    p_value = np.sum(permuted_returns_list >= actual_returns) / iterations
    
    return actual_returns, permuted_returns_list, p_value

class WalkForwardAnalysis:
    """
    Manages the process of walk-forward optimization and testing.
    """
    def __init__(self, data, train_period_days, test_period_days):
        self.data = data
        self.train_period = pd.Timedelta(days=train_period_days)
        self.test_period = pd.Timedelta(days=test_period_days)
        self.results = []

    def run(self, mcpt_iterations=1000):
        """
        Executes the walk-forward analysis.
        """
        start_date = self.data.index.min()
        end_date = self.data.index.max()
        
        current_date = start_date + self.train_period

        pbar = tqdm(total=(end_date - current_date).days, desc="Walk-Forward Analysis")

        while current_date + self.test_period <= end_date:
            train_start = current_date - self.train_period
            train_end = current_date - pd.Timedelta(days=1)
            test_start = current_date
            test_end = current_date + self.test_period - pd.Timedelta(days=1)

            # --- 1. Training Phase ---
            train_data = self.data.loc[train_start:train_end]
            if train_data.empty:
                current_date += self.test_period
                pbar.update(self.test_period.days)
                continue
            
            best_lookback, _ = optimize_donchian(train_data)

            # --- 2. Testing Phase ---
            test_data = self.data.loc[test_start:test_end]
            if test_data.empty:
                current_date += self.test_period
                pbar.update(self.test_period.days)
                continue

            signals = donchian_breakout(test_data, best_lookback)
            log_returns = np.log(test_data['close']).diff()

            # --- 3. MCPT ---
            # CRITICAL: Align signals and returns correctly to avoid lookahead bias
            # Signal on day T should capture return from day T to T+1
            # So we use signals[:-1] (all but last) * log_returns[1:] (returns from day 1 onwards)
            # This ensures signal[T] captures return[T+1]
            aligned_signals = signals.iloc[:-1].reset_index(drop=True)
            aligned_returns = log_returns.iloc[1:].reset_index(drop=True)
            
            # Ensure same length and drop any NaN values
            min_len = min(len(aligned_signals), len(aligned_returns))
            aligned_signals = aligned_signals.iloc[:min_len]
            aligned_returns = aligned_returns.iloc[:min_len]
            
            # Drop any NaN values (shouldn't be any after alignment, but just in case)
            valid_mask = ~(aligned_returns.isna() | aligned_signals.isna())
            aligned_signals = aligned_signals[valid_mask]
            aligned_returns = aligned_returns[valid_mask]
            
            if len(aligned_signals) == 0 or len(aligned_returns) == 0:
                # No valid data for this period
                actual_ret = 0.0
                permuted_rets = [0.0] * mcpt_iterations
                p_value = 1.0
            else:
                actual_ret, permuted_rets, p_value = monte_carlo_permutation_test(
                    aligned_signals, aligned_returns, mcpt_iterations
                )
            
            # --- 4. Store Results ---
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
                'permuted_returns': permuted_rets,  # Store all permuted returns for visualization
            })

            # Move to the next period
            current_date += self.test_period
            pbar.update(self.test_period.days)
        
        pbar.close()
        return pd.DataFrame(self.results)
