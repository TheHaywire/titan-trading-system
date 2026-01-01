"""
Extract text from 'A Complete Guide to Volume Price Analysis.pdf'
"""
import pdfplumber

pdf_path = r"c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025\TABooks\A Complete Guide to Volume Price Analysis.pdf"
output_path = r"c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025\vpa_book_extract.txt"

print(f"Extracting: {pdf_path}")

try:
    with pdfplumber.open(pdf_path) as pdf:
        full_text = []
        # Extract first 50 pages for improved speed to check structure, 
        # normally we'd do all but let's be efficient first or wait 
        # actually let's just do the whole thing, it's safer.
        print(f"Total Pages: {len(pdf.pages)}")
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text.append(f"--- PAGE {i+1} ---\n{text}\n")
            if i % 20 == 0:
                print(f"Processed {i} pages...")
                
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(full_text))
            
    print(f"✅ Saved to {output_path}")

except Exception as e:
    print(f"❌ Error: {e}")
