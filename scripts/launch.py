"""
🚀 TITAN AUTONOMOUS ENGINE (v2.0)
The Central Nervous System of the Institutional Trading Platform.

Directives:
1. Orchestrate Data Fees, Context Analysis, and Strategy Execution.
2. Enforce Risk Protocols (Kill Switch).
3. Provide Real-Time Intelligence via Rich Terminal UI.
"""

import sys
import os
import time
import argparse
import logging
import threading
from datetime import datetime
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import ta
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box

# Add project root to path
sys.path.append(os.getcwd())

from titan_system.strategies.live_crypto_trend import LiveCryptoTrend
from titan_system.strategies.live_gold_breakout import LiveGoldBreakout

# --- CONFIGURATION ---
SYMBOLS = ['ETHUSD', 'BTCUSD', 'GOLD']
TIMEFRAME = mt5.TIMEFRAME_M15 # Switched to M15 for Intraday/Scalping
UPDATE_INTERVAL = 60 # Seconds

# Logging
logging.basicConfig(
    filename='data/titan_engine.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TitanEngine")

from titan_system.core.execution import MT5Execution

class SimpleConfig:
    """Minimal Config for Execution Engine"""
    max_slippage = 20
    mt5_login = 0
    mt5_password = ""
    mt5_server = ""

# --- ANALYST AGENT (CONTEXT ENGINE) ---
class AnalystAgent:
    def __init__(self):
        pass

    def calculate_context_score(self, df):
        """
        Calculates Composite Context Score (0-100)
        Ref: TITAN_AUTONOMOUS_BEHAVIOR_SPEC.md
        """
        try:
            if len(df) < 200: return 50, "Insufficient Data"
            
            c = df['close']
            
            # A. TREND VECTOR (50%)
            sma200 = ta.trend.sma_indicator(c, window=200)
            adx = ta.trend.ADXIndicator(df['high'], df['low'], c, window=14).adx()
            
            score_trend = 0
            if c.iloc[-1] > sma200.iloc[-1]: score_trend += 20
            if adx.iloc[-1] > 25: score_trend += 15
            
            # EMA Alignment
            ema8 = ta.trend.ema_indicator(c, window=8).iloc[-1]
            ema21 = ta.trend.ema_indicator(c, window=21).iloc[-1]
            ema50 = ta.trend.ema_indicator(c, window=50).iloc[-1]
            if ema8 > ema21 > ema50: score_trend += 15
            
            # B. VOLATILITY VECTOR (30%)
            atr = ta.volatility.AverageTrueRange(df['high'], df['low'], c, window=14).average_true_range()
            sma_atr = atr.rolling(20).mean()
            
            score_vol = 0
            if atr.iloc[-1] > sma_atr.iloc[-1]: score_vol += 15
            
            bb = ta.volatility.BollingerBands(c, window=20)
            bbw = bb.bollinger_wband()
            bbw_mean = bbw.rolling(20).mean()
            if bbw.iloc[-1] > bbw_mean.iloc[-1]: score_vol += 15
            
            # C. STRUCTURE VECTOR (20%)
            high20 = df['high'].rolling(20).max().shift(1).iloc[-1]
            score_struct = 0
            if c.iloc[-1] > high20: score_struct += 10
            
            rsi = ta.momentum.rsi(c, window=14).iloc[-1]
            if 50 < rsi < 70: score_struct += 10
            
            total_score = score_trend + score_vol + score_struct
            
            # Determine Regime
            regime = "NEUTRAL"
            if total_score >= 80: regime = "PRISTINE BULL"
            elif total_score >= 60: regime = "MILD BULL"
            elif total_score >= 40: regime = "CHOP"
            else: regime = "BEAR/CRASH"
            
            return total_score, regime
            
        except Exception as e:
            logger.error(f"Analyst Error: {e}")
            return 50, "Error"

# --- UNIVERSE SCANNER (THE GATEKEEPER) ---
class UniverseScanner:
    def __init__(self):
        self.initial_filter_passed = []
        self.active_watch_list = [] # The "In-Play" List

    def scan_full_universe(self):
        """
        Scans ALL 1500+ Symbols to find 'Tradable Candidates'.
        Runs every 4 hours.
        """
        logger.info("Starting Full Universe Scan (1500+ Symbols)...")
        if not mt5.initialize(): return []
        
        all_symbols = mt5.symbols_get()
        if not all_symbols: return []
        
        candidates = []
        # Filter 1: Basic Tradability (Spread, visible in generic list)
        for s in all_symbols:
            # Skip custom or weird symbols if needed, filtering by Path/Group is good
            # For now, simplistic filter:
            if "Exotic" in s.path: continue 
            
            candidates.append(s.name)
            
        logger.info(f"Universe Size: {len(candidates)}")
        
        candidates_to_score = candidates
        # Limit to 300 to prevent ultra-long scans in Python
        if len(candidates) > 300:
             # Heuristic: Prefer USD pairs, Gold, Majors
             candidates_to_score = [s for s in candidates if "USD" in s or "EUR" in s or "JPY" in s or "GOLD" in s or "XAU" in s][:300]

        scored_candidates = []
        
        for i, sym in enumerate(candidates_to_score):
            if i % 50 == 0: print(f"Scanning {i}/{len(candidates_to_score)}...")
            
            # Fetch minimal data (Global Trend D1)
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 20)
            if rates is None or len(rates) < 20: continue
            
            c = pd.Series([x['close'] for x in rates])
            pct_change = abs((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2])
            
            if pct_change > 0.005: 
                scored_candidates.append(sym)
                
        self.active_watch_list = scored_candidates[:50] 
        logger.info(f"Active Watchlist updated: {len(self.active_watch_list)} symbols")
        return self.active_watch_list

