"""
AUTONOMOUS TRADING BOT - Full Professional Scalper
===================================================
Complete autonomous trading system:
1. SCAN for new high-conviction signals
2. EXECUTE trades with proper risk (5%)
3. MANAGE positions (break-even, trailing stops, loss cutting)
4. REPEAT continuously

This is YOUR trading assistant running 24/7.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import time
import logging
from datetime import datetime
from titan_system.core.memory import MemorySystem
from titan_system.execution.trade_manager import TradeManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [BOT] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AutonomousBot")


class AutonomousTradingBot:
    """
    Full autonomous trading system.
    Scans, executes, and manages all trades.
    """
    
    def __init__(self):
        # Timing
        self.scan_interval = 30  # Scan every 30 seconds
        self.last_signal_time = {}  # Prevent duplicate signals
        self.signal_cooldown = 300  # 5 min between signals per symbol
        
        # Risk settings
        self.risk_percent = 0.05  # 5% risk per trade
        self.max_positions_per_symbol = 2
        
        # Trade management
        self.breakeven_trigger = 1.0  # BE at 1:1
        self.trail_trigger = 1.5  # Trail at 1.5:1
        self.trail_distance = 0.5  # Trail 50% of profit
        self.managed_positions = {}
        
        # Symbols to scan
        self.watchlist = [
            "GOLD", "XAUUSD",
            "BTCUSD", "ETHUSD",
            "US100", "US30", "GER40",
            "EURUSD", "GBPUSD", "USDJPY"
        ]
        
        # Signal threshold
        self.min_signal_score = 70
        
        # Persistence
        self.memory = MemorySystem()
        self.trade_manager = TradeManager(managed_magics=[888888])
    
    def start(self):
        logger.info("=" * 60)
        logger.info("AUTONOMOUS TRADING BOT - ACTIVE")
        logger.info("=" * 60)
        logger.info("Mode: SCAN + EXECUTE + MANAGE")
        logger.info("Risk: 5% per trade")
        logger.info("Watchlist: " + str(len(self.watchlist)) + " symbols")
        logger.info("")
        
        if not mt5.initialize():
            logger.error("MT5 failed")
            return
        
        acc = mt5.account_info()
        logger.info("Account: " + str(acc.login))
        logger.info("Equity: $" + str(round(acc.equity, 2)))
        logger.info("")
        logger.info("Starting autonomous loop...")
        logger.info("")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                
                # 1. Manage existing positions
                self.manage_all_positions()
                
                # 2. Scan for new signals
                signals = self.scan_for_signals()
                
                # 3. Execute new signals
                for sig in signals:
                    self.execute_signal(sig)
                
                # 4. Status update every 2 minutes
                if cycle % 4 == 0:
                    self.print_status()
                
                time.sleep(self.scan_interval)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error("Error: " + str(e))
                time.sleep(10)
        
        mt5.shutdown()
    
    def scan_for_signals(self):
        """Scan all symbols for high-conviction setups"""
        signals = []
        
        for symbol in self.watchlist:
            try:
                if not mt5.symbol_select(symbol, True):
                    continue
                
                # Check if we already have max positions
                positions = mt5.positions_get(symbol=symbol)
                if positions and len(positions) >= self.max_positions_per_symbol:
                    continue
                
                # Check cooldown
                now = time.time()
                if symbol in self.last_signal_time:
                    if now - self.last_signal_time[symbol] < self.signal_cooldown:
                        continue
                
                # Get data
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
                if rates is None or len(rates) < 50:
                    continue
                
                df = pd.DataFrame(rates)
                signal = self.analyze_symbol(symbol, df)
                
                if signal and signal["score"] >= self.min_signal_score:
                    signals.append(signal)
                    self.last_signal_time[symbol] = now
                    
            except Exception as e:
                pass
        
        return signals
    
    def analyze_symbol(self, symbol, df):
        """Analyze a symbol and return signal if valid"""
        # Calculate indicators
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        df['MOM'] = df['close'].pct_change(5) * 100
        df['ATR'] = (df['high'] - df['low']).rolling(14).mean()
        
        df['HIGH_20'] = df['high'].rolling(20).max()
        df['LOW_20'] = df['low'].rolling(20).min()
        df['RANGE_POS'] = (df['close'] - df['LOW_20']) / (df['HIGH_20'] - df['LOW_20'])
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Score the setup
        score = 50
        direction = None
        reasons = []
        
        # RSI
        if curr['RSI'] < 30:
            score += 25
            direction = "BUY"
            reasons.append("RSI Oversold")
        elif curr['RSI'] > 70:
            score += 25
            direction = "SELL"
            reasons.append("RSI Overbought")
        elif curr['RSI'] < 40:
            score += 10
            if not direction: direction = "BUY"
            reasons.append("RSI Low")
        elif curr['RSI'] > 60:
            score += 10
            if not direction: direction = "SELL"
            reasons.append("RSI High")
        
        # EMA Cross
        bullish_cross = prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21']
        bearish_cross = prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21']
        
        if bullish_cross:
            score += 20
            direction = "BUY"
            reasons.append("Bullish EMA Cross")
        elif bearish_cross:
            score += 20
            direction = "SELL"
            reasons.append("Bearish EMA Cross")
        elif curr['EMA9'] > curr['EMA21']:
            score += 10
            if direction != "SELL":
                direction = "BUY"
            reasons.append("Bullish Trend")
        elif curr['EMA9'] < curr['EMA21']:
            score += 10
            if direction != "BUY":
                direction = "SELL"
            reasons.append("Bearish Trend")
        
        # Momentum
        if curr['MOM'] > 0.3:
            score += 10
            if direction != "SELL":
                direction = "BUY"
            reasons.append("Bullish Momentum")
        elif curr['MOM'] < -0.3:
            score += 10
            if direction != "BUY":
                direction = "SELL"
            reasons.append("Bearish Momentum")
        
        # Range position
        if curr['RANGE_POS'] < 0.2 and direction == "BUY":
            score += 10
            reasons.append("At Range Low")
        elif curr['RANGE_POS'] > 0.8 and direction == "SELL":
            score += 10
            reasons.append("At Range High")
        
        if direction and score >= self.min_signal_score:
            return {
                "symbol": symbol,
                "direction": direction,
                "score": score,
                "reasons": reasons,
                "atr": curr['ATR'],
                "price": curr['close']
            }
        
        return None
    
    def execute_signal(self, signal):
        """Execute a trade signal"""
        symbol = signal["symbol"]
        direction = signal["direction"]
        score = signal["score"]
        atr = signal["atr"]
        
        logger.info("")
        logger.info("=" * 40)
        logger.info("[SIGNAL] " + symbol + " " + direction + " (Score: " + str(score) + ")")
        logger.info("Reasons: " + ", ".join(signal["reasons"]))
        
        # Get symbol info
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not info or not tick:
            logger.error("Cannot get symbol info")
            return False
        
        # Calculate position size (5% risk)
        acc = mt5.account_info()
        risk_amount = acc.equity * self.risk_percent
        sl_distance = atr * 2
        
        # Estimate pip value (rough)
        if "USD" in symbol and symbol.endswith("USD"):
            pip_value = 1  # Crypto/Commodity vs USD
        elif "JPY" in symbol:
            pip_value = 0.01 * 100000 / 100  # JPY pairs
        else:
            pip_value = 10  # Standard forex ~$10/pip per lot
        
        lot_size = risk_amount / (sl_distance * pip_value) if sl_distance > 0 else 0.1
        lot_size = round(lot_size, 2)
        lot_size = max(info.volume_min, min(lot_size, info.volume_max))
        lot_size = min(lot_size, 5.0)  # Cap at 5 lots for safety
        
        # Set entry, SL, TP
        if direction == "BUY":
            price = tick.ask
            sl = price - sl_distance
            tp = price + (sl_distance * 2)  # 2:1 RR
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            sl = price + sl_distance
            tp = price - (sl_distance * 2)
            order_type = mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": round(sl, info.digits),
            "tp": round(tp, info.digits),
            "deviation": 50,
            "magic": 888888,
            "comment": "Auto_" + direction[:1] + "_" + str(score),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info("[EXECUTED] " + symbol + " " + direction + " " + str(lot_size) + " lots @ " + str(round(result.price, info.digits)))
            logger.info("SL: " + str(round(sl, info.digits)) + " | TP: " + str(round(tp, info.digits)))
            
            # Record in local persistent storage
            trade_data = {
                'id': str(result.order),
                'ticket': result.order,
                'symbol': symbol,
                'type': direction,
                'volume': lot_size,
                'open_price': result.price,
                'sl': sl,
                'tp': tp,
                'open_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'magic': 888888,
                'comment': "Auto_" + direction[:1] + "_" + str(score),
                'strategy_name': "Autonomous_Signal_Scout"
            }
            self.memory.record_trade(trade_data)
            return True
        else:
            logger.error("[FAILED] " + str(result.comment))
            return False
    
    def manage_all_positions(self):
        """Manage all open positions"""
        positions = mt5.positions_get()
        
        if not positions:
            return
        
        for pos in positions:
            if pos.magic == 888888:
                self.trade_manager.apply_tier_protection(pos)
    
    def manage_position(self, pos):
        """Manage a single position"""
        symbol = pos.symbol
        ticket = pos.ticket
        direction = "BUY" if pos.type == 0 else "SELL"
        entry = pos.price_open
        current = pos.price_current
        sl = pos.sl
        tp = pos.tp
        profit = pos.profit
        
        info = mt5.symbol_info(symbol)
        if not info:
            return
        
        point = info.point
        
        # Calculate R multiple
        if direction == "BUY":
            risk_dist = entry - sl if sl > 0 else 0
            profit_dist = current - entry
        else:
            risk_dist = sl - entry if sl > 0 else 0
            profit_dist = entry - current
        
        if risk_dist <= 0:
            return
        
        r_mult = profit_dist / risk_dist
        
        # Track state
        key = str(ticket)
        if key not in self.managed_positions:
            self.managed_positions[key] = {"be_done": False}
        
        state = self.managed_positions[key]
        
        # BREAK-EVEN at 1:1
        if r_mult >= self.breakeven_trigger and not state["be_done"]:
            new_sl = entry + (point * 10 if direction == "BUY" else -point * 10)
            if self.modify_sl(ticket, symbol, new_sl, tp):
                logger.info("[BE] " + symbol + " " + direction + " -> Break-even ($" + str(round(profit, 2)) + ")")
                state["be_done"] = True
        
        # TRAILING at 1.5:1+
        if r_mult >= self.trail_trigger:
            trail_dist = profit_dist * self.trail_distance
            if direction == "BUY":
                new_sl = current - trail_dist
                if new_sl > sl:
                    self.modify_sl(ticket, symbol, new_sl, tp)
                    logger.info("[TRAIL] " + symbol + " -> SL: " + str(round(new_sl, info.digits)))
            else:
                new_sl = current + trail_dist
                if new_sl < sl:
                    self.modify_sl(ticket, symbol, new_sl, tp)
                    logger.info("[TRAIL] " + symbol + " -> SL: " + str(round(new_sl, info.digits)))
    
    def modify_sl(self, ticket, symbol, new_sl, tp):
        """Modify stop loss"""
        info = mt5.symbol_info(symbol)
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": symbol,
            "sl": round(new_sl, info.digits),
            "tp": tp if tp > 0 else 0,
        }
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    def print_status(self):
        """Print current status"""
        acc = mt5.account_info()
        positions = mt5.positions_get()
        
        logger.info("-" * 40)
        logger.info("[STATUS] Equity: $" + str(round(acc.equity, 2)) + " | Positions: " + str(len(positions) if positions else 0))


if __name__ == "__main__":
    bot = AutonomousTradingBot()
    bot.start()
