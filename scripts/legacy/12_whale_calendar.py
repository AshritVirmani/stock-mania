"""
Whale Calendar - Complete Strategy Calendar

This script generates a comprehensive calendar that combines:
1. Whale buy signals (based on volume, spread, CLV, etc.)
2. Regime data (from data_with_regimes.csv)

Key Features:
- Regime 3 (Crash): Signals get crossed out (⛔) - these are bull traps
- Regime 1 (Rally): Signals get a gold star (⭐) - high conviction
- Shows last 6 months of trading activity

Usage:
    python3 12_whale_calendar.py <analysis_file_path>
    python3 12_whale_calendar.py analysis_results/RELIANCE.NS/data/RELIANCE.NS_analysis.csv
"""

import os
import sys
import pandas as pd
import calendar
from datetime import datetime

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Base directory for analysis results
BASE_DIR = os.path.join(PROJECT_ROOT, "analysis_results")


def get_ticker_dir(symbol):
    """Get analysis subdirectory for ticker."""
    path = os.path.join(BASE_DIR, symbol, "analysis")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def load_merged_data(file_path, symbol):
    """
    Loads Price Data AND merges it with the previously generated Regime Data.
    
    Args:
        file_path: Path to the analysis CSV file
        symbol: Stock symbol (e.g., 'RELIANCE.NS')
    
    Returns:
        pandas.DataFrame: Merged dataframe with price data and regime information
    """
    # 1. Load Price/Indicator Data
    try:
        with open(file_path, 'r') as f:
            _ = f.readline()
            h2 = f.readline()
        skip = [1, 2] if ("Ticker" in h2 or "Price" in h2) else []
        df = pd.read_csv(file_path, skiprows=skip, index_col=0, parse_dates=True)
    except Exception as e:
        print(f"⚠️  Error reading CSV with skiprows, trying standard read: {e}")
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)

    # 2. Load Regime Data (The "Previous Data")
    # We look in the analysis folder for the regime file
    regime_path = os.path.join(BASE_DIR, symbol, "analysis", "data_with_regimes.csv")
    
    if os.path.exists(regime_path):
        print(f"✅ Found Regime Data: {regime_path}")
        df_regime = pd.read_csv(regime_path, index_col=0, parse_dates=True)
        # Merge 'regime' column into main df
        if 'regime' in df_regime.columns:
            # We combine using index to ensure dates match
            df = df.join(df_regime[['regime']], how='left')
            print(f"   Merged regime data: {df['regime'].notna().sum()} dates have regime info")
    else:
        print("⚠️  Regime Data not found. Calendar will lack Regime filters.")
        df['regime'] = 2  # Default to 'Normal' if missing

    return df


