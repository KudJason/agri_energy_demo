import os
import sys
from rdflib import Graph
from pyshacl import validate

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_TTL = os.path.join(BASE_DIR, "knowledge_base/extracted_rules_llm.ttl")
SHAPES_TTL = os.path.join(BASE_DIR, "knowledge_base/shapes.ttl")
ONTOLOGY_TTL = os.path.join(BASE_DIR, "knowledge_base/core.ttl")

def main():
    print("--- SHACL Validation ---")
    
    if not os.path.exists(DATA_TTL):
        print(f"Error: Data file not found at {DATA_TTL}")
        return

    if not os.path.exists(SHAPES_TTL):
        print(f"Error: Shapes file not found at {SHAPES_TTL}")
        return

    print(f"Validating {DATA_TTL}...")
    print(f"Using shapes from {SHAPES_TTL}...")

    # Load Data Graph (and mix in Ontology for RDFS reasoning if needed)
    data_graph = Graph()
    data_graph.parse(DATA_TTL, format="turtle")
    
    # Optional: Load ontology for extra context (subclass of, etc)
    if os.path.exists(ONTOLOGY_TTL):
         data_graph.parse(ONTOLOGY_TTL, format="turtle")

    # Load Shapes Graph
    shapes_graph = Graph()
    shapes_graph.parse(SHAPES_TTL, format="turtle")

    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference='rdfs',
        abort_on_first=False,
        allow_warnings=False,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False
    )

    if conforms:
        print("\n✅ Validation Successful: Data conforms to SHACL shapes.")
    else:
        print("\n❌ Validation Failed: Data does NOT conform to SHACL shapes.")
        print("\n--- Validation Report ---")
        print(results_text)
        
if __name__ == "__main__":
    main()
