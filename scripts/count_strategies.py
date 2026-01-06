import os

files = [f for f in os.listdir('titan_system/backtest') if f.startswith('strategies_') and f.endswith('.py')]
total = 0

for f in sorted(files):
    with open(f'titan_system/backtest/{f}') as file:
        content = file.read()
        count = content.count('class ') - content.count('BaseStrategy')
        print(f'{f}: {count} strategies')
        total += count

print(f'\n=== TOTAL: {total} strategy classes ===')
