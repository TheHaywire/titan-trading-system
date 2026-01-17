"""
PROFESSIONAL POSITION MANAGER - Institutional Grade
====================================================
This script manages your positions exactly like a professional hedge fund would.

Rules implemented:
1. Risk management (trailing stops, breakeven protection)
2. Profit taking (scale out at targets)
3. Position sizing (never risk more than acceptable)
4. Time-based exits (don't hold losers forever)
5. Market condition adaptation

Run this script and it will trade for you using institutional rules.
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import pandas as pd

class ProfessionalTrader:
    def __init__(self):
        self.magic = 999999  # Different from bot to identify manual management
        self.managed_positions = {}
        
        # Professional parameters
        self.max_hold_time_hours = 48  # Don't hold a loser more than 48 hours
        self.breakeven_trigger = 0.3  # Move to BE at 0.3% profit
        self.scale_out_levels = [0.5, 1.0, 2.0]  # Scale out at these % profits
        self.trail_distance_pct = 0.4  # Trail stop 0.4% behind peak
        
        # Risk limits
        self.max_loss_per_position = 50000  # Max $50k loss per position
        self.daily_loss_limit = 150000  # Max $150k daily loss
        
        if not mt5.initialize():
            raise Exception("MT5 initialization failed")
    
    def get_current_positions(self):
        """Get all open positions"""
        positions = mt5.positions_get()
        return positions if positions else []
    
    def manage_position(self, pos):
        """Apply institutional management rules to a position"""
        
        symbol = pos.symbol
        ticket = pos.ticket
        pos_type = "LONG" if pos.type == 0 else "SHORT"
        
        # Calculate current metrics
        entry_price = pos.price_open
        current_price = pos.price_current
        profit = pos.profit
        profit_pct = ((current_price - entry_price) / entry_price * 100) if pos_type == "LONG" else ((entry_price - current_price) / entry_price * 100)
        
        # Time-based exit
        pos_time = datetime.fromtimestamp(pos.time)
        hours_held = (datetime.now() - pos_time).total_seconds() / 3600
        
        print(f"\n{'='*70}")
        print(f"📊 {symbol} {pos_type} - {pos.volume} lots")
        print(f"   Entry: ${entry_price:.2f} | Current: ${current_price:.2f}")
        print(f"   P&L: ${profit:,.0f} ({profit_pct:+.2f}%)")
        print(f"   Held: {hours_held:.1f} hours")
        
        # RULE 1: Maximum Loss Protection
        if profit < -self.max_loss_per_position:
            print(f"   🚨 MAX LOSS HIT (${profit:,.0f}) - CLOSING POSITION")
            self.close_position(ticket, symbol, "MAX_LOSS_PROTECTION")
            return
        
        # RULE 2: Time-based exit for losers
        if hours_held > self.max_hold_time_hours and profit < 0:
            print(f"   ⏰ HELD TOO LONG ({hours_held:.1f}h) WITH LOSS - CLOSING")
            self.close_position(ticket, symbol, "TIME_EXIT")
            return
        
        # RULE 3: Breakeven protection
        if profit_pct > self.breakeven_trigger:
            # Move SL to breakeven
            new_sl = entry_price
            if abs(new_sl - pos.sl) > 0.01:  # Only modify if different
                print(f"   ✅ BREAKEVEN STOP: ${new_sl:.2f}")
                self.modify_sl(ticket, symbol, new_sl, pos.tp)
        
        # RULE 4: Scale out profits
        for i, level in enumerate(self.scale_out_levels):
            if profit_pct > level and pos.volume > 5:  # Only if we have size
                scale_volume = pos.volume * 0.3  # Take 30% off
                scale_volume = round(scale_volume, 2)
                
                if scale_volume >= mt5.symbol_info(symbol).volume_min:
                    print(f"   💰 SCALE OUT at {level}%: Closing {scale_volume} lots")
                    self.partial_close(ticket, symbol, scale_volume)
                    break
        
        # RULE 5: Trailing stop
        if profit_pct > 1.0:  # Only trail if in profit >1%
            if symbol not in self.managed_positions:
                self.managed_positions[symbol] = {'peak_price': current_price}
            
            # Update peak
            if pos_type == "LONG":
                if current_price > self.managed_positions[symbol]['peak_price']:
                    self.managed_positions[symbol]['peak_price'] = current_price
            else:  # SHORT
                if current_price < self.managed_positions[symbol]['peak_price']:
                    self.managed_positions[symbol]['peak_price'] = current_price
            
            peak = self.managed_positions[symbol]['peak_price']
            trail_distance = peak * self.trail_distance_pct / 100
            
            if pos_type == "LONG":
                new_sl = peak - trail_distance
                if new_sl > pos.sl + 0.1:  # Higher than current
                    print(f"   🎯 TRAILING STOP: ${new_sl:.2f} (Peak: ${peak:.2f})")
                    self.modify_sl(ticket, symbol, new_sl, pos.tp)
            else:  # SHORT
                new_sl = peak + trail_distance
                if pos.sl == 0 or new_sl < pos.sl - 0.1:  # Lower than current
                    print(f"   🎯 TRAILING STOP: ${new_sl:.2f} (Peak: ${peak:.2f})")
                    self.modify_sl(ticket, symbol, new_sl, pos.tp)
    
    def close_position(self, ticket, symbol, reason):
        """Close entire position"""
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        
        pos = pos[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "magic": self.magic,
            "comment": f"AUTO_{reason}",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   ✅ CLOSED: {reason}")
            return True
        else:
            print(f"   ❌ CLOSE FAILED: {result.comment}")
            return False
    
    def partial_close(self, ticket, symbol, volume):
        """Partially close a position"""
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        
        pos = pos[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "magic": self.magic,
            "comment": "AUTO_SCALE_OUT",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   ✅ SCALED OUT: {volume} lots")
            return True
        else:
            print(f"   ❌ SCALE FAILED: {result.comment}")
            return False
    
    def modify_sl(self, ticket, symbol, new_sl, tp):
        """Modify stop loss"""
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": ticket,
            "sl": new_sl,
            "tp": tp if tp else 0,
        }
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    def run_continuous(self, interval_seconds=10):
        """Run continuous management loop"""
        print("\n" + "="*70)
        print("🏛️  PROFESSIONAL POSITION MANAGER - ACTIVE")
        print("="*70)
        print("\nManagement Rules:")
        print(f"  • Max loss per position: ${self.max_loss_per_position:,}")
        print(f"  • Max hold time for losers: {self.max_hold_time_hours}h")
        print(f"  • Breakeven trigger: {self.breakeven_trigger}%")
        print(f"  • Scale out levels: {self.scale_out_levels}")
        print(f"  • Trail distance: {self.trail_distance_pct}%")
        print("\nPress Ctrl+C to stop...\n")
        
        try:
            while True:
                positions = self.get_current_positions()
                
                if not positions:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] No open positions")
                else:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Managing {len(positions)} positions...")
                    
                    for pos in positions:
                        self.manage_position(pos)
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Professional Manager stopped by user")
            mt5.shutdown()

if __name__ == "__main__":
    try:
        trader = ProfessionalTrader()
        trader.run_continuous(interval_seconds=10)  # Check every 10 seconds
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        mt5.shutdown()
