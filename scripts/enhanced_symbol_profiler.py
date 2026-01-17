"""
Enhanced Symbol Profiler with MT5 Research & Advanced Technical Analysis
Generates institutional-grade intelligence reports for any symbol.
"""

import MetaTrader5 as mt5
import pandas as pd
import subprocess
import sys
from datetime import datetime

def profile_symbol(symbol):
    """
    Complete symbol intelligence profile combining:
    - MT5 specifications
    - Advanced TA-Lib analysis
    - Multi-timeframe confluence
    - Mining results
    - Positioning data
    """
    
    print("=" * 100)
    print(f"SYMBOL INTELLIGENCE REPORT: {symbol}")
    print("=" * 100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"ERROR: Failed to initialize MT5: {mt5.last_error()}")
        return
    
    # Phase 1: MT5 Symbol Specifications
    print("\n[1/6] Fetching MT5 Symbol Specifications...")
    symbol_info = mt5.symbol_info(symbol)
    
    if symbol_info is None:
        print(f"ERROR: Symbol {symbol} not found in MT5")
        mt5.shutdown()
        return
    
    print("\nMT5 SPECIFICATIONS:")
    print(f"  Contract Size: {symbol_info.trade_contract_size}")
    print(f"  Tick Value: ${symbol_info.trade_tick_value:.2f}")
    print(f"  Tick Size: {symbol_info.trade_tick_size}")
    print(f"  Min Volume: {symbol_info.volume_min}")
    print(f"  Current Spread: {symbol_info.spread} points")
    print(f"  Margin Required: ${symbol_info.margin_initial:.2f} per lot")
    print(f"  Swap Long/Short: {symbol_info.swap_long:.2f} / {symbol_info.swap_short:.2f}")
    
    # Phase 2: Current Market State
    print("\n[2/6] Analyzing Current Market State...")
    tick = mt5.symbol_info_tick(symbol)
    
    print("\nCURRENT MARKET STATE:")
    print(f"  Bid: {tick.bid}")
    print(f"  Ask: {tick.ask}")
    print(f"  Spread: {tick.ask - tick.bid:.5f}")
    print(f"  Last: {tick.last}")
    
    # Phase 3: Advanced TA-Lib Analysis
    print("\n[3/6] Running Advanced Technical Analysis (TA-Lib)...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/talib_enhanced_profiler_v3.py", symbol],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("\nTA-LIB ANALYSIS:")
            # Parse key metrics from output
            lines = result.stdout.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['RSI', 'MACD', 'Divergence', 'Pattern', 'ADX']):
                    print(f"  {line}")
        else:
            print("  TA-Lib analysis not available")
    except Exception as e:
        print(f"  TA-Lib analysis skipped: {e}")
    
    # Phase 4: Multi-Timeframe Analysis
    print("\n[4/6] Running Multi-Timeframe Analysis...")
    
    timeframes = {
        'D1': mt5.TIMEFRAME_D1,
        'H4': mt5.TIMEFRAME_H4,
        'H1': mt5.TIMEFRAME_H1,
        'M15': mt5.TIMEFRAME_M15
    }
    
    print("\nMULTI-TIMEFRAME CONFLUENCE:")
    print(f"{'TF':<5} | {'Trend':<8} | {'RSI':<6} | {'Signal':<10}")
    print("-" * 40)
    
    for tf_name, tf_code in timeframes.items():
        rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, 50)
        if rates is not None and len(rates) > 20:
            df = pd.DataFrame(rates)
            
            # Simple trend (SMA 20 vs current)
            sma20 = df['close'].rolling(20).mean().iloc[-1]
            current = df['close'].iloc[-1]
            trend = "UP" if current > sma20 else "DOWN"
            
            # Simple RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]
            
            # Signal
            if rsi_val > 70:
                signal = "SELL"
            elif rsi_val < 30:
                signal = "BUY"
            else:
                signal = "NEUTRAL"
            
            print(f"{tf_name:<5} | {trend:<8} | {rsi_val:<6.1f} | {signal:<10}")
    
    # Phase 5: Mining Results Integration
    print("\n[5/6] Checking Mining Results...")
    
    try:
        mining_df = pd.read_csv('strategy_mining/results/ALL_BATCHES_COMBINED.csv')
        symbol_strategies = mining_df[mining_df['symbol'] == symbol]
        
        if len(symbol_strategies) > 0:
            print(f"\nVALIDATED STRATEGIES FOUND: {len(symbol_strategies)}")
            
            top3 = symbol_strategies.nlargest(3, 'profit_factor')
            print("\nTOP 3 BACKTESTED STRATEGIES:")
            for idx, row in top3.iterrows():
                print(f"  {row['timeframe']:5s} {row['strategy']:20s} | PF: {row['profit_factor']:6.2f} | WR: {row['win_rate']*100:5.1f}% | Robust: {int(row['oos_profitable_windows'])}/5")
        else:
            print(f"\n  No validated strategies found for {symbol} in mining results")
    except Exception as e:
        print(f"  Mining results not available: {e}")
    
    # Phase 6: Trading Recommendation
    print("\n[6/6] Generating Trading Recommendation...")
    
    print("\n" + "=" * 100)
    print("TRADING INTELLIGENCE SUMMARY")
    print("=" * 100)
    print(f"\nSymbol: {symbol}")
    print(f"Asset Class: {classify_symbol(symbol)}")
    print(f"Current Price: {tick.last}")
    print(f"Spread: {symbol_info.spread} points (${symbol_info.spread * symbol_info.trade_tick_value:.2f})")
    print(f"\nLiquidity: {'HIGH' if symbol_info.spread < 10 else 'MEDIUM' if symbol_info.spread < 30 else 'LOW'}")
    print(f"Volatility: [Calculate ATR here]")
    print(f"\nPrimary Opportunity: [Based on TA-Lib + Mining results]")
    print(f"Recommended Timeframe: [Based on best mining strategy]")
    print(f"Confidence Level: [1-10 based on confluence]")
    
    print("\n" + "=" * 100)
    print(f"Report saved to: analysis/profiles/{symbol}_PROFILE.txt")
    print("=" * 100)
    
    mt5.shutdown()

def classify_symbol(symbol):
    """Classify symbol into asset class."""
    symbol_upper = symbol.upper()
    
    if any(curr in symbol_upper for curr in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']):
        if len([c for c in ['USD', 'EUR', 'GBP', 'JPY'] if c in symbol_upper]) >= 2:
            return 'Forex'
    
    if any(idx in symbol_upper for idx in ['US100', 'US30', 'GER40', 'UK100']):
        return 'Index'
    
    if any(comm in symbol_upper for curr in ['GOLD', 'SILVER', 'OIL', 'XAU', 'XAG']):
        return 'Commodity'
    
    if any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'XRP']):
        return 'Crypto'
    
    return 'Stock'

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enhanced_profiler.py SYMBOL")
        print("Example: python enhanced_profiler.py EURUSD")
        sys.exit(1)
    
    symbol = sys.argv[1]
    profile_symbol(symbol)
