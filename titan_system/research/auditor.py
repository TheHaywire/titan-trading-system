import pandas as pd
import numpy as np
import logging
import MetaTrader5 as mt5

logger = logging.getLogger("Titan.Auditor")

class TitanAuditor:
    """
    Institutional Audit Suite for measuring Market Structure and Strategy Edge.
    """
    def __init__(self, symbol):
        self.symbol = self.resolve_symbol_name(symbol)

    def resolve_symbol_name(self, name: str) -> str:
        """
        Attempts to map a generic name (e.g., 'EURUSD') to the broker's specific name.
        """
        # 1. Direct match
        if mt5.symbol_info(name): return name
        
        # 2. Hardcoded mapping
        mapping = {"GOLD": "XAUUSD", "SILVER": "XAGUSD"}
        name = mapping.get(name, name)
        if mt5.symbol_info(name): return name
        
        # 3. Pattern search (*EURUSD*)
        patterns = [f"*{name}*", f"{name}*", f"*{name}"]
        for pattern in patterns:
            symbols = mt5.symbols_get(pattern)
            if symbols:
                # Pick the first one (usually the most standard)
                return symbols[0].name
        return name

    def audit_trend_quality(self, df: pd.DataFrame) -> float:
        """
        Calculates Kaufman's Efficiency Ratio (ER).
        1.0 = Perfect Straight Line Trend
        0.0 = Pure Noise/Churn
        """
        if df.empty or len(df) < 24: return 0.0
        
        # Total change over the period
        total_change = abs(df['close'].iloc[-1] - df['close'].iloc[-24])
        
        # Sum of absolute bar-to-bar changes (The 'Noise')
        df['diff'] = abs(df['close'].diff())
        sum_noise = df['diff'].tail(24).sum()
        
        if sum_noise == 0: return 0.0
        
        er = total_change / sum_noise
        return float(er)

    def audit_liquidity(self, symbol) -> dict:
        """
        Checks real-time Spread and Volume to calculate 'Cost of Doing Business'.
        """
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            # Fallback for missing symbols
            return {
                "symbol": symbol,
                "spread_points": 0,
                "cost_usd_est": 0.0,
                "liquidity_status": "OFFLINE"
            }
            
        spread = symbol_info.spread # in points
        point = symbol_info.point
        spread_price = spread * point
        
        # Estimate cost for a 0.01 lot trade
        # For Gold, 100 points = $1.00
        cost_usd = 0
        if "XAU" in symbol or "GOLD" in symbol:
            cost_usd = spread * 0.01 # Pips approx for 0.01 lot
        else:
            cost_usd = (spread_price / 0.0001) * 0.10 # Rough conversion
            
        return {
            "symbol": symbol,
            "spread_points": spread,
            "cost_usd_est": cost_usd,
            "liquidity_status": "GOOD" if spread < 40 else "POOR"
        }

    def audit_robustness_monte_carlo(self, returns_series: pd.Series, iterations=500):
        """
        Monte Carlo Simulation: Shuffles trade returns to see if the equity 
        curve holds up across different sequences (LUCK vs EDGE).
        """
        if returns_series.empty: return 0.0
        
        pos_outcomes = 0
        for _ in range(iterations):
            shuffled = np.random.choice(returns_series, size=len(returns_series), replace=True)
            if shuffled.sum() > 0:
                pos_outcomes += 1
                
        confidence = (pos_outcomes / iterations) * 100
        return confidence

    def get_quantile_rank(self, df: pd.DataFrame, window=200) -> dict:
        """
        Institutional Metric: Where does the current return sit in the distribution?
        Returns percentile rank (0-100).
        """
        if df.empty or len(df) < window:
            return {"percentile": 50, "label": "NORMAL"}
            
        # Calculate log returns
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        current_return = df['returns'].iloc[-1]
        
        # Calculate percentiles of historical returns
        history = df['returns'].tail(window).dropna()
        percentile = (history < current_return).mean() * 100
        
        label = "ROUTINE"
        if percentile > 90: label = "EXTREME BREAKOUT (TOP 10%)"
        elif percentile < 10: label = "EXTREME DUMP (BOTTOM 10%)"
        elif percentile > 97 or percentile < 3: label = "EXHAUSTION ZONE"
        
        return {
            "percentile": float(percentile),
            "label": label,
            "is_extreme": percentile > 90 or percentile < 10
        }

    def calculate_correlation_matrix(self, symbol_data_dict: dict) -> pd.DataFrame:
        """
        Calculates Pearson correlation between symbols.
        symbol_data_dict: {'GOLD': df, 'EURUSD': df, ...}
        """
        returns_dict = {}
        for symbol, df in symbol_data_dict.items():
            if not df.empty:
                # Use log returns for normalization
                returns_dict[symbol] = np.log(df['close'] / df['close'].shift(1))
        
        returns_df = pd.DataFrame(returns_dict).dropna()
        if returns_df.empty:
            return pd.DataFrame()
            
        return returns_df.corr()

    def calculate_var(self, returns_df: pd.DataFrame, initial_value=10000, confidence=0.99) -> float:
        """
        Historical Simulation VaR (Value at Risk).
        Returns the maximum estimated loss in USD for the next period.
        """
        if returns_df.empty: return 0.0
        
        # Calculate portfolio returns (assuming equal weights for simplified institutional entry)
        portfolio_returns = returns_df.mean(axis=1)
        
        # Calculate the nth percentile (e.g. 1st percentile for 99% confidence)
        var_percentile = np.percentile(portfolio_returns, (1 - confidence) * 100)
        
        # Convert to $ amount
        var_usd = abs(var_percentile * initial_value)
        return float(var_usd)
