# Agri-Energy Knowledge Base Architecture

This directory contains the semantic data layer powering the Agri-Energy Intelligence Platform. Below is the organization of data assets mapped to the application pages.

## 📂 Directory Structure

```text
knowledge_base/
├── ontology/               # Core Schema definitions
│   └── business_core.ttl   # Main ontology (Opportunities, Criteria)
├── data/                   # Reference Data
│   └── locations.ttl       # Geographic hierarchies (Belgium, Wallonia, Flanders)
├── rules_*.ttl             # EXTRACTED Policy Rules (by extraction scripts)
├── kg_*.mmd                # Visualizations (Mermaid)
└── request_rates.csv       # operational logs
```

## 🚀 Application Page Mapping

### Page 1: Mock Demo (Hardcoded)
*   **Purpose**: Legacy POC demonstrating basic logic.
*   **Dependencies**: None (Uses hardcoded Python dictionaries).
*   **Relevance**: Historical reference only.

### Page 2: LLM & Semantic Matcher (`02_LLM_Demo.py`)
*   **Purpose**: Matches a user's **Farm Profile** against extracted rules.
*   **Key Dependencies**:
    1.  **Ontology**: `ontology/business_core.ttl` - Defines the vocabulary (`core:Opportunity`, `core:requiresCriterion`).
    2.  **Rules**: 
        *   `rules_belgium.ttl` (Live extracted from Wallonia docs)
        *   `rules_france.ttl` (Static sample)
    3.  **Reference Data**: 
        *   `data/locations.ttl` - specific region logic (e.g., matching a farm in "Wallonia" to Walloon rules).

### Page 3: KG Explorer (`03_KG_Explorer.py`)
*   **Purpose**: Admin interface to debug and visualize the Knowledge Graph.
*   **Key Dependencies**:
    1.  **Visualization**: `kg_belgium.mmd` - Generated Mermaid diagram of the graph structure.
    2.  **Metrics**: `request_rates.csv` - Telemetry from the LLM extraction process (time/cost tracking).
    3.  **SPARQL Queries**: Runs directly against all loaded `.ttl` files.

## 🔄 Automated Workflows

1.  **Extraction**: `scripts/extract_belgium_rules.py` reads PDFs/Markdown -> Updates `rules_belgium.ttl` & `request_rates.csv`.
2.  **Visualization**: `scripts/visualize_kg.py` reads `rules_belgium.ttl` -> Generates `kg_belgium.mmd`.
3.  **Querying**: `pages/03_KG_Explorer.py` reads All TTLs -> Displays Tables/Graphs.
