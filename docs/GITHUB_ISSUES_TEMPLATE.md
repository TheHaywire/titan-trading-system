# GitHub Issues - Institutional Framework

This file contains issue templates for all 12 sections. You can create these issues on GitHub using the CLI or web interface.

---

## How to Create Issues (GitHub CLI Method)

```bash
# Install GitHub CLI first (if not already installed)
# Download from: https://cli.github.com/

# Login to GitHub
gh auth login

# Navigate to your repo
cd "c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025"

# Create issues using the templates below
# Example:
gh issue create --title "[EPIC] Section 01: MT5 Platform Fundamentals" \
  --body "See templates below" \
  --label "institutional,foundation" \
  --project "https://github.com/users/TheHaywire/projects/2"
```

---

## Epic Issues (12 Total)

### [EPIC 01] MT5 Platform Fundamentals

**Title**: `[EPIC] Section 01: MT5 Platform Fundamentals`

**Labels**: `institutional`, `foundation`, `platform`

**Body**:
```markdown
## Objective
Document MT5 platform architecture, symbol properties, and order/position models to institutional standards.

## Owner
Platform Architect

## Status
🚧 In Progress (40%)

## Deliverables

- [x] Platform architecture documented
- [x] Symbol properties catalog (1500+ symbols)
- [ ] Order/position model validation on live broker
- [ ] MQL5 integration assessment

## Documentation
- [📄 Section 01 Docs](docs/institutional/SECTION_01_MT5_PLATFORM_FUNDAMENTALS.md)

## Cross-References
- MT5 Architecture: https://www.metatrader5.com/en/automated-trading/architecture
- MQL5 Trading Functions: https://www.mql5.com/en/docs/trading
- SymbolInfo Structure: https://www.mql5.com/en/docs/constants/structures/symbolinfo

## Next Milestone
Complete live broker validation by Jan 15, 2026

## Acceptance Criteria
- [ ] All symbol properties extracted and validated against broker
- [ ] Order types tested on demo account
- [ ] Netting mode confirmed
- [ ] Minimum SL/TP distances validated per symbol
- [ ] Architecture diagrams reviewed with team
```

---

### [EPIC 02] Python Connectivity & Tech Stack

**Title**: `[EPIC] Section 02: Python Connectivity & Tech Stack`

**Labels**: `institutional`, `foundation`, `connectivity`

**Body**:
```markdown
## Objective
Ensure reliable, low-latency Python-MT5 communication via the MetaTrader5 package.

## Owner
Python-MT5 Integration Lead

## Status
🚧 In Progress (60%)

## Deliverables

- [x] Tech stack documented (Python 3.10, MT5 package)
- [x] IPC bridge architecture defined
- [x] Connection lifecycle + health checks
- [ ] Error 10027 auto-detection
- [ ] Latency benchmarking (<50ms target)

## Documentation
- [📄 Section 02 Docs](docs/institutional/SECTION_02_PYTHON_CONNECTIVITY.md)
- [💻 MT5 Bridge Code](titan_system/core/mt5_bridge.py)

## Cross-References
- MetaTrader5 Package: https://pypi.org/project/MetaTrader5/
- MT5 Python API: https://www.mql5.com/en/docs/integration/python_metatrader5
- Trade Return Codes: https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes

## Next Milestone
Achieve <50ms Python-MT5 latency

## Acceptance Criteria
- [ ] All critical functions tested on demo account
- [ ] Health check logic validated
- [ ] Error 10027 detection implemented
- [ ] Reconnection logic stress tested
- [ ] Latency < 50ms confirmed
```

---

### [EPIC 07] Risk Management & Prop Firm Constraints

**Title**: `[EPIC] Section 07: Risk Management & Prop Firm Constraints`

**Labels**: `institutional`, `risk`, `compliance`

**Body**:
```markdown
## Objective
Implement 5-layer risk hierarchy and prop firm challenge rules to protect capital.

## Owner
Chief Risk Officer

## Status
🚧 In Progress (50%)

## Deliverables

- [x] Risk hierarchy (per-trade, strategy, symbol, account)
- [x] Position sizer (0.5-1% risk per trade)
- [x] Prop firm rules (daily/total loss limits)
- [ ] Correlation matrix
- [ ] Concentration limits enforcement

## Documentation
- [📄 Section 07 Docs](docs/institutional/SECTION_07_RISK_MANAGEMENT.md)
- [💻 Position Sizer](titan_system/risk/position_sizer.py)
- [💻 Prop Rules](titan_system/risk/prop_firm_rules.py)

## Cross-References
- ESMA Leverage Caps: https://www.esma.europa.eu/
- Prop Firm Rules: FTMO, TopStepTrader documentation
- MT5 Margin Calculation: https://www.mql5.com/en/articles/1690

## Next Milestone
Add portfolio correlation checks

## Acceptance Criteria
- [ ] Per-trade risk calculator validated
- [ ] Prop firm daily/total loss limits tested
- [ ] Correlation matrix implemented
- [ ] Concentration limits enforced
- [ ] Kill switch mechanism tested
```

---

### [EPIC 10] Backtesting, Validation & Verification

**Title**: `[EPIC] Section 10: Backtesting, Validation & Verification`

**Labels**: `institutional`, `quality`, `validation`, `priority-high`

