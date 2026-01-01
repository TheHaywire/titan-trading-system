
import MetaTrader5 as mt5
import os
import time
import logging
import pandas as pd

logger = logging.getLogger("Titan.Execution")

class MT5Execution:
    """
    Handles all direct interactions with the MetaTrader 5 Terminal.
    This is the ONLY class allowed to touch mt5.* functions.
    """
    def __init__(self, config):
        self.config = config
        self.connected = False
        self.account_info = None

    def connect(self) -> bool:
        """Attempts to connect to MT5 with robust path searching."""
        try:
            # Check if MetaTrader is already running first
            if mt5.initialize():
                logger.info("✅ Hooked into existing MT5 Terminal")
            else:
                # Need to launch it. Try explicit paths.
                paths = [
                    self.config.MT5_PATH + r"\terminal64.exe" if hasattr(self.config, 'MT5_PATH') else None,
                    r"C:\Program Files\MetaTrader 5\terminal64.exe",
                    r"C:\Program Files\XM Global MT5\terminal64.exe"
                ]
                
                success = False
                for path in paths:
                    if path and os.path.exists(path):
                        logger.info(f"🚀 Launching MT5 from: {path}")
                        if mt5.initialize(path=path):
                            success = True
                            # Wait for terminal to warmup
                            time.sleep(5) 
                            break
                            
                if not success:
                    # Last ditch: try basic init one more time
                    if not mt5.initialize():
                        logger.error(f"MT5 Init Failed: {mt5.last_error()}")
                        return False
            
            if not mt5.terminal_info():
                 logger.error(f"MT5 Init Failed (No Terminal Info): {mt5.last_error()}")
                 return False

            # Login if credentials provided
            # Note: MT5 allows 'offline' login if market is closed, as long as credentials serve correct
            if self.config.mt5_login:
                authorized = mt5.login(
                    login=self.config.mt5_login, 
                    password=self.config.mt5_password, 
                    server=self.config.mt5_server
                )
                if not authorized:
                    logger.error(f"MT5 Login Failed: {mt5.last_error()}")
                    # We continue even if login fails, as we might be able to read charts but not trade
                    # But for a bot, we return False to be safe
                    return False
            
            # Ensure symbols are available in Market Watch
            # This is critical for data fetching even when market is closed
            if hasattr(self.config, 'trading_symbols'):
                for symbol in self.config.trading_symbols:
                    selected = mt5.symbol_select(symbol, True)
                    if not selected:
                        logger.warning(f"Could not select {symbol} in Market Watch")
            
            self.connected = True
            logger.info(f"✅ Connected to MetaTrader 5 (Account: {self.config.mt5_login})")
            return True

        except Exception as e:
            logger.critical(f"MT5 Critical Connection Error: {e}")
            return False

    def shutdown(self):
        mt5.shutdown()
        self.connected = False

    def get_account_info(self):
        """Unified account info for circuit breaker and engine."""
        if not self.connected: 
            return {}
        
        info = mt5.account_info()
        positions = self.get_positions()
        
        if not info: 
            return {}
            
        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "leverage": info.leverage,
            "currency": info.currency,
            "positions": positions
        }

    def get_account_summary(self):
        """Backwards compatibility alias"""
        return self.get_account_info()

    def get_positions(self):
        if not self.connected:
            return []
        
        positions = mt5.positions_get()
        if not positions:
            return []
            
        return [pos._asdict() for pos in positions]

    def get_data(self, symbol, timeframe, n_candles):
        """Fetch raw candles as DataFrame with Latency Monitoring."""
        if not self.connected: return None
        
        # Latency Monitoring: Start
        start_time = time.time()
        
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_candles)
        
        # Latency Monitoring: End
        ipc_rtt = (time.time() - start_time) * 1000
        if ipc_rtt > 50:
            logger.warning(f"🐢 High IPC Latency detected for {symbol}: {ipc_rtt:.2f}ms")

        if rates is None or len(rates) == 0:
            err = mt5.last_error()
            if err[0] == 10027: # Trade Closed / Market Closed
                logger.debug(f"ℹ️ {symbol}: Market currently closed (Error 10027).")
            else:
                logger.warning(f"⚠️ {symbol}: Failed to fetch data. Error: {err}")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Map tick_volume to volume for TA library
        if 'tick_volume' in df.columns:
            df['volume'] = df['tick_volume']
        elif 'real_volume' in df.columns:
            df['volume'] = df['real_volume']
        
        return df
        
    def normalize_volume(self, symbol: str, volume: float) -> float:
        """
        Normalize volume to meet symbol constraints (step, min, max) 
        and Institutional Max Cap (2.0 lots).
        """
        if not self.connected: return volume
        
        # Institutional Hard Cap (Based on 17k trade analysis)
        MAX_INSTITUTIONAL_LOTS = 2.0
        if volume > MAX_INSTITUTIONAL_LOTS:
            logger.warning(f"⚠️ {symbol}: Volume {volume} exceeds Institutional Cap ({MAX_INSTITUTIONAL_LOTS}). Capping to 2.0.")
            volume = MAX_INSTITUTIONAL_LOTS
            
        info = mt5.symbol_info(symbol)
        if not info: return volume
        
        step = info.volume_step
        min_vol = info.volume_min
        max_vol = info.volume_max
        
        # 1. Round to nearest step
        if step > 0:
            vol = round(volume / step) * step
        else:
            vol = volume
            
        # 2. Clamp
        vol = max(min_vol, min(vol, max_vol))
        
        # 3. Precision fix (avoid 0.100000001)
        # Assuming max 2 decimals for lots usually, but using string formatting is safer
        # or round to number of decimals in step
        import math
        decimals = 0
        if "." in str(step):
            decimals = len(str(step).split(".")[1].rstrip("0"))
            
        return round(vol, decimals)


    def execute_order(self, symbol, order_type, volume, sl_pips=50, tp_pips=100, comment="Titan"):
        """
        Executes a market order with TCA (Transaction Cost Analysis) tracking.
        
        Args:
            symbol (str): Trading pair
            order_type (str): 'BUY' or 'SELL'
            volume (float): Lot size
            sl_pips (int): Stop Loss in pips
            tp_pips (int): Take Profit in pips
        """
        if not self.connected:
            return None

        # TCA: Start Timer
        import time as time_module
        tca_start = time_module.time()

        # 0. Validate & Normalize Symbol Constraints
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
             logger.error(f"Failed to get symbol info for {symbol}")
             return None
             
        # Normalize allowed volume
        final_volume = self.normalize_volume(symbol, float(volume))
        
        if final_volume < symbol_info.volume_min:
             logger.warning(f"❌ {symbol}: Volume {volume} too small (Min: {symbol_info.volume_min}). Trade Aborted.")
             return None

        # 1. Get current price (TCA: Expected Price)
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger.error(f"Failed to get tick for {symbol}")
            return None
            
        point = symbol_info.point
        
        # TCA: Capture Expected Metrics
        tca_expected_spread = (tick.ask - tick.bid) / point
        
        if order_type == 'BUY':
            mt5_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
            tca_expected_price = tick.ask
            sl = price - (sl_pips * point * 10) 
            tp = price + (tp_pips * point * 10)
        elif order_type == 'SELL':
            mt5_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
            tca_expected_price = tick.bid
            sl = price + (sl_pips * point * 10)
            tp = price - (tp_pips * point * 10)
        else:
            logger.error(f"Unknown order type: {order_type}")
            return None
     
        # 2. Prepare Request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": final_volume,
            "type": mt5_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": self.config.MAX_SLIPPAGE_POINTS if hasattr(self.config, 'MAX_SLIPPAGE_POINTS') else 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        
        # Policy: Max Deviation Enforcement (EPIC-09)
        max_allowed_slippage = request["deviation"]
        logger.debug(f"⚡ [EXECUTION POLICY] Symbol: {symbol} | Max Slippage Allowed: {max_allowed_slippage} points")
        
        # Filling Mode Logic (Robust)
        filling_modes = symbol_info.filling_mode
        
        # Priority: IOC > FOK > RETURN (Default)
        if filling_modes & 2: # IOC Supported
            request["type_filling"] = mt5.ORDER_FILLING_IOC
        elif filling_modes & 1: # FOK Supported
            request["type_filling"] = mt5.ORDER_FILLING_FOK
        else:
             # Fallback to RETURN (Market Execution default)
            request["type_filling"] = mt5.ORDER_FILLING_RETURN

        # 3. Send Order with Retry Logic
        max_retries = 3
        for attempt in range(max_retries):
            # Refresh price before each attempt
            if attempt > 0:
                time.sleep(0.5)
                tick = mt5.symbol_info_tick(symbol)
                if not tick: continue
                
                # Update Request Price
                if order_type == 'BUY':
                    request['price'] = tick.ask
                    request['sl'] = float(tick.ask - (sl_pips * point * 10))
                    request['tp'] = float(tick.ask + (tp_pips * point * 10))
                elif order_type == 'SELL':
                    request['price'] = tick.bid
                    request['sl'] = float(tick.bid + (sl_pips * point * 10))
                    request['tp'] = float(tick.bid - (tp_pips * point * 10))

            result = mt5.order_send(request)
            
            if result is None:
                logger.error("Order send failed (result is None)")
                continue
                
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                break # Success
            elif result.retcode in [mt5.TRADE_RETCODE_REQUOTE, mt5.TRADE_RETCODE_PRICE_OFF]:
                logger.warning(f"Order Requote/Price Off ({result.retcode}). Retrying... ({attempt+1}/{max_retries})")
                continue
            else:
                logger.error(f"Order failed: {result.retcode} ({result.comment})")
                # TCA: Log Failed Execution
                self._log_tca_failure(symbol, order_type, tca_expected_price, result.retcode, result.comment)
                return None
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed after {max_retries} retries.")
            return None
        
        # TCA: Calculate Metrics
        tca_end = time_module.time()
        tca_latency_ms = (tca_end - tca_start) * 1000
        tca_fill_price = result.price
        
        # Calculate Slippage (in pips)
        tca_slippage_pips = abs(tca_fill_price - tca_expected_price) / point
        
        # Get Spread at Fill Time
        tick_after = mt5.symbol_info_tick(symbol)
        tca_actual_spread = (tick_after.ask - tick_after.bid) / point if tick_after else tca_expected_spread
        
        # TCA: Log to Sheet
        self._log_tca_execution(
            ticket=result.order,
            symbol=symbol,
            side=order_type,
            expected_price=tca_expected_price,
            fill_price=tca_fill_price,
            slippage_pips=tca_slippage_pips,
            expected_spread=tca_expected_spread,
            actual_spread=tca_actual_spread,
            latency_ms=tca_latency_ms
        )
            
        # 4. Return formatted result
        return {
            "id": str(result.order), 
            "ticket": result.order,
            "symbol": symbol,
            "type": order_type,
            "volume": volume,
            "open_price": result.price,
            "sl": sl,
            "tp": tp,
            "open_time": pd.Timestamp.now().isoformat(),
            "magic": request['magic'],
            "comment": comment,
            "strategy_name": "TrendSurfer" # Hardcoded for now
        }

    def modify_position(self, ticket, sl=None, tp=None):
        """
        Modifies an existing position's SL and TP.
        Used for Break-Even and Trailing Stop logic.
        """
        if not self.connected: return False

        # Get existing position to keep price/symbol
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger.warning(f"⚠️ Position {ticket} not found for modification.")
            return False
        
        pos = positions[0]
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": pos.symbol,
            "position": ticket,
            "sl": float(sl) if sl is not None else pos.sl,
            "tp": float(tp) if tp is not None else pos.tp,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"❌ Failed to modify position {ticket}: {result.retcode} ({result.comment})")
            return False
            
        logger.info(f"✅ Modified Position {ticket}: SL={sl}, TP={tp}")
        return True

    def close_partial(self, ticket, volume_to_close):
        """
        Closes a portion of an existing position.
        Used for 'Seed Money' profit locking (Section 11/12).
        """
        if not self.connected: return False

        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger.warning(f"⚠️ Position {ticket} not found for partial close.")
            return False
            
        pos = positions[0]
        symbol = pos.symbol
        
        # Determine closing side
        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask

        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume_to_close),
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Titan-PartialClose",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"❌ Failed to partial close {ticket}: {result.retcode} ({result.comment})")
            return False
            
        logger.info(f"✅ Partial Close {ticket}: {volume_to_close} lots closed.")
        return True
    
    def _log_tca_execution(self, ticket, symbol, side, expected_price, fill_price, slippage_pips, expected_spread, actual_spread, latency_ms):
        """Log successful execution TCA metrics to Google Sheets."""
        try:
            from titan_system.integrations.google_sheets import TitanSheets
            sheets = TitanSheets()
            if not sheets.enabled:
                return
            
            ws = sheets.sheet.worksheet("TCA ANALYSIS")
            now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row = [
                ticket,
                now,
                symbol,
                side,
                f"{expected_price:.5f}",
                f"{fill_price:.5f}",
                f"{slippage_pips:.2f}",
                f"{expected_spread:.1f}",
                f"{actual_spread:.1f}",
                f"{latency_ms:.0f}",
                "✅ FILLED"
            ]
            ws.append_row(row)
        except Exception as e:
            logger.error(f"TCA Logging Failed: {e}")
    
    def _log_tca_failure(self, symbol, side, expected_price, retcode, comment):
        """Log failed execution attempts to TCA tab."""
        try:
            from titan_system.integrations.google_sheets import TitanSheets
            sheets = TitanSheets()
            if not sheets.enabled:
                return
            
            ws = sheets.sheet.worksheet("TCA ANALYSIS")
            now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row = [
                "N/A",
                now,
                symbol,
                side,
                f"{expected_price:.5f}",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                f"❌ FAILED ({retcode}: {comment})"
            ]
            ws.append_row(row)
        except Exception as e:
            logger.error(f"TCA Failure Logging Failed: {e}")
