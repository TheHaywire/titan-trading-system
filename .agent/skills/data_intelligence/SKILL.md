---
name: Data Intelligence & Fabric
description: Institutional-grade data cleaning, tick physics auditing, and gap reconstruction.
---

# Data Intelligence Skill

This skill ensures the "Fuel" (Data) for all other skills is pure. Follow these protocols for any OHLCV or Tick data processing:

### 1. Tick Physics Protocol
Before any strategy validation or feature engineering:
- Call `scripts/data_auditor.py` on the target OHLCV dataset.
- **Identify Spikes**: Flag candles where volatility exceeds the 20-period standard deviation by more than 4x (potential "fake" broker spikes).
- **Audit Wicks**: Check if High/Low spreads are realistic compared to the peer-group (other symbols in the same group).

### 2. Time-Series Integrity (Gap Recon)
Institutional models cannot handle missing time steps.
- Use `scripts/gap_reconstructor.py` to audit for missing bars in MT5 history.
- **Interpolate**: Fill gaps using forward-fill or linear interpolation to maintain a continuous time index.
- **Alert**: If a gap exceeds 4 bars (M15+) or 1 bar (H1+), log a "Data Quality Warning" in the Audit Trail.

### 3. Macro Filter Protocol
Institutional execution ignores technicals during extreme macro uncertainty.
- Call `scripts/macro_context.py` before opening any new position.
- **BLOCK**: If an "ULTRA" or "CRITICAL" event is detected within the current session, HALT all execution for that currency pair.
- **CAUTION**: Increase stop-loss buffers by 50% during "HIGH" impact event windows.

## Core Tools:
- `scripts/data_auditor.py`: Spike and anomaly detector.
- `scripts/gap_reconstructor.py`: Gap detector and time-series filler.
- `scripts/feature_factory.py`: High-dimensional feature generator.
- `scripts/macro_context.py`: Fundamental impact scout.
