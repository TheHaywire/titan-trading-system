# API Quota Management Strategy
# Ensures 24/7 operation without exhausting Gemini limits

## THE PROBLEM
- Gemini Free Tier: 20 requests/day
- Trading System: Needs to run 24/7 across all markets
- Risk: Exhausting quota in first few hours

## THE SOLUTION: Tiered Email System

### Level 1: INSTANT ALERTS (No AI, Unlimited)
**Triggers:** When a signal is detected
**Frequency:** Every 15 minutes (96 scans/day)
**Uses:** Pure Python analysis + HTML templates
**Gemini Calls:** 0

**Email Content:**
- Symbol, Price, Signal (BUY/SELL)
- SL/TP levels (ATR-based calculation)
- Trend direction
- Risk metrics
**No AI commentary needed - just facts**

### Level 2: CATEGORY DIGEST (No AI, 4x/day)
**Triggers:** Every 6 hours
**Frequency:** 4 times per day (6am, 12pm, 6pm, 12am)
**Uses:** Multi-category scanner + HTML
**Gemini Calls:** 0

**Email Content:**
- All 5 categories scanned
- Top 5 signals per category
- Comparison table
**No AI commentary - pure data**

### Level 3: STRATEGIC BRIEFING (With AI, 1x/day)
**Triggers:** 7:00 AM IST only
**Frequency:** Once per day
**Uses:** Gemini 2.5 Flash
**Gemini Calls:** 1

**Email Content:**
- Why the market is moving
- Best trade of the day
- Risk analysis
- Strategic outlook

### Level 4: WEEKLY DEEP DIVE (With AI, 1x/week)
**Triggers:** Sunday 8:00 PM IST
**Frequency:** Once per week
**Uses:** Gemini 2.5 Flash + Backtesting
**Gemini Calls:** 1

**Email Content:**
- Week performance review
- AI learns from wins/losses
- Strategy adjustments
- Next week outlook

---

## TOTAL GEMINI USAGE

**Daily:** 1 call (Strategic Briefing)
**Weekly:** 2 calls (1 daily + 1 weekly review)
**Monthly:** ~10 calls (out of 600 available)

**Safety Margin:** 98% quota unused ✅

---

## AUTONOMOUS TRADING

The bot trades WITHOUT waiting for AI:
1. Scanner detects signal
2. Python calculates SL/TP
3. **Executes trade immediately**
4. Sends you confirmation email
5. AI analysis happens later (for learning)

---

## BACKTESTING INTEGRATION

Run backtests OFFLINE (no API calls):
- Test strategies on historical data
- Results saved to JSON
- Included in weekly digest
- AI reviews results only once/week

---

**Implementation:** See `autonomous_trader.py`
