"""
TITAN FUTURES BOT (Ernest Chan Momentum)
========================================
Automated trading for TU, ES, GC Futures.
Strategy: Buy if Price > Price[t-250], Sell if Price < Price[t-250].
Hold: Daily rebalance / Monthly hold simulation.

v1.0 - Production
"""

import MetaTrader5 as mt5
import pandas as pd
import time
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# CONFIGURATION
# =============
SYMBOLS = {
    'GC': 'HGCOP-MAR26',  # Gold/Copper (Update to preferred symbol)
    'TU': 'MTU',          # Treasury
    'ES': 'SES',          # S&P 500
} 

# If you find better symbols, update them here. 
# The bot maps 'Logical Name' -> 'MT5 Symbol'

LOOKBACK = 250
CHECK_HOUR = 23  # Run once per day at 11 PM

# State File
STATE_FILE = "titan_futures_state.json"

class TitanFuturesBot:
    def __init__(self):
        self.state = self.load_state()
        if not mt5.initialize():
            print("❌ MT5 Initialization Failed")
            raise Exception("MT5 Failed")
            
    def load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"last_run": None, "positions": {}}

    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=4)

    def get_symbol(self, logical_name):
        # Allow dynamic lookup or hardcoded
        s = SYMBOLS.get(logical_name)
        # Check if actually exists
        if mt5.symbol_info(s):
            return s
        # Fallback search
        return self.find_symbol(logical_name)

    def find_symbol(self, base_name):
        symbols = mt5.symbols_get()
        matches = [s.name for s in symbols if base_name in s.name]
        return matches[0] if matches else None

    def get_data(self, symbol):
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, LOOKBACK + 5)
        if rates is None: return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def analyze_market(self, symbol):
        df = self.get_data(symbol)
        if df is None or len(df) < LOOKBACK:
            return 0 # Not enough data
            
        current = df.iloc[-1]['close']
        past = df.iloc[-1 - LOOKBACK]['close']
        
        if current > past: return 1  # BUY
        if current < past: return -1 # SELL
        return 0

    def execute_logic(self):
        print(f"\n⏰ Running Logic at {datetime.now()}")
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        if self.state.get("last_run") == today_str:
            print("✅ Already ran today. Sleeping.")
            return

        for name, default_sym in SYMBOLS.items():
            symbol = self.get_symbol(name)
            if not symbol:
                print(f"❌ Could not find symbol for {name}")
                continue
                
            print(f"🔍 Analyzing {name} ({symbol})...")
            signal = self.analyze_market(symbol)
            
            # Current Positions Check
            positions = mt5.positions_get(symbol=symbol)
            current_lots = 0
            current_type = 0 # 0=Buy, 1=Sell (MT5 standard) is implied, but let's track net
            
            if positions:
                for p in positions:
                    if p.type == mt5.ORDER_TYPE_BUY: current_lots += p.volume
                    if p.type == mt5.ORDER_TYPE_SELL: current_lots -= p.volume
            
            # Execution Logic
            # Chan Strategy: Always be in the market (Long or Short) based on momentum
            target_vol = 0.1 # Default size (User should configure)
            
            if signal == 1:
                print(f"   🚀 SIGNAL: UPTREND (Price > Price[-250])")
                if current_lots <= 0:
                    print("   👉 ACTION: Close Shorts / Open Long")
                    self.close_positions(symbol, mt5.ORDER_TYPE_SELL)
                    self.open_trade(symbol, mt5.ORDER_TYPE_BUY, target_vol)
                else:
                    print("   ✅ Already Long")
                    
            elif signal == -1:
                print(f"   🔻 SIGNAL: DOWNTREND (Price < Price[-250])")
                if current_lots >= 0:
                    print("   👉 ACTION: Close Longs / Open Short")
                    self.close_positions(symbol, mt5.ORDER_TYPE_BUY)
                    self.open_trade(symbol, mt5.ORDER_TYPE_SELL, target_vol)
                else:
                    print("   ✅ Already Short")
            else:
                print("   ⚪ Neutral signal")

        self.state["last_run"] = today_str
        self.save_state()
        print("✅ Analysis Complete")

    def open_trade(self, symbol, order_type, volume):
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 99999,
            "comment": "TitanFutures Momentum",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = mt5.order_send(request)
        if res.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"   ❌ Trade Failed: {res.comment}")
        else:
            print(f"   ✅ Trade Executed: #{res.order}")

    def close_positions(self, symbol, type_to_close):
        positions = mt5.positions_get(symbol=symbol)
        if not positions: return
        
        for p in positions:
            if p.type == type_to_close:
                tick = mt5.symbol_info_tick(symbol)
                price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
                
                req = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": p.volume,
                    "type": 1 if p.type == 0 else 0, # Reverse type
                    "position": p.ticket,
                    "price": price,
                    "magic": 99999,
                }
                mt5.order_send(req)
                print(f"   🔒 Closed Position #{p.ticket}")

    def run_forever(self):
        print("🏃 Titan Futures Bot Started...")
        while True:
            # Simple scheduler
            now = datetime.now()
            # Run if it's past check hour OR if we haven't run today yet
            self.execute_logic()
            
            print(f"💤 Sleeping for 60 minutes...")
            time.sleep(3600)  # Check every hour to restart loop

if __name__ == "__main__":
    bot = TitanFuturesBot()
    bot.run_forever()
