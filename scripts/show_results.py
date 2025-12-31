"""Extract summary from backtest results"""
import re

print("="*70)
print("PROPER BACKTEST RESULTS - Ernest Chan Methodology")
print("="*70)

# Run backtest and capture output
import subprocess
result = subprocess.run(
    ['python', 'scripts/proper_backtest_chan.py'], 
    capture_output=True, 
    text=True,
    cwd=r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025'
)

output = result.stdout + result.stderr

# Extract key sections
lines = output.split('\n')

print_next = False
for line in lines:
    if 'SUMMARY' in line or 'BEST PERFORMERS' in line or 'ERNEST CHAN' in line:
        print_next = True
    
    if print_next:
        print(line)
    
    if 'ANALYSIS COMPLETE' in line:
        break

print("\n" + "="*70)
