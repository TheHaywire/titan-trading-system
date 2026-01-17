"""
Institutional Trade Manager (Section 11/12)
Handles automated trade lifecycle events:
- Partial Profit Scale-out (50% at 1:1 RR)
- Automated Break-Even Protection
- Trailing Stop-Loss Management
"""

import logging
import numpy as np
import MetaTrader5 as mt5
from titan_system.analytics.indicators import IndicatorFactory

logger = logging.getLogger("Titan.Manager")

class TradeManager:
    def __init__(self, execution_client):
        self.execution = execution_client
        self._commentary = []

    def manage_active_trades(self, market_scans=None):
        """Main entry point called by the engine heartbeat."""
        self._commentary = [] # Clear for this cycle
        if not self.execution.connected:
            return []

        positions = mt5.positions_get()
        if not positions:
            return

        # Prepare market context map for fast lookup
        context_map = {}
        if market_scans:
            context_map = {scan['symbol']: scan for scan in market_scans if scan}

        for pos in positions:
            # Get current context for this symbol if available
            symbol_context = context_map.get(pos.symbol)
            self._process_position(pos, symbol_context)
            
        return self._commentary

    def _process_position(self, pos, context=None):
        """Evaluates a single position for lifecycle updates and alignment."""
        try:
            # 2. Skip positions not managed by Titan (based on magic number)
            # Both core (234000) and multi-symbol (234001) are tracked
            if pos.magic not in [234000, 234001]:
                return

            # A. Adaptive Invalidation Check (Unalignment)
            # If we have market context, check if the trade still makes sense
            if context:
                if self._eval_contextual_alignment(pos, context):
                    return # Position was closed due to invalidation

            # 3. Calculate Risk:Reward Metrics
            entry = pos.price_open
            current = pos.price_current
            sl = pos.sl
            
            # State Management: Is it already at Break-Even?
            tick_size = mt5.symbol_info(pos.symbol).trade_tick_size
            is_be = abs(sl - entry) <= (10 * tick_size) if sl > 0 else False
            
            # 1:1 RR Trigger Logic (if not at BE)
            if not is_be and sl > 0:
                risk_dist = abs(entry - sl)
                profit_dist = (current - entry) if pos.type == mt5.POSITION_TYPE_BUY else (entry - current)
                
                if profit_dist >= risk_dist:
                    self._trigger_lifecycle_alpha(pos)
                    return

            # Trailing Stop (if at BE or as requested)
            if is_be:
                self._handle_trailing_stop(pos)

        except Exception as e:
            logger.error(f"Error managing position {pos.ticket}: {e}")

    def _eval_contextual_alignment(self, pos, context):
        """
        Adaptive Exit Logic: Proactively closes trades that lose alignment.
        Returns True if position was closed.
        """
        bias = context.get('bias', 'NEUTRAL')
        regime = context.get('regime', {}).get('current', 'UNKNOWN')
        symbol = pos.symbol
        
        # 1. Bias Flip (The "Zombie Trade" Killer)
        # If in a BUY but bias is now BEARISH
        should_exit = False
        reason = ""
        
        if pos.type == mt5.POSITION_TYPE_BUY and bias == 'BEARISH':
            should_exit = True
            reason = "Bias Flip (BULL -> BEAR)"
        elif pos.type == mt5.POSITION_TYPE_SELL and bias == 'BULLISH':
            should_exit = True
            reason = "Bias Flip (BEAR -> BULL)"
            
        # 2. Regime Shift Analysis
        # If in a Trend trade but regime is now LOW_VOLATILITY or SQUEEZE
        if regime in ['LOW_VOLATILITY', 'RANGE']:
            # For Trend trades, range periods are dangerous "zombie" zones
            if pos.profit < 0: # Only exit losers in chop, give winners a chance to trail
                should_exit = True
                reason = f"Regime Shift to {regime} (Edge Evaporated)"

        if should_exit:
            logger.warning(f"🚨 [ADAPTIVE EXIT] {symbol} {pos.ticket}: {reason}")
            self._commentary.append(f"PROTECTION: Closing {symbol} loser early. {reason}")
            
            # Record Decision in Ledger
            try:
                from titan_system.db.database import Database
                db = Database(self.execution.config.db_path)
                db.record_decision(
                    symbol=symbol,
                    decision="ADAPTIVE_EXIT",
                    reason=reason,
                    score=0.0,
                    metadata={"ticket": pos.ticket, "profit": pos.profit, "type": pos.type}
                )
            except Exception as e:
                logger.error(f"Failed to record adaptive exit decision: {e}")

            success = self.execution.close_position(pos.ticket, comment=f"Titan-AdaptiveExit")
            if success:
                logger.info(f"✅ Closed {symbol} ({pos.ticket}) proactively to prevent 'Zombie Trade'.")
                return True
        
        return False

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
                self._commentary.append(f"PROFIT: Scaled out 50% on {pos.symbol} at 1:1 RR.")
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
            self._commentary.append(f"SAFETY: Moved {pos.symbol} to Break-Even. Risk is now Zero.")
            # Note: We can't update the comment via modify_position in MT5 easily without a new order,
            # but my modify_position uses TRADE_ACTION_SLTP which doesn't support comments.
            # To track state, we'll rely on the logic that sl == be_price in the next loop.
        else:
            logger.error(f"❌ Failed to move {pos.ticket} to Break-Even.")

    def _handle_trailing_stop(self, pos):
        """
        Implements ATR-based dynamic trailing stops.
        Active only after position is at Break-Even.
        """
        symbol = pos.symbol
        # 1. Fetch recent data to calculate current ATR
        df = self.execution.get_data(symbol, mt5.TIMEFRAME_H1, 50)
        if df is None: return
        
        df = IndicatorFactory.calculate_all(df)
        atr = df['atr'].iloc[-1]
        
        if np.isnan(atr): return

        # 2. Calculate New Trailing Stop
        current_price = pos.price_current
        trail_dist = atr * 2.0 # 2x ATR Trailing Stop
        
        if pos.type == mt5.POSITION_TYPE_BUY:
            new_sl = current_price - trail_dist
            # Only move SL UP
            if new_sl > pos.sl + (mt5.symbol_info(symbol).point * 10):
                self.execution.modify_position(pos.ticket, sl=new_sl)
                logger.info(f"📈 Trailing Buy SL Up: {symbol} -> {new_sl:.5f}")
        else:
            new_sl = current_price + trail_dist
            # Only move SL DOWN
            if new_sl < pos.sl - (mt5.symbol_info(symbol).point * 10) or pos.sl == 0:
                # Note: BE check handled in _process_position so pos.sl shouldn't be 0
                self.execution.modify_position(pos.ticket, sl=new_sl)
                logger.info(f"📉 Trailing Sell SL Down: {symbol} -> {new_sl:.5f}")
