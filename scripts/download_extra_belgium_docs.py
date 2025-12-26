import os
import re
import requests
import time
from urllib.parse import urljoin, unquote, urlparse
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKDOWN_ROOT = os.path.join(BASE_DIR, "data/markdown/belgium")
DOWNLOAD_ROOT = os.path.join(BASE_DIR, "data/downloads/belgium")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

FILE_EXTENSIONS = ('.pdf', '.xlsx', '.xls', '.docx', '.doc', '.zip', '.csv')

def sanitize_filename(text):
    if not text:
        return "unnamed_file"
    keepcharacters = (' ', '.', '_', '-')
    filename = "".join(c for c in text if c.isalnum() or c in keepcharacters).strip()
    return filename[:150] # Limit length

def get_file_info(url, headers):
    """Try to determine file extension and filename from headers if not in URL."""
    try:
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        content_type = response.headers.get('Content-Type', '').lower()
        content_disposition = response.headers.get('Content-Disposition', '')
        
        ext = None
        if 'application/pdf' in content_type:
            ext = 'pdf'
        elif 'spreadsheet' in content_type or 'excel' in content_type or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
            ext = 'xlsx'
        elif 'word' in content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
            ext = 'docx'
            
        filename = None
        if content_disposition:
            match = re.search(r'filename="?([^";]+)"?', content_disposition)
            if match:
                filename = match.group(1)
                
        return ext, filename
    except Exception as e:
        print(f"  Head request failed for {url}: {e}")
        return None, None

def download_file(url, region, original_text):
    path_obj = urlparse(url)
    filename = unquote(path_obj.path.split('/')[-1])
    
    ext = None
    for e in FILE_EXTENSIONS:
        if filename.lower().endswith(e):
            ext = e.strip('.')
            break
            
    headers = {"User-Agent": USER_AGENT}
    
    # If no extension or it looks like a generic download link, check headers
    if not ext or "/download" in url.lower() or "download" in filename.lower():
        head_ext, head_filename = get_file_info(url, headers)
        if head_ext:
            ext = head_ext
        if head_filename:
            filename = head_filename
            
    if not ext:
        # If it's still not identified, it might not be a file we want
        return False

    # Final fallback for filename
    if not filename or filename == 'download':
        filename = sanitize_filename(original_text)
        if not filename.lower().endswith(f".{ext}"):
            filename += f".{ext}"

    folder = os.path.join(DOWNLOAD_ROOT, region, ext)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)

    if os.path.exists(path):
        print(f"  Skipping existing {ext}: {filename}")
        return True

    try:
        print(f"  Downloading {ext}: {url}...")
        with requests.get(url, stream=True, headers=headers, timeout=30) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"  Saved to {path}")
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False

def scrape_and_save_md(url, region, title):
    headers = {"User-Agent": USER_AGENT}
    try:
        print(f"  Scraping HTML: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Determine content area based on region
        selector = "article" if region == "flanders" else "#main-content"
        content = soup.select_one(selector)
        if not content:
            content = soup.body
            
        if not content:
            return False
            
        markdown_text = md(str(content), heading_style="ATX")
        final_content = f"# {title}\n\nSource: {url}\n\n{markdown_text}"
        
        folder = os.path.join(MARKDOWN_ROOT, region, "extra")
        os.makedirs(folder, exist_ok=True)
        
        filename = sanitize_filename(title) + ".md"
        path = os.path.join(folder, filename)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"  Saved Markdown to {path}")
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return False

def process_markdown_file(filepath, region):
    print(f"\nProcessing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find [text](url)
    links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
    
    # Get base URL from "Source: ..." line if exists
    source_match = re.search(r'Source: (https?://[^\n]+)', content)
    base_url = source_match.group(1) if source_match else None

    for text, url in links:
        # Handle links with titles: [text](url "title")
        url = url.split()[0].strip('"').strip("'")
        
        if url.startswith('/'):
            if base_url:
                parsed_base = urlparse(base_url)
                url = f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
            else:
                continue
        
        if not url.startswith('http'):
            continue

        # Ignore noisy links
        if any(x in url.lower() for x in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'contact', 'login', 'search']):
            continue

        # 1. Check if it's a direct file link
        if any(url.lower().endswith(e) for e in FILE_EXTENSIONS) or "/download" in url.lower():
            download_file(url, region, text)
            continue
            
        # 2. Check if it's an internal policy page that we should scrape
        # Flanders: /nl/node/..., /subsidies/..., /beleid/...
        # Wallonia: /home/aides/..., /home/politique-economie/...
        is_internal = False
        if base_url:
            base_domain = urlparse(base_url).netloc
            link_domain = urlparse(url).netloc
            if base_domain == link_domain:
                is_internal = True
        
        meaningful_keywords = ['fiche', 'maatregel', 'subsidie', 'detail', 'interventions', 'aides', 'conditionnalite']
        is_meaningful = any(k in url.lower() or k in text.lower() for k in meaningful_keywords)
        
        if is_internal and is_meaningful:
            # Check if it's not the same page as source
            if url.rstrip('/') != (base_url or '').rstrip('/'):
                 scrape_and_save_md(url, region, text)

def main():
    for region in ['flanders', 'wallonia']:
        region_dir = os.path.join(MARKDOWN_ROOT, region)
        if not os.path.exists(region_dir):
            continue
            
        for filename in os.listdir(region_dir):
            if filename.endswith('.md') and filename != 'extra':
                filepath = os.path.join(region_dir, filename)
                process_markdown_file(filepath, region)

if __name__ == "__main__":
    main()
