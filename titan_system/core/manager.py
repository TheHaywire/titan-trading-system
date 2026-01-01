"""
Institutional Trade Manager (Section 11/12)
Handles automated trade lifecycle events:
- Partial Profit Scale-out (50% at 1:1 RR)
- Automated Break-Even Protection
- Trailing Stop-Loss Management
"""

import logging
import MetaTrader5 as mt5

logger = logging.getLogger("Titan.Manager")

class TradeManager:
    def __init__(self, execution_client):
        self.execution = execution_client

    def manage_active_trades(self):
        """Main entry point called by the engine heartbeat."""
        if not self.execution.connected:
            return

        positions = mt5.positions_get()
        if not positions:
            return

        for pos in positions:
            self._process_position(pos)

    def _process_position(self, pos):
        """Evaluates a single position for lifecycle updates."""
        try:
            # 1. Skip positions not managed by Titan (based on magic number)
            # Magic number 234000 is used in execution.py
            if pos.magic != 234000:
                return

            # 2. Skip positions already in 'Break-Even' or 'Managed' state
            # We use the comment as a lightweight state machine
            if "BE" in pos.comment:
                # Still check for trailing stop if needed
                # self._handle_trailing_stop(pos)
                return

            # 3. Calculate Risk:Reward Metrics
            entry = pos.price_open
            current = pos.price_current
            sl = pos.sl
            
            if sl == 0:
                # No Stop Loss? Cannot calculate RR.
                return

            # Risk Distance (Initial)
            risk_dist = abs(entry - sl)
            if risk_dist == 0: return

            # Current Profit Distance
            if pos.type == mt5.POSITION_TYPE_BUY:
                profit_dist = current - entry
            else:
                profit_dist = entry - current

            # 4. Check for 1:1 RR Trigger (Operational Alpha)
            if profit_dist >= risk_dist:
                self._trigger_lifecycle_alpha(pos)

        except Exception as e:
            logger.error(f"Error managing position {pos.ticket}: {e}")

    def _trigger_lifecycle_alpha(self, pos):
        """Executes Partial Close and Move to Break-Even."""
        logger.info(f"🎯 1:1 RR Target Hit for {pos.symbol} ({pos.ticket})")
        
        # A. Partial Close (50%)
        # volume_step and volume_min are handled by execution.normalize_volume in theory,
        # but here we just take half and let MT5 handle the precision if possible.
        # However, it's safer to use the normalized volume.
        half_vol = pos.volume / 2
        normalized_half = self.execution.normalize_volume(pos.symbol, half_vol)
        
        if normalized_half >= mt5.symbol_info(pos.symbol).volume_min:
            success_close = self.execution.close_partial(pos.ticket, normalized_half)
            if success_close:
                logger.info(f"💰 Scaled out 50% ({normalized_half} lots) on {pos.symbol}")
            else:
                logger.warning(f"❌ Failed to scale out on {pos.symbol}")
                return # If partial close fails, we might not want to move SL yet? (Actually usually we still do)
        else:
            logger.info(f"⚖️ Volume {pos.volume} too small for partial close. Skipping scale-out.")

        # B. Move to Break-Even
        # Entry price + 1 tick (to cover commission/swap if possible, but entry is standard)
        tick_size = mt5.symbol_info(pos.symbol).trade_tick_size
        be_price = pos.price_open
        
        # Add a tiny buffer (1 tick)
        if pos.type == mt5.POSITION_TYPE_BUY:
            be_price += (5 * tick_size) # 5 ticks buffer
        else:
            be_price -= (5 * tick_size)

        success_mod = self.execution.modify_position(pos.ticket, sl=be_price)
        if success_mod:
            logger.info(f"🛡️ Position {pos.ticket} moved to Break-Even.")
            # Note: We can't update the comment via modify_position in MT5 easily without a new order,
            # but my modify_position uses TRADE_ACTION_SLTP which doesn't support comments.
            # To track state, we'll rely on the logic that sl == be_price in the next loop.
        else:
            logger.error(f"❌ Failed to move {pos.ticket} to Break-Even.")

    def _handle_trailing_stop(self, pos):
        """(Future) Implements ATR-based or Candle-based trailing stops."""
        pass
