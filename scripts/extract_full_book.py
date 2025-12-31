"""
Complete extraction and analysis of Algorithmic Trading book
Focus on chapters about backtesting, overfitting, and strategy validation
"""
import pdfplumber

pdf_path = r"TABooks\Algorithmic Trading.pdf"

output_file = "algo_trading_complete_extract.txt"

print("Extracting Algorithmic Trading PDF...")
print("Looking for chapters on:")
print(" - Backtesting methodology")
print(" - Overfitting detection")
print(" - Walk-forward analysis")
print(" - Transaction costs")
print(" - Performance metrics\n")

with open(output_file, 'w', encoding='utf-8') as out:
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        
        out.write(f"ALGORITHMIC TRADING - Complete Extraction\n")
        out.write(f"Total Pages: {total_pages}\n")
        out.write("="*70 + "\n\n")
        
        # Extract ALL pages
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if text:
                out.write(f"\n{'='*70}\n")
                out.write(f"PAGE {i+1}\n")
                out.write(f"{'='*70}\n")
                out.write(text)
                out.write("\n")
                
                # Print progress
                if i % 20 == 0:
                    print(f"Extracted page {i+1}/{total_pages}")
        
        print(f"\n✅ Complete! Saved to: {output_file}")
        print(f"Total pages extracted: {total_pages}")

# Now analyze for key concepts
print("\nAnalyzing for key concepts...")

with open(output_file, 'r', encoding='utf-8') as f:
    content = f.read()
    
    keywords = [
        "overfit", "walk-forward", "transaction cost", 
        "in-sample", "out-of-sample", "parameter",
        "sharpe", "drawdown", "win rate", "expectancy"
    ]
    
    print("\nKey concept mentions:")
    for keyword in keywords:
        count = content.lower().count(keyword)
        if count > 0:
            print(f"  '{keyword}': {count} mentions")

print(f"\n📄 Full extraction saved to: {output_file}")
print("Now manually review for chapters on:")
print(" 1. Overfitting (why our filters failed)")
print(" 2. Transaction costs (our 0.25 pips vs 0.8 spread)")
print(" 3. Walk-forward (proper validation)")
