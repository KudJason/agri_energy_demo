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

# Specific Files as requested
PDF_FILES = [
    os.path.join(BASE_DIR, "data/pdfs/belgium/wallonia/Bio.2019.pdf"),
    os.path.join(BASE_DIR, "data/pdfs/belgium/wallonia/IZCNS2019.pdf"),
    os.path.join(BASE_DIR, "data/pdfs/belgium/wallonia/MAEC2019.pdf"),
    os.path.join(BASE_DIR, "data/pdfs/belgium/wallonia/Natura.2019.pdf"),
    os.path.join(BASE_DIR, "data/pdfs/belgium/wallonia/Plan stratégique wallon PAC_version 4.2.pdf")
]

# Consolidated Markdowns
MD_FILES = [
    os.path.join(BASE_DIR, "data/markdown/belgium/wallonia/all_extra_measures.md"),
    # Add other high-level MDs if useful, but 'extra' consolidation is the bulk
    os.path.join(BASE_DIR, "data/markdown/belgium/wallonia/Aides - Portail de lagriculture wallonne.md"),
    os.path.join(BASE_DIR, "data/markdown/belgium/wallonia/Pac 2023-2027 - Description des interventions - Portail de lagriculture wallonne.md")
]

OUTPUT_TTL = os.path.join(BASE_DIR, "knowledge_base/rules_belgium.ttl")

# Load Environment Variables
load_dotenv(os.path.join(BASE_DIR, ".env")) 
load_dotenv("/Users/jasonjia/Documents/industry_policy/secret/.env")

# Namespaces
CORE = Namespace("http://example.org/agri-energy/core#")

