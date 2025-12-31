"""
Category-Based ORB Backtest Runner
==================================
Backtests the Opening Range Breakout strategy across different symbol categories
(Forex, Commodities, Indices, Crypto) using REAL symbols from MT5.

Author: Titan System
"""

import MetaTrader5 as mt5
import pandas as pd
import logging
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import defaultdict

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.multi_symbol.backtester import SimpleBacktester, BacktestResult
from titan_system.multi_symbol.universe_scanner import UniverseScanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("ORB_Backtest")


def get_available_symbols_from_mt5() -> Dict[str, List[str]]:
    """
    Get REAL symbols directly from MT5, categorized by type.
    No hardcoding - uses actual symbols available in the broker.
    """
    if not mt5.initialize():
        logger.error(f"MT5 initialization failed: {mt5.last_error()}")
        return {}
    
    # Get all symbols from MT5
    symbols = mt5.symbols_get()
    if symbols is None:
        logger.error("Failed to get symbols from MT5")
        return {}
    
    categories = defaultdict(list)
    
    for sym in symbols:
        # Only tradeable symbols
        if sym.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
            continue
        
        name = sym.name.upper()
        
        # Categorize based on symbol characteristics
        if any(crypto in name for crypto in ['BTC', 'ETH', 'XRP', 'LTC', 'DOGE', 'SOL', 'ADA', 'CRYPTO']):
            categories['crypto'].append(sym.name)
        elif any(comm in name for comm in ['XAU', 'GOLD', 'XAG', 'SILVER', 'OIL', 'WTI', 'BRENT', 'NATGAS', 'COPPER', 'PLAT']):
            categories['commodity'].append(sym.name)
        elif any(idx in name for idx in ['US30', 'US500', 'US100', 'NAS100', 'SPX', 'DAX', 'FTSE', 'NIK', 'DJ30', 'NDX', 'US2000', 'VIX']):
            categories['index'].append(sym.name)
        else:
            # Check if it's a forex pair (6-7 chars, ends in common currencies)
            if len(sym.name) <= 10 and any(curr in name for curr in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD']):
                categories['forex'].append(sym.name)
    
    # Log what we found
    for cat, syms in categories.items():
        logger.info(f"Found {len(syms)} {cat.upper()} symbols: {syms[:5]}...")
    
    return dict(categories)


def validate_symbol_data(symbol: str) -> bool:
    """Check if we can get data for a symbol."""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 10)
    return rates is not None and len(rates) > 0


