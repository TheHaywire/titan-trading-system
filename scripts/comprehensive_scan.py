import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import numpy as np

def comprehensive_scanner():
    if not mt5.initialize():
        return
    
    # Get ALL available symbols from MT5
    all_symbols = mt5.symbols_get()
    
    # Build comprehensive watchlist
    priority_symbols = [
        # Metals
        "GOLD", "SILVER",
        # Major Forex
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF",
        # Cross Pairs
        "EURJPY", "GBPJPY", "AUDJPY", "EURGBP", "EURAUD", "GBPAUD",
        # Indices
        "US100Cash", "US500Cash", "US30Cash", "GER40Cash", "UK100Cash", "JPN225Cash",
        # Crypto
        "BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD",
    ]
    
    # Also include any symbols visible in market watch
    visible_symbols = [s.name for s in all_symbols if s.visible]
    
    # Combine and deduplicate
    symbols_to_scan = list(set(priority_symbols + visible_symbols))
    
    print("=" * 100)
    print(f"🔍 COMPREHENSIVE HIGH R:R SCANNER - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 100)
    print(f"\nScanning {len(symbols_to_scan)} symbols for HIGH R:R setups (>3:1)...\n")
    
    high_prob_setups = []
    high_rr_setups = []
    
    for symbol in symbols_to_scan:
        try:
            # Get tick data
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                continue
            
            current = tick.bid
            
            # Get H1 and M15 data
            h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
            
            if h1 is None or m15 is None or len(h1) < 50 or len(m15) < 50:
                continue
            
            df_h1 = pd.DataFrame(h1)
            df_m15 = pd.DataFrame(m15)
            
            # RSI calculation
            def calc_rsi(prices, period=14):
                deltas = np.diff(prices)
                seed = deltas[:period+1]
                up = seed[seed >= 0].sum()/period
                down = -seed[seed < 0].sum()/period
                rs = up/down if down != 0 else 0
                rsi = np.zeros_like(prices)
                rsi[:period] = 100. - 100./(1. + rs)
                for i in range(period, len(prices)):
                    delta = deltas[i-1]
                    upval = delta if delta > 0 else 0
                    downval = -delta if delta < 0 else 0
                    up = (up*(period-1) + upval)/period
                    down = (down*(period-1) + downval)/period
                    rs = up/down if down != 0 else 0
                    rsi[i] = 100. - 100./(1. + rs)
                return rsi
            
            rsi_h1 = calc_rsi(df_h1['close'].values)[-1]
            
            # Trend detection
            h1_ema20 = df_h1['close'].ewm(span=20).mean().iloc[-1]
            h1_ema50 = df_h1['close'].ewm(span=50).mean().iloc[-1]
            m15_ema20 = df_m15['close'].ewm(span=20).mean().iloc[-1]
            
            h1_trend = "UP" if h1_ema20 > h1_ema50 else "DOWN"
            m15_trend = "UP" if current > m15_ema20 else "DOWN"
            aligned = (h1_trend == m15_trend)
            
            # ATR for stops/targets
            df_h1['tr'] = df_h1.apply(lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1)
            atr = df_h1['tr'].tail(14).mean()
            
            # Find support/resistance
            recent_high = df_h1['high'].tail(20).max()
            recent_low = df_h1['low'].tail(20).min()
            
            # Determine setup direction and levels
            if aligned:
                direction = "LONG" if h1_trend == "UP" else "SHORT"
                
                if direction == "LONG":
                    sl = current - (atr * 1.5)
                    tp1 = current + (atr * 3)  # Wider for high R:R
                    tp2 = current + (atr * 5)  # Even wider
                    
                    # Check if there's clear runway to target
                    distance_to_resistance = recent_high - current
                    if distance_to_resistance < atr * 2:
                        continue  # Too close to resistance
                else:
                    sl = current + (atr * 1.5)
                    tp1 = current - (atr * 3)
                    tp2 = current - (atr * 5)
                    
                    # Check runway
                    distance_to_support = current - recent_low
                    if distance_to_support < atr * 2:
                        continue
                
                # Calculate R:R
                risk = abs(current - sl)
                reward1 = abs(tp1 - current)
                reward2 = abs(tp2 - current)
                
                rr1 = reward1 / risk if risk > 0 else 0
                rr2 = reward2 / risk if risk > 0 else 0
                
                # Skip if R:R too low
                if rr1 < 1.5:
                    continue
                
                # Score the setup
                score = 0
                reasons = []
                
                if aligned:
                    score += 30
                    reasons.append(f"✅ Trends aligned {h1_trend}")
                
                # RSI conditions
                if direction == "LONG" and 30 < rsi_h1 < 60:
                    score += 25
                    reasons.append(f"✅ RSI {rsi_h1:.0f} favorable for LONG")
                elif direction == "SHORT" and 40 < rsi_h1 < 70:
                    score += 25
                    reasons.append(f"✅ RSI {rsi_h1:.0f} favorable for SHORT")
                
                # Momentum
                last_5 = df_m15['close'].tail(5).values
                if (last_5[-1] > last_5[0] and direction == "LONG") or (last_5[-1] < last_5[0] and direction == "SHORT"):
                    score += 20
                    reasons.append("✅ Momentum confirms")
                
                # Pullback entry
                dist_from_ema = abs(current - m15_ema20) / current
                if dist_from_ema < 0.005:
                    score += 15
                    reasons.append("✅ Pullback entry")
                    
                # High R:R bonus
                if rr2 >= 5:
                    score += 20
                    reasons.append(f"⭐ EXTREME R:R {rr2:.1f}:1")
                elif rr2 >= 4:
                    score += 15
                    reasons.append(f"⭐ HIGH R:R {rr2:.1f}:1")
                elif rr2 >= 3:
                    score += 10
                    reasons.append(f"✅ Good R:R {rr2:.1f}:1")
                
                # Build setup object
                setup = {
                    'symbol': symbol,
                    'score': score,
                    'direction': direction,
                    'entry': current,
                    'sl': sl,
                    'tp1': tp1,
                    'tp2': tp2,
                    'rr1': rr1,
                    'rr2': rr2,
                    'rsi': rsi_h1,
                    'trend': h1_trend,
                    'reasons': reasons,
                    'atr': atr
                }
                
                # Categorize
                if score >= 70:
                    high_prob_setups.append(setup)
                
                if rr2 >= 3.0:  # High R:R threshold
                    high_rr_setups.append(setup)
        
        except Exception as e:
            pass  # Skip problematic symbols
    
    # Print HIGH PROBABILITY setups
    if high_prob_setups:
        high_prob_setups.sort(key=lambda x: x['score'], reverse=True)
        print("\n" + "="*100)
        print("🎯 HIGH PROBABILITY SETUPS (Score >= 70)")
        print("="*100)
        
        for i, s in enumerate(high_prob_setups[:5], 1):  # Top 5
            print(f"\n#{i}. {s['symbol']} - Score: {s['score']}/100 | {s['direction']} | R:R: {s['rr2']:.2f}:1")
            print(f"    Entry: {s['entry']:.5f} | SL: {s['sl']:.5f} | TP: {s['tp2']:.5f}")
            print(f"    RSI: {s['rsi']:.1f} | Trend: {s['trend']}")
    
    # Print HIGH R:R setups
    if high_rr_setups:
        high_rr_setups.sort(key=lambda x: x['rr2'], reverse=True)
        print("\n" + "="*100)
        print("💎 HIGH RISK:REWARD SETUPS (R:R >= 3:1)")
        print("="*100)
        
        for i, s in enumerate(high_rr_setups[:10], 1):  # Top 10
            print(f"\n#{i}. {s['symbol']} - R:R: {s['rr2']:.2f}:1 | Score: {s['score']}/100 | {s['direction']}")
            print(f"    Entry: {s['entry']:.5f} | SL: {s['sl']:.5f} | TP: {s['tp2']:.5f}")
            print(f"    RSI: {s['rsi']:.1f} | Reasons: {', '.join(s['reasons'][:2])}")
    
    if not high_prob_setups and not high_rr_setups:
        print("\n❌ No high-quality setups found meeting criteria.")
    
    print(f"\n{'='*100}")
    print(f"Scanned: {len(symbols_to_scan)} symbols")
    print(f"High Probability (>=70): {len(high_prob_setups)}")
    print(f"High R:R (>=3:1): {len(high_rr_setups)}")
    print(f"{'='*100}\n")
    
    mt5.shutdown()

if __name__ == "__main__":
    comprehensive_scanner()
