"""
AUTONOMOUS TRADING BOT - Full Professional Scalper
===================================================
Complete autonomous trading system:
1. SCAN for new high-conviction signals
2. DETECT market regime (Trending/Mean-Reverting/High-Vol)
3. SELECT optimal strategy for current regime
4. EXECUTE trades with proper risk (adjusted by regime)
5. MANAGE positions (break-even, trailing stops, loss cutting)
6. REPEAT continuously

This is YOUR trading assistant running 24/7.
Now with Markov Regime Detection, Auto-Strategy Selection, and TA-Lib Candlestick Patterns!
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
from titan_system.db.database import Database
from titan_system.analytics.regime_detector import MarkovRegimeSwitcher, MarketRegime
from titan_system.analytics.auto_strategy import AutoStrategySelector, StrategyType

# Import TA-Lib indicators for 20x faster calculations + candlestick patterns
try:
    import talib
    from titan_system.indicators import TitanIndicators, detect_candlestick_patterns, TALIB_AVAILABLE
except ImportError:
    TALIB_AVAILABLE = False

# Import Key Levels detector for S/R-aware trading
try:
    from titan_system.analytics.key_levels import KeyLevelsDetector
    KEY_LEVELS_AVAILABLE = True
except ImportError:
    KEY_LEVELS_AVAILABLE = False

# Import Profile Engine for Market/Volume profiles
try:
    from titan_system.analytics.profile_engine import ProfileEngine
    PROFILE_AVAILABLE = True
except ImportError:
    PROFILE_AVAILABLE = False

# Import ML Signal Filter for probability-based filtering
try:
    from titan_system.ml.signal_filter import SignalFilter, filter_signal
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [BOT] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AutonomousBot")

import json
CONFIG_MISSIONS = "config/active_missions.json"
CONFIG_ALPHA = "config/alpha_registry.json"

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
        self.risk_percent = 0.01  # 1% risk per trade (SNIPER MODE)
        self.max_positions_per_symbol = 2
        
        # Trade management
        self.breakeven_trigger = 1.0  # BE at 1:1
        self.trail_trigger = 1.5  # Trail at 1.5:1
        self.trail_distance = 0.5  # Trail 50% of profit
        self.managed_positions = {}
        
        # THE 80/20 PROFESSIONAL PORTFOLIO (Based on Complete Account Forensics)
        # These 3 symbols generate 80% of profits - FOCUS HERE
        self.professional_portfolio = ["GOLD", "EURUSD", "BTCUSD"]
        self.watchlist = self.professional_portfolio.copy()
        
        # BANNED SYMBOLS (Historical losers - $500k/year leak)
        self.banned_symbols = [
            # Exotic Pairs (−$30k cumulative)
            "EURTRY", "USDZAR", "USDMXN", "USDSGD", "USDHKD", "USDCNH",
            # Minor Crosses (−$40k cumulative)
            "AUDNZD", "NZDCAD", "AUDCAD", "GBPNZD", "EURNZD",
            # Altcoins (−$25k cumulative)
            "XRPUSD", "ADAUSD", "LTCUSD", "DOTUSD", "AVAXUSD", "SOLUSD"
        ]
        
        # Professional Limits (Forensic-Driven)
        self.max_trades_per_day = 20  # vs historical 47 avg
        self.min_position_size = 0.1  # NO more 0.01 lot waste
        self.daily_trade_count = 0
        
        # Signal threshold
        self.min_signal_score = 70
        
        # Persistence
        self.memory = MemorySystem()
        self.db = Database("data/titan.db")
        self.trade_manager = TradeManager(managed_magics=[888888])
        
        # Optimized Parameters (NEW: from VectorBT sweeps)
        self.optimized_settings = {
            "GOLD": {
                "bb_period": 10,
                "bb_std": 2.5,
                "ema_fast": 20,
                "ema_slow": 50,
                "rsi_period": 14
            },
            "BTCUSD": {
                "bb_period": 20,
                "bb_std": 2.0,
                "ema_fast": 12,
                "ema_slow": 26,
                "rsi_period": 14
            }
        }
        
        # Regime Detection & Auto-Strategy (NEW)
        self.regime_detector = MarkovRegimeSwitcher()
        self.strategy_selector = AutoStrategySelector()
        self.regime_fitted = {}  # {symbol: bool}
        self.current_regimes = {}  # {symbol: regime_state}
        self.regime_log_interval = 20  # Log regime every N cycles
        
        # TA-Lib Indicators (NEW)
        if TALIB_AVAILABLE:
            logger.info("[TALIB] TA-Lib indicators: ACTIVE (20x faster)")
        else:
            logger.warning("[TALIB] TA-Lib not available, using manual calculations")
        
        # Key Levels Detector (NEW)
        if KEY_LEVELS_AVAILABLE:
            self.key_levels = KeyLevelsDetector()
            logger.info("[LEVELS] Key Levels detector: ACTIVE (S/R aware)")
        else:
            self.key_levels = None
            logger.warning("[LEVELS] Key Levels not available")
            
        # Profile Engine (NEW)
        if PROFILE_AVAILABLE:
            self.profile_engine = ProfileEngine()
            logger.info("[PROFILE] Market/Volume Profile engine: ACTIVE")
        else:
            self.profile_engine = None
            logger.warning("[PROFILE] Profile engine not available")
            
        # ML Signal Filter (NEW)
        if ML_AVAILABLE:
            self.ml_filter = SignalFilter()
            if self.ml_filter.is_trained:
                logger.info("[ML] Signal Filter: ACTIVE (Trained)")
            else:
                logger.info("[ML] Signal Filter: ACTIVE (Untrained - collecting data)")
        else:
            self.ml_filter = None
            logger.warning("[ML] Signal Filter not available")
            
        # Mission Intelligence (NEW)
        self.active_missions = {}
        self.load_active_missions()
        
        # Alpha Registry (NEW)
        self.alpha_registry = {}
        self.load_alpha_registry()
        
        # PROFESSIONAL TIME FILTERS (Forensic Analysis: avoid Asian chop)
        self.trading_hours_utc = {
            'start': 8,   # 8AM EST = London open
            'end': 17     # 5PM EST = NY close
        }
        
        logger.info("="*60)
        logger.info("🏛️ PROFESSIONAL BOT v2.0 - Forensic-Optimized")
        logger.info("="*60)
        logger.info(f"📊 Portfolio: {self.professional_portfolio}")
        logger.info(f"🚫 Banned: {len(self.banned_symbols)} symbols")
        logger.info(f"📏 Min Size: {self.min_position_size} lots")
        logger.info(f"🎯 Max Trades/Day: {self.max_trades_per_day}")
        logger.info(f"⏰ Trading Hours: {self.trading_hours_utc['start']:02d}:00 - {self.trading_hours_utc['end']:02d}:00 UTC")
        logger.info("="*60)
    
    def resolve_alpha_symbol(self, symbol):
        """Fuzzy lookup for Alpha Registry (handles Cash/suffixes)."""
        if symbol in self.alpha_registry:
            return symbol
        # Try common suffixes
        for suffix in ["Cash", ".pro", ".m"]:
            if symbol + suffix in self.alpha_registry:
                return symbol + suffix
        # Try reverse (if watchlist has suffix but registry doesn't)
        for suffix in ["Cash", ".pro", ".m"]:
            if symbol.endswith(suffix) and symbol[:-len(suffix)] in self.alpha_registry:
                return symbol[:-len(suffix)]
        return None
    
    def load_active_missions(self):
        """Load strategic missions from AI Mission Reports."""
        if os.path.exists(CONFIG_MISSIONS):
            try:
                with open(CONFIG_MISSIONS, 'r') as f:
                    self.active_missions = json.load(f)
                logger.info(f"[MISSION] Loaded {len(self.active_missions)} active missions")
            except Exception as e:
                logger.error(f"[MISSION] Error loading missions: {e}")

    def load_alpha_registry(self):
        """Load validated Alphas from the registry and merge into watchlist."""
        if os.path.exists(CONFIG_ALPHA):
            try:
                with open(CONFIG_ALPHA, 'r') as f:
                    data = json.load(f)
                    all_alphas = data.get('alphas', [])
                    # Convert to easier lookup {symbol: data}
                    self.alpha_registry = {a['symbol']: a for a in all_alphas}
                
                logger.info(f"[ALPHA] Loaded {len(self.alpha_registry)} validated Alphas from registry")
                
                # Dynamic Watchlist Expansion: Add Alphas with Sharpe > 1.5
                top_alphas = [a['symbol'] for a in all_alphas if a.get('sharpe', 0) > 1.5]
                original_count = len(self.watchlist)
                
                for s in top_alphas:
                    # Avoid duplicates and check if tradable (handled later in loop but good to filter here)
                    if s not in self.watchlist:
                        self.watchlist.append(s)
                
                if len(self.watchlist) > original_count:
                    logger.info(f"[ALPHA] Watchlist expanded: {original_count} -> {len(self.watchlist)} symbols (Added Top Alphas)")
                
            except Exception as e:
                logger.error(f"[ALPHA] Error loading registry: {e}")
    
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
        last_reset_day = datetime.now().day
        
        try:
            while True:
                cycle += 1
                
                # === DAILY RESET (Professional Framework) ===
                current_day = datetime.now().day
                if current_day != last_reset_day:
                    self.daily_trade_count = 0
                    last_reset_day = current_day
                    logger.info("🌆 [RESET] New trading day - counter reset to 0")
                
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
        """Scan all symbols for high-conviction setups with regime awareness"""
        # Reload missions every scan cycle to pick up new reports
        self.load_active_missions()
        
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
                
                # Get M5 data for signals
                rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
                if rates_m5 is None or len(rates_m5) < 50:
                    continue
                
                df = pd.DataFrame(rates_m5)
                
                # Get H1 data for regime detection
                rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
                regime_info = None
                if rates_h1 is not None and len(rates_h1) >= 100:
                    df_h1 = pd.DataFrame(rates_h1)
                    
                    # Fit regime model on first call for this symbol
                    if symbol not in self.regime_fitted:
                        self.regime_detector.fit(df_h1)
                        self.regime_fitted[symbol] = True
                    
                    # Detect current regime
                    regime_state = self.regime_detector.detect(df_h1)
                    self.current_regimes[symbol] = regime_state
                    regime_info = self.regime_detector.get_strategy_recommendation(regime_state)
                
                # Analyze with regime context
                signal = self.analyze_symbol(symbol, df, regime_info)
                
                if signal and signal["score"] >= self.min_signal_score:
                    signals.append(signal)
                    self.last_signal_time[symbol] = now
                    
            except Exception as e:
                pass
        
        return signals
    
    def is_professional_setup(self, symbol, df):
        """Check if setup meets Professional 80/20 Framework criteria."""
        
        # FILTER 1: Symbol Whitelist
        if symbol not in self.professional_portfolio:
            return False, "Not in professional portfolio"
        
        # FILTER 2: Banned Symbol Check
        if symbol in self.banned_symbols:
            return False, "Banned symbol (historical loser)"
        
        # FILTER 3: Daily Trade Limit
        if self.daily_trade_count >= self.max_trades_per_day:
            return False, f"Daily limit reached ({self.max_trades_per_day})"
        
        # FILTER 4: Time of Day (London/NY only)
        current_hour = datetime.now().hour
        if not (self.trading_hours_utc['start'] <= current_hour < self.trading_hours_utc['end']):
            return False, f"Outside trading hours ({current_hour}:00 UTC)"
        
        # FILTER 5: H1/M15 Trend Alignment (The Physics Check)
        try:
            # Get H1 trend
            h1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 20)
            if h1_data is None or len(h1_data) < 20:
                return False, "Insufficient H1 data"
            
            h1_trend = "UP" if h1_data[-1]['close'] > h1_data[0]['close'] else "DOWN"
            
            # Get M15 trend (from current df)
            if len(df) < 20:
                return False, "Insufficient M15 data"
            
            m15_trend = "UP" if df['close'].iloc[-1] > df['close'].iloc[0] else "DOWN"
            
            # CRITICAL: Trends must align
            if h1_trend != m15_trend:
                return False, f"H1 ({h1_trend}) vs M15 ({m15_trend}) disconnected - Static Friction"
            
            # Store trend for signal generation
            self.aligned_trend = h1_trend
            
        except Exception as e:
            logger.error(f"[FILTER] Trend alignment check failed: {e}")
            return False, "Trend check error"
        
        # FILTER 6: No Surge/Stretch (Volatility Check)
        try:
            body_sizes = [abs(r['close'] - r['open']) for r in df.tail(10).to_dict('records')]
            avg_body = sum(body_sizes) / len(body_sizes) if body_sizes else 0
            last_body = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
            
            if last_body > (avg_body * 2.0):
                return False, "Volatility surge detected - wait for compression"
        except:
            pass
        
        return True, "All professional criteria met"
    
    def analyze_symbol(self, symbol, df, regime_info=None):
        """Analyze a symbol and return signal if valid (regime-aware, TA-Lib accelerated, Mission-aware)"""
        
        # === PROFESSIONAL FILTER GATE ===
        is_valid, reason = self.is_professional_setup(symbol, df)
        if not is_valid:
            # Only log rejections occasionally to reduce noise
            if hash(symbol) % 10 == 0:  # Log 10% of rejections
                logger.debug(f"[FILTER] {symbol}: {reason}")
            return None
        
        logger.info(f"✅ [FILTER] {symbol}: {reason} | Trend: {self.aligned_trend}")
        
        if regime_info is None:
            regime_info = {}
        # 0. Check for Mission Priority (NEW)
        if symbol in self.active_missions:
            mission = self.active_missions[symbol]
            curr_p = df['close'].iloc[-1]
            entry_p = mission['entry']
            
            # Check if we are near entry zone (within 0.5% for limit/market orders)
            dist_pct = abs(curr_p - entry_p) / entry_p
            if dist_pct < 0.005:
                logger.info(f"[MISSION] {symbol} at Entry Zone ({entry_p}) - Triggering Execution")
                return {
                    "symbol": symbol,
                    "direction": mission['direction'].split()[0].upper(), # e.g., "BULLISH" -> "BUY"
                    "score": 100,
                    "reasons": [f"AI MISSION: {mission['source']}", "At Entry Zone"],
                    "ml_prob": 1.0, # AI override
                    "atr": (df['high'] - df['low']).rolling(14).mean().iloc[-1],
                    "price": entry_p,
                    "sl": mission['sl'],
                    "tp": mission['tp1'],
                    "is_mission": True,
                    "risk_multiplier": mission['risk_mult']
                }
            else:
                # Still waiting for entry, log status occasionally
                if time.time() % 300 < 30:
                    logger.info(f"[MISSION] {symbol} Waiting for Entry @ {entry_p} (Current: {curr_p:.2f})")

        # 1. Check for Alpha Registry Priority (NEW)
        alpha_symbol = self.resolve_alpha_symbol(symbol)
        if alpha_symbol:
            alpha = self.alpha_registry[alpha_symbol]
            curr_p = df['close'].iloc[-1]
            
            # Simplified Signal Logic for Alpha Strategies
            direction = None
            if alpha['strategy'] == "TrendFollowing":
                sma20 = df['close'].rolling(20).mean().iloc[-1]
                sma50 = df['close'].rolling(50).mean().iloc[-1]
                if sma20 > sma50: direction = "BUY"
                elif sma20 < sma50: direction = "SELL"
                
            elif alpha['strategy'] == "MeanReversion":
                sma = df['close'].rolling(20).mean().iloc[-1]
                std = df['close'].rolling(20).std().iloc[-1]
                lower = sma - 2.5 * std
                upper = sma + 2.5 * std
                if curr_p < lower: direction = "BUY"
                elif curr_p > upper: direction = "SELL"
                
            elif alpha['strategy'] == "VolBreakout":
                high10 = df['high'].rolling(10).max().shift(1).iloc[-1]
                low10 = df['low'].rolling(10).min().shift(1).iloc[-1]
                if curr_p > high10: direction = "BUY"
                elif curr_p < low10: direction = "SELL"
            
            if direction:
                logger.info(f"[ALPHA] {symbol} Strategy {alpha['strategy']} matches ({direction})")
                return {
                    "symbol": symbol,
                    "direction": direction,
                    "score": 90, # High conviction for validated Alphas
                    "reasons": [f"ALPHA REGISTRY: {alpha['strategy']}", f"TF: {alpha['tf']}", f"Sharpe: {alpha['metrics']['sharpe']}"],
                    "ml_prob": 0.85,
                    "atr": (df['high'] - df['low']).rolling(14).mean().iloc[-1],
                    "is_alpha": True
                }

        # 1. Standard Analysis (If no mission or not at entry)
        opt = self.optimized_settings.get(symbol, {
            "ema_fast": 9, "ema_slow": 21, "rsi_period": 14, "bb_period": 20, "bb_std": 2.0
        })
        
        # Calculate indicators using TA-Lib if available (20x faster)
        if TALIB_AVAILABLE:
            try:
                # Use talib directly for custom periods
                close = df['close'].values.astype(float)
                high = df['high'].values.astype(float)
                low = df['low'].values.astype(float)
                
                df['EMA9'] = talib.EMA(close, timeperiod=opt['ema_fast'])
                df['EMA21'] = talib.EMA(close, timeperiod=opt['ema_slow'])
                df['RSI'] = talib.RSI(close, timeperiod=opt['rsi_period'])
                df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
            except Exception as e:
                logger.error(f"[TALIB] Error: {e}")
                # Fallback to manual if TA-Lib fails
                df['EMA9'] = df['close'].ewm(span=opt['ema_fast']).mean()
                df['EMA21'] = df['close'].ewm(span=opt['ema_slow']).mean()
                delta = df['close'].diff()
                gain = delta.where(delta > 0, 0).rolling(opt['rsi_period']).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(opt['rsi_period']).mean()
                df['RSI'] = 100 - (100 / (1 + gain/loss))
        else:
            # Manual calculation (slower)
            df['EMA9'] = df['close'].ewm(span=opt['ema_fast']).mean()
            df['EMA21'] = df['close'].ewm(span=opt['ema_slow']).mean()
            
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(opt['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(opt['rsi_period']).mean()
            df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        # Additional indicators (always calculate)
        df['MOM'] = df['close'].pct_change(5) * 100
        if 'ATR' not in df.columns:
            df['ATR'] = (df['high'] - df['low']).rolling(14).mean()
        
        df['HIGH_20'] = df['high'].rolling(20).max()
        df['LOW_20'] = df['low'].rolling(20).min()
        df['RANGE_POS'] = (df['close'] - df['LOW_20']) / (df['HIGH_20'] - df['LOW_20'])
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Determine current regime and strategy recommendations
        current_regime = regime_info.get('regime', 'UNKNOWN') if regime_info else 'UNKNOWN'
        preferred_strategies = regime_info.get('preferred_strategies', []) if regime_info else []
        avoid_strategies = regime_info.get('avoid_strategies', []) if regime_info else []
        regime_risk_mult = regime_info.get('risk_multiplier', 1.0) if regime_info else 1.0
        
        # Score the setup
        score = 50
        direction = None
        reasons = []
        detected_strategy_type = None
        
        # ========== CRITICAL: MTF TREND GUARD (WINNING EDGE) ==========
        # Reverse-engineered from +$31k profitable manual GOLD BULL trade @ 4470
        # RULE: Never trade against the 1D/4H trend. This prevents shorting parabolic moves.
        rates_1d = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 50)
        rates_4h = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
        
        if rates_1d is not None and rates_4h is not None:
            df_1d = pd.DataFrame(rates_1d)
            df_4h = pd.DataFrame(rates_4h)
            
            sma50_1d = df_1d['close'].rolling(50).mean().iloc[-1]
            sma50_4h = df_4h['close'].rolling(50).mean().iloc[-1]
            current_price = curr['close']
            
            trend_1d = "BULL" if current_price > sma50_1d else "BEAR"
            trend_4h = "BULL" if current_price > sma50_4h else "BEAR"
            
            logger.info(f"[MTF GUARD] {symbol}: 1D Trend={trend_1d}, 4H Trend={trend_4h}")
        else:
            # If we can't get MTF data, skip the symbol entirely (safety)
            logger.warning(f"[MTF GUARD] Cannot fetch MTF data for {symbol}. SKIPPING.")
            return None
        # ================================================================
        
        # RSI - Mean Reversion strategy
        if curr['RSI'] < 30:
            score += 25
            direction = "BUY"
            reasons.append("RSI Oversold")
            detected_strategy_type = "Mean Reversion"
        elif curr['RSI'] > 70:
            score += 25
            direction = "SELL"
            reasons.append("RSI Overbought")
            detected_strategy_type = "Mean Reversion"
        elif curr['RSI'] < 40:
            score += 10
            if not direction: direction = "BUY"
            reasons.append("RSI Low")
        elif curr['RSI'] > 60:
            score += 10
            if not direction: direction = "SELL"
            reasons.append("RSI High")
        
        # EMA Cross - Trend Following strategy
        bullish_cross = prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21']
        bearish_cross = prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21']
        
        if bullish_cross:
            score += 20
            direction = "BUY"
            reasons.append("Bullish EMA Cross")
            detected_strategy_type = "Trend Following"
        elif bearish_cross:
            score += 20
            direction = "SELL"
            reasons.append("Bearish EMA Cross")
            detected_strategy_type = "Trend Following"
        elif curr['EMA9'] > curr['EMA21']:
            score += 10
            if direction != "SELL":
                direction = "BUY"
            reasons.append("Bullish Trend")
            if not detected_strategy_type:
                detected_strategy_type = "Trend Following"
        elif curr['EMA9'] < curr['EMA21']:
            score += 10
            if direction != "BUY":
                direction = "SELL"
            reasons.append("Bearish Trend")
            if not detected_strategy_type:
                detected_strategy_type = "Trend Following"
        
        # Momentum - Momentum strategy
        if curr['MOM'] > 0.3:
            score += 10
            if direction != "SELL":
                direction = "BUY"
            reasons.append("Bullish Momentum")
            if not detected_strategy_type:
                detected_strategy_type = "Momentum"
        elif curr['MOM'] < -0.3:
            score += 10
            if direction != "BUY":
                direction = "SELL"
            reasons.append("Bearish Momentum")
            if not detected_strategy_type:
                detected_strategy_type = "Momentum"
        
        # Range position
        if curr['RANGE_POS'] < 0.2 and direction == "BUY":
            score += 10
            reasons.append("At Range Low")
        elif curr['RANGE_POS'] > 0.8 and direction == "SELL":
            score += 10
            reasons.append("At Range High")
        
        # CANDLESTICK PATTERN DETECTION (TA-Lib - NEW!)
        if TALIB_AVAILABLE:
            try:
                patterns = detect_candlestick_patterns(df)
                bullish_patterns = [p for p in patterns if p.startswith("BULLISH:")]
                bearish_patterns = [p for p in patterns if p.startswith("BEARISH:")]
                
                if bullish_patterns and direction == "BUY":
                    score += 15
                    pattern_names = ", ".join([p.split(": ")[1] for p in bullish_patterns[:2]])
                    reasons.append(f"[CDL] {pattern_names}")
                elif bearish_patterns and direction == "SELL":
                    score += 15
                    pattern_names = ", ".join([p.split(": ")[1] for p in bearish_patterns[:2]])
                    reasons.append(f"[CDL] {pattern_names}")
                elif bullish_patterns and direction == "SELL":
                    # Pattern conflicts with direction - reduce confidence
                    score -= 10
                    reasons.append("[CDL] Conflicting bullish pattern")
                elif bearish_patterns and direction == "BUY":
                    score -= 10
                    reasons.append("[CDL] Conflicting bearish pattern")
            except Exception:
                pass  # Candlestick detection failed, continue without
        
        # REGIME ADJUSTMENT: Boost/penalize score based on strategy-regime fit
        if detected_strategy_type and regime_info:
            if detected_strategy_type in preferred_strategies:
                score += 15
                reasons.append(f"[REGIME+] {detected_strategy_type} preferred in {current_regime}")
            elif detected_strategy_type in avoid_strategies:
                score -= 20
                reasons.append(f"[REGIME-] {detected_strategy_type} not ideal for {current_regime}")
            else:
                reasons.append(f"[REGIME] {current_regime}")
        
        # KEY LEVELS ADJUSTMENT: Boost/penalize based on S/R proximity (NEW!)
        if self.key_levels and direction:
            try:
                level_context = self.key_levels.get_signal_context(df, direction, symbol)
                if level_context['near_key_level']:
                    score += level_context['score_adjustment']
                    if level_context['at_support'] and direction == 'BUY':
                        reasons.append("[S/R+] At Support level")
                    elif level_context['at_resistance'] and direction == 'SELL':
                        reasons.append("[S/R+] At Resistance level")
                    elif level_context['level_alignment'] == 'against':
                        reasons.append("[S/R-] Against key level")
            except Exception:
                pass  # Key levels detection failed, continue without
                
        # MARKET PROFILE ADJUSTMENT: Institutional Value context (NEW!)
        if self.profile_engine and direction:
            try:
                p_ctx = self.profile_engine.get_session_context(df, symbol)
                tp = p_ctx['tpo_profile']
                vp = p_ctx['volume_profile']
                curr_p = p_ctx['current_price']
                
                # 1. Value Area Context
                if direction == 'BUY' and curr_p <= tp['val']:
                    score += 15
                    reasons.append("[PROFILE+] Buying at Value Area Low")
                elif direction == 'SELL' and curr_p >= tp['vah']:
                    score += 15
                    reasons.append("[PROFILE+] Selling at Value Area High")
                
                # 2. POC Context (Institutional acceptance)
                if abs(curr_p - tp['poc']) / curr_p < 0.001:
                    score += 10
                    reasons.append("[PROFILE+] At Market POC")
                    
                if abs(curr_p - vp['vpoc']) / curr_p < 0.001:
                    score += 10
                    reasons.append("[PROFILE+] At Volume POC")
                    
                # 3. Extension Check
                if direction == 'BUY' and curr_p > tp['vah'] and curr_p > vp['vvah']:
                    # Overextended, reduce score unless momentum is very high
                    if curr['RSI'] > 75:
                        score -= 15
                        reasons.append("[PROFILE-] Overextended above Value")
            except Exception:
                pass
                
        # ML SIGNAL FILTERING (NEW!)
        ml_probability = 0.5
        if self.ml_filter and direction:
            # Prepare feature data for ML
            ml_data = {
                'rsi': curr.get('RSI', 50),
                'adx': curr.get('ADX', 20),
                'ema_diff': (curr.get('EMA9', 0) - curr.get('EMA21', 0)) / curr.get('EMA21', 1) if curr.get('EMA21', 0) else 0,
                'atr_pct': curr.get('ATR', 0) / df['close'].iloc[-1],
                'regime': current_regime,
                'direction': direction,
                'score': score,
                'hour': datetime.now().hour,
                'candlestick_score': 0, # To be refined
                'range_position': (curr_p - df['low'].tail(20).min()) / (df['high'].tail(20).max() - df['low'].tail(20).min()) if (df['high'].tail(20).max() - df['low'].tail(20).min()) else 0.5
            }
            
            ml_probability, should_trade = self.ml_filter.predict(ml_data)
            
            if self.ml_filter.is_trained:
                if not should_trade:
                    # ML filter rejects the trade
                    logger.info(f"[ML] Signal Rejected: {symbol} {direction} (Prob: {ml_probability:.2%})")
                    
                    # Record in Ledger
                    self.db.record_decision(
                        symbol=symbol,
                        decision="REJECTED_ML",
                        reason=f"ML Prob {ml_probability:.2%} < threshold",
                        score=score,
                        strategy=detected_strategy_type,
                        metadata={**ml_data, "ml_prob": ml_probability}
                    )
                    return None
                else:
                    reasons.append(f"[ML+] Confirmed (Prob: {ml_probability:.2%})")
        
        
        # ========== FINAL ENFORCEMENT: TREND CONFLICT GUARD ==========
        # If we want to SELL but both 1D and 4H are BULL --> REJECT
        # If we want to BUY but both 1D and 4H are BEAR --> REJECT
        if direction == "SELL" and trend_1d == "BULL" and trend_4h == "BULL":
            logger.warning(f"[MTF GUARD] {symbol} SELL REJECTED: Price in bull trend (1D+4H)")
            self.db.record_decision(
                symbol=symbol,
                decision="REJECTED_MTF_GUARD",
                reason="Attempted to SELL in bull trend",
                score=score,
                strategy=detected_strategy_type,
                metadata={"trend_1d": trend_1d, "trend_4h": trend_4h, "direction": direction}
            )
            return None
        elif direction == "BUY" and trend_1d == "BEAR" and trend_4h == "BEAR":
            logger.warning(f"[MTF GUARD] {symbol} BUY REJECTED: Price in bear trend (1D+4H)")
            self.db.record_decision(
                symbol=symbol,
                decision="REJECTED_MTF_GUARD",
                reason="Attempted to BUY in bear trend",
                score=score,
                strategy=detected_strategy_type,
                metadata={"trend_1d": trend_1d, "trend_4h": trend_4h, "direction": direction}
            )
            return None
        # ================================================================
        
        if direction and score >= self.min_signal_score:
            return {
                "symbol": symbol,
                "direction": direction,
                "score": score,
                "reasons": reasons,
                "ml_prob": ml_probability,
                "atr": curr['ATR'],
                "price": curr['close'],
                "regime": current_regime,
                "strategy_type": detected_strategy_type,
                "risk_multiplier": regime_risk_mult
            }
        
        # Log skipped signals (low score)
        if direction:
            self.db.record_decision(
                symbol=symbol,
                decision="SKIPPED_LOW_SCORE",
                reason=f"Score {score} < {self.min_signal_score}",
                score=score,
                strategy=detected_strategy_type,
                metadata={"reasons": reasons, "ml_prob": ml_probability}
            )
        
        return None
    
    def execute_signal(self, signal):
        """Execute a trade signal with regime-aware risk"""
        symbol = signal["symbol"]
        direction = signal["direction"]
        score = signal["score"]
        atr = signal["atr"]
        regime = signal.get("regime", "UNKNOWN")
        strategy_type = signal.get("strategy_type", "Unknown")
        regime_risk_mult = signal.get("risk_multiplier", 1.0)
        
        logger.info("")
        logger.info("=" * 40)
        logger.info(f"[SIGNAL] {symbol} {direction} (Score: {score})")
        logger.info(f"Strategy: {strategy_type} | Regime: {regime}")
        logger.info("Reasons: " + ", ".join(signal["reasons"]))
        
        # Get symbol info
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not info or not tick:
            logger.error("Cannot get symbol info")
            return False
        
        # Calculate position size (5% risk, adjusted by regime)
        acc = mt5.account_info()
        base_risk = acc.equity * self.risk_percent
        risk_amount = base_risk * regime_risk_mult  # Apply regime adjustment
        sl_distance = atr * 2
        
        if regime_risk_mult != 1.0:
            logger.info(f"[REGIME] Risk adjusted: {regime_risk_mult:.1f}x (${base_risk:.0f} -> ${risk_amount:.0f})")
        
        # Estimate pip value (rough)
        if "USD" in symbol and symbol.endswith("USD"):
            pip_value = 1  # Crypto/Commodity vs USD
        elif "JPY" in symbol:
            pip_value = 0.01 * 100000 / 100  # JPY pairs
        else:
            pip_value = 10  # Standard forex ~$10/pip per lot
        
        # Calculate position size with PROFESSIONAL MINIMUM
        risk_amount = acc.balance * (self.risk_percent * regime_risk_mult)
        stop_distance_price = atr * 1.5
        contract_size = info.trade_contract_size if info.trade_contract_size > 0 else 1 # Default to 1 if not available
        
        lot_size = risk_amount / (stop_distance_price * contract_size) if stop_distance_price > 0 else 0.1
        
        # === PROFESSIONAL MINIMUM ENFORCEMENT ===
        if lot_size < self.min_position_size:
            logger.warning(f"[SIZE] Calculated {lot_size:.2f} lots < minimum {self.min_position_size}")
            lot_size = self.min_position_size
            logger.info(f"[SIZE] Enforced minimum: {self.min_position_size} lots")
        
        # Round and cap
        lot_size = round(lot_size, 2)
        lot_size = max(info.volume_min, min(lot_size, info.volume_max)) # Ensure within broker limits
        lot_size = min(lot_size, 10.0)  # Max 10 lots per trade
        
        logger.info(f"[RISK] Lot Size: {lot_size} (Risk: ${risk_amount:.2f}, ATR Stop: {stop_distance_price:.5f})")
        
        # Set entry, SL, TP
        if signal.get("is_mission"):
            # Use AI Mission Levels
            price = signal["price"] 
            sl = signal["sl"]
            tp = signal["tp"]
            # Map "BULLISH" to BUY, "BEARISH" to SELL
            direction = "BUY" if "BULL" in signal["direction"] else "SELL"
            order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        elif direction == "BUY":
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
        """Manage all open positions with Adaptive context awareness."""
        positions = mt5.positions_get()
        if not positions:
            return

        # Prepare market context for the manager
        market_scans = []
        managed_symbols = set(p.symbol for p in positions if p.magic == 888888)
        
        for symbol in managed_symbols:
            try:
                # Use current M5/H1 data to determine context (simple version)
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
                if rates is not None:
                    df = pd.DataFrame(rates)
                    # Current bias based on SMA20 (simple heuristic for de-sync detection)
                    sma20 = df['close'].rolling(20).mean().iloc[-1]
                    current_price = df['close'].iloc[-1]
                    bias = 'BULLISH' if current_price > sma20 else 'BEARISH'
                    
                    market_scans.append({
                        'symbol': symbol,
                        'bias': bias,
                        'regime': {'current': self.current_regimes.get(symbol, 'UNKNOWN')}
                    })
            except Exception:
                pass

        # Apply tiered protection + Adaptive Exits
        self.trade_manager.monitor_active_trades(market_scans=market_scans)
    
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
