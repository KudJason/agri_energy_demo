import os
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTL_FILE = os.path.join(BASE_DIR, "knowledge_base/rules_belgium.ttl")
OUTPUT_MMD = os.path.join(BASE_DIR, "knowledge_base/kg_belgium.mmd")

def generate_mermaid_diagram():
    if not os.path.exists(TTL_FILE):
        print(f"TTL file not found: {TTL_FILE}")
        return

    g = Graph()
    g.parse(TTL_FILE, format="turtle")
    
    CORE = Namespace("http://example.org/agri-energy/core#")
    
    mermaid_lines = ["graph TD"]
    
    # Query for Opportunities
    # Limit to 10 for readability in diagram, or group them
    opps = list(g.subjects(RDF.type, CORE.Opportunity))
    
    print(f"Found {len(opps)} opportunities. Generating diagram for top 20...")
    
    for i, opp in enumerate(opps[:20]):
        opp_label = g.value(opp, RDFS.label) or "Opportunity"
        opp_id = f"Opp{i}"
        
        # Clean label for Mermaid
        safe_label = str(opp_label).replace('"', '').replace('(', '').replace(')', '')[:30] + "..."
        
        mermaid_lines.append(f'    {opp_id}["{safe_label}"]')
        mermaid_lines.append(f'    class {opp_id} Opportunity')
        
        # Connect to DefinedBy (Document)
        doc = g.value(opp, CORE.definedBy)
        if doc:
            doc_label = str(doc).split("/")[-1]
            doc_id = f"Doc_{doc_label.replace('.', '_')}"
            mermaid_lines.append(f'    {doc_id}["{doc_label}"]')
            mermaid_lines.append(f'    {opp_id} -->|definedBy| {doc_id}')

    # Output
    with open(OUTPUT_MMD, "w") as f:
        f.write("\n".join(mermaid_lines))
    
    print(f"Mermaid diagram saved to {OUTPUT_MMD}")

if __name__ == "__main__":
    generate_mermaid_diagram()