# --- TITAN ENGINE ---
class TitanEngine:
    def __init__(self, mode='paper'):
        self.mode = mode
        self.analyst = AnalystAgent()
        self.scanner = UniverseScanner()
        self.config = SimpleConfig()
        self.exec = MT5Execution(self.config)
        
        # Auto-Connect for Live Trading
        if self.mode == 'live':
             if self.exec.connect():
                 logger.info("LIVE EXECUTION CONNECTED")
             else:
                 logger.critical("FAILED TO CONNECT FOR LIVE EXECUTION")
        
        self.last_scan_time = 0
        self.scan_interval = 4 * 3600
        
        self.generic_trend_strategy = LiveCryptoTrend() 
        self.generic_breakout_strategy = LiveGoldBreakout()
        
        self.state = {
            'status': 'STARTING',
            'equity': 0.0,
            'balance': 0.0,
            'positions': [],
            'regimes': {},
            'watchlist_size': 0
        }
    
    def fetch_data(self, symbol):
        # Fetching M15 Data now via Engine
        rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 300)
        if rates is None: return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def update_account_info(self):
        acct = mt5.account_info()
        if acct:
            self.state['equity'] = acct.equity
            self.state['balance'] = acct.balance
            
        positions = mt5.positions_get()
        self.state['positions'] = []
        if positions:
            for p in positions:
                self.state['positions'].append({
                    'ticket': p.ticket,
                    'symbol': p.symbol,
                    'type': 'BUY' if p.type == 0 else 'SELL',
                    'profit': p.profit,
                    'volume': p.volume
                })

    def run_cycle(self):
        # 0. UNIVERSE SCAN
        if time.time() - self.last_scan_time > self.scan_interval:
            self.state['status'] = 'SCANNING UNIVERSE...'
            active_symbols = self.scanner.scan_full_universe()
            self.last_scan_time = time.time()
            self.state['watchlist_size'] = len(active_symbols)
        else:
            active_symbols = self.scanner.active_watch_list
            if not active_symbols:
                 active_symbols = self.scanner.scan_full_universe()

        self.update_account_info()
        
        # 1. LOOP ACTIVE SYMBOLS
        for symbol in active_symbols:
            df = self.fetch_data(symbol)
            if df is None: continue
                
            # 2. ANALYZE CONTEXT
            score, regime = self.analyst.calculate_context_score(df)
            self.state['regimes'][symbol] = {'score': score, 'regime': regime}
            
            # 3. SELECT STRATEGY
            strategy = self.generic_trend_strategy 
            if any(x in symbol for x in ['XAU', 'GOLD', 'SILVER', 'XAG', 'US500', 'NAS100', 'GER30', 'GER40', 'JP225']):
                strategy = self.generic_breakout_strategy
            
            if score < 40: continue # Filters bad context
                
            # Run Strategy Logic
            decision = strategy.analyze(symbol, df)
            
            # 4. EXECUTE
            if decision['signal'] in ['BUY', 'SELL']:
                risk_mult = 1.5 if score >= 80 else 1.0
                if score < 60: risk_mult = 0.5
                
                logger.info(f"SIGNAL: {symbol} {decision['signal']} (Risk: {risk_mult}x) | Reason: {decision['reason']}")
                
                if self.mode == 'live':
                    self.execute_live_trade(symbol, decision['signal'], risk_mult)
                
        self.state['status'] = f'Active (Monitored: {len(active_symbols)})'

    def execute_live_trade(self, symbol, signal, risk_mult):
        # Prevent over-trading: Check if position exists
        existing = [p for p in self.state['positions'] if p['symbol'] == symbol]
        if existing: return # Setup already active
        
        volume = 0.01 # Start small for safety, implies user trusts us to scale later.
        if risk_mult > 1.0: volume = 0.02
        
        self.exec.execute_order(symbol, signal, volume, sl_pips=50, tp_pips=100)

    def generate_dashboard(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1)
        )
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        
        # Header
        header = Panel(
            f"[bold cyan]TITAN AUTONOMOUS ENGINE (M15 SCALPER)[/bold cyan] | Mode: [bold red]{self.mode.upper()}[/bold red] | Status: {self.state['status']} | Watchlist: {self.state['watchlist_size']}",
            style="white on blue"
        )
        layout["header"].update(header)
        
        # Left: Top Regimes
        table_regime = Table(title="Top Opportunities (Context Score)", box=box.SIMPLE)
        table_regime.add_column("Symbol", style="cyan")
        table_regime.add_column("Score", justify="right")
        table_regime.add_column("Regime", style="bold")
        
        sorted_regimes = sorted(self.state['regimes'].items(), key=lambda x: x[1]['score'], reverse=True)[:15]
        
        for sym, data in sorted_regimes:
            color = "green" if data['score'] >= 60 else ("red" if data['score'] < 40 else "yellow")
            table_regime.add_row(sym, str(data['score']), f"[{color}]{data['regime']}[/{color}]")
            
        layout["left"].update(Panel(table_regime, title="Alpha Intelligence"))
        
        # Right: Account & Positions
        table_acct = Table(title="Portfolio Status", box=box.SIMPLE)
        table_acct.add_row("Equity", f"${self.state['equity']:,.2f}")
        table_acct.add_row("Balance", f"${self.state['balance']:,.2f}")
        table_acct.add_row("Open Positions", str(len(self.state['positions'])))
        
        pos_text = "\n".join([f"{p['symbol']} {p['type']} {p['volume']} (${p['profit']:.2f})" for p in self.state['positions']])
        
        layout["right"].update(Panel(f"{pos_text}\n\nAccount Info:\nEquity: ${self.state['equity']}", title="Risk Manager"))
        
        return layout

    def start(self):
        if not mt5.initialize():
            logger.critical("MT5 Init Failed")
            return
            
        with Live(self.generate_dashboard(), refresh_per_second=1, screen=True) as live:
            while True:
                try:
                    self.run_cycle()
                    live.update(self.generate_dashboard())
                    time.sleep(UPDATE_INTERVAL)
                except KeyboardInterrupt:
                    print("Shutting down...")
                    break
                except Exception as e:
                    logger.error(f"Cycle Error: {e}")
                    time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='paper', choices=['live', 'paper'])
    args = parser.parse_args()
    
    engine = TitanEngine(mode=args.mode)
    engine.start()
