import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import numpy as np

def scan_high_probability_setups():
    if not mt5.initialize():
        return
    
    # Professional portfolio symbols
    symbols = ["GOLD", "EURUSD", "GBPUSD", "US100Cash", "US500Cash"]
    
    print("=" * 90)
    print(f"🎯 HIGH-PROBABILITY SETUP SCANNER - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 90)
    print("\nScanning for professional-grade setups with >70% probability...\n")
    
    setups = []
    
    for symbol in symbols:
        try:
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                continue
            
            current = tick.bid
            
            # Get H1 data
            h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
            
            if h1 is None or m15 is None:
                continue
            
            df_h1 = pd.DataFrame(h1)
            df_m15 = pd.DataFrame(m15)
            
            # Calculate indicators
            # RSI
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
            rsi_m15 = calc_rsi(df_m15['close'].values)[-1]
            
            # Trend alignment
            h1_ema20 = df_h1['close'].ewm(span=20).mean().iloc[-1]
            h1_ema50 = df_h1['close'].ewm(span=50).mean().iloc[-1]
            m15_ema20 = df_m15['close'].ewm(span=20).mean().iloc[-1]
            
            h1_trend = "UP" if h1_ema20 > h1_ema50 else "DOWN"
            m15_trend = "UP" if current > m15_ema20 else "DOWN"
            
            # Check alignment
            aligned = (h1_trend == m15_trend)
            
            # ATR for volatility
            df_h1['tr'] = df_h1.apply(lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1)
            atr = df_h1['tr'].tail(14).mean()
            
            # Volume check
            recent_vol = df_m15['tick_volume'].tail(10).mean()
            older_vol = df_m15['tick_volume'].tail(30).mean()
            vol_surge = recent_vol / older_vol if older_vol > 0 else 1
            
            # Determine setup quality
            score = 0
            reasons = []
            
            # Trend alignment (30 points)
            if aligned:
                score += 30
                reasons.append(f"✅ H1/M15 aligned {h1_trend}")
            
            # RSI conditions (20 points)
            if h1_trend == "UP" and rsi_h1 < 60:
                score += 20
                reasons.append(f"✅ RSI {rsi_h1:.0f} not overbought")
            elif h1_trend == "DOWN" and rsi_h1 > 40:
                score += 20
                reasons.append(f"✅ RSI {rsi_h1:.0f} not oversold")
            
            # Momentum (20 points)
            last_5_closes = df_m15['close'].tail(5).values
            momentum_direction = "UP" if last_5_closes[-1] > last_5_closes[0] else "DOWN"
            if momentum_direction == h1_trend:
                score += 20
                reasons.append(f"✅ Momentum confirms {h1_trend}")
            
            # Volatility (15 points)
            if vol_surge < 1.5:  # Not surging = good entry
                score += 15
                reasons.append("✅ No volatility surge")
            
            # Professional entry (15 points)
            pullback_dist = abs(current - m15_ema20)
            if pullback_dist / current < 0.005:  # Within 0.5% of EMA
                score += 15
                reasons.append("✅ Near M15 EMA (pullback)")
            
            # BUILD SETUP
            if score >= 70:
                direction = "LONG" if h1_trend == "UP" else "SHORT"
                
                # Calculate SL and TP
                if direction == "LONG":
                    sl = current - (atr * 1.5)
                    tp1 = current + (atr * 2)
                    tp2 = current + (atr * 3)
                else:
                    sl = current + (atr * 1.5)
                    tp1 = current - (atr * 2)
                    tp2 = current - (atr * 3)
                
                risk_pips = abs(current - sl)
                reward_pips = abs(tp2 - current)
                rr_ratio = reward_pips / risk_pips if risk_pips > 0 else 0
                
                # Position sizing based on score
                if score >= 85:
                    rec_size = "LARGE (20-30 lots)"
                    confidence = "VERY HIGH"
                elif score >= 75:
                    rec_size = "MEDIUM (10-15 lots)"
                    confidence = "HIGH"
                else:
                    rec_size = "SMALL (5-10 lots)"
                    confidence = "MODERATE"
                
                setups.append({
                    'symbol': symbol,
                    'score': score,
                    'direction': direction,
                    'entry': current,
                    'sl': sl,
                    'tp1': tp1,
                    'tp2': tp2,
                    'rr_ratio': rr_ratio,
                    'size': rec_size,
                    'confidence': confidence,
                    'reasons': reasons,
                    'rsi': rsi_h1,
                    'trend': h1_trend
                })
        
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
    
    # Print results
    if not setups:
        print("❌ No high-probability setups found at this time.\n")
        print("Current market conditions don't meet professional criteria (>70% score).")
    else:
        # Sort by score
        setups.sort(key=lambda x: x['score'], reverse=True)
        
        for i, setup in enumerate(setups, 1):
            print(f"\n{'='*90}")
            print(f"🎯 SETUP #{i}: {setup['symbol']} - SCORE: {setup['score']}/100 ({setup['confidence']})")
            print(f"{'='*90}")
            print(f"\n  Direction: {setup['direction']}")
            print(f"  Entry: ${setup['entry']:.5f}")
            print(f"  Stop Loss: ${setup['sl']:.5f}")
            print(f"  TP1: ${setup['tp1']:.5f}")
            print(f"  TP2: ${setup['tp2']:.5f}")
            print(f"  R:R Ratio: {setup['rr_ratio']:.2f}:1")
            print(f"  Recommended Size: {setup['size']}")
            print(f"\n  📊 Technical Analysis:")
            print(f"    • Trend: {setup['trend']}")
            print(f"    • RSI (H1): {setup['rsi']:.1f}")
            print(f"\n  ✅ Reasons (Professional Criteria):")
            for reason in setup['reasons']:
                print(f"    {reason}")
    
    mt5.shutdown()

if __name__ == "__main__":
    scan_high_probability_setups()
