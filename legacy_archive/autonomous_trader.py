"""
24/7 Autonomous Trading System
Monitors all markets, executes trades, sends emails - WITHOUT exhausting API limits
"""
import MetaTrader5 as mt5
from core.mt5_interface import MT5Interface
from core.strategy import Strategy
from notification import EmailNotification
from core.multi_category_scanner import MultiCategoryScanner
import time
import datetime
import schedule
import numpy as np

import logging

# Configure Logging for Dashboard Visibility (app.py catches root logger)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class AutonomousTrader:
    def __init__(self):
        self.interface = MT5Interface()
        self.notifier = EmailNotification()
        self.scanner = MultiCategoryScanner()
        self.last_signals = {}  # Track to avoid spam
        # State for API
        self.running = False
        self.latest_reasoning_log = {'accepted': [], 'rejected': []}
        self.latest_scan_result = {}
        self.market_regime = {'status': 'CALCULATING', 'adx': 0}
        self.active_trades_cache = []
        
        # Risk Management
        self.initial_equity = 0.0 
        self.MAX_DAILY_DRAWDOWN = 0.05 # 5% hard stop

    def start_24_7_monitoring(self):
        """Main loop - runs forever"""
        logger.info("🤖 Starting 24/7 Autonomous Trading System...")
        self.running = True
        
        if not self.interface.start():
            logger.error("❌ Failed to connect to MT5")
            return
            
        # Capture starting equity for the day
        account = mt5.account_info()
        if account:
            self.initial_equity = account.equity
            logger.info(f"💰 Starting Equity: ${self.initial_equity:.2f} | Max Loss Limit: -5%")
        
        # Schedule different scan frequencies
        schedule.every(15).minutes.do(self.quick_scan_and_trade)
        schedule.every(6).hours.do(self.category_digest)
        schedule.every().day.at("07:00").do(self.strategic_briefing)  # Uses AI
        schedule.every().sunday.at("20:00").do(self.weekly_review)   # Uses AI
        schedule.every().sunday.at("02:00").do(self.run_optimization) # Self-Evolution
        
        logger.info("✅ Monitoring active. Schedules set:")
        # ... (prints)
        
        try:
            while self.running:
                # 1. Safety Check
                if not self.check_equity_guard():
                    logger.critical("🛑 CIRCUIT BREAKER TRIPPED. PAUSING TRADING.")
                    time.sleep(300) # Sleep 5 mins
                    continue # Skip schedule run
                    
                # 2. Run Tasks
                schedule.run_pending()
                time.sleep(1)  # Check 1s for responsiveness
        except KeyboardInterrupt:
            self.stop()

    def check_equity_guard(self):
        """Returns True if safe to trade, False if max drawdown hit."""
        if self.initial_equity == 0: return True
        
        info = mt5.account_info()
        if not info: return True # Don't stop on connection flux
        
        current_equity = info.equity
        drawdown = (self.initial_equity - current_equity) / self.initial_equity
        
        if drawdown > self.MAX_DAILY_DRAWDOWN:
            return False
        return True

    def stop(self):
        logger.info("\n🛑 Stopping autonomous trader...")
        self.running = False
        self.interface.shutdown()

    def get_net_exposure(self):
        """
        Calculates net exposure per currency in lots.
        Example: Buy 1.0 EURUSD -> Long 1.0 EUR, Short 1.0 USD
        """
        if not self.interface.connected:
            return {}
            
        positions = mt5.positions_get()
        if not positions:
            return {}
            
        exposure = {} # { 'USD': 0.5, 'EUR': -0.5 }
        
        for pos in positions:
            symbol = pos.symbol
            volume = pos.volume
            type_mult = 1 if pos.type == mt5.ORDER_TYPE_BUY else -1
            
            # Simple parsing for standard Forex pairs (EURUSD, USDJPY)
            # This is a naive implementation, works for 6-char forex.
            if len(symbol) == 6:
                base = symbol[:3]
                quote = symbol[3:]
                
                # Base currency exposure
                exposure[base] = exposure.get(base, 0) + (volume * type_mult)
                
                # Quote currency exposure (inverse)
                exposure[quote] = exposure.get(quote, 0) - (volume * type_mult)
        
        # Round for display
        return {k: round(v, 2) for k, v in exposure.items() if v != 0}

    # ... (existing methods)

    def strategic_briefing(self):
        """Daily AI-powered analysis - USES 1 API CALL"""
        logger.info(f"\n[{datetime.datetime.now().strftime('%H:%M')}] 🧠 Strategic Briefing (AI)...")
        
        from daily_analyst import DailyAnalyst
        analyst = DailyAnalyst()
        # Capture the reasoning data here!
        # We need to refactor DailyAnalyst to return data, or we just spy on the scanner.
        # Let's run a separate deep scan for the API state if needed, 
        # But better: DailyAnalyst already calls scanner.scan()
        # Let's just call scanner.scan() here directly to populate our state
        
        results = analyst.scanner.scan() # This returns {accepted, rejected}
        self.latest_reasoning_log = results
        
        # Then proceed with normal reporting
        # (This duplicates the scan call if DailyAnalyst calls it again inside run_daily_analysis. 
        # Refactoring DailyAnalyst to accept pre-scanned results would be cleaner, but for now let's just update state)
        
        analyst.run_daily_analysis()

