import pandas as pd
from pypfopt import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns

class PortfolioOptimizer:
    def __init__(self, price_data: pd.DataFrame):
        """
        price_data: DataFrame with index as Date and columns as Tickers.
        """
        self.prices = price_data
        
    def optimize_mean_variance(self, target_volatility: float = None):
        """
        Calculate efficient frontier weights.
        """
        # 1. Calculate Expected Returns and Sample Covariance
        mu = expected_returns.mean_historical_return(self.prices)
        S = risk_models.sample_cov(self.prices)
        
        # 2. Optimize
        ef = EfficientFrontier(mu, S)
        
        if target_volatility:
            weights = ef.efficient_risk(target_volatility)
        else:
            weights = ef.max_sharpe()
            
        cleaned_weights = ef.clean_weights()
        return cleaned_weights, ef.portfolio_performance(verbose=True)

if __name__ == "__main__":
    # Test stub
    pass
