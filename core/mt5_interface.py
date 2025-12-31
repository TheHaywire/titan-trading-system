import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import config

class MT5Interface:
    def __init__(self):
        self.connected = False

    def start(self):
        """Initializes and logs into the MT5 platform."""
        # Attempt standard init
        if not mt5.initialize():
            print(f"Standard init failed, trying specific paths...")
            # Try common paths if standard fails
            paths = [
                r"C:\Program Files\MetaTrader 5\terminal64.exe",
                r"C:\Program Files\XM Global MT5\terminal64.exe",
                r"C:\Program Files (x86)\XM Global MT5\terminal64.exe"
            ]
            for path in paths:
                import os
                if os.path.exists(path):
                    print(f"Found MT5 at: {path}")
                    if mt5.initialize(path=path):
                        break
            
            if not mt5.initialize(): # Final check
                print(f"❌ FATAL: MetaTrader5 initialization failed. Error: {mt5.last_error()}")
                return False

        current_account = mt5.account_info()
        
        # Check if already connected to the correct account
        if current_account and current_account.login == config.MT5_LOGIN:
             print(f"Already connected to account: {config.MT5_LOGIN}")
             self.connected = True
             return True

        authorized = mt5.login(config.MT5_LOGIN, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
        if authorized:
            print(f"Connected to account #{config.MT5_LOGIN}")
            self.connected = True
            return True
        else:
            print(f"Failed to connect to account #{config.MT5_LOGIN}, error code: {mt5.last_error()}")
            self.connected = False
            return False

    def shutdown(self):
        mt5.shutdown()
        self.connected = False

    def get_latency(self):
        """Returns the last ping to the server in milliseconds."""
        if not self.connected:
            return -1
        
        info = mt5.terminal_info()
        if info:
             # ping_last is in microseconds, convert to ms
             return round(info.ping_last / 1000)
        return 0

    def get_symbol_info(self, symbol):
        if not self.connected:
            return None
        return mt5.symbol_info(symbol)

    def get_closes(self, symbol, timeframe, num_candles=100):
        """
        Retrieves historical close prices.
        timeframe: e.g., mt5.TIMEFRAME_H1
        """
        if not self.connected:
            return None
        
        # Retry mechanism
        for attempt in range(2):
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
            
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df
            
            # If failed, try to select symbol again and check error
            err = mt5.last_error()
            if err[0] == -10004: # IPC Connection lost
                print("Lost connection to MT5 (IPC), attempting reconnect...")
                self.start()
                continue # Retry loop

            if attempt == 0: # Only log on first failure if we retry
                 # Try selecting if not custom
                 if not mt5.symbol_select(symbol, True):
                     pass 
        
        # Final failure after retries
        # Only log if it's a real error, not just "not found"
        print(f"Failed to get rates for {symbol} (Error: {mt5.last_error()})")
        return None

    def place_market_order(self, symbol, volume, order_type):
        """
        Places a market order.
        order_type: mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL
        """
        if not self.connected:
            return None

        symbol_info = self.get_symbol_info(symbol)
        if symbol_info is None:
            print(f"{symbol} not found")
            return None

        if not symbol_info.visible:
            print(f"{symbol} is not visible, trying to select it")
            if not mt5.symbol_select(symbol, True):
                print(f"symbol_select({symbol}) failed")
                return None
        
        price = symbol_info.ask if order_type == mt5.ORDER_TYPE_BUY else symbol_info.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        print(f"Order send result: {result}")
        return result
