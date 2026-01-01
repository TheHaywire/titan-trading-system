import sys
import PyPDF2

def extract_pages(pdf_path, start_page, end_page):
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            total_pages = len(reader.pages)
            start_idx = max(0, start_page - 1)
            end_idx = min(total_pages, end_page)
            
            print(f"Extracting pages {start_page} to {end_page}...")
            
            for i in range(start_idx, end_idx):
                page_text = reader.pages[i].extract_text()
                text += f"\n--- Page {i+1} ---\n"
                text += page_text
                
            return text

    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python extract_pages.py <start_page> <end_page> <output_file>")
        sys.exit(1)
        
    pdf_path = r"c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025\TABooks\Technical Analysis For Dummies 2nd Edition.pdf"
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    output_file = sys.argv[3]
    
    content = extract_pages(pdf_path, start, end)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Content extracted to {output_file}")
