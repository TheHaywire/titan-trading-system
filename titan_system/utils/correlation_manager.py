
class CorrelationManager:
    """
    Prevents over-exposure to correlated assets (Risk Stacking).
    """
    
    def __init__(self, execution_client=None):
        self.execution = execution_client
        
    def check_exposure(self, symbol: str, signal_type: str, current_positions: list) -> bool:
        """
        Returns FALSE if trade should be blocked due to correlation.
        """
        if not current_positions:
            return True
            
        # Simplified Correlation Matrix for Majors
        # We assume USD is the driver.
        # Group 1: USD Drivers (EURUSD, GBPUSD, AUDUSD, NZDUSD) - Positively Correlated
        # Group 2: Safe Havens (USDJPY, USDCHF) - Negatively Correlated to Group 1 (usually)
        # Group 3: Metals (XAUUSD) - Correlated to Group 1
        # Group 4: Crypto (BTCUSD, ETHUSD) - High Internal Correlation
        
        base_currency = symbol[:3]
        quote_currency = symbol[3:] if len(symbol) == 6 else "USD"
        
        risk_group = "OTHER"
        if symbol in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "XAUUSD", "GOLD"]:
            risk_group = "USD_SHORT" # Buying these = Selling USD
        elif symbol in ["USDJPY", "USDCHF", "USDCAD"]:
            risk_group = "USD_LONG" # Buying these = Buying USD
        elif symbol in ["BTCUSD", "ETHUSD", "BCHUSD"]:
            risk_group = "CRYPTO"
        elif "US30" in symbol or "NAS" in symbol or "SPX" in symbol:
            risk_group = "INDICES"
            
        # Count existing exposure in this group
        group_exposure = 0
        direction_match = 0
        
        for pos in current_positions:
            pos_sym = pos['symbol']
            pos_type = "BUY" if pos['type'] == 0 else "SELL"
            
            # Determine Group
            pos_group = "OTHER"
            if pos_sym in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "XAUUSD", "GOLD"]:
                pos_group = "USD_SHORT"
            elif pos_sym in ["USDJPY", "USDCHF", "USDCAD"]:
                pos_group = "USD_LONG"
            elif pos_sym in ["BTCUSD", "ETHUSD", "BCHUSD"]:
                pos_group = "CRYPTO"
            elif "US30" in pos_sym or "NAS" in pos_sym:
                pos_group = "INDICES"
                
            if pos_group == risk_group:
                group_exposure += 1
                if pos_type == signal_type:
                    direction_match += 1
                    
        # RULE 1: Max 2 positions in same correlated group
        if group_exposure >= 2:
            print(f"   ⚠️ Blocked {symbol}: Too many positions in group {risk_group}")
            return False
            
        # RULE 2: Max 1 position per specific symbol (Don't stack same pair)
        # (This is usually handled elsewhere but good to reinforce)
        for pos in current_positions:
            if pos['symbol'] == symbol:
                print(f"   ⚠️ Blocked {symbol}: Position already exists")
                # Unless we are scaling in? Scaling is handled by Monitor, not Scanner.
                # Scanner finds NEW opportunities. So we block new entries if one exists.
                return False
                
        # RULE 3: Crypto Limit (Max 1 Crypto position at a time to avoid volatility nuke)
        if risk_group == "CRYPTO" and group_exposure >= 1:
            print(f"   ⚠️ Blocked {symbol}: Max 1 Crypto allowed")
            return False

        return True
