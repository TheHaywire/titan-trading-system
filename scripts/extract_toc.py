import sys
import os

pdf_path = r"c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025\TABooks\Technical Analysis For Dummies 2nd Edition.pdf"
output_file = r"c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025\toc_extract.txt"

try:
    import PyPDF2
    print("Using PyPDF2")
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        print(f"Total Pages: {total_pages}")
        
        with open(output_file, 'w', encoding='utf-8') as out:
            # Table of Contents usually in first 20 pages
            out.write(f"Total Pages: {total_pages}\n")
            for i in range(min(25, total_pages)):
                text = reader.pages[i].extract_text()
                out.write(f"\n--- Page {i+1} ---\n")
                out.write(text)
                out.write("\n----------------\n")
    print(f"Extraction complete. Saved to {output_file}")

except ImportError:
    print("PyPDF2 not found.")
except Exception as e:
    print(f"Error: {e}")
