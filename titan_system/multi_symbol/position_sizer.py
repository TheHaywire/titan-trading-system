"""
Position Sizer - Risk-Based Position Sizing
============================================
Implements Fixed Fractional position sizing with MT5 constraint validation.

Features:
- Risk-based lot calculation (default 2% risk per trade)
- Validates against symbol_info.volume_min and volume_step
- Supports all asset classes (Forex, Gold, Indices, Crypto)
- Kelly Criterion influence for edge-based sizing
"""

import MetaTrader5 as mt5
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("Titan.MultiSymbol.PositionSizer")


@dataclass
class PositionSizeResult:
    """Result of position sizing calculation."""
    lot_size: float
    risk_amount: float
    risk_percent: float
    sl_distance: float
    tick_value: float
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    is_valid: bool
    message: str


def get_symbol_info(symbol: str) -> Optional[dict]:
    """
    Get symbol trading constraints from MT5.
    
    Returns:
        dict with volume_min, volume_max, volume_step, tick_value, contract_size
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    
    return {
        'volume_min': info.volume_min,
        'volume_max': info.volume_max,
        'volume_step': info.volume_step,
        'tick_value': info.trade_tick_value,
        'tick_size': info.trade_tick_size,
        'contract_size': info.trade_contract_size,
        'point': info.point,
        'digits': info.digits,
        'currency_base': info.currency_base,
        'currency_profit': info.currency_profit,
    }


def calculate_tick_value(symbol: str, lot_size: float = 1.0) -> float:
    """
    Calculate the monetary value of one tick movement for a given lot size.
    
    For standard forex: 1 lot = 100,000 units, 1 pip = ~$10
    For gold (XAUUSD): 1 lot = 100 oz, 1 tick ($0.01) = $1
    
    Returns:
        Value in account currency per tick
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.0
    
    # MT5 provides tick_value directly (value per tick for 1 standard lot)
    tick_value = info.trade_tick_value * lot_size
    
    return tick_value


