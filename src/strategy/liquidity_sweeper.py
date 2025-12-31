"""
Liquidity Sweeper Strategy (The Alpha Model)
Implements: H4 Bias -> H1 Zones -> M5 Sweep Entry
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from src.core.risk import RiskManager
from src.core.logger import SystemLogger

class LiquiditySweeper:
    def __init__(self):
        self.logger = SystemLogger()
        self.risk = RiskManager()
        
        # Desirable Universe (The Mega Movers)
        desirables = {
            "COMMODITIES": ["GOLD", "XAUUSD", "SILVER", "XAGUSD", "USOIL", "WTI"],
            "INDICES": ["US100", "NAS100", "US500", "SPX500", "US30", "DJ30", "DE40", "DAX40"],
            "CRYPTO": ["BTCUSD", "BITCOIN", "ETHUSD", "ETHEREUM"],
            "FOREX": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        }
        
        # Discovery Phase
        self.symbols = []
        all_mt5_symbols = [s.name for s in mt5.symbols_get()] if mt5.initialize() else []
        
        self.logger.info(f"🔍 Discovered {len(all_mt5_symbols)} broker symbols. Mapping Universe...")
        
        for cat, potential_names in desirables.items():
            for name in potential_names:
                # 1. Exact Match
                if name in all_mt5_symbols:
                    if name not in self.symbols: self.symbols.append(name)
                    continue
                
                # 2. Partial Match (e.g. "GOLD.pro")
                matches = [s for s in all_mt5_symbols if name in s]
                if matches:
                    # Sort by shortest length (GOLD vs GOLD_micro) - heuristic
                    matches.sort(key=len)
                    best = matches[0]
                    if best not in self.symbols: 
                        self.symbols.append(best)
                        mt5.symbol_select(best, True) # FORCE ENABLE IN MARKET WATCH
        
        self.logger.info(f"✅ Active Universe ({len(self.symbols)}): {self.symbols}")
        
        # State Storage (Dict keyed by symbol)
        self.market_state = {} 
        for s in self.symbols:
            self.market_state[s] = {
                'pdh': 0.0, 'pdl': 0.0,
                'micro_high': 0.0, 'micro_low': 0.0,
                'current_price': 0.0, 'spread': 0.0, # Init fields
                'bias': "NEUTRAL",
                'structure': "EQ", # Premium/Discount/EQ
                'daily_change': 0.0,
                'plan': "WAITING FOR DATA", # The specific Trade Idea
                'state': "MONITORING",
                'active_zone_level': 0.0,
                'sweep_level': 0.0,
                'sweep_type': None
            }
            # Initial Warmup
            tick = mt5.symbol_info_tick(s)
            if tick:
                self.market_state[s]['current_price'] = tick.bid
                self.market_state[s]['spread'] = round(tick.ask - tick.bid, 2)
        
    def scan_strategic(self):
        """H4 Analysis for ALL symbols"""
        for sym in self.symbols:
            try:
                rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H4, 0, 50)
                if rates is None: continue
                df = pd.DataFrame(rates)
                
                ema_50 = df['close'].ewm(span=50).mean().iloc[-1]
                close = df['close'].iloc[-1]
                
                bias = "BULLISH" if close > ema_50 else "BEARISH"
                self.market_state[sym]['bias'] = bias
                self.logger.info(f"[{sym}] Strategic Bias: {bias}")
            except Exception as e:
                self.logger.error(f"[{sym}] Strategic Error: {e}")

    def scan_tactical(self):
        """H1 & M15 Zone Mapping for ALL symbols"""
        for sym in self.symbols:
            try:
                # 1. H1 Zones (Major)
                rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, 24) 
                if rates is not None:
                    df = pd.DataFrame(rates)
                    self.market_state[sym]['pdh'] = df['high'].max()
                    self.market_state[sym]['pdl'] = df['low'].min()
                
                # 2. M15 Zones (Minor/Micro)
                rates_m15 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 1, 20)
                if rates_m15 is not None:
                    df_m = pd.DataFrame(rates_m15)
                    self.market_state[sym]['micro_high'] = df_m['high'].max()
                    self.market_state[sym]['micro_low'] = df_m['low'].min()
                else:
                    self.market_state[sym]['micro_high'] = self.market_state[sym]['pdh']
                    self.market_state[sym]['micro_low'] = self.market_state[sym]['pdl']
                
                ms = self.market_state[sym]
                self.logger.info(f"[{sym}] Zones | Major: {ms['pdh']:.2f}/{ms['pdl']:.2f} | Micro: {ms['micro_high']:.2f}/{ms['micro_low']:.2f}")
            except Exception as e:
                self.logger.error(f"[{sym}] Tactical Scan Error: {e}")

    def refresh_market_data(self):
        """Force fetch latest prices for all symbols"""
        for sym in self.symbols:
            tick = mt5.symbol_info_tick(sym)
            if tick:
                self.market_state[sym]['current_price'] = tick.bid
                self.market_state[sym]['spread'] = round(tick.ask - tick.bid, 2)

    def on_tick(self):
        """Execution Logic for ALL symbols"""
        for sym in self.symbols:
            self._process_symbol(sym)

    def _process_symbol(self, sym):
        tick = mt5.symbol_info_tick(sym)
        if not tick: return
        
        bid = tick.bid
        ask = tick.ask
        ms = self.market_state[sym]
        
        ms['current_price'] = bid
        ms['spread'] = round(ask - bid, 5) if "USD" in sym and "JPY" not in sym else round(ask-bid, 2)
        
        # --- EXPERT METRICS ---
        # 1. Daily Change %
        # (Simplified: Close of previous D1 bar vs Current Bid. Ideally use today's open but D1 close is close enough proxy for 'change from yesterday')
        # For efficiency, we won't query history every tick. We assume 0.0 for now or add a query in refresh.
        
        # 2. Structure (Premium/Discount)
        # Range = PDH - PDL. Mid = PDL + Range/2.
        rnge = ms['pdh'] - ms['pdl']
        if rnge > 0:
            mid = ms['pdl'] + (rnge * 0.5)
            if bid > mid: ms['structure'] = "PREMIUM (Sell)"
            else: ms['structure'] = "DISCOUNT (Buy)"
        
        # 3. Trade Plan Generation
        # Logic: If Bearish H4 -> Look for Sell at Prem/PDH. If Bullish H4 -> Look for Buy at Disc/PDL.
        plan = "WAIT"
        prox_res = abs(bid - ms['pdh'])
        prox_sup = abs(bid - ms['pdl'])
        
        if ms['bias'] == "BEARISH":
            if prox_res < (rnge * 0.2): plan = f"⚠️ LOOK TO SHORT @ {ms['pdh']:.2f}"
            elif bid < ms['pdl']: plan = "⚠️ BREAKOUT RISK (CAREFUL)"
            else: plan = f"Wait for Pullback -> {ms['pdh']:.2f}"
        elif ms['bias'] == "BULLISH":
            if prox_sup < (rnge * 0.2): plan = f"💎 LOOK TO LONG @ {ms['pdl']:.2f}"
            elif bid > ms['pdh']: plan = "⚠️ BREAKOUT RISK (CAREFUL)"
            else: plan = f"Wait for Dip -> {ms['pdl']:.2f}"
        
        if ms['state'] == "IN_TRADE": plan = "💰 MANAGING POSITION"
        ms['plan'] = plan
        
        # 0. Check Open Trades
        positions = mt5.positions_get(symbol=sym)
        if positions:
            ms['state'] = "IN_TRADE"
            ms['plan'] = "💰 LIVE TRADE"
            return
        elif ms['state'] == "IN_TRADE":
            self.logger.info(f"[{sym}] Trade Closed. Resetting.")
            ms['state'] = "MONITORING"
            
        # 1. MONITORING
        if ms['state'] == "MONITORING":
            # Sweep Low?
            if bid < ms['pdl'] or bid < ms['micro_low']:
                level = ms['pdl'] if bid < ms['pdl'] else ms['micro_low']
                self.logger.info(f"[{sym}] 👀 Sweeping Low ({level:.2f})")
                ms['state'] = "SWEEP_LOW_DETECTED"
                ms['sweep_level'] = bid
                ms['active_zone_level'] = level
                self._alert_sound() # ALERT
            
            # Sweep High?
            elif bid > ms['pdh'] or bid > ms['micro_high']:
                level = ms['pdh'] if bid > ms['pdh'] else ms['micro_high']
        # Apply Buffer
        sl_price = sl_raw - 1.0 if direction == "BUY" else sl_raw + 1.0
        
        # Note: Risk Calc needs symbol-specific tick value logic (simplified to 1% generic for now)
        lot_size = self.risk.calculate_lot_size(sl_dist) 
        
        tp_dist = sl_dist * 2.0 # 1:2 RR
        tp_price = entry + tp_dist if direction == "BUY" else entry - tp_dist
        
        type_op = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": sym,
            "volume": lot_size,
            "type": type_op,
            "price": entry,
            "sl": sl_price,
            "tp": tp_price,
            "magic": 202502,
            "comment": "Titan v2.0 Multi",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(req)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            self.logger.info(f"[{sym}] ✅ Trade Executed")
            self.market_state[sym]['state'] = "IN_TRADE"
        else:
            self.logger.error(f"[{sym}] ❌ Trade Failed: {res.comment}")
            self.market_state[sym]['state'] = "MONITORING"
