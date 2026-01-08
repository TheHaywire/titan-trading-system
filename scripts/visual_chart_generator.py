"""
Visual Chart Generator - Simplified Working Version
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle


def fetch_data(symbol, timeframe_str):
    """Fetch data from MT5"""
    
    timeframes = {
        '1H': mt5.TIMEFRAME_H1,
       '4H': mt5.TIMEFRAME_H4,
        '1D': mt5.TIMEFRAME_D1,
    }
    
    bars = {'1H': 200, '4H': 150, '1D': 100}
    
    if not mt5.initialize():
        raise ConnectionError("MT5 init failed")
    
    try:
        tf = timeframes.get(timeframe_str)
        num_bars = bars.get(timeframe_str, 100)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, num_bars)
        
        if rates is None:
            raise ValueError(f"No data for {symbol}")
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
       
        return df
    finally:
        mt5.shutdown()


def create_chart(df, symbol, timeframe, output_path):
    """Create professional chart"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Candlestick chart
    for i in range(len(df)):
        row = df.iloc[i]
        color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
        
        # Body
        height = abs(row['close'] - row['open'])
        bottom = min(row['open'], row['close'])
        ax1.add_patch(Rectangle((i, bottom), 0.8, height, facecolor=color, edgecolor=color))
        
        # Wicks
        ax1.plot([i+0.4, i+0.4], [row['low'], row['high']], color=color, linewidth=0.8)
    
    # Moving averages
    ma9 = df['close'].rolling(9).mean()
    ma21 = df['close'].rolling(21).mean()
    ma55 = df['close'].rolling(55).mean()
    
    ax1.plot(ma9.values, color='blue', linewidth=1, alpha=0.7, label='MA 9')
    ax1.plot(ma21.values, color='orange', linewidth=1, alpha=0.7, label='MA 21')
    ax1.plot(ma55.values, color='purple', linewidth=1.2, alpha=0.7, label='MA 55')
    
    # Support/Resistance
    current_price = df['close'].iloc[-1]
    recent_high = df['high'].tail(30).max()
    recent_low = df['low'].tail(30).min()
    
    ax1.axhline(y=recent_high, color='red', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Resistance: {recent_high:.2f}')
    ax1.axhline(y=recent_low, color='blue', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Support: {recent_low:.2f}')
    ax1.axhline(y=current_price, color='green', linestyle='-', linewidth=2, alpha=0.8, label=f'Current: {current_price:.2f}')
    
    # Fibonacci
    swing_high = df['high'].max()
    swing_low = df['low'].min()
    diff = swing_high - swing_low
    
    fib_382 = swing_high - (0.382 * diff)
    fib_50 = swing_high - (0.5 * diff)
    fib_618 = swing_high - (0.618 * diff)
    
    ax1.axhline(y=fib_382, color='orange', linestyle=':', linewidth=0.8, alpha=0.4)
    ax1.axhline(y=fib_50, color='orange', linestyle=':', linewidth=0.8, alpha=0.4)
    ax1.axhline(y=fib_618, color='orange', linestyle=':', linewidth=0.8, alpha=0.4)
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    ax2.plot(rsi.values, color='purple', linewidth=1.5)
    ax2.axhline(y=70, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
    ax2.axhline(y=30, color='green', linestyle='--', linewidth=0.8, alpha=0.5)
    ax2.fill_between(range(len(df)), 70, 100, alpha=0.1, color='red')
    ax2.fill_between(range(len(df)), 0, 30, alpha=0.1, color='green')
    ax2.set_ylabel('RSI', fontsize=10)
    ax2.set_ylim([0, 100])
    ax2.grid(True, alpha=0.3)
    
    # Styling
    ax1.set_title(f'{symbol} - {timeframe} Timeframe Analysis', fontsize=14, weight='bold')
    ax1.set_ylabel('Price', fontsize=12)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([-2, len(df)+2])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python visual_chart_generator.py GOLD 4H")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    timeframe = sys.argv[2].upper()
    
    print(f"\n📊 Generating {symbol} {timeframe} chart...\n")
    
    try:
        df = fetch_data(symbol, timeframe)
        
        output_dir = Path("charts")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{symbol}_{timeframe}_{timestamp}.png"
        
        chart_path = create_chart(df, symbol, timeframe, str(output_file))
        
        print(f"✅ Chart saved: {chart_path}\n")
        print("  Includes:")
        print("  - Candlesticks")
        print("  - Moving averages (9, 21, 55)")
        print("  - Support & Resistance")
        print("  - Fibonacci levels")
        print("  - RSI indicator\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
