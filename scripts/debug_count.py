import os
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_BELGIUM = os.path.join(BASE_DIR, "knowledge_base/rules_belgium.ttl")
RULES_FRANCE = os.path.join(BASE_DIR, "knowledge_base/rules_france.ttl")

def debug_count():
    g = Graph()
    
    # Load Belgium
    if os.path.exists(RULES_BELGIUM):
        try:
            g.parse(RULES_BELGIUM, format="turtle")
            print(f"Loaded Belgium Rules: {len(g)} triples")
        except Exception as e:
            print(f"Error loading Belgium Rules: {e}")
    else:
        print(f"File not found: {RULES_BELGIUM}")
        
    # Load France
    if os.path.exists(RULES_FRANCE):
        g.parse(RULES_FRANCE, format="turtle")
        
    print(f"Total Triples: {len(g)}")
    
    CORE = Namespace("http://example.org/agri-energy/core#")
    
    # Count Opportunities
    opps = list(g.subjects(RDF.type, CORE.Opportunity))
    print(f"Total Opportunities (Subjects): {len(opps)}")
    
    # Count Tags
    tags = set(g.objects(None, CORE.hasTag))
    print(f"Unique Tags Found: {len(tags)}")
    for t in list(tags)[:5]:
        print(f" - {t}")
    
    # Test SPARQL Query
    query_path = os.path.join(BASE_DIR, "knowledge_base/queries/select_opportunities.sparql")
    if os.path.exists(query_path):
        with open(query_path, "r") as f:
            query_str = f.read()
            
        print("\nRunning select_opportunities.sparql...")
        try:
            res = g.query(query_str)
            print(f"Query Results Count: {len(res)}")
        except Exception as e:
            print(f"Query Error: {e}")

if __name__ == "__main__":
    debug_count()
