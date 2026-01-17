"""
Liquidity Filter Utility
========================
Pre-checks symbols for liquidity before backtesting or trading.
Prevents illiquid symbols from polluting the alpha registry.
"""
import MetaTrader5 as mt5
from typing import Optional, Dict, List, Tuple

# Import config thresholds
try:
    from titan_system.factory import factory_config as cfg
    MAX_SPREAD = cfg.MAX_SPREAD_PIPS
    MIN_TRADE_MODE = cfg.MIN_TRADE_MODE
except ImportError:
    MAX_SPREAD = 100
    MIN_TRADE_MODE = 4


def check_symbol_liquidity(symbol: str) -> Tuple[bool, Dict]:
    """
    Check if a symbol is liquid enough to trade.
    
    Returns:
        (is_liquid: bool, details: dict)
    """
    if not mt5.initialize():
        return False, {"error": "MT5 not initialized"}
    
    info = mt5.symbol_info(symbol)
    if not info:
        return False, {"error": f"Symbol {symbol} not found"}
    
    details = {
        "symbol": symbol,
        "spread": info.spread,
        "trade_mode": info.trade_mode,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "description": info.description
    }
    
    # Check liquidity criteria
    is_liquid = True
    reasons = []
    
    if info.spread >= MAX_SPREAD:
        is_liquid = False
        reasons.append(f"Spread too wide: {info.spread} >= {MAX_SPREAD}")
    
    if info.trade_mode < MIN_TRADE_MODE:
        is_liquid = False
        reasons.append(f"Trade mode restricted: {info.trade_mode} < {MIN_TRADE_MODE}")
    
    details["is_liquid"] = is_liquid
    details["rejection_reasons"] = reasons
    
    return is_liquid, details


def filter_liquid_symbols(symbols: List[str]) -> List[str]:
    """
    Filter a list of symbols to only include liquid ones.
    """
    liquid = []
    for sym in symbols:
        is_liq, _ = check_symbol_liquidity(sym)
        if is_liq:
            liquid.append(sym)
    return liquid


def get_liquid_universe(max_spread: int = 100) -> List[Dict]:
    """
    Get all MT5 symbols that pass liquidity checks.
    """
    if not mt5.initialize():
        return []
    
    all_symbols = mt5.symbols_get()
    liquid = []
    
    for sym in all_symbols:
        info = mt5.symbol_info(sym.name)
        if info and info.trade_mode >= MIN_TRADE_MODE and info.spread < max_spread:
            liquid.append({
                "symbol": sym.name,
                "spread": info.spread,
                "description": sym.description
            })
    
    # Sort by spread (tightest first)
    liquid.sort(key=lambda x: x["spread"])
    return liquid


def validate_alpha_liquidity(alpha: Dict) -> Tuple[bool, str]:
    """
    Validate that an alpha entry is on a liquid symbol.
    
    Args:
        alpha: Dict with 'symbol' key
        
    Returns:
        (is_valid: bool, reason: str)
    """
    symbol = alpha.get("symbol")
    if not symbol:
        return False, "No symbol specified"
    
    is_liquid, details = check_symbol_liquidity(symbol)
    if not is_liquid:
        return False, f"Illiquid: {', '.join(details.get('rejection_reasons', ['unknown']))}"
    
    return True, f"Liquid (spread={details['spread']})"


if __name__ == "__main__":
    # Test the filter
    mt5.initialize()
    
    test_symbols = ["GOLD", "US100Cash", "Fincantieri", "CGG", "EURUSD"]
    print("=== LIQUIDITY CHECK TEST ===\n")
    
    for sym in test_symbols:
        is_liq, details = check_symbol_liquidity(sym)
        status = "✅ LIQUID" if is_liq else "❌ ILLIQUID"
        print(f"{sym}: {status}")
        if not is_liq:
            print(f"   Reasons: {details.get('rejection_reasons', [])}")
        else:
            print(f"   Spread: {details['spread']}")
    
    mt5.shutdown()
