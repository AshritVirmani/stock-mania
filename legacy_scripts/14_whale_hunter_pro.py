"""
Whale Hunter Pro - Bloomberg-Style Deep Dive Charting

This script generates professional candlestick charts with whale signals overlaid.
Uses mplfinance for high-quality financial charting with integrated volume.

This is the "Deep Dive" tool - shows exactly where to enter based on whale signals.

Usage:
    python3 14_whale_hunter_pro.py <analysis_file_path>
    python3 14_whale_hunter_pro.py analysis_results/RELIANCE.NS/data/RELIANCE.NS_analysis.csv
"""

import os
import sys
import pandas as pd
import numpy as np
import argparse

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Base directory for analysis results
BASE_DIR = os.path.join(PROJECT_ROOT, "analysis_results")

try:
    import mplfinance as mpf
except ImportError:
    print("❌ Error: mplfinance is required. Install with: pip install mplfinance")
    sys.exit(1)


def get_ticker_dir(symbol):
    """Get analysis subdirectory for ticker."""
    path = os.path.join(BASE_DIR, symbol, "analysis")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def load_data(file_path):
    """Load data with smart header detection."""
    if not os.path.exists(file_path):
        return None
    try:
        # Smart load to handle potential header issues
        with open(file_path, 'r') as f:
            _ = f.readline()
            h2 = f.readline()
        skip = [1, 2] if ("Ticker" in h2 or "Price" in h2) else []
        df = pd.read_csv(file_path, skiprows=skip, index_col=0, parse_dates=True)
        return df
    except Exception as e:
        print(f"⚠️  Error reading with skiprows, trying standard read: {e}")
        return pd.read_csv(file_path, index_col=0, parse_dates=True)


