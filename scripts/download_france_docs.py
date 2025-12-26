import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse
import time

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_ROOT = os.path.join(BASE_DIR, "data/pdfs/france")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SOURCES = [
    {
        "name": "PSN_2023_2027",
        "url": "https://agriculture.gouv.fr/pac-2023-2027-le-plan-strategique-national", # Updated URL
        "keywords": ["plan stratégique national"],
    },
    {
        "name": "TelePAC_Forms_2025",
        "url": "https://www.telepac.agriculture.gouv.fr/telepac/html/public/aide/formulaires-2025.html",
        "keywords": ["formulaire", "notice"],
    },
    {
        "name": "Rules_Transversales",
        "url": "https://agriculture.gouv.fr/les-regles-transversales",
        "keywords": ["règle", "transversale"],
    }
]

def sanitize_filename(url):
    path = urlparse(url).path
    filename = unquote(path.split('/')[-1])
    if not filename.lower().endswith('.pdf'):
        filename += ".pdf"
    keepcharacters = (' ','.','_','-')
    filename = "".join(c for c in filename if c.isalnum() or c in keepcharacters).strip()
    return filename

def download_file(url, folder):
    try:
        filename = sanitize_filename(url)
        path = os.path.join(folder, filename)
        
        if os.path.exists(path):
            print(f"Skipping existing: {filename}")
            return

        print(f"Downloading: {url}...")
        headers = {"User-Agent": USER_AGENT}
        with requests.get(url, stream=True, headers=headers, timeout=20) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Saved to {path}")
        time.sleep(0.5) 
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def scrape_source(source):
    print(f"\n--- Scraping {source['name']} ---")
    folder = os.path.join(DOWNLOAD_ROOT, source['name'])
    os.makedirs(folder, exist_ok=True)
    
    try:
        headers = {"User-Agent": USER_AGENT}
        print(f"Fetching {source['url']}...")
        response = requests.get(source['url'], headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=True)
        count = 0
        
        for link in links:
            href = link['href']
            text = link.get_text(" ", strip=True)
            
            full_url = urljoin(source['url'], href)
            
            # Special handling for agriculture.gouv.fr /telecharger/ links
            if "agriculture.gouv.fr/telecharger/" in full_url:
                # Use text as filename
                # expect text like "Plan Stratégique National ... pdf - 16.48 Mo"
                # Remove size info if present
                clean_text = text.split("pdf -")[0].split("odf -")[0].strip()
                if not clean_text:
                    clean_text = f"doc_{href.split('/')[-1]}"
                
                filename = sanitize_filename(clean_text) # Use the sanitize function on the text
                if not filename.lower().endswith('.pdf'):
                    filename += ".pdf"
                    
                path = os.path.join(folder, filename)
                print(f"Found Download Link: {text[:50]}... -> {full_url}")
                
                # Custom download for these to avoid re-sanitizing URL as filename in download_file
                try:
                    if os.path.exists(path):
                        print(f"Skipping existing: {filename}")
                        continue

                    print(f"Downloading: {full_url} to {filename}...")
                    headers = {"User-Agent": USER_AGENT}
                    with requests.get(full_url, stream=True, headers=headers, timeout=20) as r:
                        r.raise_for_status()
                        with open(path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    print(f"Saved to {path}")
                    time.sleep(0.5)
                    count += 1
                except Exception as e:
                    print(f"Error downloading {full_url}: {e}")
                continue

            # Standard PDF link handling
            if not full_url.lower().endswith('.pdf'):
                continue

            print(f"Found PDF: {text[:50]}... -> {full_url}")
            download_file(full_url, folder)
            count += 1
            if count >= 20: 
                break
                    
        print(f"Found {count} documents for {source['name']}")
        
    except Exception as e:
        print(f"Failed to scrape {source['name']}: {e}")

if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_ROOT):
        os.makedirs(DOWNLOAD_ROOT)
        
    for source in SOURCES:
        scrape_source(source)
    print("\n\nAll downloads complete.")
