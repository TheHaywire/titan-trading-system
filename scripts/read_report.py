
try:
    with open('data/analysis_report.txt', 'r', encoding='utf-16') as f:
        print(f.read())
except Exception as e:
    print(f"UTF-16 failed: {e}")
    try:
        with open('data/analysis_report.txt', 'r', encoding='utf-8') as f:
            print(f.read())
    except Exception as e2:
        print(f"UTF-8 failed: {e2}")
