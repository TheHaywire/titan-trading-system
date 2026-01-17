"""
Correlation Guard Skill
=======================
Prevents over-exposure to specific currencies.
Recognizes that EURUSD, GBPUSD, and AUDUSD are all linked to USD.
"""

from .base import IntelligenceSkill
from typing import Dict, Any, List

class CorrelationGuardSkill(IntelligenceSkill):
    def __init__(self, max_points_per_currency: int = 3):
        super().__init__(
            name="CorrelationGuard",
            description="Manages portfolio risk by limiting exposure to correlated currencies."
        )
        self.max_points_per_currency = max_points_per_currency
        
        # Simple currency mapping
        self.CURRENCY_MAP = {
            "EURUSD": ["EUR", "USD"],
            "GBPUSD": ["GBP", "USD"],
            "USDJPY": ["USD", "JPY"],
            "USDCAD": ["USD", "CAD"],
            "AUDUSD": ["AUD", "USD"],
            "NZDUSD": ["NZD", "USD"],
            "USDCHF": ["USD", "CHF"],
            "GOLD": ["XAU", "USD"],
            "XAUUSD": ["XAU", "USD"],
            "BTCUSD": ["BTC", "USD"],
            "ETHUSD": ["ETH", "USD"]
        }

    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.active:
            return {'status': 'PASS', 'adjustment': 0, 'reason': 'Skill inactive'}

        symbol = context.get('symbol')
        proposed_dir = context.get('direction') # 'BUY' or 'SELL'
        open_positions = context.get('open_positions', []) # List of symbol names or structs

        if not symbol or not proposed_dir or symbol not in self.CURRENCY_MAP:
            return {'status': 'PASS', 'adjustment': 0, 'reason': 'Symbol not supported or no direction provided'}

        # Calculate current exposure points per currency
        # Buy EURUSD = +1 EUR, -1 USD
        # Sell EURUSD = -1 EUR, +1 USD
        exposure = {}

        def update_exp(curr, side):
            exposure[curr] = exposure.get(curr, 0) + (1 if side == 'BULL' else -1)

        for pos in open_positions:
            s = pos.get('symbol') if isinstance(pos, dict) else pos
            d = pos.get('type') if isinstance(pos, dict) else 'BUY' # Fallback
            if s in self.CURRENCY_MAP:
                base, quote = self.CURRENCY_MAP[s][0], self.CURRENCY_MAP[s][1]
                update_exp(base, 'BULL' if d == 'BUY' else 'BEAR')
                update_exp(quote, 'BEAR' if d == 'BUY' else 'BULL')

        # Check impact of proposed trade
        base, quote = self.CURRENCY_MAP[symbol][0], self.CURRENCY_MAP[symbol][1]
        
        # Proposed changes
        new_base_score = exposure.get(base, 0) + (1 if proposed_dir == 'BUY' else -1)
        new_quote_score = exposure.get(quote, 0) + (-1 if proposed_dir == 'BUY' else 1)

        reasons = []
        if abs(new_base_score) > self.max_points_per_currency:
            reasons.append(f"Over-exposure in {base} ({abs(new_base_score)} points)")
        if abs(new_quote_score) > self.max_points_per_currency:
            reasons.append(f"Over-exposure in {quote} ({abs(new_quote_score)} points)")

        if reasons:
            return {
                'status': 'BLOCK',
                'adjustment': -50,
                'reason': f"CORRELATION RISK: {', '.join(reasons)}",
                'metadata': {'exposure': exposure}
            }

        return {
            'status': 'PASS',
            'adjustment': 0,
            'reason': 'Exposure within safety limits.',
            'metadata': {'exposure': exposure}
        }
