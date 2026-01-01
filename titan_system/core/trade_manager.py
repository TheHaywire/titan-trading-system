import logging
import pandas as pd
from titan_system.core.execution import MT5Execution
from titan_system.strategies.book_strategies import BookTechnicalStrategy

logger = logging.getLogger("Titan.TradeManager")

class TradeManager:
    """
    Manages the lifecycle of open positions, specifically implementing 
    validated exit strategies like the SMA Trailing Stop.
    """
    def __init__(self, execution: MT5Execution):
        self.execution = execution
        
        # Initialize strategy instances for indicator calculation
        self.strategies = {
            "FAT_TAILS": BookTechnicalStrategy(trailing_stop_mode='SMA50')
        }
        
    def manage_positions(self, assignments: dict):
        """
        Main loop to check and update all open positions.
        
        Args:
            assignments (dict): Map of symbol -> strategy_name (e.g., {"GOLD": "FAT_TAILS"})
        """
        if not self.execution.connected:
            return

        positions = self.execution.get_positions()
        if not positions:
            return

        for pos in positions:
            symbol = pos['symbol']
            
            # 1. Identify which strategy owns this trade
            # Note: In a robust system, we might store this in the specific trade comment or magic number.
            # For now, we fallback to the global assignment map.
            strategy_name = assignments.get(symbol)
            
            if not strategy_name:
                continue
                
            # 2. Apply Exit Logic
            if strategy_name == "FAT_TAILS":
                self._apply_sma_trailing_stop(pos)
                
    def _apply_sma_trailing_stop(self, pos):
        """
        Implements the 'Fat Tail' Home Run Logic:
        - If LONG: SL = SMA 50
        - If SHORT: SL = SMA 50
        - CRITICAL: SL never moves backwards (ratchet mechanism)
        """
        symbol = pos['symbol']
        ticket = pos['ticket']
        current_sl = pos['sl']
        direction = "BUY" if pos['type'] == 0 else "SELL" # 0=Buy, 1=Sell in MT5
        
        # Fetch sufficient data for SMA 50 calculation
        # We need at least 50 candles. Safe buffer: 100.
        df = self.execution.get_data(symbol, 16385, 100) # 16385 = H1 timeframe constant in MT5? No.
        # Let's fix timeframe constant. MT5.TIMEFRAME_H1 = 16385. 
        # Using string 'H1' requires mapping in execution or here.
        # execution.get_data takes integer usually if direct mt5 wrapper, 
        # BUT execution.py wrapper accepts what? "get_data(self, symbol, timeframe, n_candles)"
        # Let's import MT5 alias
        import MetaTrader5 as mt5
        
        df = self.execution.get_data(symbol, mt5.TIMEFRAME_H1, 200)
        
        if df is None or len(df) < 50:
            logger.warning(f"Insufficient data for trailing stop on {symbol}")
            return
            
        # Calculate SMA 50 using the authentic strategy logic
        strategy = self.strategies["FAT_TAILS"]
        df = strategy.calculate_indicators(df)
        
        current_sma = df['SMA_50'].iloc[-1]
        
        # Ratchet Logic
        new_sl = current_sl
        should_update = False
        
        margin_pips = 10 # Buffer to prevent noise stop out
        point = mt5.symbol_info(symbol).point
        
        if direction == "BUY":
            # For BUY, SL should effectively be the SMA value (minus small buffer optional)
            # Logic: SL can ONLY move UP.
            # Only trail if SMA is ABOVE current SL
            # And obviously below current price (market condition) - implied by profitable trade or deep stop
            
            # Simple check: Is SMA > Open Price? (Protection) OR Break Even?
            # The logic from 'compare_exits.py' was strictly Price < SMA = Exit.
            # So SL should be exactly at SMA.
            
            candidate_sl = current_sma - (margin_pips * point)
            
            if candidate_sl > current_sl:
                # Ensure we don't set SL above current price (instant stop out)
                current_price = mt5.symbol_info_tick(symbol).bid
                if candidate_sl < current_price:
                    new_sl = candidate_sl
                    should_update = True
                    
        elif direction == "SELL":
            # For SELL, SL can ONLY move DOWN.
            candidate_sl = current_sma + (margin_pips * point)
            
            # If current_sl is 0 (no stop), any trail is an improvement, but here we assume initial SL
            if current_sl == 0 or candidate_sl < current_sl:
                current_price = mt5.symbol_info_tick(symbol).ask
                if candidate_sl > current_price:
                    new_sl = candidate_sl
                    should_update = True
        
        if should_update:
            # Significant change check (don't spam server for 0.1 pip)
            diff_pips = abs(new_sl - current_sl) / point
            if diff_pips > 5: # Min step 5 pips
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": ticket,
                    "sl": float(new_sl),
                    "tp": float(pos['tp']), # Keep existing TP (likely 0 or moonshot)
                    "magic": pos['magic']
                }
                
                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"✨ TRAILING STOP UPDATED: {symbol} | New SL: {new_sl:.2f} (SMA50)")
                else:
                    logger.error(f"Failed to update SL for {symbol}: {result.comment}")
