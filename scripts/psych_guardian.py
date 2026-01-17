# PSYCHOLOGICAL CIRCUIT BREAKER SYSTEM
# Protects you from yourself on "fucked up days"

import MetaTrader5 as mt5
from datetime import datetime
import json
import os

class PsychologicalGuardian:
    """
    This system prevents you from self-destructing.
    Run this BEFORE you start trading each day.
    """
    
    def __init__(self):
        self.config_file = "data/psych_limits.json"
        self.load_limits()
        
    def load_limits(self):
        """Load your daily limits"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.limits = json.load(f)
        else:
            # Default limits - ADJUST THESE
            self.limits = {
                'max_daily_loss': 50000,  # Max $50k loss per day
                'max_single_position_loss': 20000,  # Max $20k loss per position
                'max_trades_per_day': 20,  # Max 20 trades
                'max_add_to_loser': 1,  # Can only add to losing position ONCE
                'forced_break_after_3_losses': True,  # Must stop after 3 losses in a row
            }
            self.save_limits()
    
    def save_limits(self):
        """Save limits to file"""
        os.makedirs('data', exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.limits, f, indent=2)
    
    def check_and_enforce(self):
        """Check all limits and FORCE close if violated"""
        
        if not mt5.initialize():
            return
        
        print("=" * 80)
        print("🛡️  PSYCHOLOGICAL GUARDIAN - CHECKING LIMITS")
        print("=" * 80)
        
        account = mt5.account_info()
        positions = mt5.positions_get()
        
        # Get today's history
        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        deals = mt5.history_deals_get(today_start, datetime.now())
        
        violations = []
        
        # CHECK 1: Daily Loss Limit
        total_profit_today = sum([d.profit for d in deals]) if deals else 0
        if total_profit_today < -self.limits['max_daily_loss']:
            violations.append(f"DAILY LOSS LIMIT BREACHED: ${total_profit_today:,.0f}")
            self.force_close_all("DAILY_LOSS_LIMIT")
        
        # CHECK 2: Single Position Loss
        if positions:
            for pos in positions:
                if pos.profit < -self.limits['max_single_position_loss']:
                    violations.append(f"POSITION LOSS LIMIT: {pos.symbol} ${pos.profit:,.0f}")
                    self.force_close_position(pos, "POSITION_LOSS_LIMIT")
        
        # CHECK 3: Trade Count
        trades_today = len([d for d in deals if d.entry == 0]) if deals else 0
        if trades_today >= self.limits['max_trades_per_day']:
            violations.append(f"TRADE COUNT LIMIT: {trades_today} trades today")
            print(f"\n⛔ YOU'VE HIT YOUR DAILY LIMIT ({trades_today} trades)")
            print("    STOP TRADING. GO FOR A WALK.")
        
        # CHECK 4: Consecutive Losses
        if deals and len(deals) >= 3:
            last_3 = deals[-3:]
            if all(d.profit < 0 for d in last_3):
                violations.append("3 LOSSES IN A ROW")
                print(f"\n⛔ 3 CONSECUTIVE LOSSES DETECTED")
                print("    YOU'RE TILTING. MANDATORY BREAK.")
                self.force_close_all("CONSECUTIVE_LOSSES")
        
        # REPORT
        if violations:
            print(f"\n🚨 VIOLATIONS DETECTED:")
            for v in violations:
                print(f"   • {v}")
            print(f"\n💊 PROTECTIVE ACTIONS TAKEN")
        else:
            print(f"\n✅ All limits OK")
            print(f"   Daily P&L: ${total_profit_today:,.0f}")
            print(f"   Trades Today: {trades_today}/{self.limits['max_trades_per_day']}")
            if positions:
                print(f"   Open Positions: {len(positions)}")
                for pos in positions:
                    print(f"      {pos.symbol}: ${pos.profit:,.0f}")
        
        print("=" * 80)
        
        mt5.shutdown()
        
    def force_close_position(self, pos, reason):
        """Force close a single position"""
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "comment": f"GUARDIAN_{reason}",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   🛡️  FORCE CLOSED: {pos.symbol} (Loss: ${pos.profit:,.0f})")
    
    def force_close_all(self, reason):
        """Force close ALL positions"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        print(f"\n🚨 FORCE CLOSING ALL POSITIONS: {reason}")
        for pos in positions:
            self.force_close_position(pos, reason)
        print(f"   All positions closed. STOP TRADING TODAY.")

if __name__ == "__main__":
    guardian = PsychologicalGuardian()
    
    print("\n" + "="*80)
    print("🛡️  PSYCHOLOGICAL GUARDIAN ACTIVATED")
    print("="*80)
    print("\nThis system will:")
    print("  1. Monitor your daily loss limit")
    print("  2. Close positions hitting loss limits")
    print("  3. Detect revenge trading (3 losses in a row)")
    print("  4. Enforce rest breaks")
    print("\nRun this EVERY 5 MINUTES while trading.\n")
    
    guardian.check_and_enforce()
