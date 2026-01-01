"""
UPDATE BOT CONFIGURATION
========================
Switching back to verified symbols.
Identity verified:
- GC -> HGCOP (Copper) - Validated Profitable (Sharpe 2.16)
- TU -> MTU (Treasury) - Validated Profitable (Sharpe 1.30)
- ES -> SES (S&P) - Validated Profitable

Gold (GAUUSD) lacks history (75 days).
Action: Using Copper as the Metals proxy for now.
"""
SYMBOLS = {
    'Copper': 'HGCOP-MAR26', 
    'Treasury': 'MTU',          
    'S&P500': 'SES',          
} 
