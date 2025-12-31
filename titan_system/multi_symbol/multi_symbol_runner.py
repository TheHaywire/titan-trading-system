"""
Multi-Symbol Trading Runner
===========================
Main orchestration script that ties all components together.

This is the primary entry point for running the multi-symbol trading system.

Features:
- Scans 1,500+ symbols for liquidity (RVOL > 2.0)
- Applies ORB Trend + Mean Reversion strategies
- Enforces max 5 positions constraint
- Uses 2% fixed fractional risk sizing
- Asyncio-based for high performance

Usage:
    # Dry run (no actual trades)
    python multi_symbol_runner.py --dry-run
    
    # Live trading
    python multi_symbol_runner.py
    
    # Custom settings
    python multi_symbol_runner.py --max-positions 3 --risk 1.5 --interval 120
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from titan_system.multi_symbol.async_engine import AsyncExecutionEngine
from titan_system.multi_symbol.universe_scanner import UniverseScanner
from titan_system.multi_symbol.portfolio_manager import PortfolioManager

# Configure logging
def setup_logging(log_level: str = 'INFO', log_file: str = None):
    """Configure logging for the trading system."""
    
    formatter = logging.Formatter(
        '%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    
    # File handler (if specified)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(level=logging.DEBUG, handlers=handlers)
    
    # Reduce noise from other loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ████████╗██╗████████╗ █████╗ ███╗   ██╗                     ║
║     ╚══██╔══╝██║╚══██╔══╝██╔══██╗████╗  ██║                     ║
║        ██║   ██║   ██║   ███████║██╔██╗ ██║                     ║
║        ██║   ██║   ██║   ██╔══██║██║╚██╗██║                     ║
║        ██║   ██║   ██║   ██║  ██║██║ ╚████║                     ║
║        ╚═╝   ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝                     ║
║                                                                  ║
║         MULTI-SYMBOL ALGORITHMIC TRADING FRAMEWORK              ║
║                                                                  ║
║    • Scans 1,500+ symbols for liquidity                         ║
║    • ORB Trend + Mean Reversion strategies                      ║
║    • Asyncio-powered for speed                                  ║
║    • 2% Fixed Fractional Risk Management                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def run_quick_scan():
    """Run a quick scan to display market conditions."""
    print("\n" + "="*60)
    print("QUICK MARKET SCAN")
    print("="*60)
    
    scanner = UniverseScanner(max_workers=20)
    
    # Scan with lower threshold for demo
    active = scanner.scan_universe(min_rvol=1.5, max_symbols=200)
    
    if not active:
        print("No active symbols found. Market may be closed.")
        return
    
    print(f"\nFound {len(active)} active symbols (RVOL > 1.5)")
    print("\nTop 10 by Relative Volume:")
    print("-" * 60)
    print(f"{'Symbol':<12} {'RVOL':<8} {'ATR%':<8} {'Spread':<8} {'Category':<10}")
    print("-" * 60)
    
    for sym in active[:10]:
        print(f"{sym.symbol:<12} {sym.rvol:<8.2f} {sym.atr_percent:<8.2f} "
              f"{sym.spread:<8} {sym.category:<10}")
    
    # Category summary
    print("\nBy Category:")
    categories = {}
    for sym in active:
        cat = sym.category
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat.upper()}: {count}")


async def run_portfolio_check():
    """Display current portfolio status."""
    print("\n" + "="*60)
    print("PORTFOLIO STATUS")
    print("="*60)
    
    pm = PortfolioManager(max_positions=5)
    summary = pm.get_portfolio_summary()
    
    print(f"\nOpen Positions: {summary['position_count']}/{summary['max_positions']}")
    print(f"Available Slots: {summary['available_slots']}")
    print(f"Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
    
    if summary['symbols']:
        print(f"\nActive Symbols: {', '.join(summary['symbols'])}")
    else:
        print("\nNo active positions.")
    
    if summary['by_category']:
        print("\nBy Category:")
        for cat, count in summary['by_category'].items():
            print(f"  {cat}: {count}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Titan Multi-Symbol Algorithmic Trading Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick market scan (no trading)
  python multi_symbol_runner.py --scan
  
  # Dry run (simulate trading)
  python multi_symbol_runner.py --dry-run
  
  # Live trading with default settings
  python multi_symbol_runner.py
  
  # Custom configuration
  python multi_symbol_runner.py --max-positions 3 --risk 1.5 --interval 120
        """
    )
    
    parser.add_argument('--scan', action='store_true',
                       help='Run quick market scan only (no trading)')
    parser.add_argument('--portfolio', action='store_true',
                       help='Show portfolio status only')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate trading without executing orders')
    parser.add_argument('--max-positions', type=int, default=5,
                       help='Maximum simultaneous positions (default: 5)')
    parser.add_argument('--risk', type=float, default=2.0,
                       help='Risk per trade as %% of balance (default: 2.0)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Scan interval in seconds (default: 60)')
    parser.add_argument('--min-rvol', type=float, default=2.0,
                       help='Minimum RVOL threshold (default: 2.0)')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--log-file', type=str, default=None,
                       help='Log file path (optional)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger("Titan.Runner")
    
    # Print banner
    print_banner()
    
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE TRADING' if not args.scan else 'SCAN ONLY'}")
    print(f"Config: Max Positions={args.max_positions}, Risk={args.risk}%, Interval={args.interval}s")
    
    # Handle special modes
    if args.scan:
        await run_quick_scan()
        return
    
    if args.portfolio:
        await run_portfolio_check()
        return
    
    # Safety confirmation for live trading
    if not args.dry_run:
        print("\n" + "!"*60)
        print("WARNING: LIVE TRADING MODE")
        print("This will execute REAL trades with REAL money!")
        print("!"*60)
        
        confirm = input("\nType 'EXECUTE' to confirm live trading: ")
        if confirm != 'EXECUTE':
            print("Cancelled. Use --dry-run for simulation mode.")
            return
    
    # Initialize and run engine
    engine = AsyncExecutionEngine(
        max_concurrent=50,
        risk_percent=args.risk,
        max_positions=args.max_positions,
        scan_interval=args.interval
    )
    
    try:
        await engine.start(dry_run=args.dry_run)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        engine.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
