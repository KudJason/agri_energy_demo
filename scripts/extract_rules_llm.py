import os
import json
import time
from dotenv import load_dotenv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD, RDFS
from openai import OpenAI
from pypdf import PdfReader

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_SOURCE_DIRS = [
    os.path.join(BASE_DIR, "data/pdfs/france/TelePAC_Forms_2025"),
    os.path.join(BASE_DIR, "data/pdfs/france/PSN_2023_2027"),
    os.path.join(BASE_DIR, "data/pdfs/france/Rules_Transversales")
]
OUTPUT_TTL = os.path.join(BASE_DIR, "knowledge_base/data/rules/opportunities.ttl")

# Load Environment Variables
load_dotenv(os.path.join(BASE_DIR, ".env")) 
load_dotenv("/Users/jasonjia/Documents/industry_policy/secret/.env")

# Namespaces
CORE = Namespace("http://example.org/agri-energy/core#")

# API Setup
API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    print("Warning: DEEPSEEK_API_KEY not found in environment variables.")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
        return ""

def extract_granular_rules_perplexity(text, filename):
    prompt = f"""
    You are an Expert Legal Policy Analyst for the Agricultural Sector.
    
    OBJECTIVE:
    Analyze the provided document text and identify if it describes a **Financial Aid**, **Subsidy**, **Grant**, or **Eco-Scheme** (e.g., "Aide", "Prime", "Indemnité", "Écorégime", "MAEC").
    
    CRITICAL FILTERING RULES - READ CAREFULLY:
    1. **IGNORE administrative procedures** like "Autorisation de signature", "Délégation", "Formulaire", "Notice d'information" UNLESS they define a specific financial aid scheme.
    2. **IGNORE general definitions** of land types (e.g., "Terres arables") UNLESS they are presented as a specific aid category (e.g., "Aide à la production de légumineuses").
    3. **IGNORE procedural documents** - If the document is purely procedural (signing forms, declaring agents), return an empty list for "opportunities".
    4. **AVOID DUPLICATES** - If you see what appears to be the same measure described in different sections with slight variations in wording, extract it ONLY ONCE with the most complete information.
    5. **REQUIRE CONCRETE BENEFITS** - Only extract if the opportunity includes at least ONE of:
       - Specific payment amount (e.g., "100 EUR/ha")
       - Clear eligibility criteria (e.g., "farmers under 40 years old")
       - Application procedure with deadlines
    6. **REQUIRE UNIQUE IDENTIFIER** - Each opportunity should have an official code, reference number, or unique official name
    
    UNIQUENESS VALIDATION:
    - Look for official codes like "MAEC-BIO", "Écorégime 1", "Intervention 141", etc.
    - If the text just repeats the title of a measure without adding substantial detail, DO NOT extract it again
    - Section headings and table of contents entries are NOT separate opportunities
    
    OUTPUT FORMAT:
    Return a JSON object with a single key "opportunities", which is a LIST of objects.
    Each object must have:
    - "official_code": Unique identifier or reference code (REQUIRED - use "N/A" if truly unavailable)
    - "name_local": Official name in French.
    - "name_en": English translation.
    - "type": "Subsidy", "Grant", "Eco-Scheme" (Exclude "Procedure" and administrative documents).
    - "description": Brief summary of WHAT the aid provides and WHO benefits.
    - "valid_from": Year (e.g., "2025").
    - "eligibility_criteria": List of objects {{"variable": "...", "operator": "...", "value": "..."}}.
    - "payment_rules": List of objects {{"name": "...", "amount": "...", "unit": "..."}}.

    EXTRACT ONLY REAL FINANCIAL OPPORTUNITIES WITH UNIQUE IDENTIFIERS.
    
    ONLY JSON. DO NOT USE MARKDOWN BLOCK.
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
        {"role": "user", "content": f"{prompt}\n\nDOCUMENT CONTENT:\n{text[:50000]}"} # Truncate if too long, though Sonar has decent context
    ]
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                temperature=0,
            )
            content = response.choices[0].message.content
            # Cleanup potential markdown code blocks if the model ignores instruction
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
             if "429" in str(e) or "Rate limit" in str(e): # Handle rate limits
                print(f"Rate limit hit. Retrying in {(attempt + 1) * 5} seconds...")
                time.sleep((attempt + 1) * 5)
             else:
                print(f"Perplexity Error on {filename}: {e}")
                return {"opportunities": []}

    return {"opportunities": []}

def get_relevance_score(text_preview, filename):
    prompt = f"""
    Task: Rate the relevance of this document for extracting structured rules about Agricultural Financial Aids/Subsidies.
    
    Criteria:
    - High Score (8-10): The document explicitly DEFINES a subsidy/intervention (eligibility, amounts, conditions). Example: "Cahier des charges", "Fiche intervention".
    - Low Score (0-3): The document is a Form (Formulaire), Mandate (Mandat), Receipt (Récépissé), or pure administrative procedure without rule definitions.
    
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

