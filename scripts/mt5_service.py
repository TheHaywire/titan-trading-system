"""
MT5 SERVICE
===========
Encapsulates all MetaTrader 5 interactions.
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MT5Service:
    def __init__(self, login=None, password=None, server=None, path=None):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.connected = False

    def connect(self):
        """Initialize connection to MT5 terminal."""
        if self.connected:
            return True

        # Try initializing with parameters if provided, otherwise try default
        init_params = {}
        if self.path: init_params['path'] = self.path
        if self.login: init_params['login'] = self.login
        if self.password: init_params['password'] = self.password
        if self.server: init_params['server'] = self.server

        if not mt5.initialize(**init_params):
            logger.error(f"MT5 initialization failed, error code: {mt5.last_error()}")
            return False

        logger.info("MT5 initialized successfully.")
        self.connected = True
        return True

    def disconnect(self):
        """Shutdown MT5 connection."""
        mt5.shutdown()
        self.connected = False
        logger.info("MT5 connection closed.")

    def get_market_watch_symbols(self):
        """Get list of symbols currently in Market Watch."""
        self.connect()
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        # Filter for symbols that are visible in Market Watch
        return [s.name for s in symbols if s.visible]

    def get_prices(self, symbols: list):
        """Fetch current bid/ask/last prices for a list of symbols."""
        self.connect()
        prices = {}
        for symbol in symbols:
            it = mt5.symbol_info_tick(symbol)
            if it:
                prices[symbol] = {
                    "bid": it.bid,
                    "ask": it.ask,
                    "last": it.last,
                    "time": it.time,
                    "spread": it.ask - it.bid
                }
        return prices

    def get_positions(self):
        """Fetch current open positions."""
        self.connect()
        positions = mt5.positions_get()
        if positions is None:
            return []
        
        # Convert to list of dicts
        pos_list = []
        for p in positions:
            pos_list.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": p.volume,
                "price_open": p.price_open,
                "price_current": p.price_current,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "magic": p.magic,
                "comment": p.comment
            })
        return pos_list

    def get_account_info(self):
        """Fetch account metrics."""
        self.connect()
        acc = mt5.account_info()
        if acc is None:
            return None
        
        return {
            "login": acc.login,
            "balance": acc.balance,
            "equity": acc.equity,
            "margin": acc.margin,
            "margin_free": acc.margin_free,
            "margin_level": acc.margin_level,
            "profit": acc.profit,
            "currency": acc.currency
        }

    def get_ohlc(self, symbol, timeframe=mt5.TIMEFRAME_M1, count=100):
        """Fetch recent OHLC data."""
        self.connect()
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            return None
        return pd.DataFrame(rates)

    def place_order(self, symbol, order_type, volume, sl=None, tp=None, comment="Titan Auto"):
        """
        Execute a market order.
        order_type: 'BUY' or 'SELL'
        """
        self.connect()
        
        # Symbol info for filling order
        info = mt5.symbol_info(symbol)
        if not info:
            logger.error(f"Symbol {symbol} not found")
            return None
            
        action_type = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
        price = info.ask if order_type == "BUY" else info.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": action_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if sl: request["sl"] = float(sl)
        if tp: request["tp"] = float(tp)
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.comment}")
            return None
            
        logger.info(f"Order executed: {result.order}")
        return result._asdict()

    def close_all_positions(self):
        """PANIC: Close all open positions immediately."""
        self.connect()
        positions = self.get_positions()
        closed_count = 0
        
        for pos in positions:
            tick = mt5.symbol_info_tick(pos['symbol'])
            type_close = mt5.ORDER_TYPE_SELL if pos['type'] == "BUY" else mt5.ORDER_TYPE_BUY
            price = tick.bid if type_close == mt5.ORDER_TYPE_SELL else tick.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos['symbol'],
                "volume": pos['volume'],
                "type": type_close,
                "position": pos['ticket'],
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "PANIC CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
                
        logger.warning(f"PANIC: Closed {closed_count}/{len(positions)} positions.")
        return closed_count

if __name__ == "__main__":
    # Test block
    service = MT5Service()
    if service.connect():
        print("--- Account Info ---")
        print(service.get_account_info())
        
        print("\n--- Market Watch Symbols ---")
        print(service.get_market_watch_symbols()[:10])
        
        print("\n--- Open Positions ---")
        print(service.get_positions())
        
        service.disconnect()
    else:
        print("Failed to connect to MT5.")
