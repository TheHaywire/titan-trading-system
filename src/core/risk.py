"""
Risk Manager
The 'Circuit Breaker' and Position Sizer.
"""
import MetaTrader5 as mt5

class RiskManager:
    def __init__(self):
        self.max_daily_loss = 3.0 # %
        self.max_risk_per_trade = 1.0 # %
        
    def check_health(self) -> bool:
        """Verify account is safe to trade"""
        account = mt5.account_info()
        if not account: return False
        
        # Add logic to check daily drawdown here (stateful)
        return True
        
    def calculate_lot_size(self, stop_loss_points: float) -> float:
        """Autocalculate lot size based on Risk %"""
        account = mt5.account_info()
        if not account or stop_loss_points <= 0: return 0.01
        
        balance = account.balance
        risk_amt = balance * (self.max_risk_per_trade / 100)
        
        # Gold Value: 1.0 lot = $1 per point? No.
        # Standard: 1.0 lot = 100 oz. 1 point ($1 move) = $100 PnL.
        tick_value = 100 # Approx for XAUUSD standard
        
        lots = risk_amt / (stop_loss_points * tick_value)
        lots = round(lots, 2)
        return max(0.01, lots)
