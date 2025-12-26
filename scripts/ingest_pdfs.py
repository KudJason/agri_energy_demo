import os
import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
from pypdf import PdfReader

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_SOURCE_DIRS = [
    os.path.join(os.path.dirname(BASE_DIR), "policy_downloader/data/pdfs/france/TelePAC_Forms_2025"),
    os.path.join(BASE_DIR, "data/pdfs/flanders/Ecoregelingen_2025"),
    os.path.join(BASE_DIR, "data/pdfs/flanders/VLIF_Innovatie")
]
OUTPUT_TTL = os.path.join(BASE_DIR, "knowledge_base/ingested_policies.ttl")

# Namespaces
ELI = Namespace("http://data.europa.eu/eli/ontology#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
CORE = Namespace("http://example.org/agri-energy/core#")

def extract_metadata(filepath):
    """
    Extracts basic metadata from PDF and filename.
    """
    filename = os.path.basename(filepath)
    title = filename.replace(".pdf", "").replace("-", " ").replace("_", " ")
    
    # Try reading PDF metadata
    try:
        reader = PdfReader(filepath)
        meta = reader.metadata
        if meta.title:
            title = meta.title
    except:
        pass
        
    return {
        "filename": filename,
        "title": title,
        "date_accessed": datetime.date.today().isoformat()
    }

def ingest_pdfs():
    
    g = Graph()
    g.bind("eli", ELI)
    g.bind("dcterms", DCTERMS)
    g.bind("core", CORE)

    count = 0 
    for pdf_dir in PDF_SOURCE_DIRS:
        if not os.path.exists(pdf_dir):
            print(f"Warning: Directory {pdf_dir} not found. Skipping.")
            continue
            
        print(f"Scanning {pdf_dir}...")
        for filename in os.listdir(pdf_dir):
            if not filename.lower().endswith(".pdf"):
                continue
                
            filepath = os.path.join(pdf_dir, filename)
        meta = extract_metadata(filepath)
        
        # URI Construction: http://example.org/doc/fr/2025/{filename_slug}
        uri_slug = filename.lower().replace(".pdf", "")
        doc_uri = URIRef(f"http://example.org/doc/fr/2025/{uri_slug}")
        
        # Add Triples
        g.add((doc_uri, RDF.type, ELI.LegalResource))
        g.add((doc_uri, ELI.title_alternative, Literal(meta["filename"])))
        g.add((doc_uri, DCTERMS.title, Literal(meta["title"], lang="fr")))
        g.add((doc_uri, DCTERMS.date, Literal(meta["date_accessed"], datatype=XSD.date)))
        
        # In a real app, we would add extracted text content or link to full text here
        # g.add((doc_uri, ELI.description, Literal(full_text_start...)))
        
        print(f"  Processed: {meta['filename']}")
        count += 1

    print(f"Saving {count} documents to {OUTPUT_TTL}...")
    g.serialize(destination=OUTPUT_TTL, format="turtle")
    print("Done.")

if __name__ == "__main__":
    ingest_pdfs()
