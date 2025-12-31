
import pytest
from titan_system.risk.position_sizer import KellyPositionSizer

# Note: We renamed the logic but kept class name for now to avoid breaking imports
# Ideally Refactor class name later.

def test_fixed_fractional_gold():
    sizer = KellyPositionSizer()
    equity = 10000
    risk_pct = 1.0 # $100 Risk
    
    # CASE 1: GOLD (XAUUSD)
    # Entry: 2000, SL: 1998 (Diff $2.0)
    # Loss per Lot on $2 move = $200
    # Expected Lots = $100 / $200 = 0.5
    
    lots = sizer.calculate_position_size(equity, "XAUUSD", 2000.0, 1998.0, risk_pct)
    assert lots == 0.5

def test_fixed_fractional_eurusd():
    sizer = KellyPositionSizer()
    equity = 10000
    risk_pct = 1.0 # $100 Risk
    
    # CASE 2: EURUSD
    # Entry: 1.1000, SL: 1.0990 (10 Pips)
    # Loss per Lot on 10 pips = $100
    # Expected Lots = $100 / $100 = 1.0
    
    lots = sizer.calculate_position_size(equity, "EURUSD", 1.1000, 1.0990, risk_pct)
    # Our simple logic uses (Diff / 0.0001) * 10
    # (0.0010 / 0.0001) * 10 = 10 * 10 = 100 per lot
    # Risk 100 / 100 = 1.0
    assert lots == 1.0
