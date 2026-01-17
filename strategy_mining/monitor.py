"""
Live Monitor for Brute-Force Strategy Mining Engine
Provides a real-time terminal dashboard of active positions and performance.
"""

import MetaTrader5 as mt5
import time
import os
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import strategy_mining.mining_config as config

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_pnl_color(pnl):
    if pnl > 0:
        return "\033[92m" # Green
    elif pnl < 0:
        return "\033[91m" # Red
    else:
        return "\033[0m"  # Default

def print_dashboard():
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return

    while True:
        try:
            clear_screen()
            acc = mt5.account_info()
            positions = mt5.positions_get(magic=config.MT5_MAGIC_NUMBER)
            
            print("=" * 80)
            print(f" TITAN MINING ENGINE - LIVE MONITOR | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            print(f" Account: {acc.login} | Equity: ${acc.equity:,.2f} | Margin: {acc.margin_level:.1f}%")
            print("-" * 80)
            
            if not positions:
                print("\n   >>> NO ACTIVE POSITIONS <<<")
            else:
                print(f"{'Symbol':<10} | {'Type':<5} | {'Lots':<6} | {'Entry':<10} | {'Current':<10} | {'PnL ($)':<12} | {'R-Stat'}")
                print("-" * 80)
                
                total_pnl = 0
                for p in positions:
                    p_type = "SELL" if p.type == mt5.POSITION_TYPE_SELL else "BUY"
                    tick = mt5.symbol_info_tick(p.symbol)
                    curr_price = tick.bid if p.type == mt5.POSITION_TYPE_BUY else tick.ask
                    
                    # Calculate R-Multiple (Approximate)
                    # We assume 1R = Initial SL distance. If SL is 0, we can't calculate R.
                    r_stat = "N/A"
                    if p.sl != 0:
                        risk_per_unit = abs(p.price_open - p.sl)
                        if risk_per_unit > 0:
                            profit_per_unit = (curr_price - p.price_open) if p.type == mt5.POSITION_TYPE_BUY else (p.price_open - curr_price)
                            r_stat = f"{profit_per_unit / risk_per_unit:+.2f}R"

                    color = get_pnl_color(p.profit)
                    print(f"{p.symbol:<10} | {p_type:<5} | {p.volume:<6.2f} | {p.price_open:<10.5f} | {curr_price:<10.5f} | {color}{p.profit:>11.2f}\033[0m | {r_stat}")
                    total_pnl += p.profit
                
                print("-" * 80)
                color = get_pnl_color(total_pnl)
                print(f"{'TOTAL FLOATING PnL':<54} | {color}${total_pnl:>11.2f}\033[0m")

            print("=" * 80)
            print(" [Ctrl+C] to Exit | Updating every 2 seconds...")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print_dashboard()
