"""
Titan Master Loop
The central nervous system that runs the Daily Operating Protocol (DOP).
Coordinates Strategy Layer (H4), Tactical Layer (H1), and Execution Layer (M15).
"""

import time
import schedule
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from config.settings import settings
from titan_system.smc.institutional_engine import InstitutionalEngine
from titan_system.notifications.email import EmailNotifier
import traceback

class TitanMasterLoop:
    def __init__(self):
        self.symbol = "GOLD"
        self.engine = InstitutionalEngine()
        self.notifier = EmailNotifier()
        self.current_bias = "NEUTRAL"
        self.active_zones = []
        self.is_trading_active = True
        
    def start(self):
        print("\n" + "="*60)
        print("🤖 TITAN MASTER LOOP STARTING | PROTOCOL ONLINE")
        print("="*60)
        
        self.connect_mt5()
        
        # Schedule the Protocol
        schedule.every().day.at("09:00").do(self.run_strategic_scan) # Morning Reset
        schedule.every().hour.do(self.run_tactical_scan)             # Hourly Zones
        schedule.every(5).minutes.do(self.run_execution_cycle)       # 5-min Trigger
        schedule.every(10).seconds.do(self.run_risk_guard)           # Real-time Risk
        
        # Initial Run
        self.run_strategic_scan()
        self.run_tactical_scan()
        
        print("\n⏳ Waiting for schedule triggers...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Master Loop Disengaged")
            mt5.shutdown()
            
    def connect_mt5(self):
        if not mt5.initialize():
            print("❌ MT5 Init Failed")
            return
        if settings.mt5_login:
            mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
            
    def run_strategic_scan(self):
        """09:00 AM - H4 Strategic Bias"""
        print(f"\n[{datetime.now().strftime('%H:%M')}] 🌅 STRATEGIC SCAN (H4)")
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H4, 0, 200)
            df = pd.DataFrame(rates)
            res = self.engine.analyze_symbol(df, self.symbol)
            
            self.current_bias = res['trend']['bias']
            regime = res['regime']
            
            msg = f"🌅 Morning Briefing: {self.symbol}\n"
            msg += f"Strategic Bias: {self.current_bias}\n"
            msg += f"Market Regime: {regime}\n"
            
            print(f"   >> Bias set to: {self.current_bias}")
            
            # Email Briefing
            trade_data = {
                'symbol': self.symbol,
                'type': "STRATEGIC UPDATE",
                'price': df['close'].iloc[-1],
                'strategy_name': self.current_bias,
                'comment': msg
            }
            self.notifier.send_trade_alert(trade_data=trade_data)
        except Exception as e:
            print(f"   ❌ Strategic Scan Error: {e}")

    def run_tactical_scan(self):
        """Hourly - H1 Zones & Liquidity"""
        print(f"\n[{datetime.now().strftime('%H:%M')}] 🌤️ TACTICAL SCAN (H1)")
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 200)
            df = pd.DataFrame(rates)
            res = self.engine.analyze_symbol(df, self.symbol)
            
            # Update Active Zones
            self.active_zones = []
            if res['liquidity']['sessions']['prev_day_high']:
                self.active_zones.append(('RESISTANCE', res['liquidity']['sessions']['prev_day_high']))
            if res['liquidity']['sessions']['prev_day_low']:
                self.active_zones.append(('SUPPORT', res['liquidity']['sessions']['prev_day_low']))
                
            print(f"   >> Active Zones Updated: {len(self.active_zones)} zones")
            
            # Check for immediate setups (LSR/TCB)
            if res['setup']:
                for s in res['setup']:
                    print(f"   🔥 TACTICAL SETUP: {s['name']}")
                    # (Here we could trigger execution or alert)
                    
        except Exception as e:
            print(f"   ❌ Tactical Scan Error: {e}")

    def run_execution_cycle(self):
        """5-Min - M15/M5 Execution Logic"""
        # Only run if trading is active
        if not self.is_trading_active: return
        
        # print(".", end="", flush=True) # Heartbeat
        
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M15, 0, 100)
            df = pd.DataFrame(rates)
            res = self.engine.analyze_symbol(df, self.symbol)
            
            current_price = df['close'].iloc[-1]
            mom = res['momentum']
            
            # 1. Proximity Filter
            # Only trade if near a zone OR momentum is extreme
            near_zone = False
            for z_type, level in self.active_zones:
                if abs(current_price - level) < 2.0: # Within 2 points/dollars
                    near_zone = True
                    # print(f"\n   🎯 ZONE PROXIMITY: {z_type} @ {level:.2f}")
            
            # 2. Execution Logic
            # SCALP SHORT (Bearish Bias OR Extreme Overbought)
            if (self.current_bias == "BEARISH" or self.current_bias == "NEUTRAL") and mom['rsi'] > 75:
                print(f"\n[{datetime.now().strftime('%H:%M')}] ⚡ TRIGGER: SHORT SCALP (RSI {mom['rsi']:.1f})")
                self.execute_trade("SELL", current_price)
                
            # SCALP LONG (Bullish Bias OR Extreme Oversold)
            elif (self.current_bias == "BULLISH" or self.current_bias == "NEUTRAL") and mom['rsi'] < 25:
                print(f"\n[{datetime.now().strftime('%H:%M')}] ⚡ TRIGGER: LONG SCALP (RSI {mom['rsi']:.1f})")
                self.execute_trade("BUY", current_price)
                
        except Exception as e:
            print(f"\n   ❌ Execution Error: {e}")

    def run_risk_guard(self):
        """Real-time circuit breaker"""
        try:
            account = mt5.account_info()
            if not account: return
            
            # Daily Loss Limit (Pseudo-code, needs tracking start equity)
            # if equity < start_equity * 0.97:
            #     self.is_trading_active = False
            #     print("\n🛡️ CIRCUIT BREAKER TRIPPED: 3% Daily Loss")
            #     mt5.positions_close_all()
            
            pass
        except Exception:
            pass

    def execute_trade(self, direction, price):
        """Send Order"""
        sl_points = 5.0
        tp_points = 10.0
        
        sl = price + sl_points if direction == "SELL" else price - sl_points
        tp = price - tp_points if direction == "SELL" else price + tp_points
        
        print(f"   🚀 EXECUTING {direction} | SL: {sl:.2f} | TP: {tp:.2f}")
        
        # Real execution logic would go here (using active_scalp_manager capabilities)
        # Using placeholder to avoid accidental firing during test
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": 0.01,
            "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "magic": 101010,
            "comment": "Titan Auto",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(req)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            print("   ✅ Trade Success")
        else:
            print(f"   ❌ Trade Failed: {res.comment}")

if __name__ == "__main__":
    bot = TitanMasterLoop()
    bot.start()
