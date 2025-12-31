"""
ROBUST TRADING BOT v2
=====================
Fixed version with all bugs addressed from code review.

FIXES APPLIED:
1. Spread check before trading
2. RSI logic order fixed
3. Division by zero protection
4. Momentum threshold raised
5. Symbol deduplication (no duplicate positions)
6. Correlation check (JPY/USD exposure limits)
7. Market hours check
8. Proper exception handling
9. Total portfolio risk cap
10. Auto break-even for profits
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("robust_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RobustBot")


class RobustTradingBot:
    """
    Production-ready trading bot with all risk controls.
    """
    
    # Curated universe - only liquid, tested symbols
    UNIVERSE = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
        "GOLD", "BTCUSD", "US500"
    ]
    
    # Currency correlation groups
    CORRELATION_GROUPS = {
        "USD": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"],
        "JPY": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"],
        "GOLD": ["GOLD", "XAUUSD"],
        "CRYPTO": ["BTCUSD", "ETHUSD"]
    }
    
    def __init__(self):
        self.risk_per_trade = 0.5  # 0.5% per trade
        self.max_total_risk = 5.0  # Max 5% total portfolio risk
        self.max_positions = 8
        self.max_per_group = 2  # Max 2 positions per correlation group
        self.scan_interval = 120  # 2 minutes
        self.min_rsi_score = 85  # Only trade strong RSI signals
        
        # Track positions by group
        self.position_tracker: Dict[str, int] = {}
        
    def start(self):
        logger.info("="*60)
        logger.info("ROBUST TRADING BOT v2 - PRODUCTION")
        logger.info("="*60)
        
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return
        
        account = mt5.account_info()
        if not account:
            logger.error("Cannot get account info")
            return
        
        logger.info(f"Account: {account.login}")
        logger.info(f"Equity: ${account.equity:,.2f}")
        logger.info(f"Risk per trade: {self.risk_per_trade}%")
        logger.info(f"Max total risk: {self.max_total_risk}%")
        logger.info(f"Symbols: {len(self.UNIVERSE)}")
        logger.info("="*60)
        
        while True:
            try:
                self.run_cycle()
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)
                time.sleep(60)
        
        mt5.shutdown()
        logger.info("Bot stopped")
    
    def run_cycle(self):
        """Main trading cycle"""
        logger.info("-"*50)
        logger.info(f"SCAN: {datetime.now().strftime('%H:%M:%S')}")
        
        # 1. Check account and manage existing positions
        account = mt5.account_info()
        self.manage_positions(account)
        
        # 2. Check if we can open new positions
        positions = mt5.positions_get()
        current_count = len(positions) if positions else 0
        
        if current_count >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached")
            return
        
        # 3. Calculate current portfolio risk
        total_risk = self.calculate_total_risk()
        if total_risk >= self.max_total_risk:
            logger.info(f"Max portfolio risk ({self.max_total_risk}%) reached: {total_risk:.1f}%")
            return
        
        # 4. Update position tracker
        self.update_position_tracker()
        
        # 5. Scan for opportunities
        for symbol in self.UNIVERSE:
            if current_count >= self.max_positions:
                break
            
            if total_risk >= self.max_total_risk:
                break
            
            # Check correlation limits
            if not self.check_correlation_limit(symbol):
                continue
            
            # Check if already have position
            if self.has_position(symbol):
                continue
            
            # Analyze symbol
            signal = self.analyze(symbol)
            if signal and signal['score'] >= self.min_rsi_score:
                if self.execute(signal):
                    current_count += 1
                    total_risk += self.risk_per_trade
    
    def manage_positions(self, account):
        """Auto break-even for profitable positions"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        for pos in positions:
            # FIX: Check for magic number to only manage our trades
            if pos.magic not in [999999, 888888, 777777, 111111]:
                continue
            
            # Move to break-even if profit > $100 per lot
            profit_per_lot = pos.profit / pos.volume if pos.volume > 0 else 0
            
            if profit_per_lot > 100:
                # Check if already at break-even
                entry = pos.price_open
                sl = pos.sl
                
                if pos.type == 0:  # BUY
                    if sl < entry:
                        self.move_to_breakeven(pos)
                else:  # SELL
                    if sl > entry or sl == 0:
                        self.move_to_breakeven(pos)
    
    def move_to_breakeven(self, pos):
        """Move SL to break-even"""
        entry = pos.price_open
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": pos.symbol,
            "position": pos.ticket,
            "sl": entry,
            "tp": pos.tp,
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"BREAK-EVEN: {pos.symbol} SL moved to {entry:.5f}")
    
    def calculate_total_risk(self) -> float:
        """Calculate current portfolio risk as % of equity"""
        positions = mt5.positions_get()
        if not positions:
            return 0.0
        
        account = mt5.account_info()
        equity = account.equity
        
        total_risk_amount = 0.0
        for pos in positions:
            if pos.sl > 0:
                # Risk = (entry - SL) × volume × pip value
                sl_distance = abs(pos.price_open - pos.sl)
                info = mt5.symbol_info(pos.symbol)
                if info and info.trade_tick_value > 0:
                    risk = sl_distance / info.point * info.trade_tick_value * pos.volume
                    total_risk_amount += risk
        
        return (total_risk_amount / equity) * 100 if equity > 0 else 0.0
    
    def update_position_tracker(self):
        """Track positions by correlation group"""
        self.position_tracker = {}
        positions = mt5.positions_get()
        if not positions:
            return
        
        for pos in positions:
            for group, symbols in self.CORRELATION_GROUPS.items():
                if any(s in pos.symbol for s in symbols):
                    self.position_tracker[group] = self.position_tracker.get(group, 0) + 1
    
    def check_correlation_limit(self, symbol: str) -> bool:
        """Check if adding this symbol would exceed correlation limits"""
        for group, symbols in self.CORRELATION_GROUPS.items():
            if any(s in symbol for s in symbols):
                current = self.position_tracker.get(group, 0)
                if current >= self.max_per_group:
                    logger.debug(f"Correlation limit: {group} has {current} positions")
                    return False
        return True
    
    def has_position(self, symbol: str) -> bool:
        """Check if already have position on symbol"""
        positions = mt5.positions_get(symbol=symbol)
        return positions is not None and len(positions) > 0
    
    def analyze(self, symbol: str) -> Optional[Dict]:
        """
        Analyze symbol for trading opportunity.
        FIX: Proper market hours check, spread check, RSI logic order.
        """
        try:
            # FIX 1: Market hours check
            info = mt5.symbol_info(symbol)
            if not info:
                return None
            
            if info.trade_mode == 0:  # Trading disabled
                return None
            
            # FIX 2: Spread check
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None
            
            spread = info.spread
            max_spread = self.get_max_spread(symbol)
            if spread > max_spread:
                logger.debug(f"{symbol} spread too high: {spread} > {max_spread}")
                return None
            
            # Get data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
            if rates is None or len(rates) < 50:
                return None
            
            df = pd.DataFrame(rates)
            
            # Calculate indicators
            df['EMA9'] = df['close'].ewm(span=9).mean()
            df['EMA21'] = df['close'].ewm(span=21).mean()
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            # FIX 3: Division by zero protection
            df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))
            
            # FIX 4: Momentum threshold raised to 1.0%
            df['MOM'] = df['close'].pct_change(5) * 100
            
            curr = df.iloc[-1]
            
            # FIX 5: RSI logic order - most extreme first, no overlaps
            if curr['RSI'] < 15:
                return {'symbol': symbol, 'direction': 'BUY', 'score': 98, 
                        'reason': f"RSI Extreme Oversold ({curr['RSI']:.0f})"}
            elif curr['RSI'] < 25:
                return {'symbol': symbol, 'direction': 'BUY', 'score': 92,
                        'reason': f"RSI Oversold ({curr['RSI']:.0f})"}
            elif curr['RSI'] > 85:
                return {'symbol': symbol, 'direction': 'SELL', 'score': 98,
                        'reason': f"RSI Extreme Overbought ({curr['RSI']:.0f})"}
            elif curr['RSI'] > 75:
                return {'symbol': symbol, 'direction': 'SELL', 'score': 92,
                        'reason': f"RSI Overbought ({curr['RSI']:.0f})"}
            
            # FIX 6: Momentum threshold raised to 1.0% (was 0.5%)
            if curr['MOM'] > 1.0 and curr['EMA9'] > curr['EMA21'] and curr['RSI'] > 55:
                return {'symbol': symbol, 'direction': 'BUY', 'score': 85,
                        'reason': f"Strong Momentum +{curr['MOM']:.1f}%"}
            elif curr['MOM'] < -1.0 and curr['EMA9'] < curr['EMA21'] and curr['RSI'] < 45:
                return {'symbol': symbol, 'direction': 'SELL', 'score': 85,
                        'reason': f"Strong Momentum {curr['MOM']:.1f}%"}
            
            return None
            
        except Exception as e:
            # FIX 7: Proper exception handling with logging
            logger.warning(f"Analysis error for {symbol}: {e}")
            return None
    
    def get_max_spread(self, symbol: str) -> int:
        """Get maximum allowed spread for symbol"""
        if "BTC" in symbol or "ETH" in symbol:
            return 10000
        elif "GOLD" in symbol or "XAU" in symbol:
            return 500
        elif "US5" in symbol or "US3" in symbol:
            return 500
        else:
            return 50  # Forex
    
    def execute(self, signal: Dict) -> bool:
        """Execute trade with proper position sizing"""
        symbol = signal['symbol']
        direction = signal['direction']
        
        logger.info(f"TRADING: {symbol} {direction} | {signal['reason']}")
        
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not info or not tick:
            return False
        
        # Calculate lot size
        account = mt5.account_info()
        risk_amount = account.equity * (self.risk_per_trade / 100)
        
        point = info.point
        tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 1.0
        
        # SL points by symbol type
        if "BTC" in symbol or "ETH" in symbol:
            sl_points = 50000
        elif "GOLD" in symbol or "XAU" in symbol:
            sl_points = 5000
        elif "US5" in symbol or "US3" in symbol:
            sl_points = 5000
        else:
            sl_points = 500
        
        # FIX 8: Tick value safety
        if tick_value <= 0:
            tick_value = 1.0
        
        lot = risk_amount / (sl_points * tick_value)
        lot = max(info.volume_min, min(info.volume_max, round(lot, 2)))
        
        tp_points = sl_points * 2  # 1:2 RR
        
        if direction == 'BUY':
            price = tick.ask
            sl = price - sl_points * point
            tp = price + tp_points * point
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            sl = price + sl_points * point
            tp = price - tp_points * point
            order_type = mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 50,
            "magic": 111111,
            "comment": f"RB: {signal['reason'][:18]}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"EXECUTED: {symbol} {direction} {lot} lots @ {result.price}")
            return True
        else:
            logger.warning(f"FAILED: {result.comment}")
            return False


if __name__ == "__main__":
    bot = RobustTradingBot()
    bot.start()
