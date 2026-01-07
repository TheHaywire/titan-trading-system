import MetaTrader5 as mt5
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import track

# Path Hack
sys.path.append(os.path.join(os.getcwd()))

from titan_system.core.memory import MemorySystem

console = Console()

def sync_trades(days=5):
    console.print(f"[bold cyan]🔄 SYNCHRONIZING TRADES FROM MT5 ({days} days)[/bold cyan]")
    
    if not mt5.initialize():
        console.print("[red]MT5 initialization failed[/red]")
        return

    memory = MemorySystem()
    
    # Fetch history
    from_date = datetime.now() - timedelta(days=days)
    to_date = datetime.now()
    
    history_deals = mt5.history_deals_get(from_date, to_date)
    
    if history_deals is None or len(history_deals) == 0:
        console.print("[yellow]No trade history found.[/yellow]")
        mt5.shutdown()
        return

    df = pd.DataFrame(list(history_deals), columns=history_deals[0]._asdict().keys())
    
    # Filter for closing deals (out/out_by) to get realized profit
    # entry: 0=in, 1=out, 2=out_by, 3=in_out
    closed_deals = df[df['entry'] != 0].copy()
    
    if closed_deals.empty:
        console.print("[yellow]No closed trades found in history.[/yellow]")
        mt5.shutdown()
        return

    console.print(f"Found {len(closed_deals)} closed deals in MT5 history.")
    
    synced_count = 0
    for _, deal in track(closed_deals.iterrows(), total=len(closed_deals), description="Syncing to titan.db..."):
        # We need to map MT5 deal to our Trade Record format
        # For a closed deal, 'profit' is realized.
        # We try to find the matching 'in' deal for entry time/price, or just use deal data
        
        # If it's a 'deal', it has a ticket (the deal ticket) and position_id (the trade ticket)
        trade_id = str(deal['position_id'])
        
        trade_data = {
            'id': trade_id,
            'ticket': int(deal['position_id']),
            'symbol': deal['symbol'],
            'type': "SELL" if deal['type'] == 0 else "BUY", # if deal is OUT SELL, original was BUY? 
            # Actually MT5 deal types: 0=BUY, 1=SELL. 
            # If deal['entry'] is OUT and type is SELL, it means it closed a BUY.
            'volume': float(deal['volume']),
            'open_price': 0.0, # We'd need to fetch the original deal for this
            'sl': 0.0,
            'tp': 0.0,
            'open_time': datetime.fromtimestamp(deal['time']).strftime('%Y-%m-%d %H:%M:%S'),
            'close_time': datetime.fromtimestamp(deal['time']).strftime('%Y-%m-%d %H:%M:%S'),
            'close_price': float(deal['price']),
            'profit': float(deal['profit']) + float(deal['commission']) + float(deal['swap']),
            'magic': int(deal['magic']),
            'comment': deal['comment'],
            'strategy_name': "MT5_SYNCED"
        }
        
        # Try to find the entry deal to get open price/time
        entry_deal = df[(df['position_id'] == deal['position_id']) & (df['entry'] == 0)]
        if not entry_deal.empty:
            e = entry_deal.iloc[0]
            trade_data['open_price'] = float(e['price'])
            trade_data['open_time'] = datetime.fromtimestamp(e['time']).strftime('%Y-%m-%d %H:%M:%S')
            trade_data['type'] = "BUY" if e['type'] == 0 else "SELL"
            
        memory.record_trade(trade_data)
        synced_count += 1

    console.print(f"[bold green]✅ SUCCESSFULLY SYNCED {synced_count} TRADES TO TITAN.DB[/bold green]")
    mt5.shutdown()

if __name__ == "__main__":
    sync_trades(days=10) # Sync last 10 days to be sure