class WhaleHunterPro:
    """Professional whale signal charting with candlesticks."""
    
    def __init__(self, df, symbol):
        self.df = df.copy()
        self.symbol = symbol

    def calculate_metrics(self):
        """Calculates Whale Score using the standard logic."""
        df = self.df
        
        # Ensure required columns exist
        required_cols = ['High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return df
        
        # 1. Indicators
        vol_mean = df['Volume'].rolling(20).mean()
        vol_std = df['Volume'].rolling(20).std()
        df['Vol_Z'] = (df['Volume'] - vol_mean) / (vol_std + 1e-8)
        
        df['Spread'] = df['High'] - df['Low']
        avg_spread = df['Spread'].rolling(20).mean()
        df['Spread_Ratio'] = df['Spread'] / (avg_spread + 1e-8)
        
        df['CLV'] = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'] + 1e-8)
        
        # Calculate VWAP if not present
        if 'volume_vwap' not in df.columns:
            df['volume_vwap'] = (df['High'] + df['Low'] + df['Close']) / 3

        # 2. Scoring
        df['Whale_Score'] = 0
        df.loc[df['Vol_Z'] > 2.0, 'Whale_Score'] += 2
        df.loc[df['Spread_Ratio'] > 1.5, 'Whale_Score'] += 1
        df.loc[df['Spread_Ratio'] < 0.5, 'Whale_Score'] += 1
        df.loc[df['CLV'] > 0.5, 'Whale_Score'] += 2
        df.loc[df['Close'] > df['volume_vwap'], 'Whale_Score'] += 1
        
        if 'volume_cmf' in df.columns:
            df.loc[df['volume_cmf'] > 0.05, 'Whale_Score'] += 1
        
        if 'trend_adx' in df.columns:
            df.loc[df['trend_adx'] > 25, 'Whale_Score'] += 1
            
        return df

    def plot_professional_chart(self):
        """
        Generates a High-Res Candlestick Chart with Volume and Signals.
        """
        print(f"🎨 Generating Professional Chart for {self.symbol}...")
        
        # Limit to last 6 months for visual clarity
        if len(self.df) > 0:
            cutoff_date = self.df.index.max() - pd.DateOffset(months=6)
            plot_df = self.df.loc[self.df.index >= cutoff_date].copy()
        else:
            print("⚠️  No data available for plotting")
            return
        
        if len(plot_df) == 0:
            print("⚠️  No data in last 6 months")
            return
        
        # Ensure we have OHLCV columns for mplfinance
        required_ohlc = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_ohlc = [col for col in required_ohlc if col not in plot_df.columns]
        if missing_ohlc:
            print(f"❌ Missing OHLCV columns: {missing_ohlc}")
            return
        
        # Create Marker Series (NaNs are ignored by plotter)
        # We use parallel lists to store marker price levels
        ignition_markers = [np.nan] * len(plot_df)
        stealth_markers = [np.nan] * len(plot_df)
        trap_markers = [np.nan] * len(plot_df)
        
        for i in range(len(plot_df)):
            row = plot_df.iloc[i]
            score = row.get('Whale_Score', 0)
            spread_r = row.get('Spread_Ratio', 0)
            vol_z = row.get('Vol_Z', 0)
            clv = row.get('CLV', 0)
            
            # LOGIC: IGNITION (Green Triangle)
            if (score >= 7) and (spread_r > 1.2) and (clv > 0.5):
                ignition_markers[i] = row['Low'] * 0.98  # Below candle
                
            # LOGIC: STEALTH (Blue Circle)
            elif (score >= 6) and (vol_z > 1.5) and (spread_r < 0.8):
                stealth_markers[i] = row['Low'] * 0.98  # Below candle
                
            # LOGIC: TRAP (Red X)
            elif (score >= 6) and (vol_z > 1.5) and (clv < -0.2):
                trap_markers[i] = row['High'] * 1.02  # Above candle

        # Create AddPlots (The Overlays)
        apds = []
        
        # Only add plots if markers exist
        if not all(np.isnan(x) for x in ignition_markers):
            apds.append(mpf.make_addplot(
                ignition_markers, 
                type='scatter', 
                markersize=100, 
                marker='^', 
                color='#00e676'
            ))  # Green
            
        if not all(np.isnan(x) for x in stealth_markers):
            apds.append(mpf.make_addplot(
                stealth_markers, 
                type='scatter', 
                markersize=80, 
                marker='o', 
                color='#2979ff'
            ))  # Blue
            
        if not all(np.isnan(x) for x in trap_markers):
            apds.append(mpf.make_addplot(
                trap_markers, 
                type='scatter', 
                markersize=100, 
                marker='v', 
                color='#ff1744'
            ))  # Red

        # File Path
        out_path = os.path.join(get_ticker_dir(self.symbol), "whale_entry_map_pro.png")
        
        # Styling (The "Pro" Look)
        # 'yahoo' style mimics standard financial charts nicely
        try:
            s = mpf.make_mpf_style(base_mpf_style='yahoo', y_on_right=True)
        except:
            # Fallback if yahoo style not available
            s = mpf.make_mpf_style(y_on_right=True)
        
        # Prepare data for mplfinance (needs OHLCV columns)
        plot_data = plot_df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        
        # Plot
        try:
            mpf.plot(
                plot_data,
                type='candle',       # The main upgrade
                volume=True,         # Integrated volume bar
                style=s,
                addplot=apds if apds else None,
                title=f"\n{self.symbol} INSTITUTIONAL FOOTPRINTS (PRO)\n(Green=Ignition, Blue=Stealth, Red=Trap)",
                figsize=(14, 8),
                panel_ratios=(6, 2),  # Bigger price chart, smaller volume
                savefig=dict(fname=out_path, dpi=200, bbox_inches='tight')
            )
            print(f"✅ Professional Chart saved to: {out_path}")
        except Exception as e:
            print(f"❌ Error generating chart: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 14_whale_hunter_pro.py <analysis_file_path>")
        print("\nExample:")
        print("  python3 14_whale_hunter_pro.py analysis_results/RELIANCE.NS/data/RELIANCE.NS_analysis.csv")
        return

    file_path = sys.argv[1]
    
    # Extract symbol from file path
    path_parts = file_path.split(os.sep)
    symbol = None
    for part in path_parts:
        if part.endswith('.NS'):
            symbol = part
            break
    
    if symbol is None:
        # Fallback: try to extract from filename
        filename = os.path.basename(file_path)
        if '_analysis.csv' in filename:
            symbol = filename.replace('_analysis.csv', '')
        else:
            print(f"❌ Could not extract symbol from path: {file_path}")
            print("   Please provide path in format: analysis_results/SYMBOL.NS/data/SYMBOL.NS_analysis.csv")
            return
    
    print(f"📊 Generating Professional Whale Chart for {symbol}")
    
    # 1. Load
    raw_df = load_data(file_path)
    if raw_df is not None and len(raw_df) > 0:
        # 2. Analyze
        pro = WhaleHunterPro(raw_df, symbol)
        pro.calculate_metrics()
        
        # 3. Plot Pro Chart
        pro.plot_professional_chart()
    else:
        print(f"❌ Failed to load data from {file_path}")


if __name__ == "__main__":
    main()

