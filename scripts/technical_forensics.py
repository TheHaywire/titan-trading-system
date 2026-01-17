import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def get_detailed_tech(symbol, time_pos):
    # Fetch M15 and H1 context
    m15 = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M15, time_pos, 20)
    h1 = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_H1, time_pos, 5)
    
    if m15 is None or h1 is None:
        return "Data Missing"
        
    # M15 Trend
    m15_trend = "UP" if m15[-1]['close'] > m15[0]['close'] else "DOWN"
    # H1 Trend
    h1_trend = "UP" if h1[-1]['close'] > h1[0]['close'] else "DOWN"
    
    # RSI Proxy (Simple)
    body_sizes = [abs(r['close'] - r['open']) for r in m15]
    avg_body = sum(body_sizes) / len(body_sizes)
    last_body = abs(m15[-1]['close'] - m15[-1]['open'])
    volatility_surge = last_body > (avg_body * 2)
    
    return {
        "M15": m15_trend,
        "H1": h1_trend,
        "Surge": "YES" if volatility_surge else "NO",
        "Price": m15[-1]['close']
    }

def analyze_all_trades_technically(days=7):
    if not mt5.initialize():
        return
        
    from_date = datetime.now() - timedelta(days=days)
    history = mt5.history_deals_get(from_date, datetime.now())
    if not history:
        print("No trades found for this week.")
        return

    df = pd.DataFrame(list(history), columns=history[0]._asdict().keys())
    
    # Filter for entry deals to group by symbol
    print(f"# 📊 Weekly Technical Forensic Data ({days} Days)")
    
    symbol_stats = []
    
    for pos_id, group in df.groupby('position_id'):
        entry = group[group['entry'] == mt5.DEAL_ENTRY_IN]
        if entry.empty: continue
        
        symbol = entry['symbol'].iloc[0]
        type_name = "Buy" if entry['type'].iloc[0] == 0 else "Sell"
        profit = group['profit'].sum()
        time_done = int(entry['time'].iloc[0])
        
        tech = get_detailed_tech(symbol, time_done)
        if isinstance(tech, str): continue
        
        symbol_stats.append({
            'Symbol': symbol,
            'Type': type_name,
            'Profit': profit,
            'M15': tech['M15'],
            'H1': tech['H1'],
            'Surge': tech['Surge'],
            'Time': datetime.fromtimestamp(time_done)
        })

    df_stats = pd.DataFrame(symbol_stats)
    if not df_stats.empty:
        for symbol, group in df_stats.groupby('Symbol'):
            print(f"\n## {symbol} Weekly Physics")
            print(group[['Time', 'Type', 'Profit', 'M15', 'H1', 'Surge']].to_markdown(index=False))

    mt5.shutdown()

if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    analyze_all_trades_technically(days)