def main():
    print("--- Granular LLM Rule Extraction (DeepSeek) ---")
    if not API_KEY:
        print("Error: API Key not found. Please set DEEPSEEK_API_KEY.")
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

    # Track processed files
    processed_log_path = os.path.join(BASE_DIR, "knowledge_base/processed_files.txt")
    processed_files = set()
    if os.path.exists(processed_log_path):
        with open(processed_log_path, "r") as f:
            processed_files = set(f.read().splitlines())

    processed_count = 0
    # 1. Collect and Rank Files
    all_files_to_score = []
    
    print("\n--- Phase 1: Scoring and Ranking Files ---")
    for pdf_dir in PDF_SOURCE_DIRS:
        if not os.path.exists(pdf_dir): 
            print(f"Directory not found: {pdf_dir}")
            continue
            
        files = sorted([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")])
        for filename in files:
            if filename in processed_files:
                continue
                
            filepath = os.path.join(pdf_dir, filename)
            # Extract preview for scoring
            text = extract_text_from_pdf(filepath)
            if not text: continue
            
            score = get_relevance_score(text, filename)
            print(f"  Scored {score}/10: {filename}")
            all_files_to_score.append({'path': filepath, 'filename': filename, 'score': score, 'text': text})

    # Sort by score descending
    all_files_to_score.sort(key=lambda x: x['score'], reverse=True)
    
    # Filter Top 20% or Score >= 7
    if not all_files_to_score:
        print("No files found to process.")
        return

    # Strategy: Top 20% to ensure we process the most relevant ones
    top_n_count = max(1, int(len(all_files_to_score) * 0.2))
    target_files = all_files_to_score[:top_n_count]
    
    print(f"\n--- Phase 2: Processing Top {len(target_files)} Files (from {len(all_files_to_score)}) ---")
    for tf in target_files:
        print(f"  [Selected] Score {tf['score']}: {tf['filename']}")
        
    for item in target_files:
        filename = item['filename']
        filepath = item['path']
        text = item['text'] # Reuse extracted text to save time
        
        print(f"\nProcessing {filename} (Score: {item['score']})...")
        
        try:
            print(f"Extracted {len(text)} characters. Sending to DeepSeek...")

            # 2. Extract Structure via LLM
            data = extract_granular_rules_perplexity(text, filename)
            
            uri_slug_base = filename.lower().replace(".pdf", "")
            
            if "opportunities" in data:
                print(f"Found {len(data['opportunities'])} opportunities.")
                for idx, item in enumerate(data["opportunities"]):
                    
                    # STRATEGY CHANGE: Use Official Code for URI
                    official_code = item.get("official_code", "N/A")
                    
                    if official_code and official_code != "N/A":
                        safe_code = "".join(c if c.isalnum() else "_" for c in official_code).lower()
                        opp_uri = URIRef(f"http://example.org/opportunity/fr/2025/code/{safe_code}")
                    else:
                        # Fallback
                        opp_uri = URIRef(f"http://example.org/opportunity/{uri_slug_base}_{idx}")

                    doc_uri = URIRef(f"http://example.org/doc/fr/2025/{uri_slug_base}")

                    if (opp_uri, RDF.type, CORE.Opportunity) not in g:
                        g.add((opp_uri, RDF.type, CORE.Opportunity))
                        
                    g.add((opp_uri, CORE.definedBy, doc_uri))
                    
                    # Store official code if provided
                    if item.get("official_code") and item["official_code"] != "N/A":
                        g.add((opp_uri, CORE.hasInterventionCode, Literal(item["official_code"])))
                    
                    # Labels
                    if item.get("name_local"):
                        g.add((opp_uri, RDFS.label, Literal(item["name_local"], lang="fr")))
                    if item.get("name_en"):
                        g.add((opp_uri, RDFS.label, Literal(item["name_en"], lang="en")))
                    
                    # Versioning
                    if item.get("valid_from"):
                        g.add((opp_uri, CORE.validFrom, Literal(item["valid_from"], datatype=XSD.gYear)))
                        
                    # Granular Eligibility Criteria
                    for c_idx, crit in enumerate(item.get("eligibility_criteria", [])):
                        crit_uri = URIRef(f"{opp_uri}/criterion/{c_idx}")
                        g.add((crit_uri, RDF.type, CORE.EligibilityCriteria))
                        g.add((opp_uri, CORE.hasEligibilityCriteria, crit_uri))
                        
                        if crit.get("variable"):
                            g.add((crit_uri, CORE.hasVariable, Literal(crit["variable"])))
                        if crit.get("operator"):
                            g.add((crit_uri, CORE.hasOperator, Literal(crit["operator"])))
                        if crit.get("value"):
                            g.add((crit_uri, RDF.value, Literal(crit["value"])))

                    # Granular Payment Rules
                    for p_idx, rule in enumerate(item.get("payment_rules", [])):
                        rule_uri = URIRef(f"{opp_uri}/payment/{p_idx}")
                        g.add((rule_uri, RDF.type, CORE.PaymentRule))
                        g.add((opp_uri, CORE.hasPaymentRule, rule_uri))
                        
                        if rule.get("name"):
                            g.add((rule_uri, RDFS.label, Literal(rule["name"], lang="en")))
                        if rule.get("amount"):
                            try:
                                # Handle string to float conversion safely
                                amt = float(rule["amount"])
                                g.add((rule_uri, CORE.hasValue, Literal(amt, datatype=XSD.float)))
                            except (ValueError, TypeError):
                                # Fallback to string if not a clean number
                                g.add((rule_uri, CORE.hasValue, Literal(str(rule["amount"]))))
                        if rule.get("unit"):
                            g.add((rule_uri, CORE.hasUnit, Literal(rule["unit"])))

            # Incremental Save
            g.serialize(destination=OUTPUT_TTL, format="turtle")
            with open(processed_log_path, "a") as f:
                f.write(filename + "\n")

            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\nCompleted. Saved to {OUTPUT_TTL}")
if __name__ == "__main__":
    main()
