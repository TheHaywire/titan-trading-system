"""
Weekly Trading Plan Generator - Institutional Macro Desk
Generates comprehensive market-wide trading plan across all major asset classes.
"""

import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
import subprocess
import sys

# Instrument Universe
INSTRUMENTS = {
    'Equities': {
        'US Large': [('S&P 500', 'US500', 'ES'), ('Nasdaq 100', 'US100', 'NQ'), ('Dow Jones', 'US30', 'YM')],
        'US Small': [('Russell 2000', 'US2000', 'RTY')],
        'Europe': [('DAX', 'GER40', 'FDAX'), ('FTSE', 'UK100', 'FTSE')]
    },
    'Currencies': {
        'G10 Majors': [('EUR/USD', 'EURUSD', 'EUR'), ('GBP/USD', 'GBPUSD', 'GBP'), ('USD/JPY', 'USDJPY', 'JPY')],
        'G10 Minors': [('AUD/USD', 'AUDUSD', 'AUD'), ('NZD/USD', 'NZDUSD', 'NZD')],
        'EM': [('USD/TRY', 'USDTRY', 'TRY'), ('USD/ZAR', 'USDZAR', 'ZAR')]
    },
    'Energies': {
        'Crude': [('WTI Crude', 'OIL', 'CL'), ('Natural Gas', 'NGAS', 'NG')]
    },
    'Metals': {
        'Precious': [('Gold', 'GOLD', 'GC'), ('Silver', 'SILVER', 'SI')],
        'Industrial': [('Copper', 'COPPER', 'HG')]
    },
    'Crypto': {
        'Major': [('Bitcoin', 'BTCUSD', 'BTC'), ('Ethereum', 'ETHUSD', 'ETH')]
    }
}

from data_intelligence import DataIntelligence

# Create intelligence engine
intel = DataIntelligence()

import time

def resolve_symbol(root):
    """
    Finds the best matching symbol in MT5 for a given root.
    Prioritizes 'Cash' symbols, then indices, then futures.
    """
    if not mt5.initialize():
        return None
        
    # 1. Exact match
    if mt5.symbol_select(root, True):
        time.sleep(1) # Allow MT5 to populate data
        return root
        
    # 2. Try with 'Cash' suffix
    cash_sym = f"{root}Cash"
    if mt5.symbol_select(cash_sym, True):
        time.sleep(1)
        return cash_sym
        
    # 3. Try with common suffixes
    for suffix in ["m", ".pro", ".raw"]:
        s = f"{root}{suffix}"
        if mt5.symbol_select(s, True):
            time.sleep(1)
            return s
            
    # 4. Search full list
    all_symbols = [s.name for s in mt5.symbols_get()]
    for s in all_symbols:
        if root.upper() in s.upper():
            if mt5.symbol_select(s, True):
                time.sleep(1)
                return s
            
    return None

def get_mtf_trends(symbol_root):
    """Get multi-timeframe trend analysis with retries."""
    symbol = resolve_symbol(symbol_root)
    if not symbol:
        return 'N/A', 'N/A', 'N/A', None
        
    # Retry loop for data population
    for attempt in range(3):
        try:
            # Daily
            rates_d = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 50)
            if rates_d is not None and len(rates_d) >= 20:
                df_d = pd.DataFrame(rates_d)
                sma20_d = df_d['close'].rolling(20).mean().iloc[-1]
                current_d = df_d['close'].iloc[-1]
                trend_d = '↑' if current_d > sma20_d else '↓'
                
                # Weekly (using H4 100 as proxy)
                rates_w = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 100)
                if rates_w is not None and len(rates_w) >= 50:
                    df_w = pd.DataFrame(rates_w)
                    sma50_w = df_w['close'].rolling(50).mean().iloc[-1]
                    current_w = df_w['close'].iloc[-1]
                    trend_w = '↑' if current_w > sma50_w else '↓'
                    
                    # HTF determination
                    if trend_d == '↑' and trend_w == '↑': htf = 'Bullish'
                    elif trend_d == '↓' and trend_w == '↓': htf = 'Bearish'
                    else: htf = 'Mixed'
                    
                    return trend_d, trend_w, htf, symbol
            
            # Wait and retry if data is missing
            time.sleep(2)
        except Exception as e:
            print(f"    Attempt {attempt+1} failed for {symbol}: {e}")
            time.sleep(2)
            
    return 'N/A', 'N/A', 'N/A', symbol

def calculate_net_score(symbol, trend_d, trend_w, positioning, seasonal, oi_change):
    """
    Implements institutional scoring from -2 to +2 per component.
    """
    # 1. Trend Alignment (-2 to +2)
    trend_score = 0
    if trend_d == '↑' and trend_w == '↑': trend_score = 2
    elif trend_d == '↓' and trend_w == '↓': trend_score = -2
    elif trend_d == '↑': trend_score = 1
    elif trend_d == '↓': trend_score = -1
    
    # 2. Momentum (-2 to +2) - Proxy based on RSI or price location
    mom_score = 1 if trend_d == '↑' else -1
    
    # 3. Positioning Risk (-2 to +2) - Contrarian Logic
    pos_score = 0
    if "Extreme Long" in positioning: pos_score = -2
    elif "Speculative Long" in positioning: pos_score = -1
    elif "Extreme Short" in positioning: pos_score = 2
    elif "Net Short" in positioning: pos_score = 1
    
    # 4. Volatility Regime (-2 to +2)
    vol_score = 0 # Baseline
    
    # 5. Fundamental Pressure (-2 to +2)
    fund_score = 1 if seasonal in ["Positive", "Strong Positive"] else (-1 if seasonal in ["Negative", "Strong Negative"] else 0)
    
    net_score = trend_score + mom_score + pos_score + vol_score + fund_score
    return net_score

