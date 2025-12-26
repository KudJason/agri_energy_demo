import os
import json
import time
import glob
from dotenv import load_dotenv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD, RDFS
from openai import OpenAI
from pypdf import PdfReader

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Discover France PDF Files
FRANCE_PDF_DIR = os.path.join(BASE_DIR, "data/pdfs/france")
PDF_FILES = []
if os.path.exists(FRANCE_PDF_DIR):
    for root, dirs, files in os.walk(FRANCE_PDF_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                PDF_FILES.append(os.path.join(root, file))
else:
    print(f"Warning: Directory {FRANCE_PDF_DIR} does not exist.")

# No Markdown files for France yet
MD_FILES = []

OUTPUT_TTL = os.path.join(BASE_DIR, "knowledge_base/rules_france.ttl")

# Load Environment Variables
load_dotenv(os.path.join(BASE_DIR, ".env")) 
load_dotenv("/Users/jasonjia/Documents/industry_policy/secret/.env")

# Namespaces
CORE = Namespace("http://example.org/agri-energy/core#")

# API Setup
API_KEY = os.getenv("PERPLEXITY_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")

CHUNK_SIZE = 40000 # Characters per chunk to fit in context window comfortably
RATE_LIMIT_DELAY = 5 # Seconds between requests

def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
        return ""

def extract_text_from_md(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading MD {filepath}: {e}")
        return ""

def extract_rules_chunk(text_chunk, filename, chunk_id):
    prompt = f"""
    You are an Expert Legal Policy Analyst for the Agricultural Sector in France.
    
    OBJECTIVE:
    Analyze the provided document text chunk and identify structured data for **Financial Aid**, **Subsidies**, **Grants**, or **Eco-Schemes**.
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "opportunities": [
            {{
                "name_local": "Name in French",
                "name_en": "Name in English",
                "type": "Subsidy/Grant/Scheme",
                "description": "Short summary",
                "valid_from": "2023",
                "eligibility_criteria": [
                    {{"variable": "area", "operator": ">", "value": "10"}}
                ],
                "payment_rules": [
                    {{"name": "Base payment", "amount": 100, "unit": "EUR/ha"}}
                ]
            }}
        ]
    }}
    
    If no opportunities found in this chunk, return {{"opportunities": []}}.
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
        {"role": "user", "content": f"{prompt}\n\nCHUNK CONTENT:\n{text_chunk}"}
    ]
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"  > Sending chunk {chunk_id} to API (Attempt {attempt+1})...")
            start_time = time.time()
            response = client.chat.completions.create(
                model="sonar",
                messages=messages,
                temperature=0.1,
            )
            elapsed = time.time() - start_time
            print(f"  < Received response in {elapsed:.2f}s")
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Rate limiting sleep
            time.sleep(RATE_LIMIT_DELAY)
            
            return json.loads(content)
        except Exception as e:
            print(f"  ! Error on chunk {chunk_id}: {e}")
            if "429" in str(e):
                wait = (attempt + 1) * 10
                print(f"    Rate limit. Waiting {wait}s...")
                time.sleep(wait)
            else:
                return {"opportunities": []}
    return {"opportunities": []}

def main():
    print("--- Extracting France Rules (Condensed & Rate Limited) ---")
    if not API_KEY:
        print("Error: API Key not found.")
        return

    g = Graph()
    g.bind("core", CORE)
    g.bind("rdfs", RDFS)
    # Load existing graph
    if os.path.exists(OUTPUT_TTL):
        try:
            g.parse(OUTPUT_TTL, format="turtle")
            print(f"Loaded existing graph with {len(g)} triples.")
        except Exception as e:
            print(f"Error loading existing graph: {e}")

    # Track processed
    processed = set()
    PROGRESS_FILE = os.path.join(BASE_DIR, "knowledge_base/processed_france_files.txt")
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            processed = set(f.read().splitlines())

    # Request Rate Log
    RATE_LOG = os.path.join(BASE_DIR, "knowledge_base/request_rates_france.csv")
    if not os.path.exists(RATE_LOG):
        with open(RATE_LOG, "w") as f:
            f.write("Filename,ChunkID,TimeSeconds,OppsFound,Timestamp\n")

    # Combine file lists
    all_files = [(f, 'pdf') for f in PDF_FILES] + [(f, 'md') for f in MD_FILES]
    
    if not all_files:
        print(f"No files found to process. Please ensure PDFs are in {FRANCE_PDF_DIR}")
        return

    for filepath, ftype in all_files:
        if not os.path.exists(filepath):
            print(f"Skipping missing file: {filepath}")
            continue
            
        filename = os.path.basename(filepath)
        if filename in processed:
            print(f"Skipping cached: {filename}")
            continue

        print(f"\nProcessing {filename}...")
        
        # 1. Extract Text
        if ftype == 'pdf':
            text = extract_text_from_pdf(filepath)
        else:
            text = extract_text_from_md(filepath)
            
        if not text:
            print("  Empty text.")
            continue
            
        print(f"  Length: {len(text)} characters.")
        
        # 2. Chunking
        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        print(f"  Split into {len(chunks)} chunks.")
        
        # 3. Process Chunks
        for i, chunk in enumerate(chunks):
            # Check for existing data to resume at chunk level
            # Check if likely already processed: look for the first opportunity of this chunk
            slug = filename.replace(" ", "_").replace(".", "_").lower()
            expected_uri_check = URIRef(f"http://example.org/opportunity/fr/{slug}_c{i}_0")
            
            if (expected_uri_check, RDF.type, CORE.Opportunity) in g:
                print(f"  Skipping chunk {i} (already in Graph).")
                continue

            start_ts = time.time()
            data = extract_rules_chunk(chunk, filename, i)
            duration = time.time() - start_ts - RATE_LIMIT_DELAY # approximate API time
            
            # Log Rate
            opp_count = len(data.get("opportunities", []))
            with open(RATE_LOG, "a") as rf:
                rf.write(f"{filename},{i},{duration:.2f},{opp_count},{time.ctime()}\n")

            # 4. RDF Generation
            if "opportunities" in data:
                print(f"  Found {opp_count} opps in chunk {i}.")
                for idx, item in enumerate(data["opportunities"]):
                    # Unique URI based on file, chunk, and index
                    opp_uri = URIRef(f"http://example.org/opportunity/fr/{slug}_c{i}_{idx}")
                    doc_uri = URIRef(f"http://example.org/doc/fr/{slug}")

                    g.add((opp_uri, RDF.type, CORE.Opportunity))
                    g.add((opp_uri, CORE.definedBy, doc_uri))
                    
                    if item.get("name_local"):
                        g.add((opp_uri, RDFS.label, Literal(item["name_local"], lang="fr")))
                    if item.get("name_en"):
                        g.add((opp_uri, RDFS.label, Literal(item["name_en"], lang="en")))
                    if item.get("description"):
                         g.add((opp_uri, CORE.description, Literal(item["description"], lang="en")))
                         
                    # Criteria & Payments (simplified)
                    for c in item.get("eligibility_criteria", []):
                         g.add((opp_uri, CORE.requiresCriterion, Literal(str(c))))

            # Save Incrementally PER CHUNK
            g.serialize(destination=OUTPUT_TTL, format="turtle")
            print(f"  Saved progress for {filename} chunk {i}.")

        with open(PROGRESS_FILE, "a") as pf:
            pf.write(filename + "\n")
    
    print(f"\nCompleted. Total {len(g)} triples saved to {OUTPUT_TTL}")
if __name__ == "__main__":
    main()
