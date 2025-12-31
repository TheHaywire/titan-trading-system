import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.getcwd())

def fetch_complete_history():
    """Fetch all historical deals from MT5 account."""
    print("🔍 Fetching Complete Trading History...")
    
    if not mt5.initialize():
        print("❌ MT5 Init Failed")
        return None
    
    # Get account info
    account_info = mt5.account_info()
    print(f"📊 Account: {account_info.login}")
    print(f"💰 Balance: ${account_info.balance:,.2f}")
    
    # Fetch ALL deals (from account creation to now)
    # MT5 stores deals, not just trades
    deals = mt5.history_deals_get(datetime(2020, 1, 1), datetime.now())
    
    if deals is None or len(deals) == 0:
        print("❌ No trade history found")
        return None
    
    print(f"✅ Found {len(deals)} deals")
    
    # Convert to DataFrame
    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    
    # Filter: Only ENTRY and EXIT deals (not balance operations)
    df = df[df['entry'].isin([mt5.DEAL_ENTRY_IN, mt5.DEAL_ENTRY_OUT])]
    
    # Add human-readable columns
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['side'] = df['type'].apply(lambda x: 'BUY' if x == mt5.DEAL_TYPE_BUY else 'SELL')
    df['entry_type'] = df['entry'].apply(lambda x: 'ENTRY' if x == mt5.DEAL_ENTRY_IN else 'EXIT')
    
    # Save to CSV
    output_file = "data/trade_history_full.csv"
    os.makedirs("data", exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"💾 Saved to {output_file}")
    
    return df

def analyze_trades(df):
    """Perform statistical analysis on trades."""
    print("\n📈 TRADE ANALYSIS REPORT")
    print("=" * 60)
    
    # 1. Overall Stats
    total_deals = len(df)
    total_profit = df['profit'].sum()
    total_commission = df['commission'].sum()
    net_profit = total_profit + total_commission
    
    print(f"\n🎯 OVERALL PERFORMANCE")
    print(f"Total Deals: {total_deals}")
    print(f"Gross Profit: ${total_profit:,.2f}")
    print(f"Commission: ${total_commission:,.2f}")
    print(f"Net Profit: ${net_profit:,.2f}")
    
    # 2. Winners vs Losers
    exits = df[df['entry_type'] == 'EXIT'].copy()
    winners = exits[exits['profit'] > 0]
    losers = exits[exits['profit'] < 0]
    
    win_rate = len(winners) / len(exits) * 100 if len(exits) > 0 else 0
    avg_win = winners['profit'].mean() if len(winners) > 0 else 0
    avg_loss = losers['profit'].mean() if len(losers) > 0 else 0
    
    print(f"\n💰 WIN/LOSS BREAKDOWN")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Winners: {len(winners)} (Avg: ${avg_win:.2f})")
    print(f"Losers: {len(losers)} (Avg: ${avg_loss:.2f})")
    print(f"Profit Factor: {abs(winners['profit'].sum() / losers['profit'].sum()):.2f}" if len(losers) > 0 else "N/A")
    
    # 3. By Symbol
    print(f"\n📊 TOP SYMBOLS BY PROFIT")
    symbol_pnl = exits.groupby('symbol')['profit'].agg(['sum', 'count', 'mean']).sort_values('sum', ascending=False)
    print(symbol_pnl.head(10))
    
    # 4. By Time (Session Analysis)
    exits['hour'] = exits['time'].dt.hour
    exits['session'] = exits['hour'].apply(classify_session)
    
    print(f"\n🕒 PROFIT BY SESSION")
    session_pnl = exits.groupby('session')['profit'].agg(['sum', 'count', 'mean'])
    print(session_pnl)
    
    # 5. Hold Duration (if we can pair entries/exits)
    print(f"\n⏱️ HOLD DURATION ANALYSIS")
    print("(Requires ticket matching - skipping for now)")
    
    return {
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'best_symbols': symbol_pnl.head(5).to_dict(),
        'session_performance': session_pnl.to_dict()
    }

def classify_session(hour):
    """Classify GMT hour into trading session."""
    if 21 <= hour or hour < 6:
        return "ASIAN"
    elif 6 <= hour < 14:
        return "LONDON"
    else:
        return "NY"

if __name__ == "__main__":
    df = fetch_complete_history()
    if df is not None:
        stats = analyze_trades(df)
        print("\n✅ Analysis Complete")
