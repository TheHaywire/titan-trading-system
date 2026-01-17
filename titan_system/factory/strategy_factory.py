"""
STRATEGY FACTORY - Main Orchestrator  
====================================
Continuous edge discovery system that generates, validates, deploys, and manages
profitable trading strategies with institutional-grade risk controls.

Main Workflow:
1. Generate strategy candidates
2. Backtest with out-of-sample validation
3. Run robustness tests
4. Deploy winners to paper trading
5. Promote to live with gradual ramping
6. Monitor and auto-retire underperformers
7. Evolve and optimize continuously
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

from .strategy_genome import StrategyGenome
from .strategy_registry import StrategyRegistry
from .generators.idea_generator import IdeaGenerator
from . import factory_config as cfg

# Setup logging
logging.basicConfig(
    level=getattr(logging, cfg.LOG_LEVEL),
    format='%(asctime)s [FACTORY] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("StrategyFactory")


class StrategyFactory:
    """
    Meta-level trading system orchestrator.
    Continuously generates and manages a portfolio of profitable strategies.
    """
    
    def __init__(self):
        """Initialize the factory with all subsystems."""
        logger.info("=" * 60)
        logger.info("STRATEGY FACTORY - Initializing")
        logger.info("=" * 60)
        
        # Core components
        self.registry = StrategyRegistry(cfg.STRATEGY_DB)
        self.idea_generator = IdeaGenerator()
        
        # State tracking
        self.cycle_num = 0
        self.last_cycle_time = None
        self.generation_num = 0
        
        # Load current state from registry
        self.portfolio_state = self._get_portfolio_state()
        
        logger.info(f"Registry: {cfg.STRATEGY_DB}")
        logger.info(f"Current State:")
        logger.info(f"  - Live Strategies: {self.portfolio_state['live_count']}")
        logger.info(f"  - Paper Strategies: {self.portfolio_state['paper_count']}")
        logger.info(f"  - Total PnL: ${self.portfolio_state['total_pnl']:.2f}")
        logger.info("=" * 60)
    
    # ==================== MAIN CYCLE ====================
    
    def run_cycle(self):
        """
        Execute one complete factory cycle:
        1. Generate candidates
        2. Validate existing strategies
        3. Check for promotions/retirements
        4. Monitor portfolio risk
        """
        self.cycle_num += 1
        self.last_cycle_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info(f"FACTORY CYCLE #{self.cycle_num} - {self.last_cycle_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Check portfolio health (CRITICAL)
            if not self._check_portfolio_risk():
                logger.error("⚠️  PORTFOLIO RISK LIMIT BREACHED - HALTING FACTORY")
                return
            
            # Step 2: Monitor live strategies
            self._monitor_live_strategies()
            
            # Step 3: Check paper trading promotions
            self._check_paper_promotions()
            
            # Step 4: Generate new candidates (if we have capacity)
            if self._can_generate_more():
                self._generate_and_register_candidates()
            else:
                logger.info("⏸  Max strategy limit reached - skipping generation")
            
            # Step 5: Portfolio summary
            self._print_portfolio_summary()
            
            logger.info(f"✅ Cycle #{self.cycle_num} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Factory cycle failed: {e}", exc_info=True)
    
    def run_continuous(self, cycle_hours: int = None):
        """
        Run continuous factory operation.
        
        Args:
            cycle_hours: Hours between cycles (default from config)
        """
        cycle_hours = cycle_hours or cfg.FACTORY_CYCLE_HOURS
        cycle_seconds = cycle_hours * 3600
        
        logger.info(f"🚀 Starting continuous operation (cycle every {cycle_hours}h)")
        
        try:
            while True:
                self.run_cycle()
                
                # Wait for next cycle
                next_cycle = datetime.now() + timedelta(seconds=cycle_seconds)
                logger.info(f"⏰ Next cycle: {next_cycle.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("")
                
                time.sleep(cycle_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Factory stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
    
    # ==================== GENERATION ====================
    
    def _generate_and_register_candidates(self):
        """Generate new strategy candidates and register them."""
        logger.info("🧬 Generating new strategy candidates...")
        
        # Determine how many to generate
        # We generate a full batch of candidates every cycle to maximize discovery.
        # Candidates are stored in the DB and filtered later, so they don't consume paper slots.
        generate_count = cfg.MAX_CANDIDATES_PER_CYCLE
        
        if generate_count <= 0:
            logger.info("  ⏸  Generation disabled in config")
            return
        
        # Generate candidates
        candidates = self.idea_generator.generate_batch(count=generate_count)
        
        logger.info(f"  Generated {len(candidates)} candidates:")
        
        # Register each candidate
        registered_count = 0
        for candidate in candidates:
            try:
                strategy_id = self.registry.add_candidate(
                    candidate,
                    notes=f"Auto-generated in cycle #{self.cycle_num}"
                )
                logger.info(f"    ✓ {candidate.name} (ID: {strategy_id[:8]}...)")
                registered_count += 1
            except Exception as e:
                logger.error(f"    ✗ Failed to register {candidate.name}: {e}")
        
        logger.info(f"  ✅ Registered {registered_count}/{len(candidates)} candidates")
        
        # Note: Actual backtesting happens in a separate process/module
        # For Phase 1, we're just registering candidates
        logger.info("  💡 Backtest these candidates with: python -m titan_system.factory.backtest_candidates")
    
    # ==================== MONITORING ====================
    
    def _monitor_live_strategies(self):
        """Monitor health of live strategies and auto-retire if needed."""
        logger.info("🔍 Monitoring live strategies...")
        
        live_strategies = self.registry.get_live_strategies()
        
        if not live_strategies:
            logger.info("  No live strategies to monitor")
            return
        
        for strategy in live_strategies:
            strategy_id = strategy['id']
            name = strategy['genome']['name'] if isinstance(strategy['genome'], dict) else "Unknown"
            
            # Check kill switches
            retired, reason = self._check_kill_switches(strategy)
            
            if retired:
                logger.warning(f"  🔴 RETIRING: {name} - {reason}")
                self.registry.update_status(
                    strategy_id,
                    StrategyRegistry.STATUS_RETIRED,
                    reason
                )
            else:
                # Strategy is healthy
                sharpe = strategy.get('live_sharpe', 0)
                pnl = strategy.get('live_pnl', 0)
                dd = strategy.get('live_drawdown', 0) * 100
                logger.info(f"  ✅ {name}: Sharpe={sharpe:.2f}, PnL=${pnl:.2f}, DD={dd:.1f}%")
    
    def _check_kill_switches(self, strategy: Dict) -> tuple:
        """
        Check if strategy should be auto-retired.
        
        Returns:
            (should_retire: bool, reason: str)
        """
        # Kill Switch 1: Excessive Drawdown
        if strategy.get('live_drawdown', 0) > cfg.MAX_STRATEGY_DRAWDOWN:
            return (True, f"Drawdown {strategy['live_drawdown']*100:.1f}% > {cfg.MAX_STRATEGY_DRAWDOWN*100}%")
        
        # Kill Switch 2: Consecutive Losses
        if strategy.get('consecutive_losses', 0) >= cfg.AUTO_RETIRE_CONSECUTIVE_LOSSES:
            return (True, f"{strategy['consecutive_losses']} consecutive losses")
        
        # Kill Switch 3: Live Sharpe << Backtest Sharpe (edge decay)
        live_sharpe = strategy.get('live_sharpe', 0)
        bt_sharpe = strategy.get('bt_sharpe', 0)
        live_trades = strategy.get('live_trades', 0)
        
        if live_trades >= 30 and live_sharpe < 0.5 and bt_sharpe > 1.5:
            return (True, f"Edge decay: Live Sharpe {live_sharpe:.2f} << Backtest {bt_sharpe:.2f}")
        
        # Kill Switch 4: Inactive (no trades in 7 days)
        last_trade = strategy.get('last_trade_time')
        if last_trade:
            try:
                last_trade_dt = datetime.fromisoformat(last_trade)
                days_since = (datetime.now() - last_trade_dt).days
                if days_since > 7:
                    return (True, f"Inactive for {days_since} days")
            except:
                pass
        
        return (False, "Healthy")
    
    def _check_paper_promotions(self):
        """Check if any paper trading strategies are ready for live promotion."""
        logger.info("📊 Checking paper trading performance...")
        
        paper_strategies = self.registry.get_paper_strategies()
        
        if not paper_strategies:
            logger.info("  No paper strategies to evaluate")
            return
        
        for strategy in paper_strategies:
            strategy_id = strategy['id']
            name = strategy['genome']['name'] if isinstance(strategy['genome'], dict) else "Unknown"
            
            # Check if ready for promotion
            should_promote, reason = self._should_promote_to_live(strategy)
            
            if should_promote:
                # Check if we have capacity for new live strategy
                if self.portfolio_state['live_count'] >= cfg.MAX_LIVE_STRATEGIES:
                    logger.info(f"  ⏸  {name} ready but max live limit reached")
                    continue
                
                logger.info(f"  🚀 PROMOTING: {name} - {reason}")
                self.registry.update_status(strategy_id, StrategyRegistry.STATUS_LIVE)
                
                # TODO: Actually deploy the strategy to autonomous_bot
                # For Phase 1, just updating status
                logger.info(f"  💡 Deploy with: python scripts/deploy_strategy.py {strategy_id}")
            else:
                logger.info(f"  ⏳ {name}: {reason}")
    
    def _should_promote_to_live(self, strategy: Dict) -> tuple:
        """
        Determine if paper strategy should be promoted to live.
        
        Returns:
            (should_promote: bool, reason: str)
        """
        created_at = datetime.fromisoformat(strategy['created_at'])
        days_in_paper = (datetime.now() - created_at).days
        
        # Rule 1: Must complete minimum paper trading period
        if days_in_paper < cfg.PAPER_TRADING_DAYS:
            return (False, f"Day {days_in_paper}/{cfg.PAPER_TRADING_DAYS} in paper trading")
        
        # Rule 2: Must have minimum number of trades
        live_trades = strategy.get('live_trades', 0)
        if live_trades < cfg.PAPER_MIN_TRADES:
            return (False, f"Only {live_trades}/{cfg.PAPER_MIN_TRADES} trades")
        
        # Rule 3: Must maintain minimum Sharpe
        live_sharpe = strategy.get('live_sharpe', 0)
        if live_sharpe < cfg.PAPER_PROMOTION_SHARPE:
            return (False, f"Sharpe {live_sharpe:.2f} < {cfg.PAPER_PROMOTION_SHARPE}")
        
        # Rule 4: Check drawdown
        live_dd = strategy.get('live_drawdown', 0)
        if live_dd > 0.15:  #15% DD limit in paper
            return (False, f"Drawdown {live_dd*100:.1f}% too high")
        
        # All checks passed
        return (True, f"Passed paper evaluation: {live_trades} trades, Sharpe {live_sharpe:.2f}")
    
    # ==================== RISK MANAGEMENT ====================
    
    def _check_portfolio_risk(self) -> bool:
        """
        Check portfolio-level risk limits.
        
        Returns:
            True if portfolio is healthy, False if emergency stop needed
        """
        # Refresh portfolio state
        self.portfolio_state = self._get_portfolio_state()
        
        # Currently, just checking drawdown
        # TODO: Add leverage, correlation, VaR checks
        
        max_dd = self.portfolio_state.get('max_drawdown', 0)
        
        if max_dd > cfg.MAX_PORTFOLIO_DRAWDOWN:
            logger.error(f"🚨 EMERGENCY: Portfolio DD {max_dd*100:.1f}% > {cfg.MAX_PORTFOLIO_DRAWDOWN*100}%")
            # TODO: Trigger emergency stop of all strategies
            return False
        
        return True
    
    def _can_generate_more(self) -> bool:
        """Check if we can generate more strategies."""
        return (self.portfolio_state['paper_count'] < cfg.MAX_PAPER_STRATEGIES and
                self.portfolio_state['live_count'] < cfg.MAX_LIVE_STRATEGIES)
    
    # ==================== REPORTING ====================
    
    def _get_portfolio_state(self) -> Dict:
        """Get current portfolio metrics from registry."""
        return self.registry.get_portfolio_metrics()
    
    def _print_portfolio_summary(self):
        """Print portfolio status summary."""
        state = self.portfolio_state
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("PORTFOLIO SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Live Strategies:  {state['live_count']}/{cfg.MAX_LIVE_STRATEGIES}")
        logger.info(f"Paper Strategies: {state['paper_count']}/{cfg.MAX_PAPER_STRATEGIES}")
        logger.info(f"Retired Total:    {state['retired_count']}")
        logger.info(f"")
        logger.info(f"Total PnL:        ${state['total_pnl']:.2f}")
        logger.info(f"Avg Sharpe:       {state['avg_sharpe']:.2f}")
        logger.info(f"Max Drawdown:     {state['max_drawdown']*100:.1f}%")
        logger.info(f"Total Trades:     {state['total_trades']}")
        logger.info("=" * 60)


# ==================== CLI ENTRY POINT ====================

def main():
    """Main entry point for running the factory."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Strategy Factory - Continuous Edge Discovery")
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single',
                        help='Run mode: single cycle or continuous')
    parser.add_argument('--cycle-hours', type=int, default=cfg.FACTORY_CYCLE_HOURS,
                        help='Hours between cycles (continuous mode)')
    
    args = parser.parse_args()
    
    factory = StrategyFactory()
    
    if args.mode == 'single':
        factory.run_cycle()
    else:
        factory.run_continuous(cycle_hours=args.cycle_hours)


if __name__ == "__main__":
    main()
