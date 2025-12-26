import os
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_BELGIUM = os.path.join(BASE_DIR, "knowledge_base/rules_belgium.ttl")
RULES_FRANCE = os.path.join(BASE_DIR, "knowledge_base/rules_france.ttl")
OUTPUT_TTL = os.path.join(BASE_DIR, "knowledge_base/rules_enriched.ttl")

# Namespaces
CORE = Namespace("http://example.org/agri-energy/core#")

def enrich_graph():
    print("--- Enriching Knowledge Graph with Tags ---")
    g = Graph()
    
    # Load existing rules
    for f in [RULES_BELGIUM, RULES_FRANCE]:
        if os.path.exists(f):
            print(f"Loading {f}...")
            g.parse(f, format="turtle")
            
    # Define Tagging Rules (Keyword -> Tag)
    # This acts as a simple "Classifier"
    tag_map = {
        "Organic": ["organic", "biologique", " bio "],
        "Young Farmer": ["young farmer", "jeune agriculteur", "installation"],
        "Livestock": ["livestock", "cattle", "cow", "sheep", "bovin", "ovin", "brebis", "élevage", "bétail"],
        "Dairy": ["dairy", "lait", "laitière"],
        "Crops": ["crop", "culture", "céréale", "protein", "protéagineux", "wheat", "blé", "corn", "maïs"],
        "Environment": ["environment", "climate", "carbon", "biodiversity", "environnement", "climat", "carbone", "biodiversité", "eco-scheme", "éco-régime"],
        "Investment": ["investment", "investissements", "equipment", "matériel", "construction"],
        "Forestry": ["forest", "forêt", "wood", "bois"],
        "Horticulture": ["fruit", "vegetable", "légume", "verger", "orchard"],
        "Beekeeping": ["bee", "apiculture", "honey", "miel", "ruche"]
    }
    
    count = 0
    
    # Iterate all Opportunities
    for opp in g.subjects(RDF.type, CORE.Opportunity):
        # Gather text context
        text_context = ""
        
        # Labels
        for label in g.objects(opp, RDFS.label):
            text_context += str(label).lower() + " "
            
        # Descriptions
        for desc in g.objects(opp, CORE.description):
            text_context += str(desc).lower() + " "
            
        # Criteria (Raw)
        for crit in g.objects(opp, CORE.requiresCriterion):
            text_context += str(crit).lower() + " "
            
        # Apply Tags
        for tag, keywords in tag_map.items():
            if any(k in text_context for k in keywords):
                g.add((opp, CORE.hasTag, Literal(tag)))
                count += 1
                
    print(f"Added {count} tags to opportunities.")
    
    # Save Enriched Graph
    # We save to a new file or overwrite. For now, let's overwrite the Belgium file (or a combined one).
    # Actually, better to keep them separate. Let's just update the in-memory graph usage or save a cache.
    # User wants "generated from all opportunity tags", so persistence is best.
    # Let's write to a new 'enriched' file and update the loader to use it.
    
    g.serialize(destination=OUTPUT_TTL, format="turtle")
    print(f"Saved enriched graph to {OUTPUT_TTL}")

if __name__ == "__main__":
    enrich_graph()
