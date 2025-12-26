import os
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_FILE = os.path.join(BASE_DIR, "knowledge_base/rules_belgium.ttl")
LOCATIONS_FILE = os.path.join(BASE_DIR, "knowledge_base/data/locations.ttl")
ONTOLOGY_FILE = os.path.join(BASE_DIR, "knowledge_base/ontology/business_core.ttl")

def query_kg():
    print("--- Querying Agri-Energy Knowledge Graph ---")
    
    g = Graph()
    
    # Load Files
    try:
        g.parse(ONTOLOGY_FILE, format="turtle")
        g.parse(LOCATIONS_FILE, format="turtle")
        if os.path.exists(RULES_FILE):
            g.parse(RULES_FILE, format="turtle")
            print(f"Loaded {len(g)} triples.")
        else:
            print("Rules file not found yet. (Extraction might still be running)")
            return
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    # Define Namespaces
    CORE = Namespace("http://example.org/agri-energy/core#")
    
    # Simple Query: Find all Opportunities and their labels
    # In a real scenario, we would filter by ?farm location = :Wallonia checks
    query_str = """
    PREFIX core: <http://example.org/agri-energy/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?opp ?label ?doc
    WHERE {
        ?opp a core:Opportunity ;
             rdfs:label ?label .
        OPTIONAL { ?opp core:definedBy ?doc }
        
        # Filter for English labels to make it readable, or French if missing
        FILTER (lang(?label) = 'en' || lang(?label) = 'fr')
    }
    LIMIT 10
    """
    
    print("\nExecuting SPARQL Query: Finding Opportunities...")
    q = prepareQuery(query_str)
    results = g.query(q)
    
    print(f"Found {len(results)} results:\n")
    for row in results:
        print(f"Opportunity: {row.label}")
        print(f"  URI: {row.opp}")
        print(f"  Source: {row.doc}")
        print("-" * 30)

if __name__ == "__main__":
    query_kg()
