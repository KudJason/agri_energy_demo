import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse
import time

# Configuration
DOWNLOAD_DIR = "data/pdfs/flanders"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SOURCES = [
    {
        "name": "Ecoregelingen_2025",
        "url": "https://lv.vlaanderen.be/steun/glb-2023-2027/ecoregelingen",
        "keywords": ["fiche", "handleiding", "voorwaarden"],
    },
    {
        "name": "VLIF_Innovatie",
        "url": "https://lv.vlaanderen.be/subsidies/vlif-investeringssteun-voor-landbouwers/innovatieve-investeringen",
        "keywords": ["handleiding", "tabel", "lijst"],
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
    folder = os.path.join(DOWNLOAD_DIR, source['name'])
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
            text = link.get_text(" ", strip=True).lower()
            
            full_url = urljoin(source['url'], href)
            
            if not full_url.lower().endswith('.pdf'):
                continue

            # Optional keyword filtering if needed, but for now grab all PDFs on the relevant pages
            # as they are usually specific to the policy
            
            print(f"Found PDF: {text[:50]}... -> {full_url}")
            download_file(full_url, folder)
            count += 1
            if count >= 10: 
                break
                    
        print(f"Found {count} documents for {source['name']}")
        
    except Exception as e:
        print(f"Failed to scrape {source['name']}: {e}")

if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    for source in SOURCES:
        scrape_source(source)
    print("\n\nAll downloads complete.")
