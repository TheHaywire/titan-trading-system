"""
Export MT5 Trade History for Trading Journals
==============================================
Exports your trades to CSV format compatible with:
- Tradervue
- TraderSync
- Edgewonk
- Any spreadsheet

Run: python export_trades.py
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os

def export_trades(days=90):
    """Export trade history to CSV for trading journal import."""
    
    if not mt5.initialize():
        print("Failed to connect to MT5")
        return None
    
    # Get trade history
    from_date = datetime.now() - timedelta(days=days)
    deals = mt5.history_deals_get(from_date, datetime.now())
    
    if not deals:
        print("No trades found")
        mt5.shutdown()
        return None
    
    # Convert to DataFrame
    data = []
    for d in deals:
        if d.profit != 0 or d.volume > 0:  # Include all trades
            data.append({
                'Date': datetime.fromtimestamp(d.time).strftime('%Y-%m-%d'),
                'Time': datetime.fromtimestamp(d.time).strftime('%H:%M:%S'),
                'Symbol': d.symbol,
                'Side': 'Buy' if d.type == 0 else 'Sell' if d.type == 1 else 'Other',
                'Quantity': d.volume,
                'Price': d.price,
                'P&L': d.profit,
                'Commission': d.commission,
                'Swap': d.swap,
                'Order': d.order,
                'Deal': d.ticket,
            })
    
    df = pd.DataFrame(data)
    
    # Save to CSV
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, f'trades_export_{datetime.now().strftime("%Y%m%d")}.csv')
    df.to_csv(output_path, index=False)
    
    print(f"\n✅ Exported {len(df)} trades to: {output_path}")
    print(f"\n📊 Summary:")
    print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"   Total P&L: ${df['P&L'].sum():,.2f}")
    print(f"   Unique symbols: {df['Symbol'].nunique()}")
    
    # Show top performers
    if not df.empty:
        symbol_pnl = df.groupby('Symbol')['P&L'].sum().sort_values(ascending=False)
        print(f"\n📈 Top Performers:")
        for sym, pnl in symbol_pnl.head(3).items():
            print(f"   {sym}: ${pnl:,.2f}")
        
        print(f"\n📉 Worst Performers:")
        for sym, pnl in symbol_pnl.tail(3).items():
            print(f"   {sym}: ${pnl:,.2f}")
    
    mt5.shutdown()
    return output_path

if __name__ == "__main__":
    print("="*60)
    print("MT5 Trade Exporter for Trading Journals")
    print("="*60)
    
    days = 90  # Export last 90 days
    export_trades(days)
    
    print("\n" + "="*60)
    print("You can now import this CSV into:")
    print("  - Tradervue (https://tradervue.com)")
    print("  - TraderSync (https://tradersync.com)")
    print("  - Edgewonk (https://edgewonk.com)")
    print("  - Google Sheets / Excel")
    print("="*60)