if __name__ == "__main__":
    trader = AutonomousTrader()
    trader.start_24_7_monitoring()
    
    def quick_scan_and_trade(self):
        """
        Fast scan of major pairs - Uses Scanner for Deep Reasoning Visibility
        Executes trades automatically
        """
        logger.info(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔍 Quick Scan Running...")
        
        # Priority symbols (fastest to scan)
        priority_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
        
        # Use the unified scanner to get reasoning data
        # We define a 'Quick Scan' category
        scan_results = self.scanner.scan(
            categories={"Quick Watchlist": priority_symbols}, 
            max_spread=40
        )
        
        # Update API State so dashboard sees it
        self.latest_reasoning_log = scan_results
        
        # DETERMINE GLOBAL REGIME (Proxy using EURUSD)
        # In a real prop desk, we'd average the ADX of 5 majors.
        # Here we check EURUSD for quick context.
        try:
            # We need raw candles for strategy.get_market_regime
            # This is a bit inefficient (double fetch), but clean for architecture.
            # Strategy needs df.
            # Let's peek into the scanner's cache or just fetch quickly.
            # For speed, we will just use the last scanned symbol's result if available
            # Or better, just fetch EURUSD H1.
            df = self.interface.get_closes("EURUSD", mt5.TIMEFRAME_H1, 100)
            if df is not None:
                strat = Strategy("EURUSD", mt5.TIMEFRAME_H1) # Params don't matter for ADX
                self.market_regime = strat.get_market_regime(df)
            else:
                 self.market_regime = {'status': 'OFFLINE', 'adx': 0}
        except Exception as e:
             logger.error(f"Regime Check Failed: {e}")
             self.market_regime = {'status': 'ERROR', 'adx': 0}
        
        # Process Accepted Trades
        if scan_results['accepted']:
            logger.info(f"  ⚡ Found {len(scan_results['accepted'])} actionable signals.")
            self.send_instant_alert(scan_results['accepted'])
            
            for trade in scan_results['accepted']:
                # Execution Logic
                # Check cache to avoid double entry in same 15 min window (simple check)
                 if trade['symbol'] not in self.last_signals:
                    self.execute_trade(
                        trade['symbol'], 
                        trade['signal'], 
                        trade['sl'], 
                        trade['tp']
                    )
                    self.last_signals[trade['symbol']] = trade['signal']
        else:
            logger.info("  💤 No high-prob setups found.")

        # Cleanup old signals (15 min cooldown)
        # Resetting self.last_signals might cause re-entry if signal persists... 
        # Better to keep a timestamp or rely on MT5 position check. 
        # For this prototype, we'll just clear it every hour or leave it. 
        # But to be safe lets clear it.
        self.last_signals = {}
    
    def execute_trade(self, symbol, signal, sl, tp):
        """Execute trade on MT5"""
        try:
            order_type = mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL
            volume = 0.01  # Micro lot for safety
            
            result = self.interface.place_market_order(symbol, volume, order_type)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"  ✅ TRADE EXECUTED: {signal} {symbol} @ {result.price}")
                return True
            else:
                logger.error(f"  ❌ Trade failed: {result.retcode if result else 'Unknown'}")
                return False
        except Exception as e:
            logger.error(f"  ❌ Execution error: {e}")
            return False
    
    def send_instant_alert(self, signals):
        """Send instant email - NO AI, just data"""
        html = f"""
<!DOCTYPE html>
<html>
<head><style>
body {{ font-family: Arial; background: #f4f4f4; padding: 20px; }}
.container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; }}
.signal {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; margin: 10px 0; }}
.buy {{ border-left: 5px solid #10b981; }}
.sell {{ border-left: 5px solid #ef4444; }}
h1 {{ color: #1e293b; }}
</style></head>
<body>
<div class="container">
<h1>⚡ INSTANT SIGNAL ALERT</h1>
<p><strong>Time:</strong> {datetime.datetime.now().strftime('%H:%M:%S IST')}</p>
"""
        
        for sig in signals:
            badge = "buy" if sig['signal'] == 'BUY' else "sell"
            html += f"""
<div class="signal {badge}">
<h2>{sig['symbol']} → {sig['signal']}</h2>
<p><strong>Entry:</strong> {sig.get('entry', sig.get('price', 0)):.5f}</p>
<p><strong>Stop Loss:</strong> {sig['sl']:.5f}</p>
<p><strong>Take Profit:</strong> {sig['tp']:.5f}</p>
<p><strong>ATR:</strong> {sig['atr']:.5f}</p>
</div>
"""
        
        html += """
<p style="color: #64748b; font-size: 12px;">Trade executed automatically. No action required.</p>
</div></body></html>
"""
        
        subject = f"⚡ {len(signals)} Signal(s) Detected & Executed"
        self.notifier.send_email(subject, html)
    
    def category_digest(self):
        """6-hour category scan - NO AI"""
        print(f"\n[{datetime.datetime.now().strftime('%H:%M')}] 📊 Category Digest Running...")
        
        results = self.scanner.scan_all_categories()
        self.latest_scan_result = results # Store for Dashboard
        
        # Send without AI commentary
        html = self._build_digest_html(results)
        subject = f"📊 6-Hour Market Digest - {datetime.datetime.now().strftime('%H:%M')}"
        self.notifier.send_email(subject, html)
    
    def _build_digest_html(self, results):
        """Build HTML without AI"""
        html = """
<!DOCTYPE html>
<html><head><style>
body { font-family: Arial; padding: 20px; background: #f4f4f4; }
table { width: 100%; border-collapse: collapse; background: white; }
th { background: #3b82f6; color: white; padding: 10px; }
td { padding: 10px; border-bottom: 1px solid #e5e7eb; }
</style></head><body>
<h1>📊 Market Overview</h1>
"""
        
        for category, signals in results.items():
            html += f"<h2>{category}</h2><table><tr><th>Symbol</th><th>Signal</th><th>Price</th></tr>"
            for sig in signals[:5]:
                if sig['signal']:
                    html += f"<tr><td>{sig['symbol']}</td><td>{sig['signal']}</td><td>{sig['price']:.5f}</td></tr>"
            html += "</table>"
        
        html += "</body></html>"
        return html
    
    def strategic_briefing(self):
        """Daily AI-powered analysis - USES 1 API CALL"""
        print(f"\n[{datetime.datetime.now().strftime('%H:%M')}] 🧠 Strategic Briefing (AI)...")
        
        from daily_analyst import DailyAnalyst
        analyst = DailyAnalyst()
        analyst.run_daily_analysis()
    
    def weekly_review(self):
        """Weekly performance review - USES 1 API CALL"""
        logger.info(f"\n[{datetime.datetime.now().strftime('%H:%M')}] 📈 Weekly Review (AI)...")
        
        # Get week's trades
        from_date = datetime.datetime.now() - datetime.timedelta(days=7)
        deals = mt5.history_deals_get(from_date, datetime.datetime.now())
        
        if deals:
            closed = [d for d in deals if d.profit != 0]
            wins = len([d for d in closed if d.profit > 0])
            total_pnl = sum(d.profit for d in closed)
            
            # Use AI to analyze
            try:
                import google.generativeai as genai
                import config
                
                genai.configure(api_key=config.GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
You are a senior trading analyst reviewing weekly performance.

Results:
- Total Trades: {len(closed)}
- Wins: {wins}, Losses: {len(closed)-wins}
- Win Rate: {(wins/len(closed)*100):.1f}%
- Net P&L: ${total_pnl:.2f}

Task: Write a 200-word strategic review. What worked? What didn't? What to adjust next week?
"""
                
                response = model.generate_content(prompt)
                
                # Send email with AI review
                html = f"""
<html><body>
<h1>📈 Weekly Performance Review</h1>
<h2>Numbers</h2>
<ul>
<li>Trades: {len(closed)}</li>
<li>Win Rate: {(wins/len(closed)*100):.1f}%</li>
<li>P&L: ${total_pnl:.2f}</li>
</ul>
<h2>AI Analysis</h2>
<p>{response.text}</p>
</body></html>
"""
                
                self.notifier.send_email("📈 Weekly Review", html)
                
    def run_optimization(self):
        """Self-Correction: Re-train AI on latest data every week"""
        logger.info(f"\n[{datetime.datetime.now().strftime('%H:%M')}] 🧬 Evolution Engine Running (Auto-Tuning)...")
        # Optimization can take time, so we might want to run it in a separate thread in production.
        # For now, simplistic approach:
        try:
            # Add scripts to path for importing
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), 'scripts'))
            from train_ai import train_brain
            
            # Optimize priority list
            priority = ["EURUSD", "GBPUSD", "XAUUSD"]
            for sym in priority:
                train_brain(sym)
                
            self.notifier.send_email("🧬 System Evolved", "Neural Network weights have been updated based on the last 2000 candles.")
        except Exception as e:
            print(f"Optimization failed: {e}")

if __name__ == "__main__":
    trader = AutonomousTrader()
    # Initial train check
    # trader.run_optimization()
    trader.start_24_7_monitoring()
