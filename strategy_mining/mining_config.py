"""
Configuration module for Brute-Force Strategy Mining & Execution Engine
All system parameters, strategy ranges, and risk settings in one place.
"""

from datetime import datetime
from typing import List, Dict, Tuple

# ============================================================================
# MT5 CONNECTION SETTINGS
# ============================================================================
MT5_ACCOUNT = None  # Set to None for default account
MT5_PASSWORD = None
MT5_SERVER = None
MT5_TIMEOUT_MS = 60000
MT5_MAGIC_NUMBER = 777777  # Unique identifier for this system's trades

# ============================================================================
# DATA FETCHING SETTINGS
# ============================================================================
# SNIPER_LIST: Focused set of high-alpha symbols for faster mining
SNIPER_LIST = [
    'GOLD', 'XAUUSD', 'US100', 'US100Cash', 'US30', 'US30Cash', 
    'BTCUSD', 'EURUSD', 'GBPUSD', 'GER40'
]

# Batch Processing Settings
USE_SNIPER_MODE = False  # If False, mine ALL visible symbols in batches
BATCH_SIZE = 100  # Number of symbols to process per batch (lower = more frequent updates)

TIMEFRAMES = {
    'M15': 15,
    'H1': 60,
    'H4': 240
}

# Number of bars to fetch for backtesting (higher = more data, longer runtime)
LOOKBACK_BARS = 5000

# Parallel fetching settings
MAX_WORKERS = 10  # Concurrent threads for data fetching

# ============================================================================
# STRATEGY PARAMETER GRIDS
# ============================================================================

# Mean Reversion (Z-Score VWAP) Parameters
MEAN_REVERSION_PARAMS = {
    'z_thresholds': [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5],
    'vwap_window': [20, 50, 100],  # VWAP calculation window
    'std_window': [20, 50],  # Rolling standard deviation window
}

# Trend Following (Dual-EMA Crossover) Parameters
TREND_FOLLOWING_PARAMS = {
    'ema_combinations': [
        (5, 20), (8, 21), (10, 30), (13, 34),
        (21, 55), (34, 89), (50, 200)
    ]
}

# Volatility Expansion (Keltner Breakout) Parameters
VOLATILITY_EXPANSION_PARAMS = {
    'atr_period': [14, 20],
    'keltner_multipliers': [1.5, 2.0, 2.5, 3.0, 3.5],
    'ema_period': [20, 50]  # Middle band (basis)
}

# ============================================================================
# BACKTESTING SETTINGS
# ============================================================================
COMMISSION_PCT = 0.0  # Commission as % of trade value (e.g., 0.0005 = 0.05%)
SLIPPAGE_PIPS = 0.5  # Average slippage per trade in pips

# Performance filters (minimum requirements to consider a strategy)
MIN_PROFIT_FACTOR = 1.8
MIN_TRADES = 30  # Minimum number of trades for statistical significance
MIN_SHARPE_RATIO = 0.5

# ============================================================================
# WALK-FORWARD ANALYSIS SETTINGS
# ============================================================================
WFA_NUM_WINDOWS = 5  # Number of time windows for walk-forward
WFA_IN_SAMPLE_PCT = 0.7  # 70% in-sample, 30% out-of-sample per window
WFA_MIN_OOS_PROFITABLE_WINDOWS = 4  # Must be profitable in 4 out of 5 OOS windows
MIN_CUMULATIVE_RETURN = 0.01  # Minimum 1% cumulative return across all OOS windows
FORCE_REMINE = False  # If False, load existing results from disk if available

# ============================================================================
# DYNAMIC RISK MANAGEMENT SETTINGS
# ============================================================================

# Position Sizing
KELLY_FRACTION_MIN = 0.5  # Minimum Kelly multiplier (conservative)
KELLY_FRACTION_MAX = 2.5  # Maximum Kelly multiplier (aggressive during high confidence)
KELLY_FRACTION_DEFAULT = 1.0  # Default Kelly multiplier

# Per-Trade Risk Limits
MIN_RISK_PER_TRADE_PCT = 0.3  # Minimum risk per trade (during drawdown/low confidence)
MAX_RISK_PER_TRADE_PCT = 2.5  # Maximum risk per trade (during high confidence/win streaks)
DEFAULT_RISK_PER_TRADE_PCT = 1.0  # Default risk per trade

# Confidence-Based Scaling
CONFIDENCE_THRESHOLD_HIGH = 0.8  # Above this = aggressive sizing
CONFIDENCE_THRESHOLD_LOW = 0.5  # Below this = conservative sizing
CONFIDENCE_LOOKBACK_TRADES = 20  # Number of recent trades to calculate confidence

# Volatility Adjustment
VOLATILITY_LOW_THRESHOLD = 0.7  # If ATR < 0.7 × historical, increase position
VOLATILITY_HIGH_THRESHOLD = 1.5  # If ATR > 1.5 × historical, decrease position
VOLATILITY_MULTIPLIER_LOW = 1.3  # Position multiplier during low volatility
VOLATILITY_MULTIPLIER_HIGH = 0.7  # Position multiplier during high volatility

# Win-Streak Acceleration
WIN_STREAK_MIN = 3  # Minimum consecutive wins to trigger acceleration
WIN_STREAK_MIN_PROFIT_R = 3.0  # Minimum total profit in R-multiples
PYRAMID_MAX_POSITIONS = 3  # Maximum positions in same direction/symbol
PYRAMID_MULTIPLIERS = [1.0, 1.25, 1.5]  # Size multipliers for positions 1, 2, 3

