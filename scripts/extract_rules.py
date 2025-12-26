import os
import re
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
from pypdf import PdfReader

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_SOURCE_DIR = os.path.join(os.path.dirname(BASE_DIR), "policy_downloader/data/pdfs/france/TelePAC_Forms_2025")
OUTPUT_TTL = os.path.join(BASE_DIR, "knowledge_base/extracted_rules.ttl")

# Namespaces
CORE = Namespace("http://example.org/agri-energy/core#")
ELI = Namespace("http://data.europa.eu/eli/ontology#")

def extract_text(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

def classify_document(text, filename):
    """
    Classifies the document based on keywords.
    """
    text_lower = text.lower()
    fname_lower = filename.lower()
    
    if "bio" in fname_lower or "agriculture biologique" in text_lower:
        return CORE.Organic
    if "hve" in text_lower or "haute valeur environnementale" in text_lower:
        return CORE.HVE3
    if "panneaux photovoltaïques" in text_lower or "agrivoltaïsme" in text_lower:
        return CORE.AgriPV
    return None

def extract_criteria(text):
    """
    Extracts numerical criteria:
    - Duration (e.g., "5 ans")
    - Density/Quota (e.g., "100 arbres par hectare")
    """
    criteria = {}
    
    # Duration (e.g., "5 ans", "5 années")
    dur_match = re.search(r'(\d+)\s*(?:ans|années)', text)
    if dur_match:
        try:
            criteria['duration'] = float(dur_match.group(1))
        except:
            pass

    # Density (e.g., "100 ... par hectare")
    # Matches "100 arbres par hectare"
    dens_match = re.search(r'(\d+)\s*\w+\s*par\s*hectare', text)
    if dens_match:
        try:
            criteria['density'] = float(dens_match.group(1))
        except:
            pass
            
    return criteria

def main():
    print("--- Extracting Rules from PDFs ---")
    g = Graph()
    g.bind("core", CORE)
    
    count = 0
    for filename in os.listdir(PDF_SOURCE_DIR):
        if not filename.lower().endswith(".pdf"):
            continue
            
        filepath = os.path.join(PDF_SOURCE_DIR, filename)
        uri_slug = filename.lower().replace(".pdf", "")
        doc_uri = URIRef(f"http://example.org/doc/fr/2025/{uri_slug}")
        
        text = extract_text(filepath)
        if not text:
            continue
            
        # 1. Classify
        doc_type = classify_document(text, filename)
        
        # 2. Extract Criteria
        criteria = extract_criteria(text)
        
        if doc_type or criteria:
            print(f"Processed {filename}: Type={doc_type}, Criteria={criteria}")
            
            # Create Opportunity Node
            opp_uri = URIRef(f"http://example.org/opportunity/{uri_slug}")
            g.add((opp_uri, RDF.type, CORE.Opportunity))
            g.add((opp_uri, CORE.definedBy, doc_uri))
            
            if doc_type:
                # Link to certification (using hasCertification or similar property from ontology)
                # For demo, we treat the Opportunity AS that type sort of
                g.add((opp_uri, CORE.requiresCertification, doc_type)) 
                
            if 'duration' in criteria:
                 # Modeling duration as a generic float constraint for now
                 g.add((opp_uri, CORE.minDurationYears, Literal(criteria['duration'], datatype=XSD.float)))
                 
            if 'density' in criteria:
                 g.add((opp_uri, CORE.maxDensityPerHa, Literal(criteria['density'], datatype=XSD.float)))

            count += 1

    print(f"Extracted rules for {count} documents.")
    g.serialize(destination=OUTPUT_TTL, format="turtle")
    print(f"Saved to {OUTPUT_TTL}")

if __name__ == "__main__":
    main()
