# Simplified GitHub Issues Creation Script
# Creates all 12 epic issues without labels (add labels manually later)

$ghPath = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "TheHaywire/titan-trading-system"

$issues = @(
    @{
        title = "[EPIC-01] MT5 Platform Fundamentals"
        body  = "**Owner**: Platform Architect | **Status**: 40% | **Priority**: Medium`n`n## Deliverables`n- [x] Platform architecture documented`n- [x] Symbol properties catalog (1500+ symbols)`n- [ ] Order/position model validation`n- [ ] MQL5 integration assessment`n`n**Docs**: [Section 01](https://github.com/TheHaywire/titan-trading-system/blob/main/docs/institutional/SECTION_01_MT5_PLATFORM_FUNDAMENTALS.md)`n`n**Next**: Complete live broker validation by Jan 15"
    },
    @{
        title = "[EPIC-02] Python Connectivity & Tech Stack"
        body  = "**Owner**: Integration Lead | **Status**: 60% | **Priority**:Medium`n`n## Deliverables`n- [x] Tech stack documented`n- [x] IPC bridge architecture`n- [x] Connection lifecycle + health checks  `n- [ ] Error 10027 auto-detection`n- [ ] Latency <50ms`n`n**Docs**: [Section 02](https://github.com/TheHaywire/titan-trading-system/blob/main/docs/institutional/SECTION_02_PYTHON_CONNECTIVITY.md)"
    },
    @{
        title = "[EPIC-03] Trading Concepts & Methodology"
        body  = "**Owner**: Education Lead | **Status**: 50% | **Priority**: Medium`n`n## Deliverables`n- [x] R:R ratio framework`n- [ ] Expectancy formulas`n- [ ] Win rate vs R:R analysis`n- [ ] Institutional risk philosophy`n`n**Next**: Publish expectancy calculator"
    },
    @{
        title = "[EPIC-04] Instrument Universe & Symbol Catalog"
        body  = "**Owner**: Universe Manager | **Status**: 85% COMPLETE | **Priority**: Low`n`n## Deliverables`n- [x] Asset classes enumerated`n- [x] Symbol catalog (JSON)`n- [x] Fat Tail Top20 identified`n- [x] Strategy-symbol assignments`n`n**Docs**: [FAT_TAIL_OPPORTUNITIES.md](https://github.com/TheHaywire/titan-trading-system/blob/main/docs/FAT_TAIL_OPPORTUNITIES.md)"
    },
    @{
        title = "[EPIC-05] Session Management & Health"
        body  = "**Owner**: Reliability Engineer | **Status**: 45% | **Priority**: HIGH`n`n## Deliverables`n- [x] Session manager basics`n- [ ] Health metrics dashboard`n- [ ] 3-tier kill switch`n- [ ] Reconnection stress tests`n`n**Next**: Implement kill switch mechanism"
    },
    @{
        title = "[EPIC-06] Strategy Library & Research Process"
        body  = "**Owner**: Head of Research | **Status**: 55% | **Priority**: Medium`n`n## Deliverables`n- [x] Strategy catalog (BookTechnical, InstitutionalGold)`n- [x] Research workflow`n- [ ] Multi-agent architecture`n- [ ] Formal hypothesis docs`n`n**Next**: Document 5 strategy hypotheses"
    },
    @{
        title = "[EPIC-07] Risk Management & Prop Firm Constraints"
        body  = "**Owner**: Chief Risk Officer | **Status**: 50% | **Priority**: HIGH`n`n## Deliverables`n- [x] 5-layer risk hierarchy`n- [x] Position sizer (0.5-1% risk)`n- [x] Prop firm rules`n- [ ] Correlation matrix`n- [ ] Concentration limits`n`n**Docs**: [Section 07](https://github.com/TheHaywire/titan-trading-system/blob/main/docs/institutional/SECTION_07_RISK_MANAGEMENT.md)"
    },
    @{
        title = "[EPIC-08] Data Pipeline & Feature Engineering"
        body  = "**Owner**: Data Team | **Status**: 30% | **Priority**: Medium`n`n## Deliverables`n- [ ] Data source catalog`n- [ ] Feature store design`n- [ ] Data integrity checks`n- [ ] Quarantine & alerting`n`n**Next**: Build feature store prototype"
    },
    @{
        title = "[EPIC-09] Execution Architecture & Order Lifecycle"
        body  = "**Owner**: Execution Architect | **Status**: 65% | **Priority**: HIGH`n`n## Deliverables`n- [x] Order lifecycle documented`n- [x] Order building logic`n- [ ] Execution policies`n- [ ] Latency monitoring`n`n**Next**: Add per-trade slippage analysis"
    },
    @{
        title = "[EPIC-10] Backtesting, Validation & Verification"
        body  = "**Owner**: Model Validation Lead | **Status**: 45% | **Priority**: 🚨 CRITICAL`n`n## Deliverables`n- [x] Python backtest framework`n- [ ] MT5 Strategy Tester integration`n- [ ] Walk-forward optimization`n- [ ] Cross-validation (MT5 vs Python)`n- [ ] Performance metrics`n`n**⚠️ BLOCKER**: Must complete before scaling capital >$10K"
    },
    @{
        title = "[EPIC-11] Monitoring, Logging & Audit Trail"
        body  = "**Owner**: Operations Lead | **Status**: 25% | **Priority**: 🚨 CRITICAL`n`n## Deliverables`n- [ ] System log architecture`n- [ ] Time synchronization (NTP)`n- [ ] Real-time dashboard (P&L, exposure, health)`n- [ ] Audit trail (trade → strategy → rationale)`n`n**⚠️ BLOCKER**: Required for prop firm compliance"
    },
    @{
        title = "[EPIC-12] CEO Documentation & Review"
        body  = "**Owner**: Documentation Team | **Status**: 20% | **Priority**: HIGH`n`n## Deliverables`n- [ ] Executive summaries (all 12 sections)`n- [ ] Reference mapping table`n- [ ] Known limitations disclosure`n- [ ] External auditor review`n`n**Docs**: [INSTITUTIONAL_MASTER_PLAN.md](https://github.com/TheHaywire/titan-trading-system/blob/main/docs/INSTITUTIONAL_MASTER_PLAN.md)`n`n**Next CEO Review**: Jan 15, 2026"
    }
)

$issueNumbers = @()

foreach ($issue in $issues) {
    Write-Host "Creating: $($issue.title)..."
    try {
        $result = & $ghPath issue create --repo $repo --title $issue.title --body $issue.body 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Created" -ForegroundColor Green
            $issueNumbers += $result
        }
        else {
            Write-Host "  ❌ Failed: $result" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
    }
    Start-Sleep -Seconds 2
}

Write-Host "`n✅ Issue creation complete!"
Write-Host "Created issues: $($issueNumbers.Count)/12"
Write-Host "`nView at: https://github.com/TheHaywire/titan-trading-system/issues"
Write-Host "`nNext step: Add labels manually via GitHub web interface:"
Write-Host "  - institutional (all issues)"
Write-Host "  - priority-critical (issues 10, 11)"
Write-Host "  - priority-high (issues 5, 7, 9, 12)"
