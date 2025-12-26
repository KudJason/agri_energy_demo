import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse
import time
from markdownify import markdownify as md

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_ROOT = os.path.join(BASE_DIR, "data/pdfs/belgium")
MARKDOWN_ROOT = os.path.join(BASE_DIR, "data/markdown/belgium")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Starting points that are less likely to change
SOURCES = [
    {
        "region": "flanders",
        "name": "Flanders_GLB_2023_2027",
        "start_url": "https://lv.vlaanderen.be/beleid/landbouwbeleid-eu/gemeenschappelijk-landbouwbeleid-glb/2023-2027-algemeen-kader",
        "navigation_keywords": ["Strategisch Plan"],
        "doc_keywords": ["strategisch plan", "glb", "pdf"],
        "html_scrape": True,
        "content_selector": "article" # Vlaanderen uses <article> or .region-content
    },
    {
        "region": "wallonia",
        "name": "Wallonia_PAC_2023_2027",
        "start_url": "https://agriculture.wallonie.be/plan-strategique-pac-2023-2027",
        "navigation_keywords": ["Contexte et contenu"],
        "doc_keywords": ["plan stratégique", "pac", "pdf"],
        "html_scrape": True,
        "content_selector": "#main-content" # Common ID, need to verify
    }
]

def sanitize_filename(text):
    keepcharacters = (' ','.','_','-')
    filename = "".join(c for c in text if c.isalnum() or c in keepcharacters).strip()
    return filename

def get_soup(url):
    print(f"Fetching {url}...")
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')

def download_file(url, folder):
    try:
        path_url = urlparse(url).path
        filename = unquote(path_url.split('/')[-1])
        if not filename.lower().endswith('.pdf'):
            filename += ".pdf"
        filename = sanitize_filename(filename)
        
        path = os.path.join(folder, filename)
        
        if os.path.exists(path):
            print(f"Skipping existing PDF: {filename}")
            return

        print(f"Downloading PDF: {url}...")
        headers = {"User-Agent": USER_AGENT}
        with requests.get(url, stream=True, headers=headers, timeout=20) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Saved PDF to {path}")
        time.sleep(0.5) 
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def save_markdown(title, html_content, folder, url):
    try:
        filename = sanitize_filename(title) + ".md"
        path = os.path.join(folder, filename)
        
        markdown_text = md(str(html_content), heading_style="ATX")
        
        # Add metadata
        final_content = f"# {title}\n\nSource: {url}\n\n{markdown_text}"
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"Saved Markdown to {path}")
    except Exception as e:
        print(f"Error saving markdown for {title}: {e}")

def scrape_recursive(url, source, depth, max_depth, visited, pdf_folder, md_folder):
    if depth > max_depth or url in visited:
        return
    
    visited.add(url)
    print(f"\n[Depth {depth}] Scrubbing: {url}")
    
    try:
        soup = get_soup(url)
        
        # 1. Download PDFs
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text(" ", strip=True)
            full_url = urljoin(url, href)
            
            if full_url.lower().endswith('.pdf'):
                # Optional: Filter by keywords if needed, but "exhaustive" implies grabbing most
                if source['doc_keywords']:
                    # Weak filter: Check if ANY keyword matches OR if it's clearly a policy doc
                    # For now, let's grab all PDFs on these targeted pages to be safe
                    pass
                
                print(f"Found PDF: {text[:50]}... -> {full_url}")
                download_file(full_url, pdf_folder)

        # 2. Scrape HTML Content
        if source.get('html_scrape'):
            title = soup.title.string if soup.title else "page_content"
            content = None
            selector = source.get('content_selector')
            if selector:
               content = soup.select_one(selector)
            
            if not content:
                content = soup.body
                
            if content:
                print(f"Saving Markdown for: {title}")
                save_markdown(title, content, md_folder, url)

        # 3. Recursive Step: Find sub-pages
        if depth < max_depth:
            # We need to be careful not to crawl the entire internet.
            # Filter links that are "children" or "siblings" in the policy section.
            
            candidate_links = []
            site_domain = urlparse(url).netloc
            
            # Use specific selectors for menu/content links if possible to reduce noise
            # For Flanders: region-content
            # For Wallonia: main-content
            
            area_selector = source.get('content_selector', 'body')
            area = soup.select_one(area_selector)
            if not area: 
                area = soup.body
                
            sub_links = area.find_all('a', href=True)
            
            for link in sub_links:
                href = link['href']
                full_url = urljoin(url, href)
                parsed_scraped = urlparse(full_url)
                
                # Basic domain check
                if parsed_scraped.netloc != site_domain:
                    continue
                
                # Filter out obvious non-content
                if any(x in full_url.lower() for x in ['login', 'contact', 'search', 'agenda', 'nieuws']):
                    continue

                # Custom path filters
                if source['region'] == 'flanders':
                     # Keep within landbouwbeleid or similar relevant paths
                     if '/beleid' not in full_url and '/landbouwbeleid' not in full_url:
                         continue
                elif source['region'] == 'wallonia':
                     # Keep within specific sections
                     if '/home/politique-economie' not in full_url and '/home/aides' not in full_url:
                         continue

                if full_url not in visited and not full_url.lower().endswith('.pdf'):
                    scrape_recursive(full_url, source, depth + 1, max_depth, visited, pdf_folder, md_folder)
                    
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")

def scrape_region(source):
    print(f"\n--- Scraping {source['name']} ({source['region']}) ---")
    pdf_folder = os.path.join(DOWNLOAD_ROOT, source['region'])
    md_folder = os.path.join(MARKDOWN_ROOT, source['region'])
    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(md_folder, exist_ok=True)
    
    current_url = source['start_url']
    
    # Initial Navigation if needed (same as before)
    if "navigation_keywords" in source:
        try:
            soup = get_soup(current_url)
            found_next = False
            for keyword in source["navigation_keywords"]:
                links = soup.find_all('a', href=True)
                for link in links:
                    text = link.get_text(" ", strip=True)
                    if keyword.lower() in text.lower():
                        next_url = urljoin(current_url, link['href'])
                        print(f"Navigating to start: {text[:40]}... -> {next_url}")
                        current_url = next_url
                        found_next = True
                        break 
                if found_next:
                    break
        except Exception as e:
            print(f"Navigation failed: {e}")
            return

    # Start Recursive Crawl
    visited = set()
    scrape_recursive(current_url, source, 1, 3, visited, pdf_folder, md_folder) # Depth limit 3



if __name__ == "__main__":
    for source in SOURCES:
        scrape_region(source)
    print("\n\nAll downloads complete.")
