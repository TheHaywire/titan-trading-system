
import numpy as np

class StatisticalMetrics:
    """
    Advanced Statistical Metrics for Mean Reversion.
    """
    
    @staticmethod
    def calculate_half_life(series: np.array) -> float:
        """
        Calculates the Half-Life of a mean-reverting series using the Ornstein-Uhlenbeck process.
        Formula: dx(t) = -theta * (x(t) - mu) * dt + sigma * dW(t)
        
        We regress dx(t) on x(t) to find theta (mean reversion speed).
        Half-Life = -ln(2) / theta
        
        Returns:
            float: number of bars expected to revert half-way to mean.
        """
        if len(series) < 10:
            return 0.0
            
        # 1. Create Lagged Series
        x_t = series[:-1] 
        x_t1 = series[1:] # t+1
        
        # 2. Calculate Delta
        dx = x_t1 - x_t
        
        # 3. Regress dx on x_t ( Linear Fit: dx = theta * x_t + const )
        # Ideally we regress on (x_t - mean), but slope is same.
        # Check for constant?
        
        # Using numpy polyfit(x, y, 1) -> returns slope, intercept
        slope, intercept = np.polyfit(x_t, dx, 1)
        
        # theta is the negative of the slope (if slope is negative, it's mean reverting)
        theta = slope
        
        # If theta is positive, it's trending (momentum), not mean reverting.
        if theta >= 0:
            return 999.0 # Infinite half life (trending)
            
        # Half Life formula: -ln(2) / theta
        half_life = -np.log(2) / theta
        
        return half_life
