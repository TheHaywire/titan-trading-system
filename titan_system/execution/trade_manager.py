import MetaTrader5 as mt5
import logging
from datetime import datetime

logger = logging.getLogger("Titan.TradeManager")

class TradeManager:
    """
    Tiered Profit Protection & Exit Optimization.
    Tiers:
    - 0.5R: Move SL to 50% risk (De-risking)
    - 0.8R: Move SL to Entry + Buffer (Break-Even)
    - 1.2R+: Trail SL based on ATR
    """
    def __init__(self, managed_magics=None):
        # If None, manage all trades. Otherwise, filter by magic numbers.
        self.managed_magics = managed_magics or [234001, 777777, 888888, 999001, 123456]
        self.heartbreak_threshold = 100.0 # $ amount identifying a "reversing" trade

    def monitor_active_trades(self):
        """Polls MT5 for open positions and applies tiered de-risking."""
        positions = mt5.positions_get()
        if positions is None:
            return

        for pos in positions:
            # Filter by magic number if specified
            if self.managed_magics and pos.magic not in self.managed_magics:
                continue
            
            self.apply_tier_protection(pos)

    def apply_tier_protection(self, pos):
        """Calculates R-Multiple and applies the appropriate protection tier."""
        symbol = pos.symbol
        ticket = pos.ticket
        entry_price = pos.price_open
        current_price = pos.price_current
        sl = pos.sl
        tp = pos.tp
        magic = pos.magic
        
        info = mt5.symbol_info(symbol)
        if not info: return

        # 1. Determine direction and initial risk
        # MT5 types: 0 = BUY, 1 = SELL
        is_buy = pos.type == 0
        
        # If no SL, we can't calculate R-multiples for protection
        if sl == 0:
            # Fallback: Use ATR for synthetic risk if no SL is present
            return 

        initial_risk = abs(entry_price - sl)
        if initial_risk == 0: return

        # Calculate current profit in units (price delta)
        current_profit = (current_price - entry_price) if is_buy else (entry_price - current_price)
        r_multiple = current_profit / initial_risk

        # Calculate Buffer (Asset specific)
        # GOLD usually needs 50-100 points, Forex 10-20.
        buffer_points = 50 if "GOLD" in symbol or "XAU" in symbol else 15
        buffer = buffer_points * info.point

        # 2. Apply Tiers
        new_sl = sl
        
        # --- TIER 3: Trailing at 1.2R+ ---
        if r_multiple >= 1.2:
            # Trail based on ATR or a fixed % of profit
            # Let's use a 30% profit lock-in trail
            trail_offset = current_profit * 0.3
            if is_buy:
                target_sl = current_price - trail_offset
                if target_sl > sl: new_sl = target_sl
            else:
                target_sl = current_price + trail_offset
                if target_sl < sl or sl == 0: new_sl = target_sl
                
            logger.info(f"[TIER 3] Trailing Active for {symbol} (#{ticket}) @ {r_multiple:.2f}R")

        # --- TIER 2: Full Break-Even at 0.8R ---
        elif r_multiple >= 0.8:
            if is_buy:
                target_sl = entry_price + buffer
                if target_sl > sl: new_sl = target_sl
            else:
                target_sl = entry_price - buffer
                if target_sl < sl or sl == 0: new_sl = target_sl
            
            # Also handle partial TP if logic requires (e.g. for Magic 234001)
            if magic == 234001 and pos.volume > 0.01:
                self.take_partial_profit(pos, 0.5)
                
            logger.info(f"[TIER 2] Break-Even for {symbol} (#{ticket}) @ {r_multiple:.2f}R")

        # --- TIER 1: Partial De-Risk at 0.5R ---
        elif r_multiple >= 0.5:
            # Move SL to 50% of original risk
            if is_buy:
                target_sl = entry_price - (initial_risk * 0.5)
                if target_sl > sl: new_sl = target_sl
            else:
                target_sl = entry_price + (initial_risk * 0.5)
                if target_sl < sl or sl == 0: new_sl = target_sl
            
            logger.info(f"[TIER 1] Risk Reduced for {symbol} (#{ticket}) @ {r_multiple:.2f}R")

        # 3. Modify Order if SL changed
        if new_sl != sl:
            self.modify_sl(ticket, symbol, new_sl, tp)

    def modify_sl(self, ticket, symbol, new_sl, tp):
        """Sends SL modification to MT5."""
        info = mt5.symbol_info(symbol)
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": symbol,
            "sl": round(new_sl, info.digits),
            "tp": round(tp, info.digits) if tp > 0 else 0
        }
        res = mt5.order_send(request)
        if res.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to modify SL for #{ticket}: {res.comment}")
            return False
        return True

    def take_partial_profit(self, pos, ratio):
        """Closes a portion of the position."""
        close_volume = round(pos.volume * ratio, 2)
        if close_volume < 0.01: return
        
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == 0 else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": close_volume,
            "type": 1 if pos.type == 0 else 0, # Reverse type
            "position": pos.ticket,
            "price": price,
            "deviation": 20,
            "magic": pos.magic,
            "comment": "Tiered Partial TP",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        mt5.order_send(request)
        logger.info(f"[PARTIAL TP] Closed {close_volume} lots on {pos.symbol} (#{pos.ticket})")
