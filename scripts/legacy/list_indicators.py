"""
Quick script to list all Technical Analysis indicator names from your analysis files
"""

import pandas as pd
import os
import sys

def list_indicators_from_csv(csv_file):
    """List all indicators from a CSV analysis file"""
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    try:
        # Read CSV header
        df = pd.read_csv(csv_file, header=0, skiprows=[1, 2], nrows=1)
        
        # Filter indicator columns
        base_columns = ['Date', 'Price', 'Close', 'High', 'Low', 'Open', 'Volume']
        indicators = [col for col in df.columns if col not in base_columns]
        
        # Group by category
        categories = {
            'volume_': [],
            'volatility_': [],
            'trend_': [],
            'momentum_': [],
            'others_': []
        }
        
        for col in indicators:
            for prefix in categories.keys():
                if col.startswith(prefix):
                    categories[prefix].append(col)
                    break
        
        # Display results
        print("="*70)
        print(f"📊 TECHNICAL ANALYSIS INDICATORS")
        print("="*70)
        print(f"\nSource: {csv_file}")
        print(f"Total Indicators: {len(indicators)}")
        print("\n" + "-"*70)
        
        for prefix, indicator_list in categories.items():
            if indicator_list:
                category_name = prefix.replace('_', '').upper()
                print(f"\n{category_name} ({len(indicator_list)} indicators):")
                print("-" * 70)
                for i, ind in enumerate(sorted(indicator_list), 1):
                    # Remove prefix for cleaner display
                    clean_name = ind.replace(prefix, '')
                    print(f"  {i:2}. {ind:30} ({clean_name})")
        
        print("\n" + "="*70)
        print("\n💡 Usage in code:")
        print("   df['momentum_rsi']  # Access RSI")
        print("   df['trend_macd']    # Access MACD")
        print("   df['volatility_bbh'] # Access Bollinger upper band")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Default to first available analysis file
        output_dir = "output"
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith('_analysis.csv')]
            if files:
                csv_file = os.path.join(output_dir, files[0])
                print(f"Using: {csv_file}\n")
            else:
                print("❌ No analysis files found in output/ directory")
                print("   Please run analyze_indian_stocks.py first")
                return
        else:
            print("❌ Output directory not found")
            return
    
    list_indicators_from_csv(csv_file)


if __name__ == "__main__":
    main()