# API Setup
# API Setup
API_KEY = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

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
    You are an Expert Legal Policy Analyst for the Agricultural Sector in Belgium (Wallonia).
    
    OBJECTIVE:
    Analyze the provided document text chunk and identify structured data for **Financial Aid**, **Subsidies**, **Grants**, or **Eco-Schemes**.
    
    CRITICAL ANTI-DUPLICATION RULES:
    1. **Each opportunity MUST have a unique official identifier** (e.g., "MB13", "MC7", "141", "331", "372", etc.)
    2. **DO NOT extract the same measure multiple times** - if you see what appears to be the same aid scheme described in different wordings, extract it ONLY ONCE using the most complete description
    3. **IGNORE procedural/administrative content** - do NOT extract opportunities from:
       - Table of contents or navigation sections
       - Administrative notifications (e.g., "Autorisation de signature", "Formulaire")
       - General definitions or explanations UNLESS they define a specific aid scheme
       - Repeated headers or footers
    4. **If this chunk seems to repeat information from earlier in the document**, check if the opportunity was likely already extracted and SKIP it
    5. **Only extract if there are CONCRETE benefits**: aid amount, eligibility criteria, or application procedures
    
    UNIQUENESS VALIDATION:
    - Each opportunity should have a distinct official code or identifier (e.g., "MAEC MB13", "Intervention 331", "Eco-regime 141")
    - If you cannot find an official identifier, use the most specific official name
    - If an opportunity appears to be just a section heading or repetition of a previous measure, DO NOT extract it
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "opportunities": [
            {{
                "official_code": "MB13",  // REQUIRED: unique intervention code or identifier
                "name_local": "Name in French",
                "name_en": "Name in English",
                "type": "Subsidy/Grant/Scheme",
                "tags": ["Organic", "Livestock", "Investment", "Young Farmer"],
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
    
    If no NEW, UNIQUE opportunities found in this chunk, return {{"opportunities": []}}.
    ONLY return valid JSON. DO NOT use markdown code blocks.
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
                model="deepseek-reasoner",
                messages=messages,
                temperature=0,
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

def get_relevance_score(text_preview, filename):
    prompt = f"""
    Task: Rate the relevance of this document for extracting structured rules about Agricultural Financial Aids/Subsidies.
    
    Criteria:
    - High Score (8-10): The document explicitly DEFINES a subsidy/intervention (eligibility, amounts, conditions) or is a "strategic plan" with measure definitions.
    - Low Score (0-3): The document is a Form, Mandate, or pure administrative procedure without rule definitions.
    
    Filename: {filename}
    Content Preview:
    {text_preview[:2000]}
    
    Output: Return ONLY a single integer from 0 to 10.
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        # Extract first digit found
        import re
        match = re.search(r'\d+', content)
        if match:
            return int(match.group())
        return 0
    except Exception as e:
        print(f"Error scoring {filename}: {e}")
        return 0
    return {"opportunities": []}

def main():
    print("--- Extracting Belgium Rules (Condensed & Rate Limited) ---")
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
    # Simple heuristic: if we have definedBy doc_uri, we processed it.
    # But files might have multiple chunks.
    # Better to use a separate log file for progress
    PROGRESS_FILE = os.path.join(BASE_DIR, "knowledge_base/processed_belgium_files.txt")
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            processed = set(f.read().splitlines())

    # Request Rate Log
    RATE_LOG = os.path.join(BASE_DIR, "knowledge_base/request_rates.csv")
    if not os.path.exists(RATE_LOG):
        with open(RATE_LOG, "w") as f:
            f.write("Filename,ChunkID,TimeSeconds,OppsFound,Timestamp\n")

    # Combine file lists
    all_files_to_scan = [(f, 'pdf') for f in PDF_FILES] + [(f, 'md') for f in MD_FILES]
    
    scored_files = []
    print("\n--- Phase 1: Scoring and Ranking Files ---")
    
    for filepath, ftype in all_files_to_scan:
        if not os.path.exists(filepath):
            print(f"Skipping missing file: {filepath}")
            continue
            
        filename = os.path.basename(filepath)
        if filename in processed:
            continue
            
        # Extract Text
        if ftype == 'pdf':
            text = extract_text_from_pdf(filepath)
        else:
            text = extract_text_from_md(filepath)
            
        if not text:
            print("  Empty text.")
            continue
            
        score = get_relevance_score(text, filename)
        print(f"  Scored {score}/10: {filename}")
        scored_files.append({'path': filepath, 'filename': filename, 'ftype': ftype, 'score': score, 'text': text})

    # Sort
    scored_files.sort(key=lambda x: x['score'], reverse=True)
    
    if not scored_files:
        print("No files to process.")
        return

    # Top 20%
    top_n = max(1, int(len(scored_files) * 0.2))
    target_files = scored_files[:top_n]
    
    print(f"\n--- Phase 2: Processing Top {len(target_files)} Files (from {len(scored_files)}) ---")
    for tf in target_files:
        print(f"  [Selected] Score {tf['score']}: {tf['filename']}")
    
    for item in target_files:
        filename = item['filename']
        filepath = item['path']
        ftype = item['ftype']
        text = item['text'] # Reuse text
        # ... logic continues ...

        print(f"\nProcessing {filename}...")
        
        # 1. Text already extracted
        # if ftype == 'pdf': ... (removed loop)
             
        print(f"  Length: {len(text)} characters.")
        
        # 2. Chunking
        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        print(f"  Split into {len(chunks)} chunks.")
        
        # 3. Process Chunks
        file_success = True
        for i, chunk in enumerate(chunks):
            # Check for existing data to resume at chunk level
            # Check if likely already processed: look for the first opportunity of this chunk
            slug = filename.replace(" ", "_").replace(".", "_").lower()
            
            # Note: with Official Code URI change, resume logic based on slug URI is less reliable
            # but we kept fallback URIs, so it might still work. 
            # For this run we just process.
            
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
                    # STRATEGY CHANGE: Use Official Code for URI if available to prevent duplicates
                    slug = filename.replace(" ", "_").replace(".", "_").lower()
                    
                    official_code = item.get("official_code", "N/A")
                    if official_code and official_code != "N/A":
                        # Sanitize code for URI
                        safe_code = "".join(c if c.isalnum() else "_" for c in official_code).lower()
                        # Base URI on the CODE, not the file
                        opp_uri = URIRef(f"http://example.org/opportunity/be/wal/code/{safe_code}")
                    else:
                        # Fallback to file-based URI if no code
                        opp_uri = URIRef(f"http://example.org/opportunity/be/wal/{slug}_c{i}_{idx}")

                    doc_uri = URIRef(f"http://example.org/doc/be/wal/{slug}")

                    # Check if already exists to avoid overwriting stable data with partial data
                    # (Optional: could merge, but for now let's just assert existence)
                    if (opp_uri, RDF.type, CORE.Opportunity) not in g:
                         g.add((opp_uri, RDF.type, CORE.Opportunity))
                         
                    # Always link to the defining document (one opportunity can be defined in multiple docs)
                    g.add((opp_uri, CORE.definedBy, doc_uri))
                    
                    # Store official code if provided
                    if item.get("official_code") and item["official_code"] != "N/A":
                        g.add((opp_uri, CORE.hasInterventionCode, Literal(item["official_code"])))
                    
                    # For properties, we overwrite/add. RDF handles multiple labels fine, 
                    # but for description we might want to be careful. 
                    # For this pass, we'll add them.
                    
                    if item.get("name_local"):
                        g.add((opp_uri, RDFS.label, Literal(item["name_local"], lang="fr")))
                    if item.get("name_en"):
                        g.add((opp_uri, RDFS.label, Literal(item["name_en"], lang="en")))
                    if item.get("description"):
                         g.add((opp_uri, CORE.description, Literal(item["description"], lang="en")))
                         
                    # ADD TAGS
                    for tag in item.get("tags", []):
                        g.add((opp_uri, CORE.hasTag, Literal(tag, lang="en")))
                        
                    # Criteria & Payments (simplified)
                    # Note: This might accumulate criteria if run multiple times without clearing.
                    # Since we deleted the file, this is fine for a fresh run.
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
