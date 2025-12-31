
import MetaTrader5 as mt5
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
from config.settings import settings

def main():
    if not mt5.initialize():
        print("❌ MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    # 3. Today's History
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    history = mt5.history_deals_get(today, datetime.now() + timedelta(days=1))
    
    realized_pnl = 0.0
    trades_count = 0
    
    if history:
        for deal in history:
            if deal.entry == mt5.DEAL_ENTRY_OUT: # Closing deal
                realized_pnl += deal.profit
                realized_pnl += deal.swap
                realized_pnl += deal.commission
                trades_count += 1
                
    print(f"\nTODAY'S RESULTS")
    print(f"Realized PnL: ${realized_pnl:,.2f}")
    print(f"Trades Closed: {trades_count}")
    print("="*50)
    
    # 1. Account Info
    account = mt5.account_info()
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
