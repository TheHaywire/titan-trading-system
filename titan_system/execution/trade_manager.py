import MetaTrader5 as mt5
import logging
from datetime import datetime

logger = logging.getLogger("Titan.TradeManager")

class TradeManager:
    """
    Institutional Trade Lifecycle Management.
    Automates Break-Even (BE) and Partial Take-Profit (Partial TP).
    """
    def __init__(self, be_threshold_pips=10, partial_tp_percent=0.5):
        self.be_threshold_pips = be_threshold_pips
        self.partial_tp_percent = partial_tp_percent
        self.managed_tickets = set() # Track which tickets we've already de-risked

    def monitor_active_trades(self):
        """
        Polls MT5 for open positions and applies de-risking logic.
        """
        positions = mt5.positions_get()
        if positions is None:
            return

        for pos in positions:
            # We only manage trades with our magic number (institutional identifier)
            if pos.magic != 234001:
                continue
            
            # 1. State Check: Is this trade already 'Zero-Risked'?
            # For BUY: If SL is >= Entry, it's already managed.
            # For SELL: If SL is <= Entry, it's already managed.
            is_already_be = False
            if pos.type == mt5.POSITION_TYPE_BUY:
                if pos.sl >= pos.price_open: is_already_be = True
            else:
                if pos.sl != 0 and pos.sl <= pos.price_open: is_already_be = True # sl=0 means no SL

            if is_already_be:
                continue

            self.check_de_risk(pos)

    def check_de_risk(self, pos):
        """
        Calculates if a trade is 'Safe' to move to Break-Even.
        """
        symbol = pos.symbol
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return

        point = symbol_info.point
        entry_price = pos.price_open
        current_price = pos.price_current
        order_type = pos.type # 0 for BUY, 1 for SELL
        
        # Calculate current profit in points
        if order_type == mt5.POSITION_TYPE_BUY:
            profit_points = (current_price - entry_price) / point
        else:
            profit_points = (entry_price - current_price) / point

        # Convert threshold (pips) to points (usually 1 pip = 10 points for 5-digit brokers)
        threshold_points = self.be_threshold_pips * 10 

        if profit_points >= threshold_points:
            logger.info(f"🏆 [DE-RISK] Threshold reached for {symbol} (#{pos.ticket}). Moving to BE.")
            success = self.apply_break_even_and_partial(pos)
            if success:
                self.managed_tickets.add(pos.ticket)

    def apply_break_even_and_partial(self, pos):
        """
        1. Moves SL to Entry (Break-Even)
        2. Closes 50% of the position (Bank Profits)
        """
        symbol = pos.symbol
        ticket = pos.ticket
        entry_price = pos.price_open
        volume = pos.volume
        order_type = pos.type

        # 1. Move SL to Break-Even (Entry + small buffer)
        buffer = 20 * 0.00001 # 2 points buffer
        if order_type == mt5.POSITION_TYPE_BUY:
            sl_be = entry_price + buffer
        else:
            sl_be = entry_price - buffer

        request_sl = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": sl_be,
            "tp": pos.tp
        }
        
        sl_result = mt5.order_send(request_sl)
        if sl_result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to move SL to BE for #{ticket}: {sl_result.comment}")
            return False

        # 2. Partial Profit Taking (Close 50%)
        close_volume = round(volume * self.partial_tp_percent, 2)
        if close_volume < 0.01:
            return True # Volume too small to split

        tick = mt5.symbol_info_tick(symbol)
        price_close = tick.bid if order_type == mt5.POSITION_TYPE_BUY else tick.ask
        
        request_close = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": close_volume,
            "type": mt5.ORDER_TYPE_SELL if order_type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": price_close,
            "deviation": 20,
            "magic": 234001,
            "comment": "Institutional Partial TP",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        close_result = mt5.order_send(request_close)
        if close_result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Partial TP failed for #{ticket}: {close_result.comment}")
            # We already moved SL to BE, so we consider it partially managed
            return True 

        logger.info(f"🛡️ [RISK ZEROED] #{ticket} is now free. Booked profit on {close_volume} lots.")
        return True
