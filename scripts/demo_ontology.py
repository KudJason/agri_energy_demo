import os
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
from pyshacl import validate

# Define Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
CORE_TTL = os.path.join(KB_DIR, "core.ttl")
RULES_TTL = os.path.join(KB_DIR, "rules_france.ttl")
SHAPES_TTL = os.path.join(KB_DIR, "shapes.ttl")

# Define Namespaces
CORE = Namespace("http://example.org/agri-energy/core#")
AGROVOC = Namespace("http://aims.fao.org/aos/agrovoc/")

def create_sample_data():
    g = Graph()
    g.bind("core", CORE)
    g.bind("agrovoc", AGROVOC)
    
    # 1. Valid Farm Profile (Modeled to match AgriPV requirements)
    farm_valid = URIRef("http://example.org/farm/valid")
    g.add((farm_valid, RDF.type, CORE.FarmProfile))
    g.add((farm_valid, CORE.hasSizeHa, Literal(50.5, datatype=XSD.float)))
    g.add((farm_valid, CORE.locatedIn, CORE.France))
    g.add((farm_valid, CORE.produces, AGROVOC.c_5625)) # Pasture
    
    # 2. Invalid Farm (Missing Region, Wrong Crop)
    farm_invalid = URIRef("http://example.org/farm/invalid_region")
    g.add((farm_invalid, RDF.type, CORE.FarmProfile))
    g.add((farm_invalid, CORE.hasSizeHa, Literal(15.0, datatype=XSD.float))) 
    
    return g

def run_demo():
    print("--- Agri-Energy Ontology Demo ---")
    
    # Load Ontology & Shapes & Rules
    print("Loading Ontology, Rules & Shapes...")
    ontology_graph = Graph()
    ontology_graph.parse(CORE_TTL, format="turtle")
    ontology_graph.parse(RULES_TTL, format="turtle")
    
    # Load Extracted Rules from PDFs
    EXTRACTED_TTL = os.path.join(KB_DIR, "extracted_rules.ttl")
    if os.path.exists(EXTRACTED_TTL):
        print("Loading Extracted Rules from PDFs...")
        ontology_graph.parse(EXTRACTED_TTL, format="turtle")
    
    shapes_graph = Graph()
    shapes_graph.parse(SHAPES_TTL, format="turtle")
    
    # Create Data
    data_graph = create_sample_data()
    
    # Merge for context (optional, but good for reasoning)
    full_graph = data_graph + ontology_graph
    
    print("Running SHACL Validation...")
    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ontology_graph,
        inference='rdfs',
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False
    )
    
    print("\n--- Validation Result ---")
    print(f"Conforms: {conforms}")
    print("\n--- detailed Report ---")
    print(report_text)

if __name__ == "__main__":
    run_demo()
