import MetaTrader5 as mt5
import logging
import time
import pandas as pd
import json
import os
from datetime import datetime
from titan_system.portfolio.risk_engine import RiskEngine

logger = logging.getLogger("Titan.Execution")

class MT5Executor:
    """
    Handles interactions with MT5 Terminal, enforcing Risk Checks.
    """
    def __init__(self, risk_engine: RiskEngine = None):
        self.connected = False
        self.risk_engine = risk_engine if risk_engine else RiskEngine()
        
    def connect(self) -> bool:
        """Connects to MT5."""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 Init Failed: {mt5.last_error()}")
                return False
            
            self.connected = True
            logger.info("CONNECTED to MetaTrader 5")
            return True
        except Exception as e:
            logger.critical(f"MT5 Connection Error: {e}")
            return False

    def shutdown(self):
        mt5.shutdown()
        self.connected = False

    def get_account_info(self):
        if not self.connected: return {}
        info = mt5.account_info()
        if not info: return {}
        return info._asdict()

    def execute_order(self, symbol, order_type, lot, sl_points=500, tp_points=1000, comment=""):
        """
        Main execution method with built-in Risk Engine, Spread Guard, Volatility Targeting, and News Shield.
        """
        if not self.connected:
            if not self.connect(): return None

        # 0. News Shield (Phase 12)
        if not self.check_news_shield(symbol):
            logger.warning(f"[NEWS SHIELD] Blocking trade on {symbol} due to upcoming high-impact news.")
            return None

        # 0.1 Spread Guard (TCA Audit Integration) - Dynamic by symbol type
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger.error(f"Execution Failed: Symbol {symbol} not found.")
            return None
            
        current_spread = symbol_info.spread
        
        # Dynamic spread limits based on instrument type
        if "BTC" in symbol or "ETH" in symbol or "XRP" in symbol:
            max_allowed_spread = 10000  # Crypto has wider spreads
        elif "US5" in symbol or "US3" in symbol or "USTEC" in symbol or "GER" in symbol:
            max_allowed_spread = 500  # Indices
        elif "XAU" in symbol or "GOLD" in symbol:
            max_allowed_spread = 100  # Gold
        else:
            max_allowed_spread = 50  # Forex
        
        if current_spread > max_allowed_spread:
            logger.warning(f"[SPREAD GUARD] {symbol} spread too high ({current_spread} pts). Max: {max_allowed_spread}. ABORTING.")
            return None


        # 0.2 Volatility Targeting (Phase 11)
        vol_multiplier = self.calculate_volatility_multiplier(symbol)
        adjusted_lot = round(lot * vol_multiplier, 2)
        if adjusted_lot < 0.01: adjusted_lot = 0.01

        # 1. RISK CHECK
        account = self.get_account_info()
        capital = account.get('equity', 0.0)
        balance = account.get('balance', 0.0)
        
        if self.risk_engine:
            self.risk_engine.update_drawdown(capital, balance)
            # Approx notional value validation
            if not self.risk_engine.check_trade(symbol, adjusted_lot * 100000, capital): 
                 logger.warning(f"[RISK] Trade REJECTED by Risk Engine: {symbol} {adjusted_lot} lots")
                 return None

        # 2. PREPARE ORDER
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)
        
        point = symbol_info.point
        tick = mt5.symbol_info_tick(symbol)
        if not tick: return None
        
        if order_type == 'BUY':
            mt5_action = mt5.ORDER_TYPE_BUY
            price = tick.ask
            sl = price - (sl_points * point)
            tp = price + (tp_points * point)
        elif order_type == 'SELL':
            mt5_action = mt5.ORDER_TYPE_SELL
            price = tick.bid
            sl = price + (sl_points * point)
            tp = price - (tp_points * point)
        else:
            return None

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(adjusted_lot),
            "type": mt5_action,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20,
            "magic": 234001,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # 3. SEND
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order Send Failed: {result.retcode} ({result.comment})")
            return None
            
        logger.info(f"[EXEC] Trade Executed: {symbol} {adjusted_lot} lots @ {result.price} (Vol Mult: {vol_multiplier})")
        return result._asdict()

    def check_news_shield(self, symbol) -> bool:
        """
        Institutional News Shield: Blocks trades +/- 30 mins from high-impact news.
        """
        schedule_path = "MACRO_SCHEDULE.json"
        if not os.path.exists(schedule_path):
            return True # No schedule, proceed (or log warning)

        try:
            with open(schedule_path, "r") as f:
                events = json.load(f)
        except Exception:
            return True

        now = datetime.now()
        
        # Determine the currency group for the symbol (e.g. XAUUSD -> USD)
        # Simplified logic:
        symbol_group = None
        if "USD" in symbol: symbol_group = "USD"
        elif "EUR" in symbol: symbol_group = "EUR"
        elif "GBP" in symbol: symbol_group = "GBP"
        elif "JPY" in symbol: symbol_group = "JPY"
        elif "CAD" in symbol: symbol_group = "CAD"
        elif "AUD" in symbol: symbol_group = "AUD"
        elif "CHF" in symbol: symbol_group = "CHF"
        elif "NZD" in symbol: symbol_group = "NZD"

        for e in events:
            if e['impact'] != "HIGH": continue
            
            # If the event is for the pair's currency or is a major USD event
            if e['symbol_group'] == symbol_group or e['symbol_group'] == "USD":
                event_time = datetime.strptime(e['time_ist'], "%Y-%m-%d %H:%M:%S")
                diff = abs((event_time - now).total_seconds() / 60)
                
                if diff < 30: # Within 30 minutes
                    return False
        
        return True

    def calculate_volatility_multiplier(self, symbol) -> float:
        """
        Institutional Volatility Targeting: Reduces lot size if ATR is extreme.
        """
        # Fetch H1 data (last 100 bars)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None or len(rates) < 20:
            return 1.0 # Default
            
        df = pd.DataFrame(rates)
        # Using simple range (High-Low) as ATR proxy for speed
        df['range'] = df['high'] - df['low']
        current_atr = df['range'].iloc[-1]
        historical_atr = df['range'].mean()
        
        if current_atr > 2 * historical_atr:
            logger.warning(f"[VOL TARGETING] High Volatility detected on {symbol}. Reducing lot size by 50%.")
            return 0.5
        elif current_atr < 0.3 * historical_atr:
            logger.warning(f"[VOL TARGETING] Thin liquidity detected on {symbol}. Reducing lot size by 50%.")
            return 0.5
            
        return 1.0
