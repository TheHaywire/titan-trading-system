
import numpy as np

class LinearRegressionChannel:
    """
    Mathematical Core for Linear Regression Channel.
    Calculates the 'Fair Value' line and Standard Deviation Envelopes.
    """
    def __init__(self, period: int = 100):
        self.period = period

    def calculate(self, prices: np.array):
        """
        Calculates the Linear Regression Channel for the given price array.
        Returns:
            slope (float): The trend strength.
            intercept (float): The y-intercept.
            std_dev (float): Volatility around the line.
            z_score (float): The current price's deviation from the line in sigmas.
        """
        n = len(prices)
        if n < self.period:
            return 0.0, 0.0, 0.0, 0.0

        # Usage only the last 'period' data points
        y = prices[-self.period:]
        x = np.arange(self.period)

        # Calculate Linear Regression (y = mx + b)
        # m = (n*Sum(xy) - Sum(x)*Sum(y)) / (n*Sum(x^2) - (Sum(x))^2)
        # Using numpy polyfit is faster and cleaner
        slope, intercept = np.polyfit(x, y, 1)

        # Calculate Expected Values (The Line)
        regression_line = slope * x + intercept

        # Calculate Standard Deviation (Volatility around the line)
        residuals = y - regression_line
        std_dev = np.std(residuals)

        # Current Deviation (Last Price)
        current_price = y[-1]
        expected_price = slope * (self.period - 1) + intercept
        
        # Avoid division by zero
        if std_dev == 0:
            z_score = 0.0
        else:
            z_score = (current_price - expected_price) / std_dev

        return {
            "slope": slope,
            "intercept": intercept,
            "std_dev": std_dev,
            "expected_price": expected_price,
            "z_score": z_score,
            "upper_2std": expected_price + (2 * std_dev),
            "lower_2std": expected_price - (2 * std_dev)
        }
