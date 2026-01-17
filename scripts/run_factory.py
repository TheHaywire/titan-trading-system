"""
Strategy Factory - Entry Point Script
=====================================
Runs the Strategy Factory orchestrator.

Usage:
    python scripts/run_factory.py --mode single
    python scripts/run_factory.py --mode continuous --cycle-hours 24
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from titan_system.factory.strategy_factory import StrategyFactory
from titan_system.factory import factory_config as cfg


def main():
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
