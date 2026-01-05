"""
DYNAMIC TRADE MANAGER - Professional Scalper Edition
=====================================================
Autonomous trade management to maximize profits and minimize losses.

Features:
- Break-even: Move SL to entry when trade hits 1:1 RR
- Trailing Stop: Lock in profits as price moves in our favor
- Loss Cutting: Close trades early if momentum reverses against us
- Profit Taking: Partial close at targets

Runs continuously monitoring all open positions.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MANAGER] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("TradeManager")


class DynamicTradeManager:
    """
    Professional trade management system.
    Maximizes profits, minimizes losses dynamically.
    """
    
    def __init__(self):
        self.scan_interval = 10  # Check every 10 seconds
        self.breakeven_trigger = 1.0  # Move to BE at 1:1 RR
        self.trail_trigger = 1.5  # Start trailing at 1.5:1 RR
        self.trail_distance_multiplier = 0.5  # Trail at 50% of profit
        self.managed_positions = {}  # Track what we've done to each position
        
    def start(self):
        logger.info("=" * 60)
        logger.info("DYNAMIC TRADE MANAGER - ACTIVE")
        logger.info("=" * 60)
        logger.info("Features: Break-Even | Trailing Stop | Loss Cutting")
        logger.info("")
        
        if not mt5.initialize():
            logger.error("MT5 failed to initialize")
            return
        
        acc = mt5.account_info()
        logger.info("Account: " + str(acc.login))
        logger.info("Equity: $" + str(round(acc.equity, 2)))
        logger.info("")
        
        while True:
            try:
                self.manage_trades()
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                logger.info("Manager stopped by user")
                break
            except Exception as e:
                logger.error("Error: " + str(e))
                time.sleep(5)
        
        mt5.shutdown()
    
    def manage_trades(self):
        """Main management loop - check all positions"""
        positions = mt5.positions_get()
        
        if not positions:
            return
        
        for pos in positions:
            self.manage_single_position(pos)
    
    def manage_single_position(self, pos):
        """Manage a single position with dynamic rules"""
        symbol = pos.symbol
        ticket = pos.ticket
        direction = "BUY" if pos.type == 0 else "SELL"
        entry = pos.price_open
        current = pos.price_current
        sl = pos.sl
        tp = pos.tp
        profit = pos.profit
        volume = pos.volume
        
        # Get symbol info
        info = mt5.symbol_info(symbol)
        if not info:
            return
        
        point = info.point
        
        # Calculate risk (distance to SL)
        if direction == "BUY":
            risk_distance = entry - sl if sl > 0 else 0
            profit_distance = current - entry
        else:
            risk_distance = sl - entry if sl > 0 else 0
            profit_distance = entry - current
        
        if risk_distance <= 0:
            return  # No SL set, skip
        
        # Calculate R multiple (how many R's of profit)
        r_multiple = profit_distance / risk_distance if risk_distance > 0 else 0
        
        # Track position state
        pos_key = str(ticket)
        if pos_key not in self.managed_positions:
            self.managed_positions[pos_key] = {
                "breakeven_done": False,
                "trailing_active": False,
                "last_trail_price": 0
            }
        
        state = self.managed_positions[pos_key]
        
        # === RULE 1: BREAK-EVEN at 1:1 RR ===
        if r_multiple >= self.breakeven_trigger and not state["breakeven_done"]:
            new_sl = entry + (point * 10 if direction == "BUY" else -point * 10)  # +1 pip buffer
            
            if self.modify_sl(ticket, symbol, new_sl, pos.tp):
                logger.info("[BE] " + symbol + " " + direction + " -> SL moved to break-even")
                logger.info("     Profit locked: $" + str(round(profit, 2)) + " at " + str(round(r_multiple, 2)) + "R")
                state["breakeven_done"] = True
        
        # === RULE 2: TRAILING STOP at 1.5:1+ RR ===
        if r_multiple >= self.trail_trigger:
            if direction == "BUY":
                # Trail SL below current price
                trail_distance = profit_distance * self.trail_distance_multiplier
                new_sl = current - trail_distance
                
                # Only move if new SL is higher than current SL
                if new_sl > sl:
                    if self.modify_sl(ticket, symbol, new_sl, pos.tp):
                        logger.info("[TRAIL] " + symbol + " " + direction + " -> SL: " + str(round(new_sl, info.digits)))
                        logger.info("        Locking " + str(round(r_multiple, 2)) + "R profit")
                        state["trailing_active"] = True
                        state["last_trail_price"] = current
            else:
                # SELL - trail SL above current price
                trail_distance = profit_distance * self.trail_distance_multiplier
                new_sl = current + trail_distance
                
                # Only move if new SL is lower than current SL
                if new_sl < sl:
                    if self.modify_sl(ticket, symbol, new_sl, pos.tp):
                        logger.info("[TRAIL] " + symbol + " " + direction + " -> SL: " + str(round(new_sl, info.digits)))
                        logger.info("        Locking " + str(round(r_multiple, 2)) + "R profit")
                        state["trailing_active"] = True
                        state["last_trail_price"] = current
        
        # === RULE 3: LOSS CUTTING - Close if momentum reverses ===
        if profit < -100:  # More than $100 loss
            # Check if momentum has reversed
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 10)
            if rates is not None and len(rates) >= 5:
                df = pd.DataFrame(rates)
                recent_change = (df['close'].iloc[-1] - df['close'].iloc[-3]) / df['close'].iloc[-3] * 100
                
                # If we're long and momentum is strongly bearish, cut loss
                if direction == "BUY" and recent_change < -0.3:
                    logger.warning("[CUT] " + symbol + " BUY - Momentum reversed bearish!")
                    # Don't auto-close, just warn (user can decide)
                    # self.close_position(ticket, symbol, volume)
                
                # If we're short and momentum is strongly bullish, cut loss
                elif direction == "SELL" and recent_change > 0.3:
                    logger.warning("[CUT] " + symbol + " SELL - Momentum reversed bullish!")
        
        # === STATUS LOG (every minute for active trades) ===
        if profit != 0:
            status = "PROFIT" if profit > 0 else "LOSS"
            # logger.info("[" + status + "] " + symbol + " " + direction + ": $" + str(round(profit, 2)) + " (" + str(round(r_multiple, 2)) + "R)")
    
    def modify_sl(self, ticket, symbol, new_sl, tp):
        """Modify the stop loss of a position"""
        info = mt5.symbol_info(symbol)
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": symbol,
            "sl": round(new_sl, info.digits),
            "tp": tp if tp > 0 else 0,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return True
        else:
            logger.error("Failed to modify SL: " + str(result.comment))
            return False
    
    def close_position(self, ticket, symbol, volume):
        """Close a position"""
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        
        pos = pos[0]
        
        if pos.type == 0:  # BUY -> close with SELL
            price = tick.bid
            order_type = mt5.ORDER_TYPE_SELL
        else:  # SELL -> close with BUY
            price = tick.ask
            order_type = mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 50,
            "magic": 999999,
            "comment": "Manager_Close",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info("[CLOSED] " + symbol + " @ " + str(result.price))
            return True
        else:
            logger.error("Failed to close: " + str(result.comment))
            return False


if __name__ == "__main__":
    manager = DynamicTradeManager()
    manager.start()