def calculate_position_size(
    account_balance: float,
    entry_price: float,
    stop_loss_price: float,
    risk_percent: float = 2.0,
    symbol: str = None
) -> PositionSizeResult:
    """
    Calculate optimal lot size based on risk parameters.
    
    Formula:
        Risk Amount = Balance * (Risk% / 100)
        SL Distance (ticks) = |Entry - SL| / tick_size
        Lot Size = Risk Amount / (SL Distance * Tick Value)
    
    Constraints applied:
        - lot_size >= symbol_info.volume_min
        - lot_size <= symbol_info.volume_max
        - lot_size rounded to symbol_info.volume_step
    
    Args:
        account_balance: Current account balance
        entry_price: Planned entry price
        stop_loss_price: Stop loss price
        risk_percent: Risk as percentage of balance (default 2%)
        symbol: MT5 symbol for constraint validation
        
    Returns:
        PositionSizeResult with lot_size and calculation details
    """
    # Validate inputs
    if account_balance <= 0:
        return PositionSizeResult(
            lot_size=0.0, risk_amount=0, risk_percent=risk_percent,
            sl_distance=0, tick_value=0, contract_size=0,
            volume_min=0, volume_max=0, volume_step=0,
            is_valid=False, message="Invalid account balance"
        )
    
    if entry_price <= 0 or stop_loss_price <= 0:
        return PositionSizeResult(
            lot_size=0.0, risk_amount=0, risk_percent=risk_percent,
            sl_distance=0, tick_value=0, contract_size=0,
            volume_min=0, volume_max=0, volume_step=0,
            is_valid=False, message="Invalid price values"
        )
    
    # Calculate risk amount
    risk_amount = account_balance * (risk_percent / 100.0)
    
    # Calculate SL distance in price terms
    sl_distance = abs(entry_price - stop_loss_price)
    
    if sl_distance == 0:
        return PositionSizeResult(
            lot_size=0.0, risk_amount=risk_amount, risk_percent=risk_percent,
            sl_distance=0, tick_value=0, contract_size=0,
            volume_min=0, volume_max=0, volume_step=0,
            is_valid=False, message="Stop loss cannot equal entry price"
        )
    
    # Get symbol info if available
    symbol_info = None
    tick_value = 0
    tick_size = 0.0001  # Default for forex
    contract_size = 100000  # Default for forex
    volume_min = 0.01
    volume_max = 100.0
    volume_step = 0.01
    
    if symbol and mt5.initialize():
        info = get_symbol_info(symbol)
        if info:
            symbol_info = info
            tick_value = info['tick_value']
            tick_size = info['tick_size']
            contract_size = info['contract_size']
            volume_min = info['volume_min']
            volume_max = info['volume_max']
            volume_step = info['volume_step']
    
    # Calculate lot size
    # Detect if this is a stock/CFD (contract_size = 1 usually means stock)
    is_stock_cfd = contract_size == 1 or (symbol and not any(
        pattern in symbol.upper() for pattern in 
        ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'XAU', 'GOLD', 'XAG', 
         'US30', 'US500', 'US100', 'DAX', 'FTSE', 'NAS', 'BTC', 'ETH']
    ))
    
    if is_stock_cfd:
        # For stocks: 1 lot = 1 share, risk = price move * shares
        # Simple calculation: shares = risk_amount / sl_distance
        raw_lots = risk_amount / sl_distance if sl_distance > 0 else 1
        # Cap at reasonable share count based on balance
        if entry_price > 0:
            max_shares_by_value = (account_balance * 0.10) / entry_price  # Max 10% of account value
            raw_lots = min(raw_lots, max_shares_by_value)
        logger.debug(f"Stock sizing for {symbol}: {raw_lots:.2f} shares")
        
    elif symbol_info and tick_value > 0:
        # Precise calculation using MT5 symbol info for forex/commodities
        # SL distance in ticks
        sl_ticks = sl_distance / tick_size
        
        # Value per tick for 1 lot
        value_per_tick = tick_value
        
        # Raw lot calculation
        if sl_ticks * value_per_tick > 0:
            raw_lots = risk_amount / (sl_ticks * value_per_tick)
        else:
            raw_lots = volume_min
    else:
        # Fallback calculation without MT5 data
        # Approximate based on common symbol patterns
        raw_lots = _fallback_position_size(
            symbol or "UNKNOWN", 
            account_balance, 
            entry_price, 
            sl_distance, 
            risk_percent
        )
    
    # Round to volume_step
    if volume_step > 0:
        raw_lots = round(raw_lots / volume_step) * volume_step
    
    # Apply constraints
    lot_size = max(volume_min, min(volume_max, raw_lots))
    
    # Round to 2 decimal places (most common)
    lot_size = round(lot_size, 2)
    
    # Safety cap: Never risk more than 5% of account in a single position value
    # Position value = lots * contract_size * price
    if symbol and entry_price > 0 and contract_size > 0:
        max_position_value = account_balance * 0.05  # 5% of account
        # For a stock with contract_size=10, 1 lot = 10 shares, value = 10 * price
        position_value_per_lot = contract_size * entry_price
        max_safe_lots = max_position_value / position_value_per_lot if position_value_per_lot > 0 else volume_min
        
        if lot_size > max_safe_lots and max_safe_lots >= volume_min:
            logger.warning(f"Position size capped from {lot_size:.2f} to {max_safe_lots:.2f} for safety "
                          f"(max 5% account value: ${max_position_value:.0f})")
            lot_size = max_safe_lots
            if volume_step > 0:
                lot_size = round(lot_size / volume_step) * volume_step
            lot_size = max(volume_min, round(lot_size, 2))
    
    # Ensure minimum
    if lot_size < volume_min:
        lot_size = volume_min
    
    is_valid = lot_size >= volume_min and lot_size <= volume_max
    
    return PositionSizeResult(
        lot_size=lot_size,
        risk_amount=risk_amount,
        risk_percent=risk_percent,
        sl_distance=sl_distance,
        tick_value=tick_value,
        contract_size=contract_size,
        volume_min=volume_min,
        volume_max=volume_max,
        volume_step=volume_step,
        is_valid=is_valid,
        message="OK" if is_valid else f"Lot size constrained to {lot_size}"
    )