class CompleteWhaleCalendar:
    """Complete Whale Calendar that combines whale signals with regime data."""
    
    def __init__(self, df, symbol):
        self.df = df.copy()
        self.symbol = symbol

    def calculate_events(self):
        """Calculate whale signals and apply regime filtering."""
        df = self.df
        
        # Ensure required columns exist
        required_cols = ['High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return df
        
        # --- 1. Whale Scoring (Micro) ---
        vol_mean = df['Volume'].rolling(20).mean()
        vol_std = df['Volume'].rolling(20).std()
        df['Vol_Z'] = (df['Volume'] - vol_mean) / (vol_std + 1e-8)  # Add epsilon to avoid division by zero
        
        df['Spread'] = df['High'] - df['Low']
        avg_spread = df['Spread'].rolling(20).mean()
        df['Spread_Ratio'] = df['Spread'] / (avg_spread + 1e-8)
        
        df['CLV'] = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'] + 1e-8)
        
        # Calculate VWAP if not present
        if 'volume_vwap' not in df.columns:
            # Simple VWAP approximation: typical price
            df['volume_vwap'] = (df['High'] + df['Low'] + df['Close']) / 3

        # Initialize score
        df['Score'] = 0
        
        # Scoring logic
        df.loc[df['Vol_Z'] > 2.0, 'Score'] += 2
        df.loc[df['Spread_Ratio'] > 1.5, 'Score'] += 1
        df.loc[df['Spread_Ratio'] < 0.5, 'Score'] += 1
        df.loc[df['CLV'] > 0.5, 'Score'] += 2
        df.loc[df['Close'] > df['volume_vwap'], 'Score'] += 1
        
        if 'volume_cmf' in df.columns:
            df.loc[df['volume_cmf'] > 0.05, 'Score'] += 1
        
        if 'trend_adx' in df.columns:
            df.loc[df['trend_adx'] > 25, 'Score'] += 1

        # --- 2. Event Types ---
        df['Event_Icon'] = ""
        df['CSS_Class'] = "day-neutral"
        df['Overlay'] = ""
        
        # Whale Signals
        mask_ign = (df['Score'] >= 7) & (df['Spread_Ratio'] > 1.2) & (df['CLV'] > 0.5)
        df.loc[mask_ign, 'Event_Icon'] = "🚀"
        df.loc[mask_ign, 'CSS_Class'] = "day-ignition"
        
        mask_stl = (df['Score'] >= 6) & (df['Vol_Z'] > 1.5) & (df['Spread_Ratio'] < 0.8)
        df.loc[mask_stl, 'Event_Icon'] = "🕵️"
        df.loc[mask_stl, 'CSS_Class'] = "day-stealth"
        
        mask_trp = (df['Score'] >= 6) & (df['Vol_Z'] > 1.5) & (df['CLV'] < -0.2)
        df.loc[mask_trp, 'Event_Icon'] = "🪤"
        df.loc[mask_trp, 'CSS_Class'] = "day-trap"

        # --- 3. Regime Filtering (Macro) ---
        # If Regime 3 (Crash) -> Invalidates Signals
        if 'regime' in df.columns:
            crash_mask = (df['regime'] == 3)
            df.loc[crash_mask, 'CSS_Class'] = "day-crash"  # Override color
            # If there was a signal, mark it as invalidated
            df.loc[crash_mask & (df['Event_Icon'] != ""), 'Overlay'] = "⛔"
            
            # If Regime 1 (Rally) -> Boosts Signals
            rally_mask = (df['regime'] == 1)
            # Add 'gold-star' indicator
            df.loc[rally_mask, 'Overlay'] = df.loc[rally_mask, 'Overlay'].astype(str) + "⭐"

        return df

    def generate_html_calendar(self):
        """Generate the complete HTML calendar."""
        print("📅 Fusing Regime Data & Whale Signals...")
        df = self.calculate_events()
        # Get last 6 months of data
        if len(df) > 0:
            cutoff_date = df.index.max() - pd.DateOffset(months=6)
            df = df.loc[df.index >= cutoff_date]
        
        if len(df) == 0:
            print("⚠️  No data in last 6 months. Cannot generate calendar.")
            return
        
        grouped = df.groupby([df.index.year, df.index.month])
        html_calendars = ""
        
        for (year, month), group in grouped:
            cal = calendar.monthcalendar(year, month)
            month_name = calendar.month_name[month]
            
            html_calendars += f'<div class="month-block"><h3>{month_name} {year}</h3>'
            html_calendars += '<table class="calendar-table"><thead><tr>'
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                html_calendars += f'<th>{day}</th>'
            html_calendars += '</tr></thead><tbody>'
            
            for week in cal:
                html_calendars += '<tr>'
                for day in week:
                    if day == 0:
                        html_calendars += '<td class="empty"></td>'
                    else:
                        try:
                            date_str = f"{year}-{month:02d}-{day:02d}"
                            date_index = pd.to_datetime(date_str)
                            
                            if date_index in group.index:
                                row = group.loc[date_index]
                                if isinstance(row, pd.Series):
                                    # Single row
                                    score = int(row.get('Score', 0))
                                    icon = str(row.get('Event_Icon', ''))
                                    css = str(row.get('CSS_Class', 'day-neutral'))
                                    overlay = str(row.get('Overlay', ''))
                                    price = f"{row.get('Close', 0):.1f}"
                                    regime_id = int(row.get('regime', 99))
                                else:
                                    # Multiple rows (shouldn't happen, but handle it)
                                    row = row.iloc[-1]
                                    score = int(row.get('Score', 0))
                                    icon = str(row.get('Event_Icon', ''))
                                    css = str(row.get('CSS_Class', 'day-neutral'))
                                    overlay = str(row.get('Overlay', ''))
                                    price = f"{row.get('Close', 0):.1f}"
                                    regime_id = int(row.get('regime', 99))
                                
                                # Tooltip content
                                title = f"Regime: {regime_id} | Score: {score} | Price: {price}"
                                
                                html_calendars += f'<td class="{css}" title="{title}">'
                                html_calendars += f'<div class="date-num">{day}</div>'
                                html_calendars += f'<div class="day-content">'
                                
                                # Regime 1 (Rally) gets a Gold Star indicator if not already marked
                                if "⭐" in overlay:
                                    html_calendars += f'<div class="star-badge">★</div>'
                                
                                html_calendars += f'<div class="icon">{icon}</div>'
                                
                                # Regime 3 (Crash) overlay
                                if "⛔" in overlay:
                                    html_calendars += f'<div class="block-overlay">⛔</div>'
                                
                                html_calendars += f'<div class="score">R{regime_id} | S{score}</div>'
                                html_calendars += f'</div></td>'
                            else:
                                html_calendars += f'<td class="day-neutral"><div class="date-num">{day}</div></td>'
                        except Exception as e:
                            # Silently handle errors for individual days
                            html_calendars += f'<td class="day-neutral"><div class="date-num">{day}</div></td>'
                html_calendars += '</tr>'
            html_calendars += '</tbody></table></div>'

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Complete Strategy Calendar: {self.symbol}</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #e9ecef; padding: 20px; }}
                h1 {{ text-align: center; color: #2c3e50; }}
                .legend {{ display:flex; justify-content:center; gap:15px; flex-wrap:wrap; margin-bottom:20px; background:white; padding:15px; border-radius:8px; }}
                .legend-item {{ display:flex; align-items:center; gap:5px; font-size:0.9em; font-weight:bold; }}
                
                .month-block {{ background: white; padding: 20px; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                h3 {{ margin-top: 0; color: #34495e; border-bottom: 2px solid #f1f3f5; padding-bottom: 10px; }}
                
                .calendar-table {{ width: 100%; table-layout: fixed; border-collapse: separate; border-spacing: 2px; }}
                th {{ padding: 10px; color: #adb5bd; font-size: 0.8em; text-transform: uppercase; }}
                td {{ height: 100px; border-radius: 4px; vertical-align: top; padding: 5px; position: relative; background: #f8f9fa; }}
                
                .date-num {{ font-size: 0.8em; color: #ced4da; font-weight:bold; }}
                .day-content {{ text-align: center; height:100%; display:flex; flex-direction:column; justify-content:center; }}
                .icon {{ font-size: 2em; line-height: 1; }}
                .score {{ font-size: 0.7em; color: #495057; margin-top: 5px; }}
                
                .star-badge {{ position:absolute; top:5px; right:5px; color: gold; font-size: 1.2em; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }}
                .block-overlay {{ position:absolute; top:0; left:0; width:100%; height:100%; display:flex; align-items:center; justify-content:center; font-size: 3em; opacity: 0.7; background: rgba(0,0,0,0.05); }}
                
                /* REGIME STYLES */
                .day-neutral {{ background: #fff; border: 1px solid #dee2e6; }}
                .day-ignition {{ background: #d4edda; border: 2px solid #28a745; }}
                .day-stealth {{ background: #d1ecf1; border: 2px solid #17a2b8; }}
                .day-trap {{ background: #f8d7da; border: 2px solid #dc3545; }}
                .day-crash {{ background: #e2e3e5; border: 2px solid #6c757d; opacity: 0.8; }} /* Greyed out */
                
                .empty {{ background: transparent; }}
            </style>
        </head>
        <body>
            <h1>📅 Master Strategy Calendar: {self.symbol}</h1>
            
            <div class="legend">
                <span class="legend-item">🚀 Ignition (Buy)</span>
                <span class="legend-item">🕵️ Stealth (Accumulate)</span>
                <span class="legend-item">🪤 Trap (Sell)</span>
                <span class="legend-item" style="color:gold">★ High Conviction (Regime 1)</span>
                <span class="legend-item" style="color:#6c757d">⛔ Regime Blocked (Crash)</span>
            </div>

            {html_calendars}
        </body>
        </html>
        """
        
        out_path = os.path.join(get_ticker_dir(self.symbol), "complete_whale_calendar.html")
        with open(out_path, "w", encoding='utf-8') as f:
            f.write(full_html)
        print(f"✅ Complete Calendar saved to: {out_path}")
        return out_path


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 12_whale_calendar.py <analysis_file_path>")
        print("\nExample:")
        print("  python3 12_whale_calendar.py analysis_results/RELIANCE.NS/data/RELIANCE.NS_analysis.csv")
        return

    file_path = sys.argv[1]
    
    # Extract symbol from file path
    # Expected format: analysis_results/SYMBOL.NS/data/SYMBOL.NS_analysis.csv
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
    
    print(f"📊 Generating Whale Calendar for {symbol}")
    
    # 1. Load Merged Data
    df = load_merged_data(file_path, symbol)
    
    if df is not None and len(df) > 0:
        cal = CompleteWhaleCalendar(df, symbol)
        cal.generate_html_calendar()
    else:
        print(f"❌ Failed to load data from {file_path}")


if __name__ == "__main__":
    main()

