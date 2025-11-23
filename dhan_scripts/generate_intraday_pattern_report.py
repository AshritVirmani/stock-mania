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
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); border-radius: 3px; margin: 10px 0; display: block; }}
            .chart-container {{ width: 100%; max-width: 1200px; margin: 20px auto; text-align: center; }}
            .chart-container img {{ width: 100%; max-width: 100%; height: auto; }}
            .small-chart {{ max-width: 600px; margin: 10px auto; display: block; }}
            .large-chart {{ max-width: 1400px; margin: 20px auto; display: block; }}
            .faq-section {{ background: #f0f8ff; padding: 25px; border-radius: 8px; margin: 30px 0; border-left: 5px solid #3498db; }}
            .faq-item {{ margin: 20px 0; padding: 15px; background: white; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .faq-question {{ font-weight: bold; color: #2980b9; margin-bottom: 8px; font-size: 1.1em; }}
            .faq-answer {{ color: #34495e; line-height: 1.8; }}
            .faq-answer code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
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
        # New naming pattern (symbol-prefixed) and old pattern (backward compatibility)
        pattern_mappings = {
            'Hidden Accumulation': ['hidden_accumulation.csv', 'accumulation.csv'],
            'Hidden Distribution': ['hidden_distribution.csv', 'distribution.csv'],
            'Bullish Sweep': ['bullish_sweep.csv', 'stop_hunts.csv'],
            'Bearish Sweep': ['bearish_sweep.csv', 'bearish_stop_hunts.csv'],
            'Iceberg/Absorption': ['iceberg.csv', 'icebergs.csv'],
            'Panic Sells': ['panic_sells.csv'],
            'FOMO Buys': ['fomo_buys.csv'],
            'Volume Divergence Bearish': ['vol_divergence_bearish.csv'],
            'Volume Divergence Bullish': ['vol_divergence_bullish.csv'],
            'Exhaustion Bullish': ['exhaustion_bullish.csv'],
            'Exhaustion Bearish': ['exhaustion_bearish.csv'],
            'Volume Confirmation Bullish': ['vol_confirmation_bullish.csv'],
            'Volume Confirmation Bearish': ['vol_confirmation_bearish.csv'],
            'Capitulation': ['capitulation.csv']
        }
        
        html += '<div class="grid">'
        for pattern_name, filename_options in pattern_mappings.items():
            pattern_file = None
            # Try symbol-prefixed names first, then generic names
            for filename_option in filename_options:
                # Try with symbol prefix
                symbol_prefix_file = os.path.join(simple_analysis_dir, f'{symbol}_{filename_option}')
                if os.path.exists(symbol_prefix_file):
                    pattern_file = symbol_prefix_file
                    break
                # Try without prefix
                generic_file = os.path.join(simple_analysis_dir, filename_option)
                if os.path.exists(generic_file):
                    pattern_file = generic_file
                    break
            
            if pattern_file and os.path.exists(pattern_file):
                try:
                    pattern_data = pd.read_csv(pattern_file, index_col=0, parse_dates=True)
                    if len(pattern_data) > 0:
                        html += f'<div><h4>{pattern_name}</h4>'
                        html += f'<p><strong>Count:</strong> {len(pattern_data)}</p>'
                        # Show top 3 examples
                        display_cols = ['Close', 'Volume', 'Vol_Z', 'Returns', 'High', 'Low', 'Open']
                        available_cols = [col for col in display_cols if col in pattern_data.columns]
                        if available_cols:
                            html += pattern_data[available_cols].head(3).to_html(classes='table')
                        html += '</div>'
                except Exception as e:
                    logger.warning(f"Could not load pattern file {pattern_file}: {e}")
                    continue
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
        
        # Helper function to convert hour number to IST time
        def hour_to_ist(hour_num):
            """Convert hour number (0-23) to IST time string with proper AM/PM format"""
            if pd.isna(hour_num):
                return "N/A"
            hour_int = int(hour_num)
            # Handle 24-hour format with AM/PM
            if hour_int == 0:
                return "12:00 AM - 1:00 AM IST"
            elif 1 <= hour_int < 9:
                return f"{hour_int}:00 AM - {hour_int+1}:00 AM IST"
            elif hour_int == 9:
                return "9:00 AM - 10:00 AM IST (Market opens at 9:15 AM)"
            elif hour_int == 10:
                return "10:00 AM - 11:00 AM IST"
            elif hour_int == 11:
                return "11:00 AM - 12:00 PM IST"
            elif hour_int == 12:
                return "12:00 PM - 1:00 PM IST"
            elif hour_int == 13:
                return "1:00 PM - 2:00 PM IST"
            elif hour_int == 14:
                return "2:00 PM - 3:00 PM IST"
            elif hour_int == 15:
                return "3:00 PM - 4:00 PM IST (Market closes at 3:30 PM)"
            elif 16 <= hour_int <= 23:
                return f"{hour_int-12}:00 PM - {hour_int-11}:00 PM IST" if hour_int > 12 else f"{hour_int}:00 PM - {hour_int+1}:00 PM IST"
            else:
                return f"{hour_int}:00 IST"
        
        # Load and display summary stats
        hourly_file = os.path.join(time_dir, 'hourly_analysis.csv')
        if os.path.exists(hourly_file):
            hourly_df = pd.read_csv(hourly_file, index_col=0)
            if 'cumulative_return_pct' in hourly_df.columns:
                best_hour = hourly_df['cumulative_return_pct'].idxmax()
                worst_hour = hourly_df['cumulative_return_pct'].idxmin()
                html += f'<div class="insight-box"><h3>Key Insights</h3><ul>'
                html += f'<li><strong>Best Hour:</strong> Hour {int(best_hour)} ({hour_to_ist(best_hour)}) - {hourly_df.loc[best_hour, "cumulative_return_pct"]:.2f}% cumulative return</li>'
                html += f'<li><strong>Worst Hour:</strong> Hour {int(worst_hour)} ({hour_to_ist(worst_hour)}) - {hourly_df.loc[worst_hour, "cumulative_return_pct"]:.2f}% cumulative return</li>'
                if 'Volume_mean' in hourly_df.columns:
                    vol_hour = hourly_df["Volume_mean"].idxmax()
                    html += f'<li><strong>Highest Volume Hour:</strong> Hour {int(vol_hour)} ({hour_to_ist(vol_hour)}) - {hourly_df["Volume_mean"].max():,.0f} avg volume</li>'
                html += f'</ul></div>'
        
        # Add hourly analysis table
        if os.path.exists(hourly_file):
            html += '<div><h3>Hourly Analysis Summary</h3>'
            # Show top 5 hours by cumulative return
            display_cols = ['cumulative_return_pct', 'returns_mean_pct', 'volatility_mean_pct', 'Volume_mean']
            available_cols = [col for col in display_cols if col in hourly_df.columns]
            if available_cols:
                top_hours = hourly_df.nlargest(5, 'cumulative_return_pct')[available_cols].copy()
                # Add IST time column
                top_hours['IST_Time'] = top_hours.index.map(hour_to_ist)
                # Reorder columns to show IST time first
                cols_order = ['IST_Time'] + [c for c in top_hours.columns if c != 'IST_Time']
                top_hours = top_hours[cols_order]
                html += top_hours.to_html(classes='table')
            html += '</div>'
        
        # Add day-of-week analysis
        day_file = os.path.join(time_dir, 'day_of_week_analysis.csv')
        if os.path.exists(day_file):
            day_df = pd.read_csv(day_file, index_col=0)
            html += '<div><h3>Day of Week Analysis</h3>'
            display_cols = ['returns_mean_pct', 'volatility_mean_pct', 'Volume_mean']
            available_cols = [col for col in display_cols if col in day_df.columns]
            if available_cols:
                html += day_df[available_cols].to_html(classes='table')
            html += '</div>'
        
        # Close the grid before adding images
        html += '</div>'  # Close grid
        
        # Add images in separate rows to prevent overlapping
        html += '<div style="display: flex; flex-direction: column; gap: 30px; margin-top: 20px;">'
        
        # Hourly patterns chart
        hourly_img_path = os.path.join(time_dir, 'hourly_patterns.png')
        if os.path.exists(hourly_img_path):
            rel_path = os.path.relpath(hourly_img_path, output_dir)
            html += f'<div class="chart-container" style="width: 100%; margin-bottom: 30px;"><h4>Hourly Patterns</h4><img src="{rel_path}" alt="hourly_patterns"></div>'
        
        # Day of week patterns chart
        day_img_path = os.path.join(time_dir, 'day_of_week_patterns.png')
        if os.path.exists(day_img_path):
            rel_path = os.path.relpath(day_img_path, output_dir)
            html += f'<div class="chart-container small-chart" style="width: 100%; max-width: 800px; margin: 0 auto 30px;"><h4>Day of Week Patterns</h4><img src="{rel_path}" alt="day_of_week_patterns"></div>'
        
        # Time heatmap
        heatmap_img_path = os.path.join(time_dir, 'time_heatmap.png')
        if os.path.exists(heatmap_img_path):
            rel_path = os.path.relpath(heatmap_img_path, output_dir)
            html += f'<div class="chart-container large-chart" style="width: 100%; margin-bottom: 30px;"><h4>Time Heatmap (Green = Positive Returns, Red = Negative Returns)</h4><img src="{rel_path}" alt="time_heatmap"></div>'
        
        html += '</div>'  # Close image container
        
        # FAQ for Time-Based Patterns
        html += """
                </div>
                <div class="faq-section">
                    <h3>❓ FAQ: Time-Based Patterns</h3>
                    <div class="faq-item">
                        <div class="faq-question">Q: What do the hour numbers mean?</div>
                        <div class="faq-answer">
                            <strong>Hour numbers correspond to IST (Indian Standard Time):</strong><br>
                            - <strong>Hour 9:</strong> 9:00 AM - 10:00 AM IST (Market opens at 9:15 AM)<br>
                            - <strong>Hour 10:</strong> 10:00 AM - 11:00 AM IST<br>
                            - <strong>Hour 11:</strong> 11:00 AM - 12:00 PM IST<br>
                            - <strong>Hour 12:</strong> 12:00 PM - 1:00 PM IST<br>
                            - <strong>Hour 13:</strong> 1:00 PM - 2:00 PM IST<br>
                            - <strong>Hour 14:</strong> 2:00 PM - 3:00 PM IST<br>
                            - <strong>Hour 15:</strong> 3:00 PM - 4:00 PM IST (Market closes at 3:30 PM)<br><br>
                            <strong>Note:</strong> Hours 0-8 are pre-market, and hours 16-23 are post-market. Only hours 9-15 contain trading data.
                        </div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">Q: What do the charts show?</div>
                        <div class="faq-answer">
                            <strong>Hourly Patterns Chart (3 panels):</strong><br>
                            - <strong>Top Panel:</strong> X-axis = Hour (9-15), Y-axis = Cumulative Return (%) - Shows which hours are most profitable<br>
                            - <strong>Middle Panel:</strong> X-axis = Hour, Y-axis = Average Volatility (%) - Shows price range by hour<br>
                            - <strong>Bottom Panel:</strong> X-axis = Hour, Y-axis = Average Volume - Shows trading activity by hour<br><br>
                            <strong>Day of Week Patterns (2 panels):</strong><br>
                            - <strong>Top:</strong> X-axis = Day (Mon-Fri), Y-axis = Average Return (%) - Best/worst days<br>
                            - <strong>Bottom:</strong> X-axis = Day, Y-axis = Average Volatility (%) - Volatility by day<br><br>
                            <strong>Time Heatmap:</strong><br>
                            - X-axis = Hour (9-15), Y-axis = Day of Week (Mon-Fri)<br>
                            - Color = Average Return (Green = positive, Red = negative)<br>
                            - Shows which hour-day combinations are most profitable
                        </div>
                    </div>
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
        
        # Add volume breakouts table
        breakouts_file = os.path.join(vol_dir, 'volume_breakouts.csv')
        if os.path.exists(breakouts_file):
            try:
                breakouts_df = pd.read_csv(breakouts_file, index_col=0, parse_dates=True)
                if len(breakouts_df) > 0:
                    html += '<div><h3>Volume Breakouts</h3>'
                    html += f'<p><strong>Total Breakouts:</strong> {len(breakouts_df)}</p>'
                    # Show top 5 breakouts
                    display_cols = ['Close', 'Volume', 'direction']
                    available_cols = [col for col in display_cols if col in breakouts_df.columns]
                    if available_cols:
                        html += breakouts_df[available_cols].head(5).to_html(classes='table')
                    html += '</div>'
            except Exception as e:
                logger.warning(f"Could not load volume breakouts: {e}")
        
        # Close grid before adding images
        html += '</div>'  # Close grid
        
        # Add images in separate rows
        html += '<div style="display: flex; flex-direction: column; gap: 30px; margin-top: 20px;">'
        
        # Volume spike scatter
        spike_img_path = os.path.join(vol_dir, 'volume_spike_scatter.png')
        if os.path.exists(spike_img_path):
            rel_path = os.path.relpath(spike_img_path, output_dir)
            # Check if we have data
            if os.path.exists(spikes_file) and len(spikes_df) > 0:
                html += f'<div class="chart-container" style="width: 100%; margin-bottom: 30px;"><h4>Volume Spike Scatter</h4><img src="{rel_path}" alt="volume_spike_scatter"></div>'
            else:
                html += '<div class="insight-box"><p>⚠️ Volume spike scatter chart exists but no spike data available. Check if volume threshold is too high.</p></div>'
        else:
            # Try to generate it if data exists
            if os.path.exists(spikes_file) and len(spikes_df) > 0:
                html += '<div class="insight-box"><p>⚠️ Volume spike scatter chart not found. Re-run volume pattern analysis to generate it.</p></div>'
            else:
                html += '<div class="insight-box"><p>⚠️ No volume spikes detected (threshold may be too high or insufficient data).</p></div>'
        
        # Volume breakout distribution
        breakout_img_path = os.path.join(vol_dir, 'volume_breakout_dist.png')
        if os.path.exists(breakout_img_path):
            rel_path = os.path.relpath(breakout_img_path, output_dir)
            html += f'<div class="chart-container small-chart" style="width: 100%; max-width: 600px; margin: 0 auto 30px;"><h4>Volume Breakout Distribution</h4><img src="{rel_path}" alt="volume_breakout_dist"></div>'
        
        html += '</div>'  # Close image container
                
        # FAQ for Volume Patterns
        html += """
                </div>
                <div class="faq-section">
                    <h3>❓ FAQ: Volume Patterns</h3>
                    <div class="faq-item">
                        <div class="faq-question">Q: What do the volume charts show?</div>
                        <div class="faq-answer">
                            <strong>Volume Spike Scatter:</strong><br>
                            - X-axis: Price change at spike time (%) - Shows if price moved up or down when volume spiked<br>
                            - Y-axis: Volume ratio (multiple of 20-period moving average) - Shows how much higher volume was vs normal<br>
                            - Color: 5-minute forward return - Shows what happened after the spike<br>
                            - <strong>Interpretation:</strong> Points in top-right (high volume + price up) suggest bullish momentum. Points in top-left suggest selling pressure.<br><br>
                            <strong>Volume Breakout Distribution:</strong><br>
                            - X-axis: Direction (Up or Down) - Shows if breakouts were bullish or bearish<br>
                            - Y-axis: Count - Number of breakouts in each direction<br>
                            - <strong>Interpretation:</strong> Breakouts require top 10% volume AND top 10% price movement - indicates strong institutional activity
                        </div>
                    </div>
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
            try:
                mom_df = pd.read_csv(mom_file)
                html += f'<div><h3>Momentum Patterns</h3>'
                html += mom_df.to_html(index=False, classes='table')
                html += '</div>'
            except Exception as e:
                logger.warning(f"Could not load momentum analysis: {e}")
        
        # Add reversal patterns table
        reversal_file = os.path.join(price_dir, 'reversal_patterns.csv')
        if os.path.exists(reversal_file):
            try:
                reversal_df = pd.read_csv(reversal_file, index_col=0, parse_dates=True)
                if len(reversal_df) > 0:
                    html += '<div><h3>Reversal Patterns</h3>'
                    html += f'<p><strong>Total Reversals:</strong> {len(reversal_df)}</p>'
                    # Show top 5 reversals
                    display_cols = ['Close', 'Volume', 'pattern_type']
                    available_cols = [col for col in display_cols if col in reversal_df.columns]
                    if available_cols:
                        html += reversal_df[available_cols].head(5).to_html(classes='table')
                    html += '</div>'
            except Exception as e:
                logger.warning(f"Could not load reversal patterns: {e}")
        
        reversal_img = os.path.join(price_dir, 'reversal_performance.png')
        if os.path.exists(reversal_img):
            rel_path = os.path.relpath(reversal_img, output_dir)
            html += f'<div class="chart-container small-chart"><h4>Reversal Pattern Performance</h4><img src="{rel_path}" alt="Reversal Performance"></div>'
            
        # FAQ for Price Patterns
        html += """
                </div>
                <div class="faq-section">
                    <h3>❓ FAQ: Price Movement Patterns</h3>
                    <div class="faq-item">
                        <div class="faq-question">Q: What are momentum and reversal patterns?</div>
                        <div class="faq-answer">
                            <strong>Momentum Patterns:</strong><br>
                            - <strong>3 Up:</strong> Three consecutive candles with positive returns - tests if momentum continues<br>
                            - <strong>3 Down:</strong> Three consecutive candles with negative returns - tests if momentum continues<br>
                            - <strong>Continuation Rate:</strong> Percentage of times the pattern continues in the same direction<br><br>
                            <strong>Reversal Patterns:</strong><br>
                            - <strong>Hammer:</strong> Long lower wick (>2x body), small upper wick - bullish reversal signal<br>
                            - <strong>Shooting Star:</strong> Long upper wick (>2x body), small lower wick - bearish reversal signal<br>
                            - <strong>Success Rate:</strong> Percentage of times the reversal actually occurred (price moved in predicted direction)
                        </div>
                    </div>
                </div>
            </div>
        """
    
    # 4. Algo Trading Patterns
    algo_dir = os.path.join(analysis_dir, 'algo_patterns')
    if os.path.exists(algo_dir):
        html += """
            <div class="section">
                <h2>🤖 Algo Trading Pattern Analysis</h2>
                <p>Identifies potential algorithmic/quantitative trading activity through iceberg timing and anomaly detection.</p>
                <div class="grid">
        """
        
        # Iceberg timing summary
        iceberg_timing_file = os.path.join(algo_dir, 'iceberg_hourly_distribution.csv')
        if os.path.exists(iceberg_timing_file):
            try:
                iceberg_timing = pd.read_csv(iceberg_timing_file)
                html += '<div class="insight-box"><h3>Iceberg Pattern Timing</h3>'
                if len(iceberg_timing) > 0:
                    peak_hour = iceberg_timing.loc[iceberg_timing['count'].idxmax(), 'hour']
                    total = iceberg_timing['count'].sum()
                    html += f'<ul>'
                    html += f'<li><strong>Total Iceberg Patterns:</strong> {total}</li>'
                    html += f'<li><strong>Peak Hour:</strong> {int(peak_hour)}:00 IST ({iceberg_timing.loc[iceberg_timing["count"].idxmax(), "percentage"]:.1f}% of patterns)</li>'
                    html += f'</ul>'
                    html += iceberg_timing.head(10).to_html(index=False, classes='table')
                html += '</div>'
            except Exception as e:
                logger.warning(f"Could not load iceberg timing: {e}")
        
        # Combined anomalies summary
        combined_anomaly_file = os.path.join(algo_dir, 'combined_anomaly_hourly.csv')
        if os.path.exists(combined_anomaly_file):
            try:
                combined_anomaly = pd.read_csv(combined_anomaly_file)
                html += '<div class="insight-box"><h3>Potential Algo Trading Windows</h3>'
                if len(combined_anomaly) > 0:
                    peak_hour = combined_anomaly.loc[combined_anomaly['count'].idxmax(), 'hour']
                    total = combined_anomaly['count'].sum()
                    html += f'<ul>'
                    html += f'<li><strong>Combined Anomalies:</strong> {total} (High Volume + High Price Move)</li>'
                    html += f'<li><strong>Peak Activity Hour:</strong> {int(peak_hour)}:00 IST ({combined_anomaly.loc[combined_anomaly["count"].idxmax(), "percentage"]:.1f}% of anomalies)</li>'
                    html += f'<li><strong>Interpretation:</strong> Clustering of anomalies suggests systematic algo trading</li>'
                    html += f'</ul>'
                    html += combined_anomaly.head(10).to_html(index=False, classes='table')
                html += '</div>'
            except Exception as e:
                logger.warning(f"Could not load combined anomalies: {e}")
        
        # Visualizations
        algo_img = os.path.join(algo_dir, 'iceberg_timing_analysis.png')
        if os.path.exists(algo_img):
            rel_path = os.path.relpath(algo_img, output_dir)
            html += f'<div class="chart-container large-chart"><h4>Iceberg Pattern Timing Analysis</h4><img src="{rel_path}" alt="Iceberg Timing"></div>'
        
        algo_patterns_img = os.path.join(algo_dir, 'algo_trading_patterns.png')
        if os.path.exists(algo_patterns_img):
            rel_path = os.path.relpath(algo_patterns_img, output_dir)
            html += f'<div class="chart-container large-chart"><h4>Algo Trading Pattern Detection</h4><img src="{rel_path}" alt="Algo Patterns"></div>'
        
        # FAQ for Algo Trading Patterns
        html += """
                </div>
                <div class="faq-section">
                    <h3>❓ FAQ: Algo Trading Pattern Analysis</h3>
                    <div class="faq-item">
                        <div class="faq-question">Q: How are algo trading patterns identified?</div>
                        <div class="faq-answer">
                            <strong>Iceberg Pattern Timing:</strong> Analyzes when iceberg orders (large hidden orders) occur. Clustering in specific time windows suggests systematic algo trading.<br><br>
                            <strong>Volume Anomalies:</strong> Volume spikes >3 standard deviations above 20-period average - indicates unusual activity, potentially from large algo orders.<br><br>
                            <strong>Price Anomalies:</strong> Price movements >3 standard deviations - sudden, unexpected moves often from algo execution.<br><br>
                            <strong>Combined Anomalies:</strong> Simultaneous high volume (>2.5σ) AND high price movement (>2.5σ) - strongest indicator of algo trading activity.<br><br>
                            <strong>Peak Activity Hours:</strong> Hours with highest concentration of anomalies indicate when quant traders/algo systems are most active.
                        </div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">Q: What do the algo trading charts show?</div>
                        <div class="faq-answer">
                            <strong>Iceberg Timing Analysis (4 panels):</strong><br>
                            - Top Left: X-axis = Hour (9-15), Y-axis = Count - Shows which hours have most iceberg orders<br>
                            - Top Right: X-axis = Day of week, Y-axis = Count - Shows which days have most iceberg activity<br>
                            - Bottom Left: X-axis = Time bucket (15-min windows), Y-axis = Count - Top 10 time windows for icebergs<br>
                            - Bottom Right: X-axis = Date, Y-axis = Cumulative count - Shows trend over time<br><br>
                            <strong>Algo Trading Patterns (4 panels):</strong><br>
                            - Top Left: X-axis = Hour, Y-axis = Count of volume anomalies<br>
                            - Top Right: X-axis = Hour, Y-axis = Count of combined anomalies (high vol + high price)<br>
                            - Bottom Left: X-axis = Time bucket, Y-axis = Count - Top 10 windows for combined anomalies<br>
                            - Bottom Right: Summary statistics and interpretation
                        </div>
                    </div>
                </div>
            </div>
        """
    
    # 5. Indicator Combinations (if available)
    combo_dir = os.path.join(analysis_dir, 'indicator_combinations')
    if os.path.exists(combo_dir):
        html += """
            <div class="section">
                <h2>🔗 Indicator Combinations</h2>
                <p>Analysis of combined indicator signals (requires indicator data).</p>
                <div class="grid">
        """
        
        # Load top pairs table
        pair_file = os.path.join(combo_dir, 'top_pairs.csv')
        if os.path.exists(pair_file):
            try:
                df = pd.read_csv(pair_file)
                html += '<div><h3>Top Indicator Pairs</h3>'
                html += df.head(10).to_html(index=False, classes='table')
                html += '</div>'
            except Exception as e:
                logger.warning(f"Could not load top pairs: {e}")
        
        pair_img = os.path.join(combo_dir, 'pair_accuracy.png')
        if os.path.exists(pair_img):
            rel_path = os.path.relpath(pair_img, output_dir)
            html += f'<div><h4>Pair Accuracy Visualization</h4><img src="{rel_path}" alt="Pair Accuracy"></div>'
        else:
            html += '<div class="insight-box"><p>⚠️ Indicator combination analysis requires indicator data. Run feature engineering step first.</p></div>'
            
        # FAQ for Indicator Combinations
        html += """
                </div>
                <div class="faq-section">
                    <h3>❓ FAQ: Indicator Combinations</h3>
                    <div class="faq-item">
                        <div class="faq-question">Q: What is indicator combination analysis?</div>
                        <div class="faq-answer">
                            This section analyzes how different technical indicators work together. It identifies pairs of indicators that, when used together, provide better accuracy than individual indicators.<br><br>
                            <strong>Note:</strong> This analysis requires indicator data from the feature engineering step. If you see a message about missing indicator data, run the feature engineering step first.
                        </div>
                    </div>
                </div>
            </div>
        """
    
    # 6. Last 7 Days Analysis
    html += """
            <div class="section">
                <h2>📅 Last 7 Days Analysis</h2>
                <p>Recent performance trends and patterns from the last 7 trading days.</p>
                <div class="grid">
        """
    
    # Try to load the raw data to get last 7 days
    try:
        # Find the raw data file
        raw_data_file = None
        if simple_analysis_dir:
            # Look for raw data in parent directory
            parent_dir = os.path.dirname(simple_analysis_dir) if simple_analysis_dir else analysis_dir
            data_dir = os.path.join(parent_dir, '..', 'data')
            if os.path.exists(data_dir):
                # Find raw data file
                for f in os.listdir(data_dir):
                    if f.endswith('_raw.csv') and symbol.replace('.NS', '') in f:
                        raw_data_file = os.path.join(data_dir, f)
                        break
        
        if raw_data_file and os.path.exists(raw_data_file):
            df_recent = pd.read_csv(raw_data_file, index_col=0, parse_dates=True)
            # Get last 7 TRADING days (not calendar days)
            if len(df_recent) > 0:
                # Get unique trading dates
                df_recent['trading_date'] = df_recent.index.date
                unique_dates = sorted(df_recent['trading_date'].unique(), reverse=True)
                
                # Get last 7 trading days
                last_7_trading_dates = unique_dates[:7] if len(unique_dates) >= 7 else unique_dates
                df_last7 = df_recent[df_recent['trading_date'].isin(last_7_trading_dates)].copy()
                
                if len(df_last7) > 0:
                    # Calculate daily stats
                    df_last7['date'] = df_last7.index.date
                    daily_stats = df_last7.groupby('date').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).reset_index()
                    daily_stats.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    daily_stats['Return'] = ((daily_stats['Close'] - daily_stats['Open']) / daily_stats['Open'] * 100).round(2)
                    daily_stats['Range'] = ((daily_stats['High'] - daily_stats['Low']) / daily_stats['Open'] * 100).round(2)
                    daily_stats = daily_stats[['Date', 'Open', 'High', 'Low', 'Close', 'Return', 'Range', 'Volume']]
                    daily_stats['Date'] = pd.to_datetime(daily_stats['Date']).dt.strftime('%Y-%m-%d')
                    daily_stats = daily_stats.sort_values('Date', ascending=False)  # Most recent first
                    
                    html += '<div class="insight-box"><h3>Last 7 Days Summary</h3>'
                    html += f'<ul>'
                    html += f'<li><strong>Total Days:</strong> {len(daily_stats)}</li>'
                    html += f'<li><strong>Average Daily Return:</strong> {daily_stats["Return"].mean():.2f}%</li>'
                    html += f'<li><strong>Best Day:</strong> {daily_stats.loc[daily_stats["Return"].idxmax(), "Date"]} ({daily_stats["Return"].max():.2f}%)</li>'
                    html += f'<li><strong>Worst Day:</strong> {daily_stats.loc[daily_stats["Return"].idxmin(), "Date"]} ({daily_stats["Return"].min():.2f}%)</li>'
                    html += f'<li><strong>Average Daily Range:</strong> {daily_stats["Range"].mean():.2f}%</li>'
                    html += f'</ul></div>'
                    
                    html += '<div><h3>Daily Performance Table</h3>'
                    html += daily_stats.to_html(index=False, classes='table', float_format=lambda x: f'{x:,.2f}' if isinstance(x, float) else str(x))
                    html += '</div>'
                    
                    # Detailed Analysis
                    html += '<div class="insight-box"><h3>Detailed 7-Day Analysis</h3>'
                    
                    # Trend analysis
                    returns_trend = daily_stats['Return'].values
                    if len(returns_trend) >= 3:
                        recent_trend = returns_trend[:3].mean()  # Last 3 days
                        earlier_trend = returns_trend[-3:].mean() if len(returns_trend) >= 6 else returns_trend[3:].mean()
                        trend_direction = "Improving" if recent_trend > earlier_trend else "Declining"
                        html += f'<ul>'
                        html += f'<li><strong>Recent Trend (Last 3 Days):</strong> {recent_trend:.2f}% avg return</li>'
                        html += f'<li><strong>Earlier Trend:</strong> {earlier_trend:.2f}% avg return</li>'
                        html += f'<li><strong>Trend Direction:</strong> {trend_direction}</li>'
                    
                    # Volatility analysis
                    volatility_trend = daily_stats['Range'].values
                    avg_volatility = volatility_trend.mean()
                    high_vol_days = len([r for r in volatility_trend if r > avg_volatility * 1.5])
                    html += f'<li><strong>Average Volatility:</strong> {avg_volatility:.2f}%</li>'
                    html += f'<li><strong>High Volatility Days (>1.5x avg):</strong> {high_vol_days} days</li>'
                    
                    # Volume analysis
                    volume_trend = daily_stats['Volume'].values
                    avg_volume = volume_trend.mean()
                    high_vol_days_count = len([v for v in volume_trend if v > avg_volume * 1.5])
                    html += f'<li><strong>Average Daily Volume:</strong> {avg_volume:,.0f}</li>'
                    html += f'<li><strong>High Volume Days (>1.5x avg):</strong> {high_vol_days_count} days</li>'
                    html += f'</ul></div>'
                    
                    # Prediction Model
                    html += '<div class="insight-box"><h3>📈 Prediction Model (Next 3 Trading Days)</h3>'
                    
                    try:
                        import numpy as np
                        from scipy import stats
                        
                        # Simple prediction models
                        recent_returns = daily_stats['Return'].head(5).values  # Last 5 days
                        recent_closes = daily_stats['Close'].head(5).values
                        
                        # Model 1: Linear trend
                        if len(recent_returns) >= 3:
                            x = np.arange(len(recent_returns))
                            slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_returns)
                            next_3_days_pred = [intercept + slope * (len(recent_returns) + i) for i in range(1, 4)]
                            
                            # Model 2: Moving average
                            ma_pred = np.mean(recent_returns)
                            
                            # Model 3: Weighted average (recent days weighted more)
                            weights = np.array([0.3, 0.25, 0.2, 0.15, 0.1][:len(recent_returns)])
                            weights = weights / weights.sum()
                            weighted_pred = np.average(recent_returns, weights=weights)
                            
                            # Model 4: Price trend
                            if len(recent_closes) >= 3:
                                price_slope, price_intercept, _, _, _ = stats.linregress(x[:len(recent_closes)], recent_closes)
                                current_price = recent_closes[0]
                                predicted_prices = [current_price + price_slope * i for i in range(1, 4)]
                                predicted_returns_from_price = [((predicted_prices[i] - current_price) / current_price * 100) for i in range(3)]
                            else:
                                predicted_returns_from_price = [ma_pred] * 3
                            
                            # Combine predictions (ensemble)
                            ensemble_pred = np.mean([next_3_days_pred, [ma_pred]*3, [weighted_pred]*3, predicted_returns_from_price], axis=0)
                            
                            html += '<ul>'
                            html += f'<li><strong>Day 1 Prediction:</strong> {ensemble_pred[0]:.2f}% return</li>'
                            html += f'<li><strong>Day 2 Prediction:</strong> {ensemble_pred[1]:.2f}% return</li>'
                            html += f'<li><strong>Day 3 Prediction:</strong> {ensemble_pred[2]:.2f}% return</li>'
                            html += f'<li><strong>Average Expected Return (3 days):</strong> {ensemble_pred.mean():.2f}%</li>'
                            html += f'<li><strong>Predicted Price Range:</strong> {predicted_prices[2]:.2f} - {predicted_prices[0]:.2f}</li>'
                            html += f'</ul>'
                            html += '<p><strong>Model Components:</strong></p>'
                            html += '<ul style="font-size: 0.9em;">'
                            html += f'<li>Linear Trend Model: {next_3_days_pred[0]:.2f}% (slope: {slope:.3f})</li>'
                            html += f'<li>Moving Average Model: {ma_pred:.2f}%</li>'
                            html += f'<li>Weighted Average Model: {weighted_pred:.2f}%</li>'
                            html += f'<li>Price Trend Model: {predicted_returns_from_price[0]:.2f}%</li>'
                            html += f'</ul>'
                            html += '<p><em>Note: Predictions are based on recent trends and should be used with caution. Past performance does not guarantee future results.</em></p>'
                        else:
                            html += '<p>⚠️ Insufficient data for prediction model (need at least 3 days).</p>'
                    except Exception as e:
                        logger.warning(f"Prediction model error: {e}")
                        html += f'<p>⚠️ Error generating predictions: {str(e)}</p>'
                    
                    html += '</div>'
                else:
                    html += '<div class="insight-box"><p>⚠️ No data available for last 7 trading days.</p></div>'
            else:
                html += '<div class="insight-box"><p>⚠️ No data available for analysis.</p></div>'
        else:
            html += '<div class="insight-box"><p>⚠️ Raw data file not found. Last 7 days analysis requires raw data.</p></div>'
    except Exception as e:
        logger.warning(f"Could not generate last 7 days analysis: {e}")
        html += '<div class="insight-box"><p>⚠️ Error generating last 7 days analysis.</p></div>'
    
    # FAQ for Last 7 Days Analysis
    html += """
                </div>
                <div class="faq-section">
                    <h3>❓ FAQ: Last 7 Trading Days Analysis</h3>
                    <div class="faq-item">
                        <div class="faq-question">Q: What does "Last 7 Trading Days" mean?</div>
                        <div class="faq-answer">
                            This refers to the <strong>last 7 unique trading days</strong> (excluding weekends and holidays), not calendar days. For example, if today is Friday, it includes the last 7 weekdays with trading activity.<br><br>
                            The analysis includes:<br>
                            - Daily OHLC (Open, High, Low, Close) prices<br>
                            - Daily returns and price ranges<br>
                            - Volume analysis<br>
                            - Trend analysis comparing recent vs earlier performance<br>
                            - Prediction model for next 3 trading days
                        </div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">Q: How accurate is the prediction model?</div>
                        <div class="faq-answer">
                            The prediction model uses an <strong>ensemble of 4 different approaches</strong> to forecast next 3 trading days:<br><br>
                            <strong>1. Linear Trend Model:</strong> Extrapolates recent return trend using linear regression<br>
                            <strong>2. Moving Average Model:</strong> Uses average of recent returns<br>
                            <strong>3. Weighted Average Model:</strong> Gives more weight to recent days (30% most recent)<br>
                            <strong>4. Price Trend Model:</strong> Analyzes price movement and converts to expected returns<br><br>
                            <strong>Important:</strong> This is a simple trend-following model based on historical patterns. Real markets are complex and unpredictable. Use predictions as one input among many, not as definitive forecasts. Past performance does not guarantee future results.
                        </div>
                    </div>
                </div>
            </div>
        """
    
    # FAQ Section
    html += """
            <div class="section">
                <h2>❓ Frequently Asked Questions (FAQ)</h2>
                <div class="faq-section">
    """
    
    faq_items = [
        {
            "q": "What are the different sections in this report?",
            "a": """
            <strong>1. Price-Volume Behavioral Patterns:</strong> Detects institutional patterns like Hidden Accumulation, Distribution, Sweeps, and Iceberg orders using Smart Money features (Synthetic IV, OBV, Sentiment Skew).<br><br>
            <strong>2. Time-Based Patterns:</strong> Analyzes returns, volatility, and volume across different hours of day and days of week to identify optimal trading times.<br><br>
            <strong>3. Volume Patterns:</strong> Identifies volume spikes, breakouts, and volume-price relationships that indicate significant market activity.<br><br>
            <strong>4. Price Movement Patterns:</strong> Analyzes momentum (3 consecutive up/down candles) and reversal patterns (Hammers, Shooting Stars).<br><br>
            <strong>5. Algo Trading Pattern Analysis:</strong> Identifies potential algorithmic trading activity through iceberg timing and anomaly detection.<br><br>
            <strong>6. Last 7 Trading Days:</strong> Detailed analysis of recent performance with prediction model for next 3 days.
            """
        },
        {
            "q": "What do the X-axis and Y-axis represent in the charts?",
            "a": """
            <strong>Hourly Patterns Chart:</strong><br>
            - X-axis: Hour of day (0-15, representing 9:15 AM to 3:30 PM IST)<br>
            - Y-axis (Top): Cumulative return per hour in percentage (%)<br>
            - Y-axis (Middle): Average volatility (price range) in percentage (%)<br>
            - Y-axis (Bottom): Average volume (number of shares traded)<br><br>
            
            <strong>Day of Week Patterns:</strong><br>
            - X-axis: Day of week (Monday through Friday)<br>
            - Y-axis (Top): Average return in percentage (%)<br>
            - Y-axis (Bottom): Average volatility in percentage (%)<br><br>
            
            <strong>Time Heatmap:</strong><br>
            - X-axis: Hour of day (9-15, representing trading hours)<br>
            - Y-axis: Day of week (Monday to Friday)<br>
            - Color: Average return percentage (Green = positive, Red = negative)<br><br>
            
            <strong>Volume Spike Scatter:</strong><br>
            - X-axis: Price change at spike time in percentage (%)<br>
            - Y-axis: Volume ratio (multiple of 20-period moving average)<br>
            - Color: 5-minute forward return<br><br>
            
            <strong>Volume Breakout Distribution:</strong><br>
            - X-axis: Direction (Up or Down)<br>
            - Y-axis: Count of breakouts<br><br>
            
            <strong>Reversal Pattern Performance:</strong><br>
            - X-axis: Pattern type (Hammer, Shooting Star)<br>
            - Y-axis: Success rate or average return in percentage (%)<br><br>
            
            <strong>Iceberg Timing Analysis (4-panel):</strong><br>
            - Top Left: X-axis = Hour, Y-axis = Count of iceberg patterns<br>
            - Top Right: X-axis = Day of week, Y-axis = Count<br>
            - Bottom Left: X-axis = Time bucket (15-min windows), Y-axis = Count<br>
            - Bottom Right: X-axis = Date, Y-axis = Cumulative count<br><br>
            
            <strong>Algo Trading Patterns (4-panel):</strong><br>
            - Top Left: X-axis = Hour, Y-axis = Count of volume anomalies<br>
            - Top Right: X-axis = Hour, Y-axis = Count of combined anomalies<br>
            - Bottom Left: X-axis = Time bucket, Y-axis = Count<br>
            - Bottom Right: Summary statistics text
            """
        },
        {
            "q": "What are Smart Money features?",
            "a": """
            <strong>Synthetic IV (Implied Volatility):</strong> Estimated volatility using Parkinson's method from High/Low price ranges. Higher values indicate increased uncertainty.<br><br>
            <strong>Smart Money Flow (Detrended OBV):</strong> On-Balance Volume minus its 200-period moving average. Positive values suggest accumulation, negative suggests distribution.<br><br>
            <strong>Sentiment Skew:</strong> Skewness of returns over a rolling window. Positive skew = greed/optimism, negative skew = fear/pessimism.
            """
        },
        {
            "q": "What are the different pattern types?",
            "a": """
            <strong>Hidden Accumulation:</strong> Large volume with small price movement - institutions buying without moving price.<br><br>
            <strong>Hidden Distribution:</strong> Large volume with small price movement - institutions selling without moving price.<br><br>
            <strong>Bullish Sweep:</strong> Price breaks above recent high with volume - potential bullish momentum.<br><br>
            <strong>Bearish Sweep:</strong> Price breaks below recent low with volume - potential bearish momentum.<br><br>
            <strong>Iceberg:</strong> Very high volume (>3σ) with minimal price change - large hidden orders being executed slowly.<br><br>
            <strong>Capitulation:</strong> Extreme selling pressure with high volume and negative sentiment - potential reversal point.
            """
        },
        {
            "q": "How is the prediction model calculated?",
            "a": """
            The prediction model uses an <strong>ensemble approach</strong> combining 4 different models:<br><br>
            <strong>1. Linear Trend Model:</strong> Fits a linear regression to recent returns and extrapolates forward.<br><br>
            <strong>2. Moving Average Model:</strong> Uses the simple average of recent returns as prediction.<br><br>
            <strong>3. Weighted Average Model:</strong> Gives more weight to recent days (30% most recent, decreasing weights for older days).<br><br>
            <strong>4. Price Trend Model:</strong> Analyzes price movement trend and converts to expected returns.<br><br>
            The final prediction is the average of all 4 models. <strong>Note:</strong> This is a simple trend-following model and should be used with caution. Real markets are complex and unpredictable.
            """
        },
        {
            "q": "What are anomalies and how are they detected?",
            "a": """
            <strong>Volume Anomalies:</strong> Volume spikes that are >3 standard deviations above the 20-period rolling average. These indicate unusual trading activity, potentially from large institutional orders or algo trading.<br><br>
            <strong>Price Anomalies:</strong> Price movements that are >3 standard deviations above the 20-period rolling average of absolute returns. These indicate sudden, unexpected price moves.<br><br>
            <strong>Combined Anomalies:</strong> Simultaneous high volume (>2.5σ) AND high price movement (>2.5σ). These are strong indicators of algorithmic trading activity or large institutional moves.
            """
        },
        {
            "q": "What does 'Last 7 Trading Days' mean?",
            "a": """
            This refers to the <strong>last 7 unique trading days</strong> (excluding weekends and holidays), not calendar days. The analysis includes:<br><br>
            - Daily OHLC (Open, High, Low, Close) prices<br>
            - Daily returns and price ranges<br>
            - Volume analysis<br>
            - Trend analysis comparing recent vs earlier performance<br>
            - Prediction model for next 3 trading days
            """
        },
        {
            "q": "How should I interpret the time heatmap?",
            "a": """
            The time heatmap shows <strong>average returns by hour and day of week</strong>.<br><br>
            - <strong>Green cells:</strong> Positive average returns for that hour-day combination<br>
            - <strong>Red cells:</strong> Negative average returns<br>
            - <strong>Darker colors:</strong> Stronger returns (positive or negative)<br>
            - <strong>Brighter colors:</strong> Weaker returns<br><br>
            Use this to identify:<br>
            - Best hours to trade (consistently green)<br>
            - Worst hours to trade (consistently red)<br>
            - Day-specific patterns (e.g., Friday afternoons might show different patterns)
            """
        },
        {
            "q": "What is the difference between 'Simple Analysis' and 'Smart Money Analysis'?",
            "a": """
            <strong>Simple Analysis:</strong> Uses basic Z-score calculations on raw OHLCV data to detect patterns like Panic Sells, FOMO Buys, etc.<br><br>
            <strong>Smart Money Analysis:</strong> Uses advanced features (Synthetic IV, Detrended OBV, Sentiment Skew) to detect more sophisticated institutional patterns like Hidden Accumulation/Distribution, Liquidity Sweeps, and Iceberg orders. This is more accurate for identifying professional trading activity.
            """
        }
    ]
    
    for item in faq_items:
        html += f'<div class="faq-item">'
        html += f'<div class="faq-question">Q: {item["q"]}</div>'
        html += f'<div class="faq-answer">{item["a"]}</div>'
        html += f'</div>'
    
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
