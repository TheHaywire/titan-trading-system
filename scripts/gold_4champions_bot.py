"""
GOLD MULTI-STRATEGY BOT - 4 VALIDATED CHAMPIONS
==============================================
Deploys all 4 validated strategies in a single bot
"""

import sys
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
from rich.console import Console
from rich.table import Table

# Add parent directory to path
sys.path.insert(0, 'c:/Users/manan/OneDrive/Documents/Metatrader Trading System 7-12-2025')

# Import from correct locations
from titan_system.backtest.strategies_momentum_extended import TripleEMA_Strategy
from titan_system.backtest.strategies_batches_4_8 import StatisticalMomentum_Strategy
from titan_system.backtest.strategies_volume import OnBalanceVolume_Strategy
# Use gold_champion_bot which is already deployed
import os
champion_bot_running = os.path.exists('scripts/gold_champion_bot.py')

console = Console()

class GoldChampionsBot:
    """Multi-strategy bot running all 4 validated GOLD champions"""
    
    def __init__(self):
        self.symbol = "GOLD"
        self.timeframe = mt5.TIMEFRAME_H4
        self.magic_numbers = {
            'H4_M15': 1001,
            'Triple_EMA': 1002,
            'Stat_Mom': 1003,
            'OBV': 1004
        }
        
        # Initialize strategies
        self.strategies = {
            'H4_M15': MTF_Trend_Entry_Strategy(),
            'Triple_EMA': TripleEMA_Strategy(),
            'Stat_Mom': StatisticalMomentum_Strategy(),
            'OBV': OnBalanceVolume_Strategy()
        }
        
        self.account_balance = 10000
        self.risk_per_strategy = 0.01  # 1% per strategy = 4% max total
        
    def init_mt5(self):
        """Initialize MT5 connection"""
        if not mt5.initialize():
            console.print("[red]MT5 initialization failed[/red]")
            return False
        
        info = mt5.account_info()
        if info:
            self.account_balance = info.balance
            console.print(f"[green]MT5 Connected | Balance: ${info.balance:,.2f}[/green]")
        return True
    
    def get_data(self):
        """Fetch H4 GOLD data"""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 300)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def analyze_all_strategies(self, df):
        """Run all strategies and return signals"""
        signals = {}
        
        for name, strategy in self.strategies.items():
            try:
                df_with_indicators = strategy.calculate_indicators(df.copy())
                signal = strategy.analyze(df_with_indicators)
                if signal:
                    signals[name] = signal
            except Exception as e:
                console.print(f"[red]{name} error: {e}[/red]")
        
        return signals
    
    def calculate_lot_size(self, stop_loss_pips):
        """Calculate position size based on risk"""
        if stop_loss_pips <= 0:
            return 0.01
        
        risk_amount = self.account_balance * self.risk_per_strategy
        pip_value = 10  # Standard for GOLD
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Limit to 0.01-1.0 lots
        return max(0.01, min(1.0, round(lot_size, 2)))
    
    def place_trade(self, strategy_name, signal, current_price):
        """Place trade for strategy"""
        magic = self.magic_numbers[strategy_name]
        
        # Calculate lot size
        sl_pips = abs(current_price - signal['stop_loss']) * 100
        lot_size = self.calculate_lot_size(sl_pips)
        
        direction = mt5.ORDER_TYPE_BUY if signal['direction'] == 'BUY' else mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot_size,
            "type": direction,
            "price": current_price,
            "sl": signal['stop_loss'],
            "tp": signal['take_profit'],
            "magic": magic,
            "comment": f"Champion_{strategy_name}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            console.print(f"[green]✅ {strategy_name}: {signal['direction']} {lot_size} lots @ {current_price}[/green]")
            return True
        else:
            console.print(f"[red]❌ {strategy_name} order failed: {result.comment}[/red]")
            return False
    
    def check_existing_positions(self):
        """Check if strategies already have positions"""
        positions = mt5.positions_get(symbol=self.symbol)
        active_magics = set()
        
        if positions:
            for pos in positions:
                if pos.magic in self.magic_numbers.values():
                    active_magics.add(pos.magic)
        
        return active_magics
    
    def run(self):
        """Main loop"""
        if not self.init_mt5():
            return
        
        console.print("\n[bold cyan]🏆 GOLD 4-CHAMPIONS BOT ACTIVE[/bold cyan]\n")
        
        try:
            while True:
                # Get current data
                df = self.get_data()
                if df is None:
                    continue
                
                current_price = df.iloc[-1]['close']
                
                # Check existing positions
                active_magics = self.check_existing_positions()
                
                # Analyze all strategies
                signals = self.analyze_all_strategies(df)
                
                # Display
                table = Table(title=f"GOLD @ ${current_price:.2f}")
                table.add_column("Strategy", style="cyan")
                table.add_column("Signal", style="yellow")
                table.add_column("Status", style="green")
                
                for name, strategy in self.strategies.items():
                    magic = self.magic_numbers[name]
                    has_position = magic in active_magics
                    signal = signals.get(name)
                    
                    if signal and not has_position:
                        # New signal - place trade
                        self.place_trade(name, signal, current_price)
                        status = f"OPENED {signal['direction']}"
                    elif has_position:
                        status = "ACTIVE"
                    else:
                        status = "WAITING"
                    
                    signal_str = f"{signal['direction']}" if signal else "None"
                    table.add_row(name, signal_str, status)
                
                console.clear()
                console.print(table)
                console.print(f"\n[dim]Last update: {datetime.now().strftime('%H:%M:%S')}[/dim]")
                
                # Wait 1 hour (since H4 timeframe)
                import time
                time.sleep(3600)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Bot stopped by user[/yellow]")
        finally:
            mt5.shutdown()


if __name__ == "__main__":
    bot = GoldChampionsBot()
    bot.run()
