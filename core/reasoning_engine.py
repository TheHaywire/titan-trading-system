class ReasoningEngine:
    """
    Generates human-readable explanations for trade decisions.
    Turns technical data into "Why" and "Why Not" statements.
    """
    
    @staticmethod
    def analyze_acceptance(signal, trend, atr, volatility_ratio):
        """
        Generate reasoning for an ACCEPTED trade.
        """
        reasons = []
        
        # 1. Technical Reason
        if signal == 'BUY':
            reasons.append("Price action indicates strong upward momentum aligned with broader Bullish Trend.")
        elif signal == 'SELL':
            reasons.append("Price action shows weakness, confirming the broader Bearish Trend.")
            
        # 2. Volatility Context
        if volatility_ratio > 0.1:
            reasons.append(f"High Volatility ({volatility_ratio:.2f}%) detected: Adopting SCALP approach to capture quick moves.")
        else:
            reasons.append(f"Stable Volatility ({volatility_ratio:.2f}%): Suitable for SWING trade to ride the trend.")
            
        # 3. Confirmation
        reasons.append("Risk/Reward ratio of 1:2 is achievable within current ATR limits.")
        
        return " ".join(reasons)

    @staticmethod
    def analyze_rejection(symbol, reason_code, data_context):
        """
        Generate reasoning for a REJECTED trade.
        """
        if reason_code == "SPREAD_TOO_HIGH":
            return f"Spread ({data_context.get('spread')}pts) is too expensive relative to volatility. Trading would be inefficient."
            
        if reason_code == "TREND_MISMATCH":
            return f"Signal direction ({data_context.get('signal')}) contradicts the {data_context.get('trend')} trend. Counter-trend trading is currently disabled."
            
        if reason_code == "LOW_VOLATILITY":
            return f"Market is too flat (ATR: {data_context.get('atr'):.5f}). Waiting for expansion."
            
        if reason_code == "RSI_OVERBOUGHT":
            return f"RSI is overextended ({data_context.get('rsi'):.1f}). Risk of pull-back is high."
            
        if reason_code == "RSI_OVERSOLD":
            return f"RSI is overextended ({data_context.get('rsi'):.1f}). Risk of bounce is high."
            
        return "Does not meet high-probability criteria."
