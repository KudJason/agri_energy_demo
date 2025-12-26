import os
from pypdf import PdfReader

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_SOURCE_DIR = os.path.join(os.path.dirname(BASE_DIR), "policy_downloader/data/pdfs/france/TelePAC_Forms_2025")

def debug_text():
    # Pick a file likely to have numbers, e.g. "Notice" or "Guide"
    target_file = "Dossier-PAC-2025_guide-admissibilite.pdf"
    filepath = os.path.join(PDF_SOURCE_DIR, target_file)
    
    if not os.path.exists(filepath):
        # Fallback to any file
        files = [f for f in os.listdir(PDF_SOURCE_DIR) if f.endswith(".pdf")]
        if not files:
            print("No PDFs found.")
            return
        filepath = os.path.join(PDF_SOURCE_DIR, files[0])

    print(f"--- Debugging Text from: {os.path.basename(filepath)} ---")
    try:
        reader = PdfReader(filepath)
        # print first 2 pages
        for i in range(min(2, len(reader.pages))):
            print(f"\n--- Page {i+1} ---")
            print(reader.pages[i].extract_text())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_text()
