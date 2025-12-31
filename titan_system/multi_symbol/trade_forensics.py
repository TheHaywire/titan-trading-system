"""
Trade Forensics - Account & Performance Analysis
=================================================
Analyzes trading history to identify patterns, profitable setups,
and areas for improvement. Provides data-driven insights.

Key Features:
- Win/loss analysis by symbol, hour, day of week
- Identifies "death zones" (times to avoid)
- Identifies "power hours" (best trading times)
- Risk metrics (max drawdown, consecutive losses)
- Manual trade detection and analysis
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger("Titan.TradeForensics")


@dataclass
class TradeStats:
    """Comprehensive trade statistics."""
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    best_trade: float
    worst_trade: float
    avg_hold_time: float  # in hours


class TradeForensics:
    """
    Analyze trading history for patterns and insights.
    
    Usage:
        forensics = TradeForensics()
        report = forensics.analyze(days=30)
        forensics.print_report(report)
    """
    
    MAGIC_NUMBERS = {
        234001: "Titan Multi-Symbol",
        234000: "Titan Engine",
        0: "Manual Trade"
    }
    
    def __init__(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    
    def get_trade_history(self, days: int = 30) -> pd.DataFrame:
        """
        Fetch trade history from MT5.
        
        Args:
            days: Number of days to look back
            
        Returns:
            DataFrame with trade details
        """
        from_date = datetime.now() - timedelta(days=days)
        to_date = datetime.now()
        
        deals = mt5.history_deals_get(from_date, to_date)
        if deals is None or len(deals) == 0:
            logger.warning("No trade history found")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        
        # Filter for actual trades (buy/sell, not deposits/adjustments)
        df = df[df['type'].isin([0, 1])]  # 0=buy, 1=sell
        
        # Add readable columns
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.day_name()
        df['is_win'] = df['profit'] > 0
        df['is_loss'] = df['profit'] < 0
        df['trade_type'] = df['type'].map({0: 'BUY', 1: 'SELL'})
        df['source'] = df['magic'].map(lambda x: self.MAGIC_NUMBERS.get(x, f"Magic:{x}"))
        
        return df
    
    def get_open_positions(self) -> pd.DataFrame:
        """Get currently open positions."""
        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        df['type_str'] = df['type'].map({0: 'BUY', 1: 'SELL'})
        df['source'] = df['magic'].map(lambda x: self.MAGIC_NUMBERS.get(x, f"Magic:{x}"))
        return df
    
    def calculate_stats(self, df: pd.DataFrame) -> TradeStats:
        """Calculate comprehensive statistics from trade DataFrame."""
        if df.empty:
            return TradeStats(
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            )
        
        wins = df[df['profit'] > 0]
        losses = df[df['profit'] < 0]
        
        total_profit = wins['profit'].sum() if not wins.empty else 0
        total_loss = abs(losses['profit'].sum()) if not losses.empty else 0
        
        # Consecutive wins/losses
        max_consec_wins = 0
        max_consec_losses = 0
        current_wins = 0
        current_losses = 0
        
        for is_win in df['is_win']:
            if is_win:
                current_wins += 1
                current_losses = 0
                max_consec_wins = max(max_consec_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consec_losses = max(max_consec_losses, current_losses)
        
        # Max drawdown calculation
        cumulative_pnl = df['profit'].cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown = running_max - cumulative_pnl
        max_dd = drawdown.max()
        
        return TradeStats(
            total_trades=len(df),
            wins=len(wins),
            losses=len(losses),
            win_rate=len(wins) / len(df) * 100 if len(df) > 0 else 0,
            total_profit=total_profit,
            total_loss=total_loss,
            net_pnl=df['profit'].sum(),
            avg_win=wins['profit'].mean() if not wins.empty else 0,
            avg_loss=losses['profit'].mean() if not losses.empty else 0,
            profit_factor=total_profit / total_loss if total_loss > 0 else float('inf'),
            max_drawdown=max_dd,
            max_consecutive_wins=max_consec_wins,
            max_consecutive_losses=max_consec_losses,
            best_trade=df['profit'].max(),
            worst_trade=df['profit'].min(),
            avg_hold_time=0  # Would need position open/close times
        )
    
    def analyze_by_symbol(self, df: pd.DataFrame) -> Dict[str, TradeStats]:
        """Analyze performance by symbol."""
        results = {}
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]
            results[symbol] = self.calculate_stats(symbol_df)
        return results
    
    def analyze_by_hour(self, df: pd.DataFrame) -> Dict[int, TradeStats]:
        """Analyze performance by trading hour (UTC)."""
        results = {}
        for hour in range(24):
            hour_df = df[df['hour'] == hour]
            if not hour_df.empty:
                results[hour] = self.calculate_stats(hour_df)
        return results
    
    def analyze_by_day(self, df: pd.DataFrame) -> Dict[str, TradeStats]:
        """Analyze performance by day of week."""
        results = {}
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            day_df = df[df['day_of_week'] == day]
            if not day_df.empty:
                results[day] = self.calculate_stats(day_df)
        return results
    
    def find_death_zones(self, by_hour: Dict[int, TradeStats]) -> List[int]:
        """Find hours with consistently negative performance."""
        death_zones = []
        for hour, stats in by_hour.items():
            # Death zone: win rate < 40% AND negative net P&L AND at least 3 trades
            if stats.win_rate < 40 and stats.net_pnl < 0 and stats.total_trades >= 3:
                death_zones.append(hour)
        return sorted(death_zones)
    
    def find_power_hours(self, by_hour: Dict[int, TradeStats]) -> List[int]:
        """Find hours with consistently positive performance."""
        power_hours = []
        for hour, stats in by_hour.items():
            # Power hour: win rate >= 55% AND positive net P&L AND at least 3 trades
            if stats.win_rate >= 55 and stats.net_pnl > 0 and stats.total_trades >= 3:
                power_hours.append(hour)
        return sorted(power_hours)
    
    def identify_best_setups(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify the most profitable trade setups."""
        # Group by symbol + hour + direction
        df['setup'] = df['symbol'] + '_' + df['hour'].astype(str) + '_' + df['trade_type']
        
        setup_stats = df.groupby('setup').agg({
            'profit': ['sum', 'count', 'mean'],
            'is_win': 'mean'
        }).round(2)
        
        setup_stats.columns = ['total_pnl', 'trade_count', 'avg_pnl', 'win_rate']
        setup_stats['win_rate'] = (setup_stats['win_rate'] * 100).round(1)
        
        # Filter for statistically significant setups
        significant = setup_stats[setup_stats['trade_count'] >= 3]
        
        # Best setups: positive P&L and decent win rate
        best = significant[
            (significant['total_pnl'] > 0) & 
            (significant['win_rate'] >= 50)
        ].sort_values('total_pnl', ascending=False)
        
        return best.head(10)
    
    def identify_worst_setups(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify losing trade setups to avoid."""
        df['setup'] = df['symbol'] + '_' + df['hour'].astype(str) + '_' + df['trade_type']
        
        setup_stats = df.groupby('setup').agg({
            'profit': ['sum', 'count', 'mean'],
            'is_win': 'mean'
        }).round(2)
        
        setup_stats.columns = ['total_pnl', 'trade_count', 'avg_pnl', 'win_rate']
        setup_stats['win_rate'] = (setup_stats['win_rate'] * 100).round(1)
        
        significant = setup_stats[setup_stats['trade_count'] >= 3]
        
        # Worst setups: negative P&L and low win rate
        worst = significant[
            (significant['total_pnl'] < 0) & 
            (significant['win_rate'] < 50)
        ].sort_values('total_pnl', ascending=True)
        
        return worst.head(10)
    
    def analyze_manual_trades(self, df: pd.DataFrame) -> Dict:
        """Specifically analyze manual trades (magic=0)."""
        manual = df[df['magic'] == 0]
        bot = df[df['magic'] != 0]
        
        return {
            'manual_stats': self.calculate_stats(manual) if not manual.empty else None,
            'bot_stats': self.calculate_stats(bot) if not bot.empty else None,
            'manual_count': len(manual),
            'bot_count': len(bot)
        }
    
    def generate_report(self, days: int = 30) -> Dict:
        """Generate comprehensive performance report."""
        df = self.get_trade_history(days)
        
        if df.empty:
            return {'error': 'No trade history found'}
        
        by_hour = self.analyze_by_hour(df)
        
        report = {
            'period_days': days,
            'overall': self.calculate_stats(df),
            'by_symbol': self.analyze_by_symbol(df),
            'by_hour': by_hour,
            'by_day': self.analyze_by_day(df),
            'death_zones': self.find_death_zones(by_hour),
            'power_hours': self.find_power_hours(by_hour),
            'best_setups': self.identify_best_setups(df),
            'worst_setups': self.identify_worst_setups(df),
            'manual_analysis': self.analyze_manual_trades(df),
            'open_positions': self.get_open_positions()
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted report."""
        if 'error' in report:
            print(f"Error: {report['error']}")
            return
        
        overall = report['overall']
        
        print("\n" + "="*70)
        print(f"  TRADE FORENSICS REPORT - Last {report['period_days']} Days")
        print("="*70)
        
        # Overall Stats
        print("\n📊 OVERALL PERFORMANCE")
        print("-"*50)
        print(f"  Total Trades: {overall.total_trades}")
        print(f"  Win/Loss: {overall.wins}W / {overall.losses}L")
        print(f"  Win Rate: {overall.win_rate:.1f}%")
        print(f"  Net P&L: ${overall.net_pnl:,.2f}")
        print(f"  Profit Factor: {overall.profit_factor:.2f}")
        print(f"  Max Drawdown: ${overall.max_drawdown:,.2f}")
        print(f"  Best Trade: ${overall.best_trade:,.2f}")
        print(f"  Worst Trade: ${overall.worst_trade:,.2f}")
        print(f"  Max Consecutive Losses: {overall.max_consecutive_losses}")
        
        # Current Positions
        open_pos = report['open_positions']
        if not open_pos.empty:
            print("\n📍 OPEN POSITIONS")
            print("-"*50)
            for _, p in open_pos.iterrows():
                print(f"  {p['symbol']}: {p['type_str']} {p['volume']} lots | "
                      f"P&L: ${p['profit']:.2f} | {p['source']}")
        
        # Death Zones
        if report['death_zones']:
            print("\n⚠️  DEATH ZONES (Avoid Trading)")
            print("-"*50)
            for hour in report['death_zones']:
                stats = report['by_hour'][hour]
                print(f"  {hour:02d}:00 UTC - Win Rate: {stats.win_rate:.1f}%, "
                      f"P&L: ${stats.net_pnl:.2f} ({stats.total_trades} trades)")
        
        # Power Hours
        if report['power_hours']:
            print("\n✅ POWER HOURS (Best Performance)")
            print("-"*50)
            for hour in report['power_hours']:
                stats = report['by_hour'][hour]
                print(f"  {hour:02d}:00 UTC - Win Rate: {stats.win_rate:.1f}%, "
                      f"P&L: ${stats.net_pnl:.2f} ({stats.total_trades} trades)")
        
        # By Symbol
        print("\n📈 PERFORMANCE BY SYMBOL")
        print("-"*50)
        by_symbol = report['by_symbol']
        sorted_symbols = sorted(by_symbol.items(), key=lambda x: x[1].net_pnl, reverse=True)
        for symbol, stats in sorted_symbols[:10]:
            emoji = "🟢" if stats.net_pnl > 0 else "🔴"
            print(f"  {emoji} {symbol}: {stats.wins}W/{stats.losses}L ({stats.win_rate:.0f}%) "
                  f"| P&L: ${stats.net_pnl:.2f}")
        
        # Manual vs Bot
        manual = report['manual_analysis']
        if manual['manual_stats']:
            print("\n🎯 MANUAL vs BOT TRADES")
            print("-"*50)
            m = manual['manual_stats']
            print(f"  Manual: {m.wins}W/{m.losses}L ({m.win_rate:.1f}%) | P&L: ${m.net_pnl:.2f}")
        if manual['bot_stats']:
            b = manual['bot_stats']
            print(f"  Bot:    {b.wins}W/{b.losses}L ({b.win_rate:.1f}%) | P&L: ${b.net_pnl:.2f}")
        
        # Best Setups
        best = report['best_setups']
        if not best.empty:
            print("\n🏆 BEST PERFORMING SETUPS")
            print("-"*50)
            for setup, row in best.head(5).iterrows():
                print(f"  {setup}: {row['win_rate']:.0f}% win rate, "
                      f"${row['total_pnl']:.2f} P&L ({int(row['trade_count'])} trades)")
        
        # Worst Setups
        worst = report['worst_setups']
        if not worst.empty:
            print("\n💀 SETUPS TO AVOID")
            print("-"*50)
            for setup, row in worst.head(5).iterrows():
                print(f"  {setup}: {row['win_rate']:.0f}% win rate, "
                      f"${row['total_pnl']:.2f} P&L ({int(row['trade_count'])} trades)")
        
        print("\n" + "="*70)
    
    def get_recommendations(self, report: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        overall = report['overall']
        
        # Win rate check
        if overall.win_rate < 40:
            recommendations.append(
                f"⚠️ Critical: Win rate is {overall.win_rate:.1f}% (below 40%). "
                "Consider reducing position sizes until strategy improves."
            )
        
        # Death zones
        if report['death_zones']:
            hours = ", ".join(f"{h}:00" for h in report['death_zones'])
            recommendations.append(
                f"🚫 Avoid trading during: {hours} UTC - historically unprofitable."
            )
        
        # Consecutive losses
        if overall.max_consecutive_losses >= 5:
            recommendations.append(
                f"⚠️ Max {overall.max_consecutive_losses} consecutive losses detected. "
                "Consider implementing a 'cooling off' period after 3 losses."
            )
        
        # Symbol blacklist
        worst_symbols = sorted(
            report['by_symbol'].items(), 
            key=lambda x: x[1].net_pnl
        )[:3]
        if worst_symbols and worst_symbols[0][1].net_pnl < -100:
            symbols = ", ".join(s[0] for s in worst_symbols if s[1].net_pnl < -100)
            recommendations.append(
                f"🔴 Consider blacklisting: {symbols} - consistent losers."
            )
        
        # Power hours
        if report['power_hours']:
            hours = ", ".join(f"{h}:00" for h in report['power_hours'])
            recommendations.append(
                f"✅ Focus trading during: {hours} UTC - best historical performance."
            )
        
        return recommendations


# Quick run
if __name__ == "__main__":
    forensics = TradeForensics()
    report = forensics.generate_report(days=30)
    forensics.print_report(report)
    
    print("\n" + "="*70)
    print("  RECOMMENDATIONS")
    print("="*70)
    for rec in forensics.get_recommendations(report):
        print(f"\n{rec}")