def get_risk_guidance(net_score, environment):
    """Determines focus and risk level based on net score."""
    if net_score >= 4:
        return 'Long', 'Aggressive'
    elif net_score >= 2:
        return 'Long', 'Normal'
    elif net_score <= -4:
        return 'Short', 'Aggressive'
    elif net_score <= -2:
        return 'Short', 'Normal'
    else:
        return 'Stand Aside', 'Reduced'

def generate_weekly_plan():
    """Generate the complete Weekly Trading Plan."""
    
    print("=" * 100)
    print("GENERATING INSTITUTIONAL WEEKLY TRADING PLAN (ROBUST SYMBOLS)")
    print("=" * 100)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    plan_rows = []
    
    for asset_class, sub_groups in INSTRUMENTS.items():
        print(f"\n[{asset_class}] Analyzing...")
        
        for sub_group, instruments_list in sub_groups.items():
            for instrument_name, symbol_root, ticker in instruments_list:
                print(f"  Processing: {instrument_name} ({symbol_root})...")
                
                # 1. Get Trend Data and Resolving Symbol
                trend_d, trend_w, htf_trend, active_symbol = get_mtf_trends(symbol_root)
                
                if not active_symbol:
                    print(f"    ⚠️ Symbol {symbol_root} NOT FOUND at broker. Skipping.")
                    continue
                
                # 2. Get Intelligence Data
                positioning = intel.get_cot_positioning(active_symbol)
                seasonal = intel.get_seasonality(active_symbol)
                oi_change = intel.get_oi_change(active_symbol)
                
                # 3. Calculate Scores
                net_score = calculate_net_score(active_symbol, trend_d, trend_w, positioning, seasonal, oi_change)
                environment = "Trend" if abs(net_score) >= 3 else ("Range" if abs(net_score) >= 1 else "Uncertain")
                focus, risk = get_risk_guidance(net_score, environment)
                
                # 4. Conviction Calculation
                mtf_aligned = (trend_d == trend_w)
                conviction = 'High' if abs(net_score) >= 5 else ('Medium' if abs(net_score) >= 2 else 'Low')
                
                # Primary Bias
                primary_bias = 'Bullish' if net_score > 0 else ('Bearish' if net_score < 0 else 'Neutral')
                
                # Notes
                notes = []
                if "Extreme" in positioning: notes.append(f"Positioning {positioning}")
                if "Strong" in seasonal: notes.append(f"Seasonality {seasonal}")
                if abs(oi_change) > 20: notes.append("OI Extreme")
                
                notes_str = ", ".join(notes) if notes else "-"
                
                # Build row
                row = {
                    'Asset Class': asset_class,
                    'Sub-Group': sub_group,
                    'Instrument': instrument_name,
                    'Ticker': ticker,
                    'Seasonal': seasonal,
                    'Trend (D/W)': f"{trend_d}/{trend_w}",
                    'HTF Trend': htf_trend,
                    'OI Change': f"{oi_change:+.1f}%",
                    'Positioning': positioning,
                    'Primary Bias': primary_bias,
                    'Conviction': conviction,
                    'Net Score': net_score,
                    'Environment': environment,
                    'Focus': focus,
                    'Risk Guidance': risk,
                    'Notes': notes_str
                }
                
                plan_rows.append(row)
    
    # Create DataFrame
    df_plan = pd.DataFrame(plan_rows)
    
    # Save to CSV
    filename = f"WEEKLY_TRADING_PLAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        df_plan.to_csv(filename, index=False)
        print("\n" + "=" * 100)
        print(f"✅ REAL-DATA PLAN GENERATED: {filename}")
        print("=" * 100)
    except PermissionError:
        backup_file = f"WEEKLY_TRADING_PLAN_LOCKED_{datetime.now().strftime('%H%M%S')}.csv"
        df_plan.to_csv(backup_file, index=False)
        print(f"\n⚠️  COULD NOT OVERWRITE {filename} (File is open). Saved to {backup_file} instead.")
    
    # Display high score opportunities
    print("\nHIGH CONVICTION FOCUS:")
    top_focus = df_plan[df_plan['Focus'] != 'Stand Aside'].sort_values('Net Score', ascending=False)
    if not top_focus.empty:
        print(top_focus[['Instrument', 'Net Score', 'Focus', 'Risk Guidance', 'Notes']])
    else:
        print("  Patience required - No high score signals found.")
    
    mt5.shutdown()
    return df_plan

if __name__ == "__main__":
    plan = generate_weekly_plan()
    print("\n✅ Weekly Trading Plan generation complete!")
