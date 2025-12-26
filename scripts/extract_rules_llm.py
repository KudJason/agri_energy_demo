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
API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    print("Warning: PERPLEXITY_API_KEY not found in environment variables.")

client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")

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
    
    CRITICAL FILTERING RULES:
    1. **IGNORE** administrative procedures like "Autorisation de signature", "Délégation", "Formulaire", "Notice d'information" UNLESS they define a specific financial aid scheme.
    2. **IGNORE** general definitions of land types (e.g., "Terres arables") UNLESS they are presented as a specific aid category (e.g., "Aide à la production de légumineuses").
    3. If the document is purely procedural (signing forms, declaring agents), return an empty list for "opportunities".
    
    OUTPUT FORMAT:
    Return a JSON object with a single key "opportunities", which is a LIST of objects.
    Each object must have:
    - "name_local": Official name in French.
    - "name_en": English translation.
    - "type": "Subsidy", "Grant", "Compliance", or "Procedure" (Exclude "Procedure" from output if possible, or we will filter it).
    - "description": Brief summary.
    - "valid_from": Year (e.g., "2025").
    - "eligibility_criteria": List of objects {{"variable": "...", "operator": "...", "value": "..."}}.
    - "payment_rules": List of objects {{"name": "...", "amount": "...", "unit": "..."}}.

    EXTRACT ONLY REAL FINANCIAL OPPORTUNITIES.
    
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
                model="sonar",
                messages=messages,
                temperature=0.1,
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

def main():
    print("--- Granular LLM Rule Extraction (Perplexity Sonar) ---")
    if not API_KEY:
        print("Error: API Key not found. Please set PERPLEXITY_API_KEY.")
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
    for pdf_dir in PDF_SOURCE_DIRS:
        if not os.path.exists(pdf_dir): 
            print(f"Directory not found: {pdf_dir}")
            continue
            
        files = sorted([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")])
        
        for filename in files: 
            if filename in processed_files:
                print(f"Skipping already processed: {filename}")
                continue

            filepath = os.path.join(pdf_dir, filename)
            print(f"\nProcessing {filename}...")
            
            try:
                # 1. Extract Text locally
                text = extract_text_from_pdf(filepath)
                if not text:
                    print(f"No text extracted from {filename}")
                    continue
                
                print(f"Extracted {len(text)} characters. Sending to Perplexity...")

                # 2. Extract Structure via LLM
                data = extract_granular_rules_perplexity(text, filename)
                
                uri_slug_base = filename.lower().replace(".pdf", "")
                
                if "opportunities" in data:
                    print(f"Found {len(data['opportunities'])} opportunities.")
                    for idx, item in enumerate(data["opportunities"]):
                        opp_uri = URIRef(f"http://example.org/opportunity/{uri_slug_base}_{idx}")
                        doc_uri = URIRef(f"http://example.org/doc/fr/2025/{uri_slug_base}")

                        g.add((opp_uri, RDF.type, CORE.Opportunity))
                        g.add((opp_uri, CORE.definedBy, doc_uri))
                        
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
