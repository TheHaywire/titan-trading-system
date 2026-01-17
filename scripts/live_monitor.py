"""
LIVE TRADING MONITOR (Safe Mode)
=================================
Shows you trading signals in real-time but waits for YOUR approval before placing trades.

Run: python scripts/live_monitor.py
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime

from titan_system.features.quant_features import QuantFeatureEngine
from titan_system.features.advanced_features import AdvancedQuantEngine
from scripts.generate_all_entries import UniversalEntryGenerator


def display_signal(symbol: str, signal, state: dict):
    """Display signal with approval prompt."""
    print("\n" + "="*80)
    print(f"🎯 TRADE SIGNAL DETECTED: {symbol}")
    print("="*80)
    
    print(f"\nMarket State:")
    print(f"  Trend: {state['trend_state']} ({state['trend_direction']})")
    print(f"  Volatility: {state['volatility']}")
    print(f"  Momentum Building: {'Yes' if state['momentum_building'] else 'No'}")
    
    print(f"\nSignal Details:")
    print(f"  Type: {signal.entry_type} {signal.direction}")
    print(f"  Confidence: {signal.confidence:.0f}/100")
    print(f"  Entry: ${signal.entry_price:.2f}")
    print(f"  Stop: ${signal.stop_loss:.2f}")
    print(f"  TP1: ${signal.take_profit_1:.2f} (50% exit)")
    print(f"  TP2: ${signal.take_profit_2:.2f} (final)")
    print(f"  R:R: 1:{signal.risk_reward:.1f}")
    print(f"  Size: {signal.position_size_multiplier:.2f}x base")
    
    print(f"\nReasoning:")
    for reason in signal.reasoning:
        print(f"  ✓ {reason}")
    
    print(f"\nTrade Management Plan:")
    if signal.entry_type == "BREAKOUT":
        print(f"  1. Enter on breakout confirmation")
        print(f"  2. Take 50% at TP1, move stop to BE")
        print(f"  3. Trail remaining with Kalman line")
    elif signal.entry_type == "PULLBACK":
        print(f"  1. Enter at current price")
        print(f"  2. Take 50% at TP1 (2R)")
        print(f"  3. Trail remaining to TP2 (4R)")
    elif signal.entry_type == "REVERSION":
        print(f"  1. Enter immediately")
        print(f"  2. Take 75% at TP1 quickly")
        print(f"  3. Close remaining on reversal")
    elif signal.entry_type == "SCALP":
        print(f"  1. Enter immediately")
        print(f"  2. Take 100% at TP1 - don't be greedy")
    
    print("\n" + "="*80)
    return signal


def monitor_symbols(symbols: list, timeframe, min_confidence: float = 70, 
                   scan_interval: int = 300):
    """Monitor symbols and display signals."""
    
    if not mt5.initialize():
        print("ERROR: MT5 initialization failed")
        return
    
    print("\n" + "="*80)
    print("LIVE TRADING MONITOR - Safe Mode")
    print("="*80)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Timeframe: H1")
    print(f"Min Confidence: {min_confidence}%")
    print(f"Scan Interval: {scan_interval}s")
    print("="*80)
    print("\n💡 Signals will be displayed when found.")
    print("💡 You can then manually place trades in MT5.\n")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n🔄 SCAN #{iteration} - {current_time}")
            
            signals_found = 0
            
            for symbol in symbols:
                # Get data
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 500)
                if rates is None or len(rates) == 0:
                    continue
                
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.rename(columns={'tick_volume': 'volume'}, inplace=True)
                
                try:
                    # Compute features
                    basic = QuantFeatureEngine.compute_all(df)
                    
                    returns = df['close'].pct_change()
                    universe = {s: returns for s in symbols if s != symbol}
                    
                    advanced = AdvancedQuantEngine.compute_all_advanced(
                        df, universe_returns=universe, market_returns=returns
                    )
                    
                    # Generate signals
                    signals, state = UniversalEntryGenerator.generate_all_entries(
                        df, basic, advanced
                    )
                    
                    if signals and signals[0].confidence >= min_confidence:
                        display_signal(symbol, signals[0], state)
                        signals_found += 1
                
                except Exception as e:
                    print(f"  Error analyzing {symbol}: {e}")
            
            if signals_found == 0:
                print(f"  ❌ No high-confidence setups found")
            else:
                print(f"\n  ✅ Found {signals_found} signal(s)")
            
            print(f"\n  💤 Next scan in {scan_interval}s...")
            time.sleep(scan_interval)
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️  MONITOR STOPPED")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    SYMBOLS = ["GOLD", "BTCUSD", "US100", "GER40"]
    
    monitor_symbols(
        symbols=SYMBOLS,
        timeframe=mt5.TIMEFRAME_H1,
        min_confidence=70,
        scan_interval=300  # 5 minutes
    )