# Trailing Stops & Profit Taking
BREAKEVEN_TRIGGER_R = 1.0  # Move to breakeven at +1R
PARTIAL_CLOSE_1_R = 2.0  # Take 50% profit at +2R
PARTIAL_CLOSE_1_PCT = 0.5  # Close 50% of position
PARTIAL_CLOSE_2_R = 4.0  # Take additional 25% at +4R
PARTIAL_CLOSE_2_PCT = 0.25  # Close 25% more (total 75% closed)
TRAILING_STOP_ATR_MULTIPLIER = 2.0  # Trail SL at Entry + (2 × ATR)

# Drawdown-Based Throttling
DD_THRESHOLD_1 = 0.01  # 1% DD - reduce to 75% risk
DD_THRESHOLD_2 = 0.02  # 2% DD - reduce to 50% risk
DD_THRESHOLD_3 = 0.025  # 2.5% DD - reduce to 25% risk (defensive mode)
DD_CIRCUIT_BREAKER = 0.03  # 3% DD - STOP ALL TRADING

DD_RISK_MULTIPLIER_1 = 0.75
DD_RISK_MULTIPLIER_2 = 0.5
DD_RISK_MULTIPLIER_3 = 0.25

# Portfolio Concentration Limits
MAX_POSITIONS_SAME_ASSET_CLASS = 3  # Max positions in same asset class
MAX_CORRELATED_POSITIONS = 2  # Max positions with correlation > threshold
CORRELATION_THRESHOLD = 0.7  # Correlation threshold for limiting
DIVERSIFICATION_BONUS_RISK_PCT = 0.25  # Extra risk % if well-diversified

# Emergency Controls
LOSER_CUTOFF_R = -1.5  # Auto-close losers exceeding -1.5R
PAUSE_DURATION_HOURS = 24  # Pause duration after circuit breaker
RECOVERY_TEST_RISK_PCT = 0.3  # Micro-trade risk during recovery testing
RECOVERY_TEST_DELAY_HOURS = 6  # Wait 6 hours before recovery testing

# ============================================================================
# EXECUTION LOOP SETTINGS
# ============================================================================
TOP_WINNERS_COUNT = 5  # Number of top strategies to trade live
SIGNAL_CHECK_INTERVAL_SEC = 5  # Check for new signals every 5 seconds
HEARTBEAT_INTERVAL_SEC = 30  # Re-initialize MT5 connection every 30 seconds

# Liquidity Filters
MAX_SPREAD_MULTIPLIER = 2.0  # Only trade if current spread < 2 × average spread
MIN_BOOK_DEPTH_LOTS = 1.0  # Minimum market book depth required

# Order Execution
ORDER_FILL_TYPE = 'IOC'  # IOC (Immediate or Cancel) or 'FOK' (Fill or Kill)
ORDER_RETRY_ATTEMPTS = 3
ORDER_RETRY_DELAY_SEC = 1

# ============================================================================
# FILE PATHS & LOGGING
# ============================================================================
RESULTS_DIR = "c:/Users/manan/OneDrive/Documents/Metatrader Trading System 7-12-2025/strategy_mining/results"
LOGS_DIR = "c:/Users/manan/OneDrive/Documents/Metatrader Trading System 7-12-2025/strategy_mining/logs"
CACHE_DIR = "c:/Users/manan/OneDrive/Documents/Metatrader Trading System 7-12-2025/strategy_mining/cache"

# Results file naming
MINING_RESULTS_FILE = f"mining_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
WINNERS_FILE = "top_winners.csv"
TRADES_LOG_FILE = "live_trades.csv"

# ============================================================================
# ASSET CLASS DEFINITIONS (for concentration limits)
# ============================================================================
ASSET_CLASSES = {
    'FX_MAJOR': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'],
    'FX_CROSS': ['EURJPY', 'GBPJPY', 'EURGBP', 'AUDNZD', 'EURCHF'],
    'INDICES': ['US100', 'US30', 'SPX500', 'GER40', 'UK100', 'US100Cash', 'US30Cash'],
    'COMMODITIES': ['XAUUSD', 'XAGUSD', 'USOIL', 'UKOIL', 'GOLD', 'SILVER'],
    'CRYPTO': ['BTCUSD', 'ETHUSD', 'XRPUSD', 'BCHUSD', 'LTCUSD']
}

# Symbol correlations (for concentration limits)
# Higher value = more correlated
SYMBOL_CORRELATIONS = {
    ('EURUSD', 'GBPUSD'): 0.75,
    ('EURUSD', 'EURGBP'): 0.82,
    ('XAUUSD', 'GOLD'): 1.0,  # Same asset, different naming
    ('XAGUSD', 'SILVER'): 1.0,
    ('US100', 'US100Cash'): 1.0,
    ('US30', 'US30Cash'): 1.0,
    # Add more as needed
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_asset_class(symbol: str) -> str:
    """Determine asset class for a symbol."""
    for asset_class, symbols in ASSET_CLASSES.items():
        if symbol.upper() in symbols:
            return asset_class
    return 'UNKNOWN'

def get_correlation(symbol1: str, symbol2: str) -> float:
    """Get correlation between two symbols."""
    pair = (symbol1.upper(), symbol2.upper())
    reverse_pair = (symbol2.upper(), symbol1.upper())
    
    if pair in SYMBOL_CORRELATIONS:
        return SYMBOL_CORRELATIONS[pair]
    elif reverse_pair in SYMBOL_CORRELATIONS:
        return SYMBOL_CORRELATIONS[reverse_pair]
    else:
        return 0.0  # Assume uncorrelated if not specified

def get_mt5_timeframe(timeframe_str: str):
    """Convert timeframe string to MT5 constant."""
    import MetaTrader5 as mt5
    
    mapping = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1,
        'W1': mt5.TIMEFRAME_W1,
        'MN1': mt5.TIMEFRAME_MN1,
    }
    
    return mapping.get(timeframe_str.upper(), mt5.TIMEFRAME_H1)