**Body**:
```markdown
## Objective
Cross-validate strategies using MT5 Strategy Tester and Python backtests.

## Owner
Model Validation Lead

## Status
🚧 In Progress (45%)

## Deliverables

- [x] Python backtest framework
- [ ] MT5 Strategy Tester integration
- [ ] Walk-forward optimization
- [ ] Cross-validation (MT5 vs Python)
- [ ] Performance metrics (Sharpe, expectancy, stress tests)

## Documentation
- [📄 Section 10 Docs](docs/institutional/SECTION_10_BACKTESTING_VALIDATION.md)

## Cross-References
- MT5 Strategy Tester: https://www.mql5.com/en/docs/runtime/testing
- Walk-Forward Analysis: Industry best practices
- Performance Metrics: Chan "Algorithmic Trading"

## Next Milestone
Align Python backtest with MT5 Strategy Tester results

## Acceptance Criteria
- [ ] MT5 Strategy Tester integrated
- [ ] Walk-forward optimization implemented
- [ ] Cross-validation shows <5% discrepancy
- [ ] Sharpe, Sortino, max DD calculated
- [ ] Monte Carlo stress tests completed
```

---

### [EPIC 11] Monitoring, Logging & Audit Trail

**Title**: `[EPIC] Section 11: Monitoring, Logging & Audit Trail`

**Labels**: `institutional`, `operations`, `compliance`, `priority-high`

**Body**:
```markdown
## Objective
Build comprehensive monitoring, logging, and audit trail for compliance.

## Owner
Operations Lead

## Status
📋 Pending (25%)

## Deliverables

- [ ] System log architecture (MT5, Python, infrastructure)
- [ ] Time synchronization (NTP)
- [ ] Dashboard design (P&L, exposure, latency, health)
- [ ] Audit trail (trade → strategy → features → rationale)

## Documentation
- [📄 Section 11 Docs](docs/institutional/SECTION_11_MONITORING_LOGGING.md)

## Cross-References
- Prop Firm Compliance Requirements
- Institutional Audit Standards

## Next Milestone
Build real-time dashboard (rich UI)

## Acceptance Criteria
- [ ] All logs time-synchronized
- [ ] Dashboard displays real-time P&L, positions, health
- [ ] Audit trail links every trade to strategy logic
- [ ] Tamper-evident logging implemented
```

---

### [EPIC 12] CEO Documentation & Review

**Title**: `[EPIC] Section 12: CEO Documentation & Review`

**Labels**: `institutional`, `documentation`, `ceo-review`, `priority-medium`

**Body**:
```markdown
## Objective
Create executive summaries and reference mappings for CEO/investor review.

## Owner
Documentation Team

## Status
📋 Pending (20%)

## Deliverables

- [ ] Executive summaries (all 12 sections)
- [ ] Reference mapping table (requirement → implementation → test → docs)
- [ ] Known limitations disclosure
- [ ] External auditor review

## Documentation
- [📄 Section 12 Docs](docs/institutional/SECTION_12_CEO_DOCUMENTATION.md)
- [📄 Master Plan](docs/INSTITUTIONAL_MASTER_PLAN.md)

## Next Milestone
Draft CEO executive summary

## Acceptance Criteria
- [ ] Executive summaries completed for all 12 sections
- [ ] Reference mapping table complete
- [ ] Limitations clearly documented
- [ ] CEO review scheduled and conducted
```

---

## Creating All Issues Via Script

Here's a PowerShell script to create all issues:

```powershell
# create_github_issues.ps1

$issues = @(
    @{
        title = "[EPIC] Section 01: MT5 Platform Fundamentals"
        labels = "institutional,foundation,platform"
    },
    @{
        title = "[EPIC] Section 02: Python Connectivity & Tech Stack"
        labels = "institutional,foundation,connectivity"
    },
    @{
        title = "[EPIC] Section 03: Trading Concepts & Methodology"
        labels = "institutional,strategy,education"
    },
    @{
        title = "[EPIC] Section 04: Instrument Universe & Symbol Catalog"
        labels = "institutional,strategy,complete"
    },
    @{
        title = "[EPIC] Section 05: Session Management & Health"
        labels = "institutional,operations,reliability"
    },
    @{
        title = "[EPIC] Section 06: Strategy Library & Research Process"
        labels = "institutional,strategy,research"
    },
    @{
        title = "[EPIC] Section 07: Risk Management & Prop Firm Constraints"
        labels = "institutional,risk,compliance"
    },
    @{
        title = "[EPIC] Section 08: Data Pipeline & Feature Engineering"
        labels = "institutional,data,operations"
    },
    @{
        title = "[EPIC] Section 09: Execution Architecture & Order Lifecycle"
        labels = "institutional,execution,operations"
    },
    @{
        title = "[EPIC] Section 10: Backtesting, Validation & Verification"
        labels = "institutional,quality,validation,priority-high"
    },
    @{
        title = "[EPIC] Section 11: Monitoring, Logging & Audit Trail"
        labels = "institutional,operations,compliance,priority-high"
    },
    @{
        title = "[EPIC] Section 12: CEO Documentation & Review"
        labels = "institutional,documentation,ceo-review,priority-medium"
    }
)

foreach ($issue in $issues) {
    Write-Host "Creating issue: $($issue.title)"
    gh issue create `
        --title $issue.title `
        --body "See docs/INSTITUTIONAL_MASTER_PLAN.md for details" `
        --label $issue.labels `
        --repo TheHaywire/titan-trading-system
}
```

Run with:
```powershell
cd "c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025"
.\create_github_issues.ps1
```
