"""
INSTITUTIONAL AUTO-TRADER
=========================
Automated trading bot using all advanced features:
- Generates entry signals (breakout/pullback/reversion/scalp)
- Places trades with exact entry/stop/TP levels
- Manages positions (scale out, trail stops)
- Logs all decisions

Run: python scripts/auto_trader.py
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
from pathlib import Path

from titan_system.features.quant_features import QuantFeatureEngine
from titan_system.features.advanced_features import AdvancedQuantEngine
from scripts.generate_all_entries import UniversalEntryGenerator, EntrySignal


class InstitutionalAutoTrader:
    """Automated trader using advanced feature signals."""
    
    def __init__(self, symbols: list, timeframe, min_confidence: float = 70, 
                 base_lot_size: float = 0.01, max_trades: int = 3):
        self.symbols = symbols
        self.timeframe = timeframe
        self.min_confidence = min_confidence
        self.base_lot_size = base_lot_size
        self.max_trades = max_trades
        
        self.log_file = Path("trade_log_auto.txt")
        
    def log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] {message}"
        print(msg)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    
    def get_data(self, symbol: str, bars: int = 500) -> pd.DataFrame:
        """Fetch OHLCV from MT5."""
        rates = mt5.copy_rates_from_pos(symbol, self.timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.rename(columns={'tick_volume': 'volume'}, inplace=True)
        return df
    
    def get_open_positions(self, symbol: str = None) -> list:
        """Get current open positions."""
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        return list(positions) if positions else []
    
    def place_trade(self, signal: EntrySignal, symbol: str) -> bool:
        """Place trade based on signal."""
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.log(f"ERROR: Symbol {symbol} not found")
            return False
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                self.log(f"ERROR: Failed to select {symbol}")
                return False
        
        # Get account balance
        account_info = mt5.account_info()
        account_balance = account_info.balance
        
        # Calculate proper lot size based on RISK
        risk_percent = 1.0  # Risk 1% per trade
        dollar_risk = account_balance * (risk_percent / 100.0)
        
        stop_distance = abs(signal.entry_price - signal.stop_loss)
        
        # Calculate lot size
        contract_size = symbol_info.trade_contract_size
        point = symbol_info.point
        
        # For different asset classes
        if "USD" in symbol or "EUR" in symbol or "GBP" in symbol or "JPY" in symbol:
            # Forex - use pip value
            pip_value = 10  # Standard for 1 lot
            pips_at_risk = stop_distance / point / 10
            lots = dollar_risk / (pips_at_risk * pip_value) if pips_at_risk > 0 else 0.01
        else:
            # Indices/Crypto - use contract size
            lots = dollar_risk / (stop_distance * contract_size) if stop_distance > 0 else 0.01
        
        # Apply Kelly/feature multiplier
        lots *= signal.position_size_multiplier
        
        # Round to step
        lot_step = symbol_info.volume_step
        lots = round(lots / lot_step) * lot_step
        
        # Apply limits
        lots = max(symbol_info.volume_min, min(lots, symbol_info.volume_max))
        
        # Prepare request
        order_type = mt5.ORDER_TYPE_BUY if signal.direction == "LONG" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if signal.direction == "LONG" else mt5.symbol_info_tick(symbol).bid
        
        point = symbol_info.point
        
        # Stop loss and take profit
        sl = signal.stop_loss
        tp = signal.take_profit_1  # Use TP1 for initial target
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lots,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234567,  # Institutional Auto-Trader magic number
            "comment": f"{signal.entry_type}_{signal.direction}_{signal.confidence:.0f}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log(f"ERROR: Order failed - {result.comment}")
            return False
        
        # Calculate position value
        position_value = lots * contract_size if contract_size > 0 else lots * price
        
        self.log(f"[OK] TRADE PLACED: {symbol}")
        self.log(f"  Type: {signal.entry_type} {signal.direction}")
        self.log(f"  Confidence: {signal.confidence:.0f}/100")
        self.log(f"  Entry: ${price:.2f}")
        self.log(f"  Stop: ${sl:.2f}")
        self.log(f"  TP1: ${tp:.2f}")
        self.log(f"  Lots: {lots:.2f}")
        self.log(f"  Position Value: ${position_value:,.0f}")
        self.log(f"  Risk: ${dollar_risk:,.2f} ({risk_percent}%)")
        self.log(f"  R:R: 1:{signal.risk_reward:.1f}")
        self.log(f"  Reasoning:")
        for reason in signal.reasoning:
            self.log(f"    - {reason}")
        
        return True
    
    def manage_positions(self):
        """Manage open positions (scale out, trail stops)."""
        positions = self.get_open_positions()
        
        for pos in positions:
            symbol = pos.symbol
            ticket = pos.ticket
            
            # Get current data
            df = self.get_data(symbol, bars=100)
            if df is None:
                continue
            
            # Compute features for management decisions
            basic = QuantFeatureEngine.compute_all(df)
            latest = basic.iloc[-1]
            
            close = latest['close']
            kalman = latest.get('kalman_trend', close)  # If advanced features available
            bb_percentile = latest['bb_percentile']
            accel = latest['price_accel']
            
            # Get position details
            entry_price = pos.price_open
            current_sl = pos.sl
            current_tp = pos.tp
            profit_pips = pos.profit
            is_long = pos.type == mt5.ORDER_TYPE_BUY
            
            # Calculate profit in R
            risk = abs(entry_price - current_sl)
            if risk > 0:
                profit_r = (close - entry_price) / risk if is_long else (entry_price - close) / risk
            else:
                profit_r = 0
            
            # MANAGEMENT RULES
            modified = False
            
            # Rule 1: Scale out 50% at 2R
            if profit_r >= 2.0 and pos.volume > self.base_lot_size:
                # Partially close
                close_volume = pos.volume / 2
                self.log(f"[SCALE] OUT {symbol} - Taking 50% profit at 2R")
                self.partial_close(ticket, close_volume)
                modified = True
            
            # Rule 2: Trail stop to breakeven at 1R
            if profit_r >= 1.0 and current_sl != entry_price:
                new_sl = entry_price
                self.log(f"[BE] MOVING TO BE {symbol} - SL to ${new_sl:.2f}")
                self.modify_position(ticket, new_sl, current_tp)
                modified = True
            
            # Rule 3: Trail with Kalman line if in profit
            if profit_r > 1.5 and not modified:
                if is_long and kalman > current_sl:
                    new_sl = kalman
                    self.log(f"[TRAIL] LONG {symbol} - SL to Kalman ${new_sl:.2f}")
                    self.modify_position(ticket, new_sl, current_tp)
                elif not is_long and kalman < current_sl:
                    new_sl = kalman
                    self.log(f"[TRAIL] SHORT {symbol} - SL to Kalman ${new_sl:.2f}")
                    self.modify_position(ticket, new_sl, current_tp)
            
            # Rule 4: Exit if momentum reverses (acceleration flips)
            if profit_r > 1.0:
                if is_long and accel < -0.5:
                    self.log(f"[EXIT] MOMENTUM REVERSE {symbol} - Closing position")
                    self.close_position(ticket)
                elif not is_long and accel > 0.5:
                    self.log(f"[EXIT] MOMENTUM REVERSE {symbol} - Closing position")
                    self.close_position(ticket)
            
            # Rule 5: Exit if BB percentile extreme (take profit on trends)
            if profit_r > 1.5:
                if is_long and bb_percentile > 0.9:
                    self.log(f"[TP] BB EXTREME {symbol} - Taking profit")
                    self.close_position(ticket)
                elif not is_long and bb_percentile < 0.1:
                    self.log(f"[TP] BB EXTREME {symbol} - Taking profit")
                    self.close_position(ticket)
    
    def partial_close(self, ticket: int, volume: float):
        """Close partial position."""
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        
        pos = pos[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234567,
            "comment": "Partial_Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    def close_position(self, ticket: int):
        """Close entire position."""
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        
        pos = pos[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234567,
            "comment": "Auto_Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    def modify_position(self, ticket: int, new_sl: float, new_tp: float):
        """Modify stop loss and take profit."""
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        
        pos = pos[0]
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": pos.symbol,
            "position": ticket,
            "sl": new_sl,
            "tp": new_tp,
        }
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    def scan_and_trade(self):
        """Main loop: scan symbols and place trades."""
        
        for symbol in self.symbols:
            # Check if already have position
            existing = self.get_open_positions(symbol)
            if len(existing) > 0:
                self.log(f"[SKIP] {symbol} - Already have position")
                continue
            
            # Check max trades limit
            all_positions = self.get_open_positions()
            if len(all_positions) >= self.max_trades:
                self.log(f"[MAX] Trades reached ({self.max_trades})")
                break
            
            # Get data
            df = self.get_data(symbol)
            if df is None:
                self.log(f"[SKIP] {symbol} - No data")
                continue
            
            # Compute features
            try:
                basic_features = QuantFeatureEngine.compute_all(df)
                
                returns = df['close'].pct_change()
                universe_returns = {s: returns for s in self.symbols if s != symbol}
                
                advanced_features = AdvancedQuantEngine.compute_all_advanced(
                    df,
                    universe_returns=universe_returns,
                    market_returns=returns
                )
                
                # Generate signals
                signals, state = UniversalEntryGenerator.generate_all_entries(
                    df, basic_features, advanced_features
                )
                
                if not signals:
                    self.log(f"[NO SETUP] {symbol} - No quality signals")
                    continue
                
                # Get best signal
                best_signal = signals[0]
                
                self.log(f"\n{'='*60}")
                self.log(f"[ANALYZE] {symbol}")
                self.log(f"  Market State: {state['trend_state']} ({state['trend_direction']})")
                self.log(f"  Volatility: {state['volatility']}")
                self.log(f"  Best Signal: {best_signal.entry_type} {best_signal.direction}")
                self.log(f"  Confidence: {best_signal.confidence:.0f}/100")
                
                # Trade if confidence meets threshold
                if best_signal.confidence >= self.min_confidence:
                    self.log(f"[OK] CONFIDENCE OK - Placing trade...")
                    success = self.place_trade(best_signal, symbol)
                    if success:
                        time.sleep(2)  # Brief pause after trade
                else:
                    self.log(f"[LOW CONF] {best_signal.confidence:.0f} < {self.min_confidence}")
                
            except Exception as e:
                self.log(f"ERROR analyzing {symbol}: {e}")
                import traceback
                traceback.print_exc()
    
    def run(self, scan_interval: int = 300):
        """Main execution loop."""
        
        if not mt5.initialize():
            self.log("ERROR: MT5 initialization failed")
            return
        
        account_info = mt5.account_info()
        self.log(f"\n{'='*60}")
        self.log(f"INSTITUTIONAL AUTO-TRADER STARTED")
        self.log(f"{'='*60}")
        self.log(f"Account: {account_info.login}")
        self.log(f"Balance: ${account_info.balance:.2f}")
        self.log(f"Symbols: {', '.join(self.symbols)}")
        self.log(f"Min Confidence: {self.min_confidence}%")
        self.log(f"Risk Per Trade: 1.0% (dynamic sizing)")
        self.log(f"Max Trades: {self.max_trades}")
        self.log(f"Scan Interval: {scan_interval}s")
        self.log(f"{'='*60}\n")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                self.log(f"\n[SCAN #{iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Manage existing positions first
                positions = self.get_open_positions()
                if positions:
                    self.log(f"Managing {len(positions)} open positions...")
                    self.manage_positions()
                
                # Scan for new trades
                self.log(f"Scanning {len(self.symbols)} symbols for entries...")
                self.scan_and_trade()
                
                # Summary
                positions_after = self.get_open_positions()
                self.log(f"\n[SCAN COMPLETE]")
                self.log(f"  Open Positions: {len(positions_after)}/{self.max_trades}")
                self.log(f"  Next scan in {scan_interval}s...")
                
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            self.log(f"\n\n[STOPPED] User interrupt")
        finally:
            mt5.shutdown()
            self.log(f"MT5 connection closed")


if __name__ == "__main__":
    # Configuration
    SYMBOLS = ["GOLD", "BTCUSD", "US100", "GER40"]  # Trade these symbols
    TIMEFRAME = mt5.TIMEFRAME_H1  # H1 timeframe
    MIN_CONFIDENCE = 70  # Only take signals 70%+ confidence
    MAX_TRADES = 3  # Max 3 concurrent trades
    SCAN_INTERVAL = 300  # Scan every 5 minutes
    
    # Create and run trader
    # Note: Position sizing is now automatic (1% risk per trade)
    trader = InstitutionalAutoTrader(
        symbols=SYMBOLS,
        timeframe=TIMEFRAME,
        min_confidence=MIN_CONFIDENCE,
        base_lot_size=0.01,  # Not used anymore, kept for compatibility
        max_trades=MAX_TRADES
    )
    
    trader.run(scan_interval=SCAN_INTERVAL)
