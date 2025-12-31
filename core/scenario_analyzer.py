class ScenarioAnalyzer:
    """
    Calculates the financial impact of trade scenarios.
    "What happens if I win/lose?"
    """
    
    @staticmethod
    def analyze_trade(entry, sl, tp, volume, symbol_properties):
        """
        Returns a dictionary with financial projections.
        symbol_properties should track contract size, currency, etc.
        For now, assuming standard Forex (100k units) and USD base.
        """
        # Simplified calculation for standard pairs
        # Needs robust pip value calc for non-USD in future
        contract_size = 100000 
        
        # Calculate Risk and Reward distance
        risk_dist = abs(entry - sl)
        reward_dist = abs(tp - entry)
        
        # Calculate P&L
        # P&L = (Price Diff) * Contract Size * Volume
        projected_loss = risk_dist * contract_size * volume
        projected_profit = reward_dist * contract_size * volume
        
        # Calculate R:R
        rr_ratio = projected_profit / projected_loss if projected_loss > 0 else 0
        
        return {
            "projected_profit": projected_profit,
            "projected_loss": projected_loss,
            "rr_ratio": rr_ratio,
            "risk_per_share": risk_dist,
            "reward_per_share": reward_dist
        }
