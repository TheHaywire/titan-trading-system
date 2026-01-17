---
name: Execution Hooks
description: Pre-trade risk gates and post-trade audit actions for institutional compliance.
---

# Execution Hooks Skill

This skill provides the "Gate Keeper" logic for the Titan system. All trades MUST pass through these hooks to ensure institutional-grade risk management.

## 1. Pre-Trade Hook Protocol

Before ANY order is sent to MT5, run the pre-trade gate:

```powershell
python .agent/hooks/pre_trade.py --symbol GOLD --direction BUY --lots 0.1
```

### Checks Performed

| Check | Purpose | Block Condition |
|-------|---------|-----------------|
| **HEARTBEAT** | System health | Status ≠ HEALTHY |
| **MACRO_FILTER** | News environment | Verdict = BLOCK |
| **KELLY_SIZING** | Position limits | Lots > Kelly × 1.5 |
| **TRADING_HOURS** | Market calendar | Weekend = True |

### Response Format

```json
{
  "gate": "PASS" or "BLOCKED",
  "checks": [...],
  "reason": "Explanation if blocked"
}
```

**If gate returns BLOCKED**, you MUST:
- Document the blocking reason
- DO NOT proceed with order placement
- Recommend waiting for conditions to clear

---

## 2. Post-Trade Hook Protocol

After ANY order is filled, run the post-trade actions:

```powershell
python .agent/hooks/post_trade.py --symbol GOLD --direction BUY --lots 0.1 --entry 2650.0 --filled 2650.5 --ticket 123456
```

### Actions Performed

| Action | Purpose |
|--------|---------|
| **TCA_ANALYSIS** | Calculate slippage and assign grade (A/B/C) |
| **AUDIT_LOG** | Log to institutional audit trail |
| **ADAPTIVE_EXIT** | Register position for dynamic management |
| **NOTIFICATION** | Queue alert for monitoring |

### TCA Grading

| Grade | Slippage % | Interpretation |
|-------|------------|----------------|
| A | < 0.01% | Excellent execution |
| B | 0.01% - 0.05% | Acceptable |
| C | > 0.05% | Review broker quality |

---

## 3. Integration with Orchestrator

The `titan_orchestrator.py` automatically calls both hooks when using `--action execute`:

```powershell
python titan_orchestrator.py --action execute --symbol GOLD --direction BUY --lots 0.1
```

This single command:
1. Runs pre-trade gate
2. If PASS, sends order to MT5
3. Runs post-trade actions
4. Returns full execution report

---

## Core Tools

- `pre_trade.py`: Risk gate before order placement
- `post_trade.py`: TCA and audit after order fill

## Dependencies

- `mt5_bridge/scripts/heartbeat_monitor.py`: For system health
- `data_intelligence/scripts/macro_context.py`: For news filter
- `factor_risk/scripts/dynamic_kelly_allocator.py`: For sizing limits
- `mt5_bridge/scripts/audit_trail_manager.py`: For logging
