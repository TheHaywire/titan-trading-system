"""
INSTITUTIONAL MULTI-TIMEFRAME TRADING BOT
==========================================
Professional-grade autonomous trading system with:

1. MULTI-TIMEFRAME ANALYSIS
   - H4: Trend direction (Higher timeframe bias)
   - H1: Zone identification (Support/Resistance)
   - M15: Entry timing (Confirmation)
   - M5: Execution (Precise entry)

2. COMPREHENSIVE INDICATORS
   - RSI (Momentum oscillator)
   - EMA 9/21/50/200 (Trend structure)
   - ATR (Volatility & position sizing)
   - ADX (Trend strength)
   - Bollinger Bands (Mean reversion)
   - MACD (Momentum confirmation)
   - Volume (Institutional activity)

3. RISK MANAGEMENT
   - 5% risk per trade
   - Max 2 positions per symbol
   - Max 10 total positions
   - Break-even at 1:1 RR
   - Trailing stop at 1.5:1+ RR
   - Session-based trading (avoid dead zones)

4. CONFLUENCE SCORING
   - Signals require multiple confirmations
   - Higher scores = higher confidence
   - Only trade Score 75+ setups
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime
from titan_system.core.memory import MemorySystem
from titan_system.execution.trade_manager import TradeManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MTF-BOT] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MTFBot")


class InstitutionalMTFBot:
    """
    Professional Multi-Timeframe Trading System
    """
    
    def __init__(self):
        # === TIMING ===
        self.scan_interval = 30
        self.last_signal_time = {}
        self.signal_cooldown = 300  # 5 min cooldown
        
        # === RISK MANAGEMENT ===
        self.risk_percent = 0.05  # 5% per trade
        self.max_positions_per_symbol = 2
        self.max_total_positions = 10
        self.max_daily_loss_percent = 0.15  # 15% daily loss limit
        self.starting_equity = None
        
        # === TIMEFRAMES ===
        self.tf_trend = mt5.TIMEFRAME_H4      # Trend direction
        self.tf_zones = mt5.TIMEFRAME_H1      # S/R zones
        self.tf_confirm = mt5.TIMEFRAME_M15   # Confirmation
        self.tf_entry = mt5.TIMEFRAME_M5      # Entry
        
        # === INDICATORS CONFIG ===
        self.ema_fast = 9
        self.ema_mid = 21
        self.ema_slow = 50
        self.ema_trend = 200
        self.rsi_period = 14
        self.atr_period = 14
        self.adx_period = 14
        self.bb_period = 20
        self.bb_std = 2
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # === THRESHOLDS ===
        self.min_signal_score = 75
        self.adx_trending = 25
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        # Persistence
        self.memory = MemorySystem()
        self.trade_manager = TradeManager(managed_magics=[777777])
        
        # === TRADE MANAGEMENT ===
        self.breakeven_trigger = 1.0
        self.trail_trigger = 1.5
        self.trail_distance = 0.5
        self.managed_positions = {}
        
        # === WATCHLIST ===
        self.watchlist = [
            "GOLD", "XAUUSD",
            "BTCUSD", "ETHUSD",
            "US100", "US30", "GER40",
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD"
        ]
        
        # === SESSION TIMES (UTC) ===
        self.sessions = {
            "asian": (0, 8),
            "london": (7, 16),
            "newyork": (13, 22)
        }
    
    def start(self):
        logger.info("=" * 60)
        logger.info("INSTITUTIONAL MTF TRADING BOT - ACTIVE")
        logger.info("=" * 60)
        logger.info("Timeframes: H4 (Trend) -> H1 (Zones) -> M15 (Confirm) -> M5 (Entry)")
        logger.info("Indicators: RSI, EMA, ATR, ADX, MACD, Bollinger")
        logger.info("Risk: 5% per trade | Max 10 positions")
        logger.info("")
        
        if not mt5.initialize():
            logger.error("MT5 failed")
            return
        
        acc = mt5.account_info()
        self.starting_equity = acc.equity
        logger.info("Account: " + str(acc.login))
        logger.info("Equity: $" + str(round(acc.equity, 2)))
        logger.info("")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                
                # Check circuit breaker
                if self.check_daily_loss_limit():
                    logger.warning("[CIRCUIT BREAKER] Daily loss limit hit. Pausing trading.")
                    time.sleep(60)
                    continue
                
                # 1. Manage existing positions
                self.manage_all_positions()
                
                # 2. Scan with MTF analysis
                signals = self.mtf_scan()
                
                # 3. Execute signals
                for sig in signals:
                    self.execute_signal(sig)
                
                # 4. Status every 2 min
                if cycle % 4 == 0:
                    self.print_status()
                
                time.sleep(self.scan_interval)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped")
                break
            except Exception as e:
                logger.error("Error: " + str(e))
                time.sleep(10)
        
        mt5.shutdown()
    
    def check_daily_loss_limit(self):
        """Circuit breaker - stop if daily loss exceeds limit"""
        if not self.starting_equity:
            return False
        acc = mt5.account_info()
        current_equity = acc.equity
        loss_percent = (self.starting_equity - current_equity) / self.starting_equity
        return loss_percent >= self.max_daily_loss_percent
    
    def mtf_scan(self):
        """Multi-timeframe scan for high-quality signals"""
        signals = []
        
        # Check max positions
        all_positions = mt5.positions_get()
        if all_positions and len(all_positions) >= self.max_total_positions:
            return signals
        
        for symbol in self.watchlist:
            try:
                if not mt5.symbol_select(symbol, True):
                    continue
                
                # Check positions per symbol
                positions = mt5.positions_get(symbol=symbol)
                if positions and len(positions) >= self.max_positions_per_symbol:
                    continue
                
                # Check cooldown
                now = time.time()
                if symbol in self.last_signal_time:
                    if now - self.last_signal_time[symbol] < self.signal_cooldown:
                        continue
                
                # === MULTI-TIMEFRAME ANALYSIS ===
                signal = self.analyze_mtf(symbol)
                
                if signal and signal["score"] >= self.min_signal_score:
                    signals.append(signal)
                    self.last_signal_time[symbol] = now
                    
            except Exception as e:
                pass
        
        return signals
    
    def get_data(self, symbol, timeframe, bars=200):
        """Get OHLCV data for a timeframe"""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) < 50:
            return None
        return pd.DataFrame(rates)
    
    def calculate_indicators(self, df):
        """Calculate all indicators on a dataframe"""
        # EMAs
        df['ema9'] = df['close'].ewm(span=self.ema_fast).mean()
        df['ema21'] = df['close'].ewm(span=self.ema_mid).mean()
        df['ema50'] = df['close'].ewm(span=self.ema_slow).mean()
        df['ema200'] = df['close'].ewm(span=self.ema_trend).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(self.atr_period).mean()
        
        # ADX
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        atr14 = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(14).mean()
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        
        # Bollinger Bands
        df['bb_mid'] = df['close'].rolling(self.bb_period).mean()
        bb_std = df['close'].rolling(self.bb_period).std()
        df['bb_upper'] = df['bb_mid'] + (self.bb_std * bb_std)
        df['bb_lower'] = df['bb_mid'] - (self.bb_std * bb_std)
        df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # MACD
        ema12 = df['close'].ewm(span=self.macd_fast).mean()
        ema26 = df['close'].ewm(span=self.macd_slow).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=self.macd_signal).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Momentum
        df['mom'] = df['close'].pct_change(5) * 100
        
        # Range position
        df['high20'] = df['high'].rolling(20).max()
        df['low20'] = df['low'].rolling(20).min()
        df['range_pct'] = (df['close'] - df['low20']) / (df['high20'] - df['low20'])
        
        return df
    
    def analyze_mtf(self, symbol):
        """
        Multi-Timeframe Analysis:
        H4: Overall trend direction
        H1: Key zones and structure
        M15: Entry confirmation
        M5: Precise timing
        """
        # Get data for all timeframes
        df_h4 = self.get_data(symbol, self.tf_trend, 100)
        df_h1 = self.get_data(symbol, self.tf_zones, 100)
        df_m15 = self.get_data(symbol, self.tf_confirm, 100)
        df_m5 = self.get_data(symbol, self.tf_entry, 100)
        
        if df_h4 is None or df_h1 is None or df_m15 is None or df_m5 is None:
            return None
        
        # Calculate indicators for each
        df_h4 = self.calculate_indicators(df_h4)
        df_h1 = self.calculate_indicators(df_h1)
        df_m15 = self.calculate_indicators(df_m15)
        df_m5 = self.calculate_indicators(df_m5)
        
        h4 = df_h4.iloc[-1]
        h1 = df_h1.iloc[-1]
        m15 = df_m15.iloc[-1]
        m5 = df_m5.iloc[-1]
        
        # === SCORING SYSTEM ===
        score = 0
        direction = None
        reasons = []
        
        # --- H4 TREND (30 points max) ---
        h4_bullish = h4['ema50'] > h4['ema200'] and h4['close'] > h4['ema50']
        h4_bearish = h4['ema50'] < h4['ema200'] and h4['close'] < h4['ema50']
        
        if h4_bullish:
            score += 20
            direction = "BUY"
            reasons.append("H4 Bullish Trend")
            if h4['adx'] > self.adx_trending:
                score += 10
                reasons.append("H4 Strong Trend")
        elif h4_bearish:
            score += 20
            direction = "SELL"
            reasons.append("H4 Bearish Trend")
            if h4['adx'] > self.adx_trending:
                score += 10
                reasons.append("H4 Strong Trend")
        
        # --- H1 STRUCTURE (20 points max) ---
        if direction == "BUY":
            if h1['close'] > h1['ema21'] and h1['ema21'] > h1['ema50']:
                score += 15
                reasons.append("H1 Bullish Structure")
            if h1['bb_pct'] < 0.3:
                score += 5
                reasons.append("H1 At BB Low")
        elif direction == "SELL":
            if h1['close'] < h1['ema21'] and h1['ema21'] < h1['ema50']:
                score += 15
                reasons.append("H1 Bearish Structure")
            if h1['bb_pct'] > 0.7:
                score += 5
                reasons.append("H1 At BB High")
        
        # --- M15 CONFIRMATION (25 points max) ---
        m15_prev = df_m15.iloc[-2]
        
        if direction == "BUY":
            # RSI oversold recovering
            if m15['rsi'] < 40 and m15['rsi'] > m15_prev['rsi']:
                score += 10
                reasons.append("M15 RSI Recovering")
            # EMA bullish cross
            if m15_prev['ema9'] <= m15_prev['ema21'] and m15['ema9'] > m15['ema21']:
                score += 15
                reasons.append("M15 Bullish Cross")
            elif m15['ema9'] > m15['ema21']:
                score += 5
                reasons.append("M15 Bullish")
            # MACD bullish
            if m15['macd_hist'] > 0 and m15_prev['macd_hist'] <= 0:
                score += 10
                reasons.append("M15 MACD Bullish")
                
        elif direction == "SELL":
            # RSI overbought declining
            if m15['rsi'] > 60 and m15['rsi'] < m15_prev['rsi']:
                score += 10
                reasons.append("M15 RSI Declining")
            # EMA bearish cross
            if m15_prev['ema9'] >= m15_prev['ema21'] and m15['ema9'] < m15['ema21']:
                score += 15
                reasons.append("M15 Bearish Cross")
            elif m15['ema9'] < m15['ema21']:
                score += 5
                reasons.append("M15 Bearish")
            # MACD bearish
            if m15['macd_hist'] < 0 and m15_prev['macd_hist'] >= 0:
                score += 10
                reasons.append("M15 MACD Bearish")
        
        # --- M5 TIMING (15 points max) ---
        m5_prev = df_m5.iloc[-2]
        
        if direction == "BUY":
            if m5['rsi'] < self.rsi_oversold:
                score += 10
                reasons.append("M5 RSI Oversold")
            if m5['mom'] > 0.2:
                score += 5
                reasons.append("M5 Bullish Mom")
        elif direction == "SELL":
            if m5['rsi'] > self.rsi_overbought:
                score += 10
                reasons.append("M5 RSI Overbought")
            if m5['mom'] < -0.2:
                score += 5
                reasons.append("M5 Bearish Mom")
        
        # --- CONFLUENCE BONUS (10 points) ---
        if len(reasons) >= 5:
            score += 10
            reasons.append("High Confluence")
        
        if direction and score >= self.min_signal_score:
            return {
                "symbol": symbol,
                "direction": direction,
                "score": score,
                "reasons": reasons,
                "atr": m5['atr'],
                "price": m5['close'],
                "h4_trend": "BULL" if h4_bullish else "BEAR" if h4_bearish else "NEUTRAL"
            }
        
        return None
    
    def execute_signal(self, signal):
        """Execute with proper position sizing"""
        symbol = signal["symbol"]
        direction = signal["direction"]
        score = signal["score"]
        atr = signal["atr"]
        
        logger.info("")
        logger.info("=" * 50)
        logger.info("[MTF SIGNAL] " + symbol + " " + direction + " (Score: " + str(score) + ")")
        logger.info("H4 Trend: " + signal["h4_trend"])
        logger.info("Reasons: " + ", ".join(signal["reasons"][:5]))
        
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not info or not tick:
            logger.error("Cannot get symbol info")
            return False
        
        # Position sizing based on ATR
        acc = mt5.account_info()
        risk_amount = acc.equity * self.risk_percent
        sl_distance = atr * 2
        
        # Estimate pip value
        if "JPY" in symbol:
            pip_value = 0.01 * 100000 / 100
        elif symbol in ["BTCUSD", "ETHUSD"]:
            pip_value = 1
        elif symbol in ["US100", "US30", "GER40"]:
            pip_value = 1
        else:
            pip_value = 10
        
        lot_size = risk_amount / (sl_distance * pip_value) if sl_distance > 0 else 0.1
        lot_size = round(lot_size, 2)
        lot_size = max(info.volume_min, min(lot_size, info.volume_max))
        lot_size = min(lot_size, 10.0)  # Hard cap
        
        if direction == "BUY":
            price = tick.ask
            sl = price - sl_distance
            tp = price + (sl_distance * 2)
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
            "magic": 777777,
            "comment": "MTF_" + direction[:1] + str(score),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info("[EXECUTED] " + str(lot_size) + " lots @ " + str(round(result.price, info.digits)))
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
                'magic': 777777,
                'comment': "MTF_" + direction[:1] + str(score),
                'strategy_name': "Institutional_MTF_Confluence"
            }
            self.memory.record_trade(trade_data)
            return True
        else:
            logger.error("[FAILED] " + str(result.comment))
            return False
    
    def manage_all_positions(self):
        """Manage positions with BE and trailing"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        for pos in positions:
            if pos.magic == 777777:
                self.trade_manager.apply_tier_protection(pos)
    
    def manage_position(self, pos):
        """BE at 1:1, Trail at 1.5:1+"""
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
        
        if direction == "BUY":
            risk_dist = entry - sl if sl > 0 else 0
            profit_dist = current - entry
        else:
            risk_dist = sl - entry if sl > 0 else 0
            profit_dist = entry - current
        
        if risk_dist <= 0:
            return
        
        r_mult = profit_dist / risk_dist
        
        key = str(ticket)
        if key not in self.managed_positions:
            self.managed_positions[key] = {"be": False}
        state = self.managed_positions[key]
        
        # Break-even
        if r_mult >= self.breakeven_trigger and not state["be"]:
            new_sl = entry + (point * 10 if direction == "BUY" else -point * 10)
            if self.modify_sl(ticket, symbol, new_sl, tp):
                logger.info("[BE] " + symbol + " " + direction + " -> Locked")
                state["be"] = True
        
        # Trailing
        if r_mult >= self.trail_trigger:
            trail_dist = profit_dist * self.trail_distance
            if direction == "BUY":
                new_sl = current - trail_dist
                if new_sl > sl:
                    self.modify_sl(ticket, symbol, new_sl, tp)
            else:
                new_sl = current + trail_dist
                if new_sl < sl:
                    self.modify_sl(ticket, symbol, new_sl, tp)
    
    def modify_sl(self, ticket, symbol, new_sl, tp):
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
        acc = mt5.account_info()
        positions = mt5.positions_get()
        logger.info("-" * 40)
        logger.info("[STATUS] Equity: $" + str(round(acc.equity, 2)) + " | Positions: " + str(len(positions) if positions else 0))


if __name__ == "__main__":
    bot = InstitutionalMTFBot()
    bot.start()
