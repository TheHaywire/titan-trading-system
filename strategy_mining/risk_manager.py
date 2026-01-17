"""
Dynamic Adaptive Risk Management System
Implements sophisticated position sizing, drawdown throttling, and profit-extraction logic.
"""

import logging
from typing import List, Dict, Any, Optional
import MetaTrader5 as mt5
import strategy_mining.mining_config as config
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, magic_number: int = config.MT5_MAGIC_NUMBER):
        self.magic_number = magic_number
        self.pause_until = None
        self.daily_starting_equity = None
        self.last_equity_check = None

    def calculate_daily_drawdown(self, current_equity: float) -> float:
        """Calculate daily drawdown from the starting equity of the day."""
        now = datetime.now()
        
        # Reset daily starting equity at midnight
        if self.last_equity_check is None or now.date() > self.last_equity_check.date():
            self.daily_starting_equity = current_equity
            self.last_equity_check = now
            
        if self.daily_starting_equity <= 0:
            return 0.0
            
        drawdown = (self.daily_starting_equity - current_equity) / self.daily_starting_equity
        return max(0.0, drawdown)

    def get_risk_multiplier(self, current_dd: float) -> float:
        """Determine risk reduction multiplier based on current drawdown."""
        if current_dd >= config.DD_THRESHOLD_3:
            return config.DD_RISK_MULTIPLIER_3
        elif current_dd >= config.DD_THRESHOLD_2:
            return config.DD_RISK_MULTIPLIER_2
        elif current_dd >= config.DD_THRESHOLD_1:
            return config.DD_RISK_MULTIPLIER_1
        return 1.0

    def calculate_strategy_confidence(self, strategy_results: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence based on recent trade performance.
        Simplified version for this implementation.
        """
        if not strategy_results:
            return 1.0
            
        wins = sum(1 for r in strategy_results if r.get('profit', 0) > 0)
        win_rate = wins / len(strategy_results)
        
        # Basic confidence: scale win rate 0-1 to 0.5-2.5 range
        confidence = 0.5 + (win_rate * 2.0)
        return max(config.KELLY_FRACTION_MIN, min(config.KELLY_FRACTION_MAX, confidence))

    def get_dynamic_position_size(self, symbol: str, strategy: str, current_equity: float, 
                                 sl_pips: float, confidence_score: float = 1.0) -> float:
        """
        Calculate dynamic position size in lots based on:
        - Account Equity
        - SL Distance
        - Confidence Multiplier
        - Drawdown Throttle
        - Kelly Criterion (Simplified)
        """
        if sl_pips <= 0:
            return 0.01 # Minimum safety
            
        # 1. Base Risk (e.g. 1%)
        risk_pct = config.DEFAULT_RISK_PER_TRADE_PCT / 100.0
        
        # 2. Apply Confidence Multiplier (Adaptive Kelly)
        risk_pct *= confidence_score
        
        # 3. Apply Drawdown Throttle
        current_dd = self.calculate_daily_drawdown(current_equity)
        risk_pct *= self.get_risk_multiplier(current_dd)
        
        # 4. Cap Risk
        max_risk = config.MAX_RISK_PER_TRADE_PCT / 100.0
        min_risk = config.MIN_RISK_PER_TRADE_PCT / 100.0
        risk_pct = max(min_risk, min(max_risk, risk_pct))
        
        # 5. Calculate Lot Size
        # Formula: Lots = (Equity * Risk%) / (SL_Pips * Pip_Value)
        # Note: Pip Value calculation depends on symbol. MT5 has helper functions.
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0.01
            
        point = symbol_info.point
        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size
        
        if tick_size == 0 or sl_pips == 0:
            return 0.01
            
        # Amount to risk in currency
        risk_amount = current_equity * risk_pct
        
        # Lots = Risk / (SL_Points * (TickValue / TickSize))
        # sl_points = sl_pips * (0.0001 / point) for 4/5 digits
        
        lot_step = symbol_info.volume_step
        lots = risk_amount / (sl_pips * 10 * (tick_value / (tick_size / point))) # Very rough estimation
        
        # More accurate lot calculation using MT5 tool:
        # lots = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, symbol, 1.0, price) # This is for margin
        
        # Final safety rounding
        lots = round(lots / lot_step) * lot_step
        return max(symbol_info.volume_min, min(symbol_info.volume_max, lots))

    def check_circuit_breaker(self, current_equity: float) -> bool:
        """Check if 3% daily drawdown limit reached."""
        dd = self.calculate_daily_drawdown(current_equity)
        if dd >= config.DD_CIRCUIT_BREAKER:
            logger.critical(f"CIRCUIT BREAKER TRIGGERED: Daily Drawdown is {dd*100:.2f}%")
            self.pause_trading(config.PAUSE_DURATION_HOURS)
            return True
        return False

    def pause_trading(self, hours: int):
        """Set a lockout period."""
        self.pause_until = datetime.now() + timedelta(hours=hours)
        logger.warning(f"Trading paused until {self.pause_until}")

    def is_trading_allowed(self) -> bool:
        """Check if system is currently allowed to trade."""
        if self.pause_until and datetime.now() < self.pause_until:
            return False
        return True

    def calculate_r_pnl(self, position) -> float:
        """Calculate current P&L in R-multiples."""
        if position.sl == 0:
            return 0.0
            
        initial_sl = position.sl # Not technically initial, but current SL
        # We need a way to know the INITIAL RISK. 
        # For simplicity, we'll assume the comment contains the initial risk or we use current SL.
        # Alternatively, we can use the TP/SL ratio if set.
        
        entry_price = position.price_open
        current_price = position.price_current
        
        # Risk = Distance from Entry to SL
        risk_distance = abs(entry_price - position.sl)
        if risk_distance == 0:
            return 0.0
            
        profit_distance = current_price - entry_price if position.type == mt5.POSITION_TYPE_BUY else entry_price - current_price
        return profit_distance / risk_distance

    def get_trailing_sl(self, position, r_multiple: float, atr: float) -> Optional[float]:
        """Calculate new SL based on R-multiples and ATR."""
        entry_price = position.price_open
        current_price = position.price_current
        is_buy = position.type == mt5.POSITION_TYPE_BUY
        
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info is None:
            return None
            
        new_sl = None
        
        # 1. Breakeven at +1R
        if r_multiple >= config.BREAKEVEN_TRIGGER_R:
            # Entry price +/- 1 point to ensure break-even
            new_sl = entry_price + (symbol_info.point if is_buy else -symbol_info.point)
            
        # 2. ATR-based trail after +2R
        if r_multiple >= config.PARTIAL_CLOSE_1_R:
            trail_dist = config.TRAILING_STOP_ATR_MULTIPLIER * atr
            new_sl = current_price - trail_dist if is_buy else current_price + trail_dist
            
        return new_sl

    def manage_trailing_stops(self, position, atr: float):
        """Update SL in MT5 if trailing conditions met."""
        r_pnl = self.calculate_r_pnl(position)
        new_sl = self.get_trailing_sl(position, r_pnl, atr)
        
        if new_sl:
            # Only move SL in direction of profit
            is_buy = position.type == mt5.POSITION_TYPE_BUY
            if is_buy and new_sl > position.sl:
                self.modify_sl(position.ticket, new_sl)
            elif not is_buy and (new_sl < position.sl or position.sl == 0):
                self.modify_sl(position.ticket, new_sl)

    def modify_sl(self, ticket: int, sl: float):
        """Send SL modification request to MT5."""
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": sl,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"SL Modification failed for {ticket}: {result.comment}")
        else:
            logger.info(f"SL Modified for {ticket} to {sl}")

    def emergency_hedge(self, symbol: str, total_volume: float, direction: int):
        """
        If Drawdown > 2.5%, open an opposite position to freeze risk.
        direction: Original direction (mt5.POSITION_TYPE_BUY or mt5.POSITION_TYPE_SELL)
        """
        logger.warning(f"CRITICAL DD (>2.5%): Hedging {symbol} to freeze risk.")
        tick = mt5.symbol_info_tick(symbol)
        
        # Hedge direction is opposite of original
        hedge_type = mt5.ORDER_TYPE_SELL if direction == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if hedge_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": total_volume,
            "type": hedge_type,
            "price": price,
            "deviation": 20,
            "magic": config.MT5_MAGIC_NUMBER,
            "comment": "EMERGENCY HEDGE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Emergency Hedge failed for {symbol}: {result.comment}")
        else:
            logger.info(f"Emergency Hedge EXECUTED for {symbol}: {total_volume} lots")
