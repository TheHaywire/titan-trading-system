"""
Institutional Data Pipeline & Integrity (EPIC-08)
Verifies market data quality before strategies ingest it.
Detects bar gaps, price outliers, and stale data.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("Titan.Data")

class DataIntegrity:
    """Detects and flags anomalies in market data."""
    
    @staticmethod
    def audit_dataframe(df, symbol):
        """
        Performs a deep audit of a candle dataframe.
        Returns (is_valid, report)
        """
        if df is None or df.empty:
            return False, "Empty Dataframe"
            
        report = []
        is_valid = True
        
        # 1. Check for Bar Gaps (Time continuity)
        # Assuming H1 data for this check
        df = df.sort_values('time')
        time_diffs = df['time'].diff().dropna()
        median_diff = time_diffs.median()
        
        gaps = time_diffs[time_diffs > median_diff * 1.5]
        if not gaps.empty:
            report.append(f"❌ Found {len(gaps)} bar gaps in history.")
            # We don't necessarily invalidate the whole DF, but we tag it.
            
        # 2. Check for Price Outliers (Flash Crashes / Bad Ticks)
        # Using Z-score on returns
        returns = df['close'].pct_change().dropna()
        if not returns.empty:
            z_scores = (returns - returns.mean()) / returns.std()
            extreme_outliers = z_scores[abs(z_scores) > 5.0] # 5 standard deviations
            if not extreme_outliers.empty:
                is_valid = False
                report.append(f"🚨 CRITICAL: Detected {len(extreme_outliers)} price outliers (>5 SD). Possible bad data.")
        
        # 3. Check for Stale Data (Zero Volatility)
        last_5 = df.tail(5)
        if last_5['close'].std() == 0:
             report.append("⚠️ Data appears stale (last 5 bars have identical prices).")
             
        report_str = " | ".join(report) if report else "✅ Data Clean"
        return is_valid, report_str

if __name__ == "__main__":
    # Mock data test
    data = {
        'time': pd.date_range(start='2023-01-01', periods=10, freq='H'),
        'close': [1.0, 1.01, 1.02, 1.01, 1.00, 1.50, 1.01, 1.02, 1.01, 1.00] # Outlier at index 5
    }
    df = pd.DataFrame(data)
    valid, msg = DataIntegrity.audit_dataframe(df, "TEST")
    print(f"Audit Result: {valid} - {msg}")
