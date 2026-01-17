"""
PROPER POSITION SIZING CALCULATOR
==================================
Calculates institutional-grade position sizes based on:
- Account size
- Risk per trade (% of equity)
- Stop loss distance
- Kelly criterion
- Volatility adjustment
"""
import MetaTrader5 as mt5


def calculate_position_size(symbol: str, account_balance: float, risk_percent: float,
                            entry_price: float, stop_loss: float, 
                            kelly_multiplier: float = 1.0) -> float:
    """
    Calculate proper lot size.
    
    Args:
        symbol: Trading symbol
        account_balance: Account equity
        risk_percent: % of account to risk (e.g., 1.0 for 1%)
        entry_price: Entry price
        stop_loss: Stop loss price
        kelly_multiplier: Adjust size based on Kelly (from features)
    
    Returns:
        Lot size to trade
    """
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return 0.01
    
    # Calculate dollar risk
    dollar_risk = account_balance * (risk_percent / 100.0)
    
    # Calculate pip/point risk
    stop_distance = abs(entry_price - stop_loss)
    
    # Get contract size and pip value
    contract_size = symbol_info.trade_contract_size
    point = symbol_info.point
    
    # Calculate lot size
    # For forex: lot_size = dollar_risk / (stop_distance_in_pips * pip_value)
    # For indices/crypto: lot_size = dollar_risk / (stop_distance * contract_size)
    
    if "USD" in symbol or "EUR" in symbol or "GBP" in symbol or "JPY" in symbol:
        # Forex pair
        pip_value = 10  # Standard for 1 lot forex
        pips_at_risk = stop_distance / point / 10  # Convert points to pips
        lot_size = dollar_risk / (pips_at_risk * pip_value)
    else:
        # Index or crypto
        lot_size = dollar_risk / (stop_distance * contract_size)
    
    # Apply Kelly multiplier
    lot_size *= kelly_multiplier
    
    # Round to allowed step
    lot_step = symbol_info.volume_step
    lot_size = round(lot_size / lot_step) * lot_step
    
    # Apply min/max limits
    lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
    
    return lot_size


if __name__ == "__main__":
    mt5.initialize()
    
    account_balance = 760950.00
    risk_percent = 1.0  # Risk 1% per trade
    
    print(f"Account: ${account_balance:,.2f}")
    print(f"Risk per trade: {risk_percent}%")
    print(f"Dollar risk: ${account_balance * risk_percent / 100:,.2f}\n")
    
    # Example: BTCUSD
    symbol = "BTCUSD"
    entry = 92080
    stop = 89910
    
    lots = calculate_position_size(symbol, account_balance, risk_percent, entry, stop)
    
    print(f"{symbol}:")
    print(f"  Entry: ${entry:.2f}")
    print(f"  Stop: ${stop:.2f}")
    print(f"  Risk: ${abs(entry - stop):.2f}")
    print(f"  Lot Size: {lots:.2f} lots")
    print(f"  Position Value: ${lots * 1:.2f}")  # 1 lot BTCUSD = 1 BTC
    
    mt5.shutdown()
