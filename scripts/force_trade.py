"""Force a trade NOW"""
import sys
sys.path.insert(0, '.')
import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()

from titan_system.strategies.proven_strategy import ProvenStrategy
from titan_system.execution.mt5_executor import MT5Executor

strategy = ProvenStrategy()
executor = MT5Executor()
executor.connect()

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'GOLD', 'BTCUSD', 'US500']

print('FORCING TRADE NOW...')
print('='*50)

traded = False
for sym in symbols:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 300)
    if rates is None:
        continue
    df = pd.DataFrame(rates)
    signal = strategy.analyze(df, sym)
    
    if signal:
        print(f'FOUND: {sym} {signal.direction}')
        print(f'Score: {signal.score}')
        
        tick = mt5.symbol_info(sym)
        point = tick.point
        sl_pts = abs(signal.entry - signal.stop_loss) / point
        tp_pts = abs(signal.take_profit - signal.entry) / point
        
        result = executor.execute_order(
            symbol=sym,
            order_type=signal.direction,
            lot=0.01,
            sl_points=int(sl_pts),
            tp_points=int(tp_pts),
            comment='FORCE_TRADE'
        )
        
        if result:
            print(f'EXECUTED!')
            traded = True
        else:
            print('Blocked by risk check')
        break

if not traded:
    print('No strategy signals - executing EURUSD BUY as test')
    result = executor.execute_order('EURUSD', 'BUY', 0.01, 500, 1000, 'TEST')
    if result:
        print('EURUSD TEST TRADE EXECUTED!')

mt5.shutdown()
