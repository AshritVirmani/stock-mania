"""
Analyze Options Fetch Results

Analyzes the fetched options data to verify completeness and coverage.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def analyze_options_data(symbol, data_dir=None):
    """Analyze fetched options data."""
    if data_dir is None:
        data_dir = Path(f"analysis_results/{symbol}/options/data")
    else:
        data_dir = Path(data_dir)
    
    print("="*80)
    print(f"OPTIONS DATA ANALYSIS: {symbol}")
    print("="*80)
    
    # Check combined CSV
    combined_file = data_dir / f"{symbol}_option_chain_combined.csv"
    if not combined_file.exists():
        print(f"❌ Combined file not found: {combined_file}")
        return
    
    df = pd.read_csv(combined_file, index_col=0, parse_dates=True)
    
    print(f"\n📊 DATA SUMMARY")
    print(f"   Total rows: {len(df):,}")
    print(f"   Date range: {df.index.min()} to {df.index.max()}")
    
    # Calculate years
    years = (df.index.max() - df.index.min()).days / 365.25
    print(f"   Coverage: {years:.2f} years")
    
    # Check timezone
    print(f"   Timezone: {df.index.tz}")
    
    # Hour distribution
    df['hour'] = df.index.hour
    print(f"\n⏰ HOUR DISTRIBUTION")
    print(f"   Hours covered: {sorted(df['hour'].unique())}")
    hour_dist = df['hour'].value_counts().sort_index()
    for hour, count in hour_dist.items():
        print(f"   {hour:02d}:00 - {count:,} rows")
    
    # Market hours check
    market_hours = df.between_time('09:15', '15:30')
    print(f"\n📈 MARKET HOURS ANALYSIS")
    print(f"   Market hours (09:15-15:30): {len(market_hours):,} rows ({len(market_hours)/len(df)*100:.1f}%)")
    print(f"   Non-market hours: {len(df) - len(market_hours):,} rows")
    
    # Daily coverage
    df['date'] = df.index.date
    unique_dates = df['date'].nunique()
    expected_days = (df.index.max().date() - df.index.min().date()).days
    print(f"\n📅 DATE COVERAGE")
    print(f"   Unique trading days: {unique_dates:,}")
    print(f"   Expected days in range: {expected_days:,}")
    print(f"   Coverage: {unique_dates/expected_days*100:.1f}%")
    
    # Check individual files
    print(f"\n📁 INDIVIDUAL FILES")
    ce_file = data_dir / f"{symbol}_ATM_CE_options.csv"
    pe_file = data_dir / f"{symbol}_ATM_PE_options.csv"
    
    if ce_file.exists():
        df_ce = pd.read_csv(ce_file, index_col=0, parse_dates=True)
        print(f"   CE: {len(df_ce):,} rows ({df_ce.index.min().date()} to {df_ce.index.max().date()})")
    
    if pe_file.exists():
        df_pe = pd.read_csv(pe_file, index_col=0, parse_dates=True)
        print(f"   PE: {len(df_pe):,} rows ({df_pe.index.min().date()} to {df_pe.index.max().date()})")
    
    # JSON file
    json_file = data_dir / f"{symbol}_option_chain.json"
    if json_file.exists():
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        print(f"\n📄 JSON FILE")
        print(f"   Size: {json_file.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"   Series: {json_data.get('total_series', 'N/A')}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "HDFCBANK.NS"
    analyze_options_data(symbol)

