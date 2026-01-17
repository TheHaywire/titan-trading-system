"""
STRATEGY FACTORY - Configuration
================================
Risk limits, performance thresholds, and operational parameters.
"""

# ==================== RISK LIMITS ====================

# Portfolio-Level Controls
MAX_PORTFOLIO_DRAWDOWN = 0.20        # Emergency stop at 20% portfolio DD
MAX_PORTFOLIO_LEVERAGE = 5.0         # Max 5x total exposure
MAX_STRATEGY_ALLOCATION = 0.15       # Max 15% of portfolio per strategy
MAX_CORRELATION_THRESHOLD = 0.70     # Halt new deployments if avg correlation > 0.7

# Per-Strategy Controls
MIN_STRATEGY_SHARPE = 1.0            # Minimum Sharpe to qualify
MIN_WIN_RATE = 0.45                  # Minimum 45% win rate
MIN_PROFIT_FACTOR = 1.3              # Minimum PF
MAX_STRATEGY_DRAWDOWN = 0.25         # Retire if DD > 25%

# Position Sizing
KELLY_FRACTION_CAP = 0.25            # Max Kelly fraction (quarter-Kelly)
DEFAULT_RISK_PER_TRADE = 0.01        # 1% default risk
POSITION_SIZE_RAMP = [0.10, 0.25, 0.50, 1.00]  # Weekly scale-up multipliers

# ==================== DEPLOYMENT RULES ====================

# Paper Trading
PAPER_TRADING_DAYS = 14              # 2 weeks mandatory paper trading
PAPER_MIN_TRADES = 20                # Minimum trades before evaluation
PAPER_PROMOTION_SHARPE = 1.0         # Must maintain Sharpe > 1.0 to promote

# Auto-Approval Thresholds
AUTO_APPROVE_SHARPE = 2.0            # Auto-deploy if Sharpe >= 2.0
MANUAL_REVIEW_SHARPE = 1.5           # Require approval if Sharpe < 1.5
AUTO_RETIRE_CONSECUTIVE_LOSSES = 7   # Auto-retire after 7 straight losses

# ==================== BACKTEST VALIDATION ====================

# Out-of-Sample Requirements
OOS_TRAIN_SPLIT = 0.70               # 70% training, 30% testing
OOS_MIN_RATIO = 0.70                 # OOS Sharpe must be >= 70% of IS Sharpe

# Robustness Tests
MONTE_CARLO_ITERATIONS = 1000        # Number of MC simulations
WALKFORWARD_WINDOWS = 12             # Monthly walk-forward periods
PARAMETER_SENSITIVITY_THRESHOLD = 0.30  # Max % degradation allowed

# Minimum Data Requirements
MIN_BACKTEST_DAYS = 365              # At least 1 year of data
MIN_BACKTEST_TRADES = 50             # At least 50 trades

# ==================== FACTORY OPERATION ====================

# Generation Cycles
FACTORY_CYCLE_HOURS = 1              # Run full cycle every hour
MAX_CANDIDATES_PER_CYCLE = 200       # Generate 200 new strategies per cycle
EVOLUTION_GENERATIONS = 10           # Run 10 evolution cycles

# Strategy Limits
MAX_LIVE_STRATEGIES = 20             # Max concurrent live strategies
MAX_PAPER_STRATEGIES = 25            # Max concurrent paper strategies

# Reoptimization
REOPTIMIZE_INTERVAL_DAYS = 3         # More frequent re-optimization
SIGNIFICANT_IMPROVEMENT_THRESHOLD = 1.15  # 15% better to trigger migration

# ==================== PERFORMANCE MONITORING ====================

# Health Check Intervals
HEALTH_CHECK_INTERVAL_MINUTES = 2    # Check strategy health every 2 min
PORTFOLIO_CHECK_INTERVAL_MINUTES = 1 # Check portfolio risk every minute

# Alert Thresholds
ALERT_DRAWDOWN_WARNING = 0.15        # Warn at 15% DD
ALERT_CORRELATION_WARNING = 0.65     # Warn if correlation approaching limit
ALERT_VOLATILITY_SPIKE = 0.05        # Warn if daily vol > 5%

# ==================== LIQUIDITY FILTERS ====================
# CRITICAL: Only trade liquid symbols to avoid spread-destroying profits

MAX_SPREAD_PIPS = 100                # Reject symbols with spread >= 100
MIN_TRADE_MODE = 4                   # Require full trading enabled
MAX_SPREAD_RATIO = 0.0005            # Spread < 0.05% of price
MIN_HOURLY_VOLUME = 100              # Minimum tick volume per hour

# ==================== DATA & EXECUTION ====================

# Symbols Universe (for generation)
# PRIORITIZED: Liquid symbols with tight spreads
SYMBOL_UNIVERSE = [
    "GOLD", "SILVER", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD",
    "US100Cash", "GER40Cash", "US30Cash", "JP225Cash", "UK100Cash"
]

# Timeframes (for generation)
TIMEFRAME_UNIVERSE = ["M5", "M15", "M30", "H1", "H4"]

# Magic Number Range (for auto-generated strategies)
MAGIC_NUMBER_START = 999000
MAGIC_NUMBER_END = 999999

# Transaction Costs (for realistic backtesting)
TRANSACTION_COSTS = {
    "GOLD": {"spread": 0.30, "commission": 0},
    "SILVER": {"spread": 0.02, "commission": 0},
    "EURUSD": {"spread": 0.00010, "commission": 0},
    "BTCUSD": {"spread": 10.0, "commission": 0},
}

SLIPPAGE_TICKS = {
    "default": 2,          
    "BTCUSD": 5,           
    "GOLD": 3
}

# ==================== EVOLUTION PARAMETERS ====================

# Genetic Algorithm
SURVIVAL_RATE = 0.30                 # Keep top 30% performers
MUTATION_RATE = 0.35                 # 35% chance to mutate
MUTANTS_PER_SURVIVOR = 5             # Create 5 mutants per survivor
NEW_BLOOD_PER_GENERATION = 20        # Add 20 fresh ideas each generation

# Parameter Ranges (for mutation/generation)
PARAMETER_RANGES = {
    "RSI": {
        "period": (2, 50),
        "oversold": (10, 40),
        "overbought": (60, 90)
    },
    "EMA": {
        "fast": (5, 50),
        "slow": (20, 200)
    },
    "BB": {
        "period": (10, 50),
        "std": (1.0, 4.0)
    },
    "ATR": {
        "period": (5, 30),
        "multiplier": (0.5, 5.0)
    },
    "KALMAN": {
        "process_variance": (0.00001, 0.001),
        "measurement_variance": (0.001, 0.05)
    },
    "ADX": {
        "period": (7, 30),
        "threshold": (15, 35)
    },
    "exit_rules": {
        "tp_mult": (0.5, 10.0),
        "sl_atr": (0.2, 5.0)
    }
}

# ==================== LOGGING & STORAGE ====================

LOG_LEVEL = "INFO"                   # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "logs/strategy_factory.log"

# Database
STRATEGY_DB = "data/strategy_factory.db"

# Auto-Generated Code Directory
AUTOGEN_DIR = "titan_system/strategies/autogen"

# Backtest Results Directory
BACKTEST_RESULTS_DIR = "data/backtest_results"
