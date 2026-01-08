
import sys
import os
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime
import time

# Path Setup
sys.path.append(os.getcwd())
from titan_system.core.execution import MT5Execution
from config.settings import settings
from titan_system.integrations.google_sheets import TitanSheets
from titan_system.utils.regime_detector import RegimeDetector
from titan_system.utils.session_manager import SessionManager
from titan_system.utils.correlation_manager import CorrelationManager

# Strategies
from titan_system.strategies.scalper_pro import MomentumScalper

def get_h1_trend(symbol):
    """Simple H1 EMA verification."""
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        if rates is None or len(rates) < 30: return "NEUTRAL"
        df = pd.DataFrame(rates)
        df['ema9'] = df['close'].ewm(span=9).mean()
        df['ema21'] = df['close'].ewm(span=21).mean()
        
        curr9 = df['ema9'].iloc[-1]
        curr21 = df['ema21'].iloc[-1]
        
        if curr9 > curr21 * 1.0001: return "BULLISH"
        if curr9 < curr21 * 0.9999: return "BEARISH"
        return "NEUTRAL"
    except Exception:
        return "NEUTRAL"

def scan_market():
    print("🌍 Connecting to Market Universe...")
    if not mt5.initialize():
        print("❌ MT5 Init failed")
        return

    # Initialize Components
    sheets = TitanSheets()
    detector = RegimeDetector()
    session_mgr = SessionManager()
    correlation_mgr = CorrelationManager()

    print("🔍 COMP 10K CHALLENGE (Institutional Filters)...")
    
    # Check Session
    session = session_mgr.get_session()
    print(f"🕒 Session: {session['status']} (Risk: {session['risk_multiplier']}x)")
    
    if not session['can_trade_majors']:
        print("💤 Asian Session (Low Volatility) - Pausing Scan")
        return

    # Get Open Positions for Correlation Check
    execution = MT5Execution(settings)
    open_positions = execution.get_positions()
    
    # DATA-DRIVEN ASSET FILTERS (Based on 17k trade analysis)
    # Target: Champions | Avoid: Profit Killers
    BLACKLIST = ["XAUUSD", "GOLD", "AUDUSD", "USDCHF", "CHFSGD", "ETHUSD", "USDHKD", "NZDSGD"]
    WHITELIST_PRIORITY = ["SILVER", "XAGUSD", "EURUSD", "GBPUSD", "BTCUSD", "US30", "NAS100"]
    
    # Combined target assets, excluding blacklist
    raw_list = ["SILVER", "XAGUSD", "EURUSD", "GBPUSD", "BTCUSD", "US30", "NAS100", "USDJPY", "USDCAD", "EURJPY"]
    target_assets = [a for a in raw_list if a not in BLACKLIST]
    
    universe = target_assets
    print(f"✅ Scanning {len(universe)} Optimized Symbols...")
    
    opportunities = []
    
    strategies = [
        MomentumScalper(config={"atr_period": 14, "ema_fast": 9, "ema_slow": 21}), 
    ]
    
    scan_list = universe
    
    for symbol in scan_list:
        # 1. DETECT REGIME
        regime = detector.detect(symbol)
        
        # Log to Dashboard
        if sheets.enabled:
            sheets.log_regime(symbol, regime)
            
        if not regime['trade_scalping']:
            print(f"   ⏩ Skipping {symbol} (Regime: {regime['regime']}, ADX: {regime['adx']:.1f})")
            continue

        # 2. CHECK MTF (H1 TREND)
        h1_trend = get_h1_trend(symbol)
        if h1_trend == "NEUTRAL":
            print(f"   ⏩ Skipping {symbol} (H1 Trend is Neutral)")
            continue
            
        # 3. SCAN M1
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
        except Exception:
            continue
            
        if rates is None or len(rates) < 50: continue
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        if 'tick_volume' in df.columns:
            df.rename(columns={'tick_volume': 'volume'}, inplace=True)
        elif 'real_volume' in df.columns:
             df.rename(columns={'real_volume': 'volume'}, inplace=True)
        
        # Analyze
        for strat in strategies:
            try:
                signal = strat.analyze(symbol, df)
                if signal and signal.get('signal') in ['BUY', 'SELL']:
                    
                    # 4. CONFIRM EXECUTION WITH H1
                    entry_signal = signal['signal']
                    if entry_signal == 'BUY' and h1_trend != 'BULLISH':
                        continue # Skip counter-trend
                    if entry_signal == 'SELL' and h1_trend != 'BEARISH':
                        continue # Skip counter-trend
                        
                    # 5. CORRELATION CHECK (NEW)
                    if not correlation_mgr.check_exposure(symbol, entry_signal, open_positions):
                        continue # Blocked by correlation manager
                    
                    # Calculate R:R
                    entry = df.iloc[-1]['close']
                    sl = signal.get('stop_loss')
                    tp = signal.get('take_profit')
                    
                    # Ensure SL/TP exist
                    atr = regime['atr'] if regime['atr'] > 0 else (df['high'] - df['low']).mean()
                    if not sl: sl = entry - (atr * 1.5) if entry_signal == 'BUY' else entry + (atr * 1.5)
                    if not tp: tp = entry + (atr * 3.0) if entry_signal == 'BUY' else entry - (atr * 3.0)
                    
                    risk = abs(entry - sl)
                    reward = abs(tp - entry)
                    
                    if risk == 0: continue
                    rr_ratio = reward / risk
                    
                    print(f"   💎 FOUND: {symbol} {strat.name} {entry_signal} R:R={rr_ratio:.2f} (Aligned with H1 {h1_trend})")
                    
                    if rr_ratio >= 1.0: 
                        opportunities.append({
                            "Symbol": symbol,
                            "Strategy": strat.name,
                            "Type": entry_signal,
                            "R:R": round(rr_ratio, 2),
                            "Confidence": signal.get('confidence', 0),
                            "Score": rr_ratio * signal.get('confidence', 0)
                        })
            except Exception as e:
                pass
                
    # Rank & Display
    if not opportunities:
        print("⚠️ No Institutional-Grade Setups Found (Filters Active)")
        return None

    # Sort by Score (Desc)
    ranked = sorted(opportunities, key=lambda x: x['Score'], reverse=True)
    
    print("\n🏆 TOP OPPORTUNITIES")
    print("=" * 60)
    print(f"{'SYMBOL':<10} {'TYPE':<6} {'R:R':<6} {'CONF':<6}")
    print("-" * 60)
    
    for op in ranked[:5]:
        print(f"{op['Symbol']:<10} {op['Type']:<6} {op['R:R']:<6} {op['Confidence']:<6}")
        
    print("=" * 60)
    
    # Return best for execution
    return ranked[0]

if __name__ == "__main__":
    scan_market()

