import logging
import math

logger = logging.getLogger("Titan.Risk.PositionSizer")

class InstitutionalPositionSizer:
    """
    Institutional Grade Position Sizing.
    
    Philosophy:
    - IGNORE Margin. Focus on Risk Capital.
    - 1% Risk = The amount we are willing to lose if SL is hit.
    - Lot Size = Risk_Amount / (SL_Distance_Points * Tick_Value_Per_Point)
    """
    
    def __init__(self, max_risk_pct=1.0):
        self.max_risk_pct = max_risk_pct

    def calculate_lots(self, account_equity, symbol_info, sl_price, entry_price):
        """
        Calculate precise lot size based on account risk and broker contract specs.
        
        Args:
            account_equity (float): Current Account Equity
            symbol_info (MT5.SymbolInfo): symbol_info object from MT5
            sl_price (float): Stop Loss Price
            entry_price (float): Entry Price
            
        Returns:
            float: Safe lot size rounded to broker step
        """
        if account_equity <= 0:
            logger.error("Equity is 0 or negative. Cannot size position.")
            return 0.0

        # 1. Determine Risk Capital ($)
        risk_capital = account_equity * (self.max_risk_pct / 100.0)
        
        # 2. Determine Stop Loss Distance
        # We need the distance in PRICE first
        price_dist = abs(entry_price - sl_price)
        
        if price_dist == 0:
            logger.error(f"SL Distance is 0 for {symbol_info.name}. Unsafe.")
            return 0.0
            
        # 3. Calculate Value per Lot for this Distance
        # Math:
        # Profit = (Price_Diff / Point) * Tick_Value * Volume
        # We want Profit = -Risk_Capital
        # Risk_Capital = (Price_Diff / Point) * Tick_Value * Volume
        # Volume = Risk_Capital / ((Price_Diff / Point) * Tick_Value)
        
        if symbol_info.point == 0 or symbol_info.trade_tick_value == 0:
            logger.error(f"Invalid Symbol Specs for {symbol_info.name}: Point={symbol_info.point}, TickVal={symbol_info.trade_tick_value}")
            return 0.0
            
        # Note: trade_tick_value is "Calculated tick value for a position" (usually for 1 lot?)
        # Let's assume standard MT5 behavior: trade_tick_value is for 1 lot movement of trade_tick_size
        
        # Adjust for Tick Size if needed (Tick Value is usually per Tick Size, not per Point)
        # But commonly in FX: Point=0.00001, TickSize=0.00001
        # In Indices: Point=0.01, TickSize=0.01
        
        ticks_at_risk = price_dist / symbol_info.trade_tick_size
        value_per_lot_at_risk = ticks_at_risk * symbol_info.trade_tick_value
        
        if value_per_lot_at_risk == 0:
            return 0.0
            
        raw_lots = risk_capital / value_per_lot_at_risk
        
        # 4. Normalize to Broker Limits
        step = symbol_info.volume_step
        min_vol = symbol_info.volume_min
        max_vol = symbol_info.volume_max
        
        # Round down to nearest step to be safe
        lots = math.floor(raw_lots / step) * step
        
        # Clamp
        final_lots = max(min_vol, min(lots, max_vol))
        
        # Formating constraint (round to correct decimals to avoid 0.010000001)
        decimals = 0
        if "." in str(step):
            decimals = len(str(step).split(".")[1].rstrip("0"))
        
        final_lots = round(final_lots, decimals)
        
        logger.info(f"Sizing {symbol_info.name}: Equity=${account_equity:.0f}, Risk=${risk_capital:.2f}, Dist={price_dist:.4f}, RawLots={raw_lots:.4f} -> {final_lots}")
        
        return final_lots
