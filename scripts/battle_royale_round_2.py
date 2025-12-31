"""
Strategy Battle Royale: ROUND 2
Testing FVG Fills, EMA Crosses, and Asia Range Fades.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import time
from titan_system.smc.fvg import FVGDetector
from config.settings import settings

def run_battle_royale_round_2():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    symbol = "GOLD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 2000) 
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Pre-calculate Indicators
    # EMA for Strategy E
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # Trackers
    pnl_D = 0.0 # FVG
    pnl_E = 0.0 # EMA Cross
    pnl_F = 0.0 # Asia Fade
    
    trades_D = 0
    trades_E = 0
    trades_F = 0
    
    active_D = None
    active_E = None
    active_F = None
    
    # Asia Range Markers
    asia_high = None
    asia_low = None
    today_date = None
    asia_fade_taken = False
    
    fvg_detector = FVGDetector(min_gap_size=1.0)
    
    with open("battle_results_round_2.txt", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")
            
        log("\n" + "="*80)
        log(f"🥊 BATTLE ROYALE RD 2: GOLD (Last 14 Days)")
        log("D: FVG Fill | E: EMA Cross | F: Asia Fade")
        log("="*80)
        
        # Need window for FVG detection
        for i in range(100, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # --- STRATEGY D: FVG FILLER (Limit Orders) ---
            # Simplified backtest: If FVG detected 2 bars ago, assume limit placed at start.
            # If price hits limit -> Enter.
            # FVG logic is complex for simple iteration. 
            # Simplified Logic: Check previous 3 candles. Huge body? Gap?
            
            # Using imported FVG Detector on a window
            window = df.iloc[i-50:i].copy() # Slice for detection
            # Convert to numpy for detector
            ops = window['open'].values
            his = window['high'].values
            los = window['low'].values
            cls = window['close'].values
            
            fvgs = fvg_detector.detect_fvg(ops, his, los, cls)
            
            if active_D:
                if active_D['type'] == 'BUY':
                    if row['low'] <= active_D['sl']: pnl_D -= 50; active_D = None
                    elif row['high'] >= active_D['tp']: pnl_D += 100; active_D = None
                else:
                    if row['high'] >= active_D['sl']: pnl_D -= 50; active_D = None
                    elif row['low'] <= active_D['tp']: pnl_D += 100; active_D = None
            
            if not active_D and fvgs:
                # Check MOST RECENT FVG
                last_fvg = fvgs[-1]
                # Only care if it's fresh (created in last 3 bars)
                if last_fvg['index'] >= 45: # within window
                    # If Bullish FVG, we want to buy at 'top' (retest)
                    if last_fvg['type'] == 'bullish_fvg':
                         # If price dips into it
                         if row['low'] <= last_fvg['top']:
                             active_D = {'type': 'BUY', 'entry': last_fvg['top'], 'sl': last_fvg['bottom'], 'tp': last_fvg['top'] + (last_fvg['top']-last_fvg['bottom'])*2}
                             trades_D += 1
                    elif last_fvg['type'] == 'bearish_fvg':
                         if row['high'] >= last_fvg['bottom']:
                             active_D = {'type': 'SELL', 'entry': last_fvg['bottom'], 'sl': last_fvg['top'], 'tp': last_fvg['bottom'] - (last_fvg['top']-last_fvg['bottom'])*2}
                             trades_D += 1

            # --- STRATEGY E: EMA CROSS (The Trend) ---
            if active_E:
                # Holding until cross back
                if active_E['type'] == 'BUY':
                    if row['ema_9'] < row['ema_21']: # Cross DOwn -> Exit
                        pnl_E += (row['close'] - active_E['entry']) * 10
                        active_E = None
                else:
                    if row['ema_9'] > row['ema_21']: # Cross Up -> Exit
                        pnl_E += (active_E['entry'] - row['close']) * 10
                        active_E = None
            else:
                # Cross Up
                if prev['ema_9'] <= prev['ema_21'] and row['ema_9'] > row['ema_21']:
                    active_E = {'type': 'BUY', 'entry': row['close']}
                    trades_E += 1
                # Cross Down
                elif prev['ema_9'] >= prev['ema_21'] and row['ema_9'] < row['ema_21']:
                    active_E = {'type': 'SELL', 'entry': row['close']}
                    trades_E += 1

            # --- STRATEGY F: ASIA FADE (The Trap) ---
            # 1. Reset Daily
            current_date = row['time'].date()
            if current_date != today_date:
                today_date = current_date
                asia_high = None
                asia_low = None
                asia_fade_taken = False
                
            # 2. Define Range (00:00 - 08:00 Server Time approx)
            # Assuming data is UTC+2 or similar. 
            current_hour = row['time'].hour
            if current_hour < 8:
                if asia_high is None or row['high'] > asia_high: asia_high = row['high']
                if asia_low is None or row['low'] < asia_low: asia_low = row['low']
            
            # 3. Trade Period (08:00 - 12:00 London Open)
            if 8 <= current_hour <= 12 and not asia_fade_taken and not active_F:
                if asia_high and row['high'] > asia_high:
                    # Breakout Up -> Fade Short
                    active_F = {'type': 'SELL', 'entry': row['close'], 'sl': row['close'] + 5.0, 'tp': row['close'] - 10.0}
                    trades_F += 1
                    asia_fade_taken = True
                elif asia_low and row['low'] < asia_low:
                    # Breakout Down -> Fade Long
                    active_F = {'type': 'BUY', 'entry': row['close'], 'sl': row['close'] - 5.0, 'tp': row['close'] + 10.0}
                    trades_F += 1
                    asia_fade_taken = True
                    
            # Manage F
            if active_F:
                if active_F['type'] == 'BUY':
                    if row['low'] <= active_F['sl']: pnl_F -= 50; active_F = None
                    elif row['high'] >= active_F['tp']: pnl_F += 100; active_F = None
                else:
                    if row['high'] >= active_F['sl']: pnl_F -= 50; active_F = None
                    elif row['low'] <= active_F['tp']: pnl_F += 100; active_F = None

        log(f"📊 RESULTS:")
        results = [
            ("D: FVG Filler", pnl_D, trades_D),
            ("E: EMA Cross", pnl_E, trades_E),
            ("F: Asia Fade", pnl_F, trades_F)
        ]
        results.sort(key=lambda x: x[1])
        
        for name, pnl, trades in results:
            log(f"   {name:<25} | PnL: ${pnl:+.2f} | Trades: {trades}")
            
        log("="*80)
        
    mt5.shutdown()

if __name__ == "__main__":
    run_battle_royale_round_2()