def _fallback_position_size(
    symbol: str,
    balance: float,
    entry: float,
    sl_distance: float,
    risk_pct: float
) -> float:
    """
    Fallback position sizing when MT5 symbol info unavailable.
    Uses approximations based on common symbol patterns.
    """
    risk_amount = balance * (risk_pct / 100.0)
    symbol_upper = symbol.upper()
    
    # Gold (XAUUSD / GOLD)
    if 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
        # 1 lot = 100 oz, $1 move = $100
        loss_per_lot = sl_distance * 100
        if loss_per_lot > 0:
            return risk_amount / loss_per_lot
    
    # JPY pairs
    elif 'JPY' in symbol_upper and len(symbol_upper) == 6:  # Forex pair like USDJPY
        # 1 pip = 0.01, value ~$10 per lot
        pips = sl_distance / 0.01
        loss_per_lot = pips * 10  # Approximate
        if loss_per_lot > 0:
            return risk_amount / loss_per_lot
    
    # Indices
    elif any(idx in symbol_upper for idx in ['US30', 'US500', 'US100', 'DAX', 'FTSE', 'NAS100', 'SPX500']):
        # Varies significantly by index
        # Approximate: 1 point = $1 per lot
        loss_per_lot = sl_distance * 1
        if loss_per_lot > 0:
            return risk_amount / loss_per_lot
    
    # Crypto
    elif any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'XRP', 'LTC', 'DOGE']):
        # Crypto: 1 lot typically = 1 unit
        # For BTC: $1 move = $1 per lot
        loss_per_lot = sl_distance * 1
        if loss_per_lot > 0:
            lots = risk_amount / loss_per_lot
            return min(lots, 1.0)  # Cap at 1 lot for crypto
    
    # Standard Forex (6 character pairs like EURUSD)
    elif len(symbol_upper) == 6 and symbol_upper.isalpha():
        # 1 pip = 0.0001, value = $10 per lot
        pips = sl_distance / 0.0001
        loss_per_lot = pips * 10
        if loss_per_lot > 0:
            return risk_amount / loss_per_lot
    
    # Stocks/CFDs (anything else - use price-based calculation)
    else:
        # For stocks: 1 share = $1 move = $1 loss
        # SL distance is in price terms
        loss_per_share = sl_distance
        if loss_per_share > 0:
            shares = risk_amount / loss_per_share
            # Cap at reasonable share count based on price
            if entry > 0:
                max_shares = (balance * 0.1) / entry  # Max 10% of balance in any position
                shares = min(shares, max_shares)
            return max(1, round(shares))  # At least 1 share
    
    return 0.01  # Minimum for unknown


