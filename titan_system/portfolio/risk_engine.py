class RiskEngine:
    def __init__(self, max_daily_drawdown: float = 0.05, max_position_size: float = 0.2):
        self.max_daily_drawdown = max_daily_drawdown
        self.max_position_size = max_position_size
        self.current_drawdown = 0.0
        
    def check_trade(self, symbol: str, size: float, capital: float) -> bool:
        """
        Returns True if trade is allowed, False otherwise.
        """
        if self.current_drawdown >= self.max_daily_drawdown:
            print(f"RISK REJECT: Max daily drawdown reached ({self.current_drawdown:.2%}).")
            return False
            
        if size / capital > self.max_position_size:
            print(f"RISK REJECT: Position size {size/capital:.2%} exceeds limit {self.max_position_size:.2%}.")
            return False
            
        return True
    
    def update_drawdown(self, current_equity: float, start_equity: float):
        dd = (start_equity - current_equity) / start_equity
        self.current_drawdown = max(0.0, dd)
