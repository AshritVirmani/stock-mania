"""
Generate Intraday Pattern Report

Aggregates results from all pattern analyses and generates a comprehensive
HTML report.
"""

import os
import pandas as pd
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_report(symbol, analysis_dir, output_dir, simple_analysis_dir=None):
    """
    Generate HTML report.
    
    Args:
        symbol (str): Stock symbol
        analysis_dir (str): Directory containing analysis results
        output_dir (str): Directory to save report
        simple_analysis_dir (str): Optional directory for simple pattern analysis results
    """
    logger.info("📝 Generating comprehensive pattern report...")
    
    # HTML Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{symbol} - Intraday Pattern Analysis</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; background: #f5f5f5; }}
            .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }}
            h3 {{ color: #34495e; margin-top: 20px; }}
            .section {{ margin-bottom: 40px; background: #f9f9f9; padding: 20px; border-radius: 5px; border: 1px solid #ddd; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 15px; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); border-radius: 3px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
            th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; font-weight: bold; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .pattern-count {{ display: inline-block; background: #3498db; color: white; padding: 5px 10px; border-radius: 3px; margin: 5px; }}
            .insight-box {{ background: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; }}
            ul {{ line-height: 1.8; }}
            li {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
        <h1>{symbol} - Intraday Pattern Discovery Report</h1>
        <p>Comprehensive analysis of intraday data to identify time, volume, and price patterns using raw OHLCV data.</p>
    """
    
    # 0. Simple Pattern Analysis (Price-Volume Patterns)
    if simple_analysis_dir and os.path.exists(simple_analysis_dir):
        html += """
        <div class="section">
            <h2>🎯 Price-Volume Behavioral Patterns</h2>
            <p>Analysis of raw OHLCV data to detect specific behavioral patterns using mathematical normalization (Z-scores).</p>
        """
        
        # Load pattern summary
        pattern_summary_file = os.path.join(simple_analysis_dir, 'pattern_summary.csv')
        if os.path.exists(pattern_summary_file):
            pattern_df = pd.read_csv(pattern_summary_file)
            html += '<div class="insight-box"><h3>Pattern Summary</h3>'
            html += pattern_df.to_html(index=False, classes='table')
            html += '</div>'
        
        # Display top patterns
        pattern_files = {
            'Panic Sells': 'panic_sells.csv',
            'FOMO Buys': 'fomo_buys.csv',
            'Iceberg/Absorption': 'icebergs.csv',
            'Bullish Stop Hunts': 'stop_hunts.csv',
            'Bearish Stop Hunts': 'bearish_stop_hunts.csv',
            'Volume Divergence Bearish': 'vol_divergence_bearish.csv',
            'Volume Divergence Bullish': 'vol_divergence_bullish.csv',
            'Exhaustion Bullish': 'exhaustion_bullish.csv',
            'Exhaustion Bearish': 'exhaustion_bearish.csv',
            'Volume Confirmation Bullish': 'vol_confirmation_bullish.csv',
            'Volume Confirmation Bearish': 'vol_confirmation_bearish.csv',
            'Accumulation': 'accumulation.csv',
            'Distribution': 'distribution.csv'
        }
        
        html += '<div class="grid">'
        for pattern_name, filename in pattern_files.items():
            pattern_file = os.path.join(simple_analysis_dir, filename)
            if os.path.exists(pattern_file):
                pattern_data = pd.read_csv(pattern_file, index_col=0, parse_dates=True)
                if len(pattern_data) > 0:
                    html += f'<div><h4>{pattern_name}</h4>'
                    html += f'<p><strong>Count:</strong> {len(pattern_data)}</p>'
                    # Show top 3 examples
                    display_cols = ['Close', 'Volume', 'Vol_Z', 'Returns']
                    available_cols = [col for col in display_cols if col in pattern_data.columns]
                    if available_cols:
                        html += pattern_data[available_cols].head(3).to_html(classes='table')
                    html += '</div>'
        html += '</div></div>'
    
    # 1. Time Patterns
    time_dir = os.path.join(analysis_dir, 'time_patterns')
    if os.path.exists(time_dir):
        html += """
            <div class="section">
                <h2>⏰ Time-Based Patterns</h2>
                <p>Analysis of returns, volatility, and volume patterns across different times of day and days of week.</p>
                <div class="grid">
        """
        
        # Load and display summary stats
        hourly_file = os.path.join(time_dir, 'hourly_analysis.csv')
        if os.path.exists(hourly_file):
            hourly_df = pd.read_csv(hourly_file, index_col=0)
            if 'cumulative_return_pct' in hourly_df.columns:
                best_hour = hourly_df['cumulative_return_pct'].idxmax()
                worst_hour = hourly_df['cumulative_return_pct'].idxmin()
                html += f'<div class="insight-box"><h3>Key Insights</h3><ul>'
                html += f'<li>Best Hour: {best_hour} ({hourly_df.loc[best_hour, "cumulative_return_pct"]:.2f}% cumulative return)</li>'
                html += f'<li>Worst Hour: {worst_hour} ({hourly_df.loc[worst_hour, "cumulative_return_pct"]:.2f}% cumulative return)</li>'
                if 'Volume_mean' in hourly_df.columns:
                    html += f'<li>Highest Volume Hour: {hourly_df["Volume_mean"].idxmax()} ({hourly_df["Volume_mean"].max():,.0f} avg volume)</li>'
                html += f'</ul></div>'
        
        for img in ['hourly_patterns.png', 'day_of_week_patterns.png', 'time_heatmap.png']:
            img_path = os.path.join(time_dir, img)
            if os.path.exists(img_path):
                # Use relative path from report location
                rel_path = os.path.join('time_patterns', img)
                html += f'<div><h4>{img.replace(".png", "").replace("_", " ").title()}</h4><img src="{rel_path}" alt="{img}"></div>'
                
        html += """
                </div>
            </div>
        """
    
    # 2. Volume Patterns
    vol_dir = os.path.join(analysis_dir, 'volume_patterns')
    if os.path.exists(vol_dir):
        html += """
            <div class="section">
                <h2>🔊 Volume Patterns</h2>
                <p>Analysis of volume spikes, breakouts, and volume-price relationships.</p>
                <div class="grid">
        """
        
        # Add volume spike summary
        spikes_file = os.path.join(vol_dir, 'volume_spikes.csv')
        if os.path.exists(spikes_file):
            spikes_df = pd.read_csv(spikes_file)
            html += f'<div class="insight-box"><h3>Volume Spike Summary</h3><ul>'
            html += f'<li>Total Spikes: {len(spikes_df):,}</li>'
            if 'ret_5min' in spikes_df.columns:
                avg_ret = spikes_df['ret_5min'].mean() * 100
                html += f'<li>Avg 5-min Return After Spike: {avg_ret:.3f}%</li>'
            html += '</ul></div>'
        
        for img in ['volume_spike_scatter.png', 'volume_breakout_dist.png']:
            img_path = os.path.join(vol_dir, img)
            if os.path.exists(img_path):
                rel_path = os.path.join('volume_patterns', img)
                html += f'<div><h4>{img.replace(".png", "").replace("_", " ").title()}</h4><img src="{rel_path}" alt="{img}"></div>'
                
        html += """
                </div>
            </div>
        """
    
    # 3. Price Patterns
    price_dir = os.path.join(analysis_dir, 'price_patterns')
    if os.path.exists(price_dir):
        html += """
            <div class="section">
                <h2>📈 Price Movement Patterns</h2>
                <p>Analysis of momentum, reversals, and price action patterns.</p>
                <div class="grid">
        """
        
        # Add momentum summary
        mom_file = os.path.join(price_dir, 'momentum_analysis.csv')
        if os.path.exists(mom_file):
            mom_df = pd.read_csv(mom_file)
            html += f'<div><h3>Momentum Patterns</h3>'
            html += mom_df.to_html(index=False, classes='table')
            html += '</div>'
        
        if os.path.exists(os.path.join(price_dir, 'reversal_performance.png')):
            rel_path = os.path.join('price_patterns', 'reversal_performance.png')
            html += f'<div><h4>Reversal Pattern Performance</h4><img src="{rel_path}" alt="Reversal Performance"></div>'
            
        html += """
                </div>
            </div>
        """
    
    # 4. Indicator Combinations (if available)
    combo_dir = os.path.join(analysis_dir, 'indicator_combinations')
    if os.path.exists(combo_dir):
        html += """
            <div class="section">
                <h2>🔗 Indicator Combinations</h2>
                <p>Analysis of combined indicator signals (requires indicator data).</p>
                <div class="grid">
        """
        
        if os.path.exists(os.path.join(combo_dir, 'pair_accuracy.png')):
            rel_path = os.path.join('indicator_combinations', 'pair_accuracy.png')
            html += f'<div><img src="{rel_path}" alt="Pair Accuracy"></div>'
            
        # Load top pairs table
        pair_file = os.path.join(combo_dir, 'top_pairs.csv')
        if os.path.exists(pair_file):
            df = pd.read_csv(pair_file)
            html += '<div><h3>Top Pairs</h3>' + df.head(10).to_html(index=False, classes='table') + '</div>'
            
        html += """
                </div>
            </div>
        """
    
    # Footer
    html += """
        </div>
    </body>
    </html>
    """
    
    report_file = os.path.join(output_dir, 'comprehensive_pattern_report.html')
    with open(report_file, 'w') as f:
        f.write(html)
        
    logger.info(f"✅ Report generated: {report_file}")
    return report_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', required=True, help='Stock symbol')
    parser.add_argument('--analysis-dir', required=True, help='Analysis directory')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--simple-analysis-dir', help='Simple pattern analysis directory')
    args = parser.parse_args()
    
    generate_report(args.symbol, args.analysis_dir, args.output_dir, args.simple_analysis_dir)
