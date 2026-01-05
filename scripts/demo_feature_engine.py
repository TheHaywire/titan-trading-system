"""
LIVE Feature Engine Demo
=========================
Shows real-time institutional features on GOLD with trading interpretations.
Demonstrates WHY each feature matters and HOW to use it for trading decisions.
"""

import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box

from titan_system.features.quant_features import (
    QuantFeatureEngine,
    MomentumFeatures,
    MeanReversionFeatures,
    VolatilityFeatures,
    TimeSeriesFeatures,
    RiskFeatures
)

console = Console()


def get_mt5_data(symbol: str, timeframe, bars: int = 500) -> pd.DataFrame:
    """Fetch OHLCV data from MT5."""
    if not mt5.initialize():
        console.print("[red]Failed to initialize MT5[/red]")
        return None
    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        console.print(f"[red]Failed to get data for {symbol}[/red]")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    return df


def display_features(symbol: str = "XAUUSD"):
    """Main demo: compute and display all features with interpretations."""
    
    console.print(Panel.fit(
        f"[bold cyan]INSTITUTIONAL FEATURE ENGINE[/bold cyan]\n"
        f"[dim]Real-time quantitative features for {symbol}[/dim]",
        border_style="cyan"
    ))
    
    # Fetch data
    console.print("\n[yellow]Fetching H1 data from MT5...[/yellow]")
    df = get_mt5_data(symbol, mt5.TIMEFRAME_H1, 500)
    
    if df is None:
        return
    
    console.print(f"[green]✓ Loaded {len(df)} bars[/green] (Latest: {df['time'].iloc[-1]})")
    
    # Compute all features
    console.print("\n[yellow]Computing institutional features...[/yellow]")
    features_df = QuantFeatureEngine.compute_all(df)
    latest = features_df.iloc[-1]
    
    # Get interpretations
    interpretations = QuantFeatureEngine.interpret(latest)
    scores = QuantFeatureEngine.get_trading_score(latest)
    
    # =========================================================================
    # DISPLAY: MARKET CHARACTER
    # =========================================================================
    console.print("\n")
    console.print(Panel.fit(
        f"[bold white]MARKET CHARACTER ANALYSIS[/bold white]",
        border_style="magenta"
    ))
    
    char_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    char_table.add_column("Feature", style="cyan")
    char_table.add_column("Value", justify="right", style="white")
    char_table.add_column("Trading Interpretation", style="yellow")
    
    # Hurst
    hurst = latest.get('hurst', 0.5)
    hurst_color = "green" if hurst > 0.55 else ("red" if hurst < 0.45 else "white")
    char_table.add_row(
        "Hurst Exponent",
        f"[{hurst_color}]{hurst:.3f}[/{hurst_color}]",
        interpretations.get('market_character', '')
    )
    
    # Autocorrelation
    autocorr = latest.get('return_autocorr', 0)
    ac_color = "green" if autocorr > 0.2 else ("red" if autocorr < -0.2 else "white")
    char_table.add_row(
        "Return Autocorrelation",
        f"[{ac_color}]{autocorr:.3f}[/{ac_color}]",
        interpretations.get('strategy_fit', '')
    )
    
    console.print(char_table)
    
    # =========================================================================
    # DISPLAY: MOMENTUM
    # =========================================================================
    console.print("\n")
    console.print(Panel.fit(
        f"[bold white]MOMENTUM FEATURES[/bold white]",
        border_style="green"
    ))
    
    mom_table = Table(box=box.ROUNDED, show_header=True, header_style="bold green")
    mom_table.add_column("Feature", style="cyan")
    mom_table.add_column("Value", justify="right", style="white")
    mom_table.add_column("Trading Use", style="yellow")
    
    roc_5 = latest.get('roc_5', 0)
    roc_10 = latest.get('roc_10', 0)
    roc_20 = latest.get('roc_20', 0)
    accel = latest.get('price_accel', 0)
    
    roc_color = "green" if roc_20 > 0 else "red"
    mom_table.add_row("ROC 5-bar", f"[{roc_color}]{roc_5:+.2f}%[/{roc_color}]", "Short-term momentum")
    mom_table.add_row("ROC 10-bar", f"[{roc_color}]{roc_10:+.2f}%[/{roc_color}]", "")
    mom_table.add_row("ROC 20-bar", f"[{roc_color}]{roc_20:+.2f}%[/{roc_color}]", "Primary trend gauge")
    
    accel_color = "green" if accel > 0 else "red"
    mom_table.add_row(
        "Price Acceleration",
        f"[{accel_color}]{accel:+.2f}[/{accel_color}]",
        interpretations.get('momentum_action', '')
    )
    
    console.print(mom_table)
    
    # =========================================================================
    # DISPLAY: MEAN REVERSION
    # =========================================================================
    console.print("\n")
    console.print(Panel.fit(
        f"[bold white]MEAN REVERSION FEATURES[/bold white]",
        border_style="blue"
    ))
    
    rev_table = Table(box=box.ROUNDED, show_header=True, header_style="bold blue")
    rev_table.add_column("Feature", style="cyan")
    rev_table.add_column("Value", justify="right", style="white")
    rev_table.add_column("Trading Use", style="yellow")
    
    bbp = latest.get('bb_percentile', 0.5)
    rsi_pct = latest.get('rsi_percentile', 50)
    zscore = latest.get('zscore_to_ma', 0)
    
    bbp_color = "green" if bbp < 0.2 else ("red" if bbp > 0.8 else "white")
    rev_table.add_row(
        "BB Percentile",
        f"[{bbp_color}]{bbp:.2f}[/{bbp_color}]",
        "0=Lower Band, 1=Upper Band"
    )
    
    rsi_color = "green" if rsi_pct < 20 else ("red" if rsi_pct > 80 else "white")
    rev_table.add_row(
        "RSI Percentile",
        f"[{rsi_color}]{rsi_pct:.0f}th[/{rsi_color}]",
        "Historical RSI rank"
    )
    
    z_color = "green" if zscore < -2 else ("red" if zscore > 2 else "white")
    rev_table.add_row(
        "Z-Score to MA(50)",
        f"[{z_color}]{zscore:+.2f}σ[/{z_color}]",
        interpretations.get('reversion_signal', '')
    )
    
    console.print(rev_table)
    
    # =========================================================================
    # DISPLAY: VOLATILITY & RISK
    # =========================================================================
    console.print("\n")
    console.print(Panel.fit(
        f"[bold white]VOLATILITY & RISK[/bold white]",
        border_style="yellow"
    ))
    
    vol_table = Table(box=box.ROUNDED, show_header=True, header_style="bold yellow")
    vol_table.add_column("Feature", style="cyan")
    vol_table.add_column("Value", justify="right", style="white")
    vol_table.add_column("Trading Use", style="yellow")
    
    hv = latest.get('hist_volatility', 0)
    vov = latest.get('vol_of_vol', 0)
    vol_regime = latest.get('vol_regime', 'MEDIUM')
    vol_pct = latest.get('vol_percentile', 50)
    
    vol_table.add_row("Historical Volatility", f"{hv:.1f}% ann.", "Position sizing input")
    vol_table.add_row("Volatility of Vol", f"{vov:.2f}", "Regime stability")
    
    regime_color = "red" if vol_regime == "HIGH" else ("green" if vol_regime == "LOW" else "yellow")
    vol_table.add_row(
        "Volatility Regime",
        f"[{regime_color}]{vol_regime} ({vol_pct:.0f}th pct)[/{regime_color}]",
        interpretations.get('vol_action', '')
    )
    
    console.print(vol_table)
    
    # =========================================================================
    # DISPLAY: TRADING SCORES
    # =========================================================================
    console.print("\n")
    console.print(Panel.fit(
        f"[bold white]ACTIONABLE TRADING SCORES[/bold white]",
        border_style="cyan"
    ))
    
    score_table = Table(box=box.DOUBLE_EDGE, show_header=True, header_style="bold cyan")
    score_table.add_column("Score", style="white")
    score_table.add_column("Value", justify="center", style="bold")
    score_table.add_column("What It Means", style="dim")
    
    trend_score = scores.get('trend_strength', 0)
    rev_score = scores.get('reversion_opportunity', 0)
    risk_score = scores.get('risk_level', 50)
    size_mult = scores.get('size_multiplier', 1.0)
    
    trend_color = "green" if trend_score > 60 else ("red" if trend_score < 40 else "yellow")
    score_table.add_row(
        "Trend Strength",
        f"[{trend_color}]{trend_score:.0f}/100[/{trend_color}]",
        ">60: Strong trend env, use breakouts"
    )
    
    rev_color = "green" if rev_score > 60 else ("yellow" if rev_score > 40 else "dim")
    score_table.add_row(
        "Reversion Opportunity",
        f"[{rev_color}]{rev_score:.0f}/100[/{rev_color}]",
        ">60: Good fade setup"
    )
    
    risk_color = "red" if risk_score > 60 else ("green" if risk_score < 40 else "yellow")
    score_table.add_row(
        "Risk Level",
        f"[{risk_color}]{risk_score:.0f}/100[/{risk_color}]",
        "<40: Safe, >60: Dangerous"
    )
    
    size_color = "green" if size_mult > 1 else ("red" if size_mult < 1 else "white")
    score_table.add_row(
        "⚡ Position Size Multiplier",
        f"[{size_color}]{size_mult:.2f}x[/{size_color}]",
        "Apply to your base lot size"
    )
    
    console.print(score_table)
    
    # =========================================================================
    # FINAL RECOMMENDATION
    # =========================================================================
    console.print("\n")
    
    # Determine overall recommendation
    if trend_score > 60 and risk_score < 50:
        rec = "[bold green]✓ TREND ENVIRONMENT[/bold green] - Use breakout entries, trail stops, let winners run"
        rec_box = "green"
    elif rev_score > 60 and risk_score < 50:
        rec = "[bold blue]↺ REVERSION SETUP[/bold blue] - Fade extremes, take quick profits, tight stops"
        rec_box = "blue"
    elif risk_score > 70:
        rec = "[bold red]⚠ HIGH RISK[/bold red] - Reduce size or sit out, vol too high"
        rec_box = "red"
    else:
        rec = "[bold yellow]◐ MIXED CONDITIONS[/bold yellow] - Be selective, smaller positions"
        rec_box = "yellow"
    
    console.print(Panel(
        f"{rec}\n\n"
        f"[dim]Based on: Hurst={hurst:.2f}, VolRegime={vol_regime}, BBP={bbp:.2f}, Autocorr={autocorr:.2f}[/dim]",
        title="[bold]TRADING RECOMMENDATION[/bold]",
        border_style=rec_box
    ))
    
    # Show how to use features for scaling
    console.print("\n")
    console.print(Panel(
        "[bold cyan]HOW TO USE THESE FEATURES:[/bold cyan]\n\n"
        "[bold]1. ENTRY DECISIONS:[/bold]\n"
        "   • Hurst > 0.55 + Trend Score > 60 → Take breakout trades\n"
        "   • Hurst < 0.45 + BBP < 0.2 → Take mean-reversion longs\n"
        "   • Autocorr positive → Follow momentum, don't fade\n\n"
        "[bold]2. POSITION SIZING:[/bold]\n"
        f"   • Current multiplier: {size_mult:.2f}x your base size\n"
        "   • High vol = smaller size, Low vol = can size up\n\n"
        "[bold]3. SCALING IN/OUT:[/bold]\n"
        "   • Price Acceleration positive → Add to winners\n"
        "   • Price Acceleration flipping negative → Take partial profits\n"
        "   • BBP hitting extremes → Take profits on trend trades\n\n"
        "[bold]4. STOP LOGIC:[/bold]\n"
        "   • High VoV (unstable vol) → Use wider stops\n"
        "   • Low VoV → Can use tighter stops\n"
        "   • Trend Score falling → Tighten stops on trend trades",
        title="Trading Framework",
        border_style="cyan"
    ))
    
    mt5.shutdown()


if __name__ == "__main__":
    display_features("GOLD")
