import os
import glob
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_ROOT = os.path.join(BASE_DIR, "data/pdfs")
MD_ROOT = os.path.join(BASE_DIR, "data/markdown")

def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        print(f"❌ Error reading {os.path.basename(filepath)}: {e}")
        return None

def convert_all():
    print(f"🚀 Starting PDF to Markdown conversion...")
    print(f"Source: {PDF_ROOT}")
    print(f"Target: {MD_ROOT}")
    
    # Walk through all directories in PDF_ROOT
    for root, dirs, files in os.walk(PDF_ROOT):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                
                # Determine relative path to replicate structure
                rel_path = os.path.relpath(root, PDF_ROOT)
                target_dir = os.path.join(MD_ROOT, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                
                md_filename = file.replace(".pdf", ".md").replace(".PDF", ".md")
                md_path = os.path.join(target_dir, md_filename)
                
                if os.path.exists(md_path):
                    # Optional: Skip if exists? For now, overwrite or skip.
                    # User asked to "convert", implies triggering it. 
                    # But let's check size to avoid re-doing work if it's already good.
                    if os.path.getsize(md_path) > 0:
                        # print(f"⏭️ Skipping {md_filename} (exists)")
                        continue
                
                print(f"📄 Converting: {file}...")
                text = extract_text_from_pdf(pdf_path)
                
                if text:
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write(f"# {file}\n\n")
                        f.write(text)
                    print(f"  ✅ Saved to {os.path.relpath(md_path, BASE_DIR)}")
                else:
                    print(f"  ⚠️ Empty text extracted for {file}")

if __name__ == "__main__":
    convert_all()
