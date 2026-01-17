"""
FLEET ORCHESTRATOR
==================
The master process manager for auto-generated trading bots.
Responsible for:
1. Syncing with Strategy Registry (Paper/Live status)
2. Launching bot processes via subprocess
3. Monitoring process health (auto-restart)
4. Tracking trade performance and Auto-Retirement
"""

import os
import sys
import time
import json
import sqlite3
import subprocess
import logging
import MetaTrader5 as mt5
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory import factory_config as cfg
from titan_system.factory.strategy_registry import StrategyRegistry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ORCHESTRATOR] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("logs/fleet_orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FleetOrchestrator")

class FleetOrchestrator:
    def __init__(self):
        self.registry = StrategyRegistry()
        self.active_processes = {} # {strategy_id: subprocess.Popen}
        self.bot_dir = Path("titan_system/strategies/autogen")
        self.poll_interval = 30 # Seconds
        self.last_trade_sync = datetime.now() - timedelta(hours=1)
        
        # Risk Thresholds
        self.MAX_DRAWDOWN = 0.05 # 5%
        self.MAX_CONS_LOSSES = 5
        
    def get_deployed_bots(self):
        """Find bots that should be running based on registry status."""
        conn = sqlite3.connect(cfg.STRATEGY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT id, genome, magic_number, live_drawdown, consecutive_losses FROM strategies WHERE status IN ('paper', 'live')")
        rows = cursor.fetchall()
        conn.close()
        
        bots = []
        for r_id, genome_json, magic, dd, cons_loss in rows:
            genome = json.loads(genome_json)
            # Find the file in autogen dir
            filename = f"autogen_{r_id[:8]}_{genome['name'].replace(' ', '_')}.py"
            filepath = self.bot_dir / filename
            
            if filepath.exists():
                bots.append({
                    "id": r_id,
                    "name": genome['name'],
                    "path": str(filepath),
                    "magic": magic,
                    "drawdown": dd or 0,
                    "cons_loss": cons_loss or 0
                })
            else:
                logger.warning(f"Strategy {r_id[:8]} marked as active but file not found: {filename}")
        
        return bots

    def sync_fleet(self):
        """Start missing bots, stop removed ones, and handle auto-retirement."""
        desired_bots = self.get_deployed_bots()
        desired_ids = {b['id'] for b in desired_bots}
        
        # 1. Stop bots no longer in 'paper/live' status
        to_stop = [s_id for s_id in self.active_processes if s_id not in desired_ids]
        for s_id in to_stop:
            self.stop_bot(s_id)
            
        # 2. Check for Auto-Retirement based on risk thresholds
        for bot in desired_bots:
            if bot['drawdown'] >= self.MAX_DRAWDOWN:
                logger.warning(f"🚨 AUTO-RETIRE: {bot['name']} breached Drawdown ({bot['drawdown']:.1%})")
                self.retire_bot(bot['id'], f"Drawdown limit reached ({bot['drawdown']:.1%})")
                continue
            
            if bot['cons_loss'] >= self.MAX_CONS_LOSSES:
                logger.warning(f"🚨 AUTO-RETIRE: {bot['name']} breached Cons. Losses ({bot['cons_loss']})")
                self.retire_bot(bot['id'], f"Max consecutive losses reached ({bot['cons_loss']})")
                continue

            # 3. Start missing bots / Restart crashed ones
            if bot['id'] not in self.active_processes:
                self.start_bot(bot)
            else:
                process = self.active_processes[bot['id']]
                if process.poll() is not None:
                    logger.warning(f"Bot {bot['name']} ({bot['id'][:8]}) crashed. Restarting...")
                    self.start_bot(bot)

    def monitor_trades(self):
        """Scrape MT5 for closed trades from active magics and update registry."""
        if not mt5.initialize():
            logger.error("MT5 failed in monitor_trades")
            return

        active_bots = self.get_deployed_bots()
        active_magics = {b['magic']: b['id'] for b in active_bots if b['magic']}
        
        if not active_magics:
            return

        # Fetch history since last sync
        history = mt5.history_deals_get(self.last_trade_sync, datetime.now())
        if history:
            for deal in history:
                if deal.magic in active_magics:
                    # We only care about deals that close a position (entry deals have profit=0)
                    if deal.entry == mt5.DEAL_ENTRY_OUT:
                        strategy_id = active_magics[deal.magic]
                        logger.info(f"📈 Trade detected for {strategy_id[:8]}: PnL = {deal.profit}")
                        
                        # Update registry
                        trade_result = {
                            'symbol': deal.symbol,
                            'direction': "SELL" if deal.type == mt5.DEAL_TYPE_BUY else "BUY", # Exit type is opposite of entry
                            'pnl': deal.profit,
                            'exit_reason': "Target/Stop" if deal.reason == mt5.DEAL_REASON_EXPERT else "Manual",
                            'entry_time': datetime.fromtimestamp(deal.time).isoformat() # This is exit time, but registry will handle
                        }
                        self.registry.update_live_performance(strategy_id, trade_result=trade_result)
            
            self.last_trade_sync = datetime.now()
        
        # ALSO SYNC OPEN POSITIONS (Unrealized PnL)
        if active_magics:
            positions = mt5.positions_get()
            if positions:
                # Group positions by magic number
                magic_pnl = {}
                for pos in positions:
                    if pos.magic in active_magics:
                        if pos.magic not in magic_pnl:
                            magic_pnl[pos.magic] = {'count': 0, 'total_pnl': 0}
                        magic_pnl[pos.magic]['count'] += 1
                        magic_pnl[pos.magic]['total_pnl'] += pos.profit
                
                # Update each strategy with current open PnL
                for magic, data in magic_pnl.items():
                    strategy_id = active_magics[magic]
                    self.registry.update_live_performance(
                        strategy_id,
                        unrealized_pnl=data['total_pnl'],
                        open_positions=data['count']
                    )

    def retire_bot(self, s_id, reason):
        """Shut down bot and mark as retired in DB."""
        self.stop_bot(s_id)
        self.registry.update_status(s_id, self.registry.STATUS_RETIRED, reason=reason)
        logger.info(f"✅ Strategy {s_id[:8]} retired: {reason}")

    def start_bot(self, bot):
        """Launch a bot process."""
        logger.info(f"🚀 Launching: {bot['name']} ({bot['id'][:8]})")
        try:
            process = subprocess.Popen(
                [sys.executable, bot['path']],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )
            self.active_processes[bot['id']] = process
            logger.info(f"   PID: {process.pid} | Magic: {bot['magic']}")
        except Exception as e:
            logger.error(f"   Failed to launch {bot['name']}: {e}")

    def stop_bot(self, s_id):
        """Terminate a bot process."""
        if s_id in self.active_processes:
            process = self.active_processes[s_id]
            logger.info(f"🛑 Stopping Strategy ID: {s_id[:8]}")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del self.active_processes[s_id]

    def run(self):
        logger.info("=" * 60)
        logger.info("TITAN FLEET ORCHESTRATOR v2.0 - ACTIVE")
        logger.info("=" * 60)
        
        if not mt5.initialize():
            logger.error("MT5 initialization failed in global orchestrator")
            return

        try:
            while True:
                self.monitor_trades()
                self.sync_fleet()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
            self.shutdown()
        finally:
            mt5.shutdown()

    def shutdown(self):
        logger.info("Shutting down fleet...")
        for s_id in list(self.active_processes.keys()):
            self.stop_bot(s_id)
        logger.info("All bots stopped. Orchestrator offline.")

if __name__ == "__main__":
    orchestrator = FleetOrchestrator()
    orchestrator.run()
