"""Extract Algorithmic Trading PDF content"""
import pdfplumber
import os

pdf_path = r"TABooks\Algorithmic Trading.pdf"

print("Reading Algorithmic Trading PDF with pdfplumber...")
print("="*70 + "\n")

try:
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}\n")
        
        # Extract first 5 pages to find table of contents
        print("FIRST 5 PAGES (Finding chapter structure):")
        print("="*70)
        
        for i in range(min(5, total_pages)):
            page = pdf.pages[i]
            text = page.extract_text()
            
            if text:
                print(f"\n--- PAGE {i+1} ---")
                print(text[:800])
                
                if "Chapter" in text or "CHAPTER" in text or "Contents" in text:
                    print(f"\n🔍 FOUND STRUCTURE ON PAGE {i+1}")
            else:
                print(f"Page {i+1}: No text extracted")
        
        print("\n" + "="*70)
        print("✅ Structure analysis complete\n")
        
        # Now extract a sample chapter (let's try page 20-30)
        print("SAMPLE CHAPTER EXTRACTION (Pages 20-30):")
        print("="*70)
        
        for i in range(19, min(30, total_pages)):
            page = pdf.pages[i]
            text = page.extract_text()
            
            if text:
                print(f"\n--- PAGE {i+1} ---")
                print(text[:600])

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
