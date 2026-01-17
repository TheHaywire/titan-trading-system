---
description: Get complete news intelligence with sentiment analysis, symbol bias, and trading implications
---

# /news - News Intelligence System

Get comprehensive news analysis with sentiment scoring, symbol-specific bias, and trading implications.

## Usage

```
/news [SYMBOL]
```

**Examples:**
- `/news GOLD` - News intelligence for Gold
- `/news US100` - News analysis for Nasdaq
- `/news` - General market sentiment

## What It Provides

### 1. Market Sentiment Analysis
- Overall bullish/bearish/mixed sentiment
- Sentiment score (-1 to +1)
- Headlines analyzed count

### 2. Symbol-Specific News Bias
- Relevant news filtered by keyword matching
- Bullish vs bearish headline count
- Confidence percentage
- Sample headlines

### 3. High-Impact Events
- Upcoming NFP, FOMC, CPI, GDP events
- Event times and expected values
- Trading blackout recommendations

### 4. Pre-Trade News Check
- Safe to trade assessment
- Warning flags for upcoming events
- Symbol bias recommendation

### 5. Headline-by-Headline Sentiment
- Each headline scored individually
- Bullish/bearish/neutral classification

## How to Run

// turbo
1. Run News Intelligence for a symbol
```powershell
python titan_system/core/news_intelligence.py GOLD
```

2. View the generated report in `analysis/NEWS_INTEL_SYMBOL_*.md`

## Integration with Other Workflows

The News Intelligence integrates with:

| Workflow | How It Uses News |
|----------|------------------|
| `/ai` | AI gets news context for smarter analysis |
| `/brief` | Daily brief includes news sentiment |
| `/titan` | Full pipeline includes news layer |
| `/council` | Strategy Council considers news impact |

## Programmatic Usage

```python
from titan_system.core.news_intelligence import get_news_context, NewsIntelligence

# Quick context for AI workflows
context = get_news_context("GOLD")
print(context["symbol_bias"])  # {'bias': 'BULLISH', 'confidence': 75, ...}
print(context["market_sentiment"])  # {'sentiment': 'MIXED', 'score': 0.1}

# Full pre-trade check
intel = NewsIntelligence()
check = intel.pre_trade_news_check("GOLD")
if not check["safe_to_trade"]:
    print(f"SKIP TRADE: {check['warnings']}")
```

## Output Example

```
NEWS INTELLIGENCE: GOLD
================================
Bias: BULLISH (75% confidence)
Bullish: 5 | Bearish: 2

Market Sentiment: MIXED (score: 0.1)

[SAFE] OK to trade
```

## Tips

- Run before major trading sessions
- Check symbol bias aligns with technical setup
- High-impact events = no trading window
- Use with `/council` for full validation
