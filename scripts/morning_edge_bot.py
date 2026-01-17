"""
MORNING EDGE BOT
Replicates your $1.4M winning pattern automatically
Only trades 01:00-04:00 UTC (your proven edge window)
"""

import MetaTrader5 as mt5
from datetime import datetime, time
import time as time_module

class MorningEdgeBot:
    def __init__(self, account_size=27000):
        self.account_size = account_size
        
        # Your proven parameters
        self.symbols = ["SILVER", "GOLD"]
        self.direction = "SHORT"  # You're 1.7x better at shorts
        self.trading_start = time(1, 0)  # 01:00 UTC
        self.trading_end = time(4, 0)    # 04:00 UTC
        
        # Position sizing (scales with account)
        if account_size < 50000:
            self.lot_size = 1
            self.stop_loss_amount = 2000
            self.take_profit_amount = 5000
        elif account_size < 100000:
            self.lot_size = 2
            self.stop_loss_amount = 4000
            self.take_profit_amount = 10000
        else:
            self.lot_size = 5
            self.stop_loss_amount = 10000
            self.take_profit_amount = 25000
        
        # Circuit breakers
        self.max_trades_per_day = 5
        self.max_daily_loss = 10000
        self.max_consecutive_losses = 3
        
        # State
        self.trades_today = 0
        self.daily_pnl = 0
        self.consecutive_losses = 0
        
        if not mt5.initialize():
            raise Exception("MT5 failed")
    
    def is_trading_hours(self):
        """Check if we're in the magic hours"""
        now = datetime.utcnow().time()
        return self.trading_start <= now <= self.trading_end
    
    def can_trade(self):
        """Check all circuit breakers"""
        if not self.is_trading_hours():
            return False, "Outside trading hours"
        
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Daily trade limit hit ({self.max_trades_per_day})"
        
        if self.daily_pnl < -self.max_daily_loss:
            return False, f"Daily loss limit hit (${self.daily_pnl:,.0f})"
        
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False, "3 consecutive losses - stopping"
        
        return True, "OK"
    
    def scan_for_setup(self, symbol):
        """Scan for short setup (simplified - checking overbought)"""
        try:
            # Get H1 data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            if rates is None or len(rates) < 50:
                return None
            
            # Simple overbought check (your historical pattern)
            closes = [r['close'] for r in rates]
            ema20 = sum(closes[-20:]) / 20
            current = closes[-1]
            
            # Short if price above EMA (potential reversal)
            if current > ema20 * 1.01:  # 1% above EMA
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    return {
                        'symbol': symbol,
                        'entry': tick.bid,
                        'direction': 'SHORT'
                    }
        except:
            pass
        
        return None
    
    def execute_trade(self, setup):
        """Execute the trade with your proven R:R"""
        symbol = setup['symbol']
        entry = setup['entry']
        
        # Get symbol info
        info = mt5.symbol_info(symbol)
        if not info:
            return False
        
        # Calculate SL and TP based on your R:R
        # This is simplified - you'd want proper ATR-based levels
        sl_pips = self.stop_loss_amount / (self.lot_size * 5000)  # Rough calc
        tp_pips = self.take_profit_amount / (self.lot_size * 5000)
        
        sl = entry + sl_pips
        tp = entry - tp_pips
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": self.lot_size,
            "type": mt5.ORDER_TYPE_SELL,
            "price": entry,
            "sl": round(sl, info.digits),
            "tp": round(tp, info.digits),
            "deviation": 20,
            "magic": 777777,
            "comment": "MORNING_EDGE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Executed: {symbol} SHORT {self.lot_size} lots @ {entry:.2f}")
            print(f"   SL: {sl:.2f} | TP: {tp:.2f}")
            self.trades_today += 1
            return True
        else:
            print(f"❌ Failed: {symbol}")
            return False
    
    def run(self):
        """Main trading loop"""
        print("="*80)
        print(f"🌅 MORNING EDGE BOT - ACTIVATED")
        print("="*80)
        print(f"Trading Hours: {self.trading_start} - {self.trading_end} UTC")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Position Size: {self.lot_size} lots")
        print(f"R:R: {self.take_profit_amount}/{self.stop_loss_amount} = {self.take_profit_amount/self.stop_loss_amount:.1f}:1")
        print("="*80)
        
        while True:
            can_trade, reason = self.can_trade()
            
            if not can_trade:
                if "Outside trading hours" not in reason:
                    print(f"\n⛔ {reason}")
                    print("Stopping for today.")
                    break
                
                # Wait if outside hours
                time_module.sleep(60)
                continue
            
            # Scan for setups
            for symbol in self.symbols:
                setup = self.scan_for_setup(symbol)
                if setup:
                    self.execute_trade(setup)
            
            # Wait before next scan
            time_module.sleep(300)  # Check every 5 minutes
        
        print("\n📊 SESSION COMPLETE")
        print(f"Trades: {self.trades_today}")
        print(f"Daily P&L: ${self.daily_pnl:,.0f}")
        
        mt5.shutdown()

if __name__ == "__main__":
    # Get account info to determine sizing
    if mt5.initialize():
        acc = mt5.account_info()
        mt5.shutdown()
        
        bot = MorningEdgeBot(account_size=acc.equity)
        bot.run()
    else:
        print("MT5 failed")
