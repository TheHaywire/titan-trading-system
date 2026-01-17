---
description: Analyze today's trade execution against the Institutional Matrix
---

# /audit - Institutional Trade Auditor & Mentor

**Audit your execution discipline. Acts as a Mentor for plan-following and a Critic for emotional gambling.**

## How to use
1. Ensure your MT5 is running and logged in.
2. Run `/audit` to compare today's closed trades against the latest Weekly Trading Plan.

## Workflow Steps

1. **Initialize MT5 Connection**
   - Connects to the local terminal to fetch the last 24 hours of trade history.

2. **Cross-Reference with the Matrix**
   - Loads the latest `WEEKLY_TRADING_PLAN_*.csv`.
   - Maps each trade symbol to its Institutional Bias (Bullish/Bearish/Neutral).

3. **Evaluate Discipline**
   - **On-Plan**: Trading in alignment with the institutional bias.
   - **Defiant**: Trading against the strong institutional bias.
   - **Gambling**: Trading symbols without a clear bias.

4. **Generate Mentor/Critic Report**
   - **Discipline Score**: 0-100% rating of your professionalism.
   - **The Roast**: Direct critique of emotional or off-plan trades.
   - **The Lesson**: Mentorship on where you showed growth and where you failed.

// turbo
5. **Run the Audit**
   - Run the command: `python scripts/trade_auditor.py`

// turbo
6. **Run TCA Analysis via Execution Skill**
```bash
python .agent/skills/execution/scripts/execution_quality_tca.py
```

7. **Check the Institutional Audit Trail**
```bash
python .agent/skills/mt5_bridge/scripts/audit_trail_manager.py
```

8. **Review Results**
   - View the generated report in `analysis/TRADE_AUDIT_YYYYMMDD.md`.
   - Check TCA grades for execution quality (A/B/C).
   - Review audit trail for all logged decisions.
