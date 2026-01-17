"""
Execution Engine & Live Loop
Monitors top strategies and executes trades with liquidity and risk checks.
"""

import time
import logging
import MetaTrader5 as mt5
import pandas as pd
from typing import List, Dict, Any
import strategy_mining.mining_config as config
from strategy_mining.data_engine import DataEngine
from strategy_mining.risk_manager import RiskManager
from strategy_mining.strategies import AlphaArchetypes

# Setup logging
logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, top_winners: pd.DataFrame):
        self.winners = top_winners
        self.data_engine = DataEngine()
        self.risk_manager = RiskManager()
        self.is_running = False

    def start_live_loop(self):
        """Enter 24/7 execution loop."""
        self.is_running = True
        logger.info(f"Starting Execution Loop for top {len(self.winners)} strategies...")
        
        while self.is_running:
            try:
                # 1. Heartbeat check (redundant but safe)
                if not mt5.initialize():
                    logger.error("Heartbeat: MT5 connection lost in main loop")
                
                # 2. Daily Drawdown / Risk Check
                account_info = mt5.account_info()
                if account_info is None:
                    continue
                
                equity = account_info.equity
                current_dd = self.risk_manager.calculate_daily_drawdown(equity)
                
                # 1. Circuit Breaker (3%)
                if current_dd >= config.DD_CIRCUIT_BREAKER:
                    logger.critical("Circuit Breaker: Closing all positions and pausing.")
                    self.close_all_positions()
                    time.sleep(60)
                    continue
                
                # 2. Emergency Hedging (2.5%)
                if current_dd >= config.DD_THRESHOLD_3: # Threshold 3 is 2.5%
                    logger.warning("High Drawdown: Investigating hedge opportunities.")
                    positions = mt5.positions_get(magic=config.MT5_MAGIC_NUMBER)
                    if positions:
                        for pos in positions:
                            # Only hedge if not already hedged (simplified check)
                            if "HEDGE" not in pos.comment:
                                self.risk_manager.emergency_hedge(pos.symbol, pos.volume, pos.type)
                
                if not self.risk_manager.is_trading_allowed():
                    time.sleep(10)
                    continue

                # 3. Monitor Strategy Signals
                for _, winner in self.winners.iterrows():
                    self.check_signal_and_execute(winner, equity)
                    
                # 4. Manage Open Positions (Trailing Stops, Partial Profit)
                self.manage_active_trades()
                
                time.sleep(config.SIGNAL_CHECK_INTERVAL_SEC)
                
            except Exception as e:
                logger.error(f"Error in live loop: {e}")
                time.sleep(5)

    def check_signal_and_execute(self, strategy_row: pd.Series, equity: float):
        """Check for a new signal and execute if valid."""
        symbol = strategy_row['symbol']
        tf_str = strategy_row['timeframe']
        strat_name = strategy_row['strategy']
        params = strategy_row['params']
        
        # Fetch recent data
        df = self.data_engine.fetch_bars(symbol, tf_str, n_bars=100)
        if df is None or df.empty:
            return
            
        # Generate signal for last candle
        signals = self.generate_signal(df, strat_name, params)
        last_signal = signals.iloc[-1]
        
        if last_signal == 0:
            return
            
        # Check if we already have a position for this strategy
        if self.has_existing_position(symbol, strat_name):
            return
            
        # Check Liquidity
        if not self.check_liquidity(symbol):
            logger.warning(f"Insufficient liquidity for {symbol}, skipping.")
            return

        # Calculate Position Size (Dynamic)
        # For simplicity, we use ATR for SL
        sl_pips = self.calculate_atr_sl(df)
        lots = self.risk_manager.get_dynamic_position_size(symbol, strat_name, equity, sl_pips)
        
        # Execute Order
        self.send_order(symbol, last_signal, lots, sl_pips)

    def generate_signal(self, df: pd.DataFrame, name: str, params: str):
        """Helper to generate live signals."""
        if name == 'MeanReversion':
            p = {k: float(v) for k, v in [item.split('=') for item in params.split(',')]}
            return AlphaArchetypes.mean_reversion_zscore_vwap(df, int(p['window']), p['z'])
        elif name == 'TrendFollowing':
            p = {k: int(v) for k, v in [item.split('=') for item in params.split(',')]}
            return AlphaArchetypes.trend_following_ema_cross(df, p['fast'], p['slow'])
        elif name == 'VolatilityExpansion':
            p = {k: float(v) for k, v in [item.split('=') for item in params.split(',')]}
            return AlphaArchetypes.volatility_expansion_keltner(df, int(p['ema']), 14, p['mult'])
        return pd.Series(0, index=df.index)

    def check_liquidity(self, symbol: str) -> bool:
        """Use mt5.market_book_get to check spread and depth."""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False
            
        # 1. Check current spread
        tick = mt5.symbol_info_tick(symbol)
        current_spread = tick.ask - tick.bid
        avg_spread = symbol_info.spread * symbol_info.point
        
        if current_spread > (avg_spread * config.MAX_SPREAD_MULTIPLIER):
            logger.warning(f"Spread too high for {symbol}: {current_spread} (Avg: {avg_spread})")
            return False
            
        # 2. Check Book Depth
        book = mt5.market_book_get(symbol)
        if book:
            total_bid_vol = sum(level.volume for level in book if level.type == mt5.BOOK_TYPE_BUY)
            total_ask_vol = sum(level.volume for level in book if level.type == mt5.BOOK_TYPE_SELL)
            
            if total_bid_vol < config.MIN_BOOK_DEPTH_LOTS or total_ask_vol < config.MIN_BOOK_DEPTH_LOTS:
                logger.warning(f"Insufficient depth for {symbol}: Bid={total_bid_vol}, Ask={total_ask_vol}")
                return False
                
        return True 

    def close_all_positions(self):
        """Emergency Close All system positions."""
        positions = mt5.positions_get(magic=config.MT5_MAGIC_NUMBER)
        if positions:
            for pos in positions:
                self.close_position(pos)
            logger.info(f"Emergency: Closed {len(positions)} system positions.")

    def close_position(self, position):
        """Close a specific position."""
        tick = mt5.symbol_info_tick(position.symbol)
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": config.MT5_MAGIC_NUMBER,
            "comment": "Mining Engine Exit",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Close failed for {position.ticket}: {result.comment}")

    def manage_active_trades(self):
        """Apply trailing stops and partial profits to all open system positions."""
        positions = mt5.positions_get(magic=config.MT5_MAGIC_NUMBER)
        if not positions:
            return
            
        for pos in positions:
            # Get ATR for trailing stop
            df = self.data_engine.fetch_bars(pos.symbol, "H1", n_bars=30)
            if df is not None:
                atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
                r_pnl = self.risk_manager.calculate_r_pnl(pos)
                
                # 1. Trailing Stop
                self.risk_manager.manage_trailing_stops(pos, atr)
                
                # 2. Partial Profits
                self.handle_partial_profits(pos, r_pnl)

    def handle_partial_profits(self, pos, r_pnl: float):
        """Execute partial closures based on R-multiples."""
        # Check if we've already taken partial profits using the comment field
        current_comment = pos.comment
        
        # 1. Take 50% at +2R
        if r_pnl >= config.PARTIAL_CLOSE_1_R and "partial_1" not in current_comment:
            close_vol = round(pos.volume * config.PARTIAL_CLOSE_1_PCT, 2)
            if close_vol >= mt5.symbol_info(pos.symbol).volume_min:
                logger.info(f"Taking 50% partial profit at +2R for {pos.symbol} (Ticket: {pos.ticket})")
                self.partial_close(pos, close_vol, "partial_1")
                return # Avoid multiple partials in same tick
        
        # 2. Take additional 25% at +4R (leaving 25% as runner)
        if r_pnl >= config.PARTIAL_CLOSE_2_R and "partial_2" not in current_comment:
            if "partial_1" in current_comment:
                # We already closed 50%, so remaining is 50%. Closing 25% of original (which is 50% of current)
                close_vol = round(pos.volume * 0.5, 2)
                if close_vol >= mt5.symbol_info(pos.symbol).volume_min:
                    logger.info(f"Taking final partial profit at +4R for {pos.symbol} (Ticket: {pos.ticket})")
                    self.partial_close(pos, close_vol, "partial_2")

    def partial_close(self, pos, volume: float, comment: str):
        """Close part of a position."""
        tick = mt5.symbol_info_tick(pos.symbol)
        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 20,
            "magic": config.MT5_MAGIC_NUMBER,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Partial close successful for {pos.ticket}: {volume} lots")
