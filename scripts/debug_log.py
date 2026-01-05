
import os

log_file = 'data/titan_engine.log'
if os.path.exists(log_file):
    with open(log_file, 'rb') as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 5000), 0) # Read last 5KB
        content = f.read().decode('utf-8', errors='ignore')
        print(content)
else:
    print("Log file not found.")
