"""
Chart Generator Module - For embedding in analysis reports
"""

import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path


class ChartGenerator:
    """Generate charts for analysis reports"""
    
    @staticmethod
    def generate_timeframe_chart(symbol: str, timeframe_str: str, df: pd.DataFrame, output_path: str) -> str:
        """Generate a chart for a specific timeframe"""
        
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [3, 1]})
            
            # Limit to last 100 bars for clarity
            df_plot = df.tail(100).copy()
            df_plot.reset_index(drop=True, inplace=True)
            
            # Candlestick chart
            for i in range(len(df_plot)):
                row = df_plot.iloc[i]
                color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
                
                # Body
                height = abs(row['close'] - row['open'])
                bottom = min(row['open'], row['close'])
                ax1.add_patch(Rectangle((i, bottom), 0.8, height, facecolor=color, edgecolor=color))
                
                # Wicks
                ax1.plot([i+0.4, i+0.4], [row['low'], row['high']], color=color, linewidth=0.8)
            
            # Moving averages
            ma9 = df_plot['close'].rolling(9).mean()
            ma21 = df_plot['close'].rolling(21).mean()
            ma55 = df_plot['close'].rolling(55).mean()
            
            ax1.plot(ma9.values, color='#2196F3', linewidth=1.2, alpha=0.8, label='MA 9')
            ax1.plot(ma21.values, color='#FF9800', linewidth=1.2, alpha=0.8, label='MA 21')
            ax1.plot(ma55.values, color='#9C27B0', linewidth=1.5, alpha=0.8, label='MA 55')
            
            # Current price line
            current_price = df_plot['close'].iloc[-1]
            ax1.axhline(y=current_price, color='#4CAF50', linestyle='-', linewidth=2, alpha=0.9)
            ax1.text(len(df_plot) * 0.02, current_price, f' {current_price:.2f}', 
                   fontsize=9, color='#4CAF50', weight='bold', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
            
            # Support/Resistance (simple version - recent high/low)
            recent_high = df_plot['high'].tail(30).max()
            recent_low = df_plot['low'].tail(30).min()
            
            if recent_high > current_price:
                ax1.axhline(y=recent_high, color='#F44336', linestyle='--', linewidth=1.2, alpha=0.6)
                ax1.text(len(df_plot) * 0.98, recent_high, f'R: {recent_high:.2f} ', 
                       fontsize=8, color='#F44336', ha='right')
            
            if recent_low < current_price:
                ax1.axhline(y=recent_low, color='#2196F3', linestyle='--', linewidth=1.2, alpha=0.6)
                ax1.text(len(df_plot) * 0.98, recent_low, f'S: {recent_low:.2f} ', 
                       fontsize=8, color='#2196F3', ha='right')
            
            # RSI
            delta = df_plot['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            ax2.plot(rsi.values, color='#9C27B0', linewidth=1.5)
            ax2.axhline(y=70, color='#F44336', linestyle='--', linewidth=0.8, alpha=0.5)
            ax2.axhline(y=30, color='#4CAF50', linestyle='--', linewidth=0.8, alpha=0.5)
            ax2.fill_between(range(len(df_plot)), 70, 100, alpha=0.1, color='#F44336')
            ax2.fill_between(range(len(df_plot)), 0, 30, alpha=0.1, color='#4CAF50')
            
            # Styling
            ax1.set_title(f'{symbol} - {timeframe_str} Chart', fontsize=13, weight='bold', pad=10)
            ax1.set_ylabel('Price', fontsize=10)
            ax1.legend(loc='upper left', fontsize=8, framealpha=0.95)
            ax1.grid(True, alpha=0.2, linestyle=':')
            ax1.set_xlim([-1, len(df_plot)+1])
            
            ax2.set_ylabel('RSI', fontsize=9)
            ax2.set_ylim([0, 100])
            ax2.set_xlabel('Bars', fontsize=9)
            ax2.grid(True, alpha=0.2, linestyle=':')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=120, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return output_path
            
        except Exception as e:
            print(f"⚠️ Chart generation failed for {timeframe_str}: {str(e)}")
            return None