def run_category_backtest(
    category: str, 
    symbols: List[str], 
    strategy: str = 'ORB',
    days: int = 30,
    max_symbols: int = 20
) -> List[BacktestResult]:
    """
    Run backtest on symbols in a category.
    Validates data availability before testing.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"BACKTESTING {strategy} on {category.upper()}")
    logger.info(f"{'='*60}")
    
    # Validate which symbols have data
    valid_symbols = []
    for sym in symbols[:max_symbols * 2]:  # Check more than needed
        if validate_symbol_data(sym):
            valid_symbols.append(sym)
            if len(valid_symbols) >= max_symbols:
                break
        else:
            logger.warning(f"  Skipping {sym} - no data available")
    
    if not valid_symbols:
        logger.warning(f"No valid symbols found for {category}")
        return []
    
    logger.info(f"Testing {len(valid_symbols)} symbols: {valid_symbols}")
    
    # Run backtest
    bt = SimpleBacktester()
    results = []
    
    for sym in valid_symbols:
        try:
            result = bt.run(sym, strategy, days)
            results.append(result)
            
            # Print individual result
            status = "✅" if result.confidence_score >= 50 else "⚠️" if result.total_trades > 0 else "❌"
            logger.info(f"  {status} {sym:12} | Trades: {result.total_trades:3} | "
                       f"WR: {result.win_rate:5.1f}% | PF: {result.profit_factor:5.2f} | "
                       f"Conf: {result.confidence_score:3.0f}")
        except Exception as e:
            logger.error(f"  ❌ {sym}: {e}")
    
    return results


def generate_summary_report(all_results: Dict[str, List[BacktestResult]]) -> str:
    """Generate a comprehensive markdown report."""
    
    lines = []
    lines.append("# ORB Backtest Results by Category")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Strategy:** Opening Range Breakout (ORB)")
    lines.append(f"**Backtest Period:** Last 30 days\n")
    
    # Summary table
    lines.append("## Category Summary\n")
    lines.append("| Category | Symbols | Avg Win Rate | Avg Profit Factor | Best Symbol | Worst Symbol |")
    lines.append("|----------|---------|--------------|-------------------|-------------|--------------|")
    
    category_stats = {}
    
    for category, results in all_results.items():
        if not results:
            continue
        
        valid_results = [r for r in results if r.total_trades > 0]
        if not valid_results:
            lines.append(f"| {category.upper()} | {len(results)} | N/A | N/A | N/A | N/A |")
            continue
        
        avg_wr = sum(r.win_rate for r in valid_results) / len(valid_results)
        pf_values = [r.profit_factor for r in valid_results if r.profit_factor != float('inf')]
        avg_pf = sum(pf_values) / len(pf_values) if pf_values else 0
        
        best = max(valid_results, key=lambda r: r.confidence_score)
        worst = min(valid_results, key=lambda r: r.confidence_score)
        
        category_stats[category] = {
            'avg_win_rate': avg_wr,
            'avg_profit_factor': avg_pf,
            'best': best,
            'worst': worst,
            'count': len(valid_results)
        }
        
        lines.append(f"| **{category.upper()}** | {len(valid_results)} | {avg_wr:.1f}% | {avg_pf:.2f} | "
                    f"{best.symbol} ({best.confidence_score:.0f}) | {worst.symbol} ({worst.confidence_score:.0f}) |")
    
    # Detailed results per category
    for category, results in all_results.items():
        if not results:
            continue
        
        lines.append(f"\n## {category.upper()} Detailed Results\n")
        lines.append("| Symbol | Trades | Wins | Losses | Win Rate | Profit Factor | Expectancy | Confidence |")
        lines.append("|--------|--------|------|--------|----------|---------------|------------|------------|")
        
        for r in sorted(results, key=lambda x: x.confidence_score, reverse=True):
            pf_str = f"{r.profit_factor:.2f}" if r.profit_factor != float('inf') else "∞"
            lines.append(f"| {r.symbol} | {r.total_trades} | {r.wins} | {r.losses} | "
                        f"{r.win_rate:.1f}% | {pf_str} | {r.expectancy:.5f} | {r.confidence_score:.0f} |")
    
    # Recommendations
    lines.append("\n## Recommendations\n")
    
    if category_stats:
        best_cat = max(category_stats.items(), key=lambda x: x[1]['avg_win_rate'])
        lines.append(f"- **Best Performing Category:** {best_cat[0].upper()} with {best_cat[1]['avg_win_rate']:.1f}% avg win rate")
        
        all_best = [stats['best'] for stats in category_stats.values()]
        if all_best:
            top_symbol = max(all_best, key=lambda r: r.confidence_score)
            lines.append(f"- **Top Symbol Overall:** {top_symbol.symbol} with confidence score {top_symbol.confidence_score:.0f}")
    
    return "\n".join(lines)


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("  ORB CATEGORY BACKTEST - Using REAL MT5 Symbols")
    print("="*70 + "\n")
    
    # Get real symbols from MT5
    logger.info("Fetching symbols from MT5...")
    categories = get_available_symbols_from_mt5()
    
    if not categories:
        logger.error("No symbols found. Is MT5 running and connected?")
        return
    
    # Run backtest for each category
    all_results = {}
    
    for category in ['forex', 'commodity', 'index', 'crypto']:
        symbols = categories.get(category, [])
        if symbols:
            results = run_category_backtest(
                category=category,
                symbols=symbols,
                strategy='ORB',
                days=30,
                max_symbols=15  # Test up to 15 symbols per category
            )
            all_results[category] = results
        else:
            logger.warning(f"No symbols found for {category}")
            all_results[category] = []
    
    # Generate and save report
    report = generate_summary_report(all_results)
    
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'ORB_CATEGORY_BACKTEST_REPORT.md'
    )
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Report saved to: {report_path}")
    logger.info(f"{'='*60}")
    
    # Print summary to console
    print("\n" + report)
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