def calculate_position_size_with_kelly(
    account_balance: float,
    entry_price: float,
    stop_loss_price: float,
    take_profit_price: float,
    win_rate: float = 0.55,
    base_risk_percent: float = 2.0,
    kelly_fraction: float = 0.5,
    symbol: str = None
) -> PositionSizeResult:
    """
    Position sizing with Kelly Criterion adjustment.
    
    Kelly Formula:
        f* = (p * b - q) / b
        Where:
        - p = probability of win
        - q = probability of loss (1 - p)
        - b = win/loss ratio (reward / risk)
    
    We use Half Kelly (kelly_fraction=0.5) to reduce volatility.
    
    Args:
        account_balance: Current account balance
        entry_price: Planned entry price
        stop_loss_price: Stop loss price
        take_profit_price: Take profit price
        win_rate: Historical win probability (default 55%)
        base_risk_percent: Base risk percentage before Kelly adjustment
        kelly_fraction: Fraction of full Kelly to use (default 0.5 = Half Kelly)
        symbol: MT5 symbol for constraint validation
        
    Returns:
        PositionSizeResult with Kelly-adjusted lot_size
    """
    # Calculate win/loss ratio (b)
    risk_distance = abs(entry_price - stop_loss_price)
    reward_distance = abs(take_profit_price - entry_price)
    
    if risk_distance == 0:
        return calculate_position_size(
            account_balance, entry_price, stop_loss_price, 
            base_risk_percent, symbol
        )
    
    b = reward_distance / risk_distance  # Win/loss ratio
    p = win_rate
    q = 1 - p
    
    # Kelly criterion
    kelly = ((p * b) - q) / b if b > 0 else 0
    
    # Apply Kelly fraction (Half Kelly)
    adjusted_kelly = kelly * kelly_fraction
    
    # Convert to risk percentage (capped at base_risk_percent)
    kelly_risk_pct = min(adjusted_kelly * 100, base_risk_percent * 2)
    kelly_risk_pct = max(kelly_risk_pct, 0.5)  # Minimum 0.5%
    
    # Blend with base risk (50% Kelly, 50% Fixed)
    final_risk_pct = (kelly_risk_pct + base_risk_percent) / 2
    
    logger.debug(f"Kelly Sizing: win_rate={win_rate:.2f}, b={b:.2f}, "
                f"kelly={kelly:.4f}, adj_risk={final_risk_pct:.2f}%")
    
    return calculate_position_size(
        account_balance, entry_price, stop_loss_price, 
        final_risk_pct, symbol
    )


def validate_lot_size(symbol: str, lot_size: float) -> Tuple[float, str]:
    """
    Validate and adjust lot size against MT5 symbol constraints.
    
    Args:
        symbol: MT5 symbol
        lot_size: Proposed lot size
        
    Returns:
        Tuple of (adjusted_lot_size, message)
    """
    if not mt5.initialize():
        return (lot_size, "MT5 not initialized")
    
    info = mt5.symbol_info(symbol)
    if info is None:
        return (lot_size, f"Symbol {symbol} not found")
    
    original = lot_size
    
    # Round to volume_step
    if info.volume_step > 0:
        lot_size = round(lot_size / info.volume_step) * info.volume_step
        lot_size = round(lot_size, 2)
    
    # Apply min/max
    lot_size = max(info.volume_min, min(info.volume_max, lot_size))
    
    if lot_size != original:
        return (lot_size, f"Adjusted from {original} to {lot_size}")
    
    return (lot_size, "OK")


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    if not mt5.initialize():
        print("MT5 init failed - using fallback calculations")
    
    # Test scenarios
    test_cases = [
        # (balance, entry, stop_loss, symbol, description)
        (100, 2000.00, 1995.00, "XAUUSD", "Small account Gold trade"),
        (1000, 1.0850, 1.0800, "EURUSD", "Medium account Forex trade"),
        (10000, 2050.00, 2040.00, "XAUUSD", "Large account Gold trade"),
        (500, 1.2750, 1.2700, "GBPUSD", "GBP trade with $500"),
    ]
    
    print("="*70)
    print("POSITION SIZING TEST")
    print("="*70)
    
    for balance, entry, sl, symbol, desc in test_cases:
        result = calculate_position_size(balance, entry, sl, risk_percent=2.0, symbol=symbol)
        
        print(f"\n{desc}")
        print(f"  Balance: ${balance:,.2f} | Entry: {entry} | SL: {sl}")
        print(f"  Risk Amount: ${result.risk_amount:.2f} (2%)")
        print(f"  SL Distance: {result.sl_distance:.5f}")
        print(f"  Calculated Lot: {result.lot_size}")
        print(f"  Valid: {result.is_valid} | {result.message}")
    
    mt5.shutdown()
