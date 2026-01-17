---
description: Generate AI-powered institutional trade reports using Gemini
---

# AI-Powered Professional Trade Report

Generate professional hedge fund-style trade reports using Google Gemini AI. The AI analyzes market data and produces institutional-grade recommendations.

## Usage

```
/ai [SYMBOL]
```

**Examples:**
- `/ai GOLD` - AI analysis for Gold
- `/ai SILVER` - AI professional report for Silver
- `/ai EURUSD` - AI trade setup for EUR/USD

## What It Generates

The AI produces a comprehensive 8-section professional report:

### 1️⃣ Executive Summary
- 2-3 sentence market overview
- Primary bias determination

### 2️⃣ Multi-Timeframe Consensus
- Weekly, Daily, 4H, 1H alignment table
- Overall MTF score (X/4)

### 3️⃣ Smart Money Analysis
- Institutional bias interpretation
- Order flow analysis
- Liquidity pool identification

### 4️⃣ Trade Setup
- Primary setup (Direction, Entry, SL, TP1/2/3)
- Alternative setup (backup plan)
- Position sizing recommendation

### 5️⃣ Probability Matrix
- Bull/Bear/Reversal scenario probabilities
- Trigger conditions for each

### 6️⃣ Risk Management
- Maximum risk percentage
- Position sizing calculation
- Scaling strategy
- Invalidation conditions

### 7️⃣ Execution Checklist
- Pre-trade verification steps
- Actionable checklist

### 8️⃣ AI Confidence Assessment
- Overall confidence score
- Supporting/Risk factors

## How to Run

// turbo
1. Run the AI Professional Analyst
```powershell
python scripts/ai_professional_analyst.py GOLD
```

2. View the generated report in `analysis/SYMBOL_AI_REPORT_*.md`

## Prerequisites

- **Gemini API Key**: Must have `GOOGLE_API_KEY` in `.env` or settings
- **google-generativeai**: Install with `pip install google-generativeai`
- **MT5 Connection**: For real-time market data

## API Usage

- Uses Gemini 2.5 Flash (or 1.5 Flash fallback)
- ~1 API call per report
- Free tier: 1500 requests/day

## Comparison with Other Workflows

| Workflow | AI | Speed | Depth | Best For |
|----------|-----|-------|-------|----------|
| `/ai` | ✅ Gemini | ~10s | 🔥🔥🔥🔥🔥 | Executive reports |
| `/pro` | ❌ | ~30s | 🔥🔥🔥🔥🔥 | Technical depth |
| `/analyze` | ❌ | ~15s | 🔥🔥🔥🔥 | Quick analysis |
| `/setup` | ❌ | ~20s | 🔥🔥🔥 | Trade setups |

## Tips

- Use `/ai` for final decision confirmation
- Combine with `/pro` for maximum depth
- AI reports are best for swing/position trades
- Check AI confidence before trading
- AI can identify patterns humans miss
