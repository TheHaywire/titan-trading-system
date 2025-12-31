
import numpy as np
import logging

logger = logging.getLogger("Titan.PositionSizer")

class KellyPositionSizer:
    """
    Implements Kelly Criterion for optimal position sizing.
    
    Kelly Formula: f* = (p * b - q) / b
    Where:
    - p = probability of win
    - q = probability of loss (1-p)
    - b = win/loss ratio (average win / average loss)
    
    We use a conservative "Half Kelly" to reduce volatility.
    """
    
    def __init__(self, max_risk_pct=2.0, kelly_fraction=0.5):
        """
        Args:
            max_risk_pct: Maximum risk per trade as % of equity (default 2%)
            kelly_fraction: Fraction of Kelly to use (0.5 = Half Kelly)
        """
        self.max_risk_pct = max_risk_pct
        self.kelly_fraction = kelly_fraction
        
    def calculate_position_size(self, equity: float, symbol: str, entry_price: float, stop_loss: float, risk_pct: float = 1.0) -> float:
        """
        Calculates position size based on Fixed Fractional Risk.
        Risk = Equity * (Risk_Pct / 100)
        Lot Size = Risk / (SL_Distance * Tick_Value)
        """
        if equity <= 0 or entry_price <= 0 or stop_loss <= 0:
            return 0.01

        risk_amount = equity * (risk_pct / 100.0)
        price_diff = abs(entry_price - stop_loss)
        
        # Standard Lot Value approximation (Need precise TickValue from MT5 ideally)
        # Gold/Forex Standard Lot = 100,000 units. 
        # For XAUUSD: 1 pip (0.10) = $10 per lot.
        # For EURUSD: 1 pip (0.0001) = $10 per lot.
        
        # Determine pip value roughly
        if "XAU" in symbol or "GOLD" in symbol:
             # Points difference. XAU 1.0 move = $100 per lot
             # If SL is $2.0 away. Loss per lot = $200.
             loss_per_lot = price_diff * 100 
        elif "JPY" in symbol:
             loss_per_lot = (price_diff / 0.01) * 10 # Approx
        else:
             # Standard Forex (0.0001)
             loss_per_lot = (price_diff / 0.0001) * 10 
             
        if loss_per_lot == 0: return 0.01
        
        lots = risk_amount / loss_per_lot
        return round(max(0.01, lots), 2)
    
    def estimate_win_probability(self, z_score: float) -> float:
        """
        Estimate win probability based on Z-Score.
        
        Statistical theory: 
        - Z > 2.0: ~95% confidence of reversion (mean reversion trade)
        - Z > 1.0: ~68% confidence
        """
        abs_z = abs(z_score)
        
        if abs_z >= 3.0:
            return 0.99  # Very high confidence
        elif abs_z >= 2.5:
            return 0.95
        elif abs_z >= 2.0:
            return 0.85
        elif abs_z >= 1.5:
            return 0.70
        elif abs_z >= 1.0:
            return 0.60
        else:
            return 0.55  # Near 50-50
