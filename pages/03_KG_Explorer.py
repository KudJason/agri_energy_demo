import streamlit as st
import pandas as pd
import os
import sys
from rdflib import Graph, Namespace, Literal
from rdflib.plugins.sparql import prepareQuery

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_BELGIUM = os.path.join(BASE_DIR, "knowledge_base/rules_belgium.ttl")
RULES_FRANCE = os.path.join(BASE_DIR, "knowledge_base/rules_france.ttl")
LOCATIONS_FILE = os.path.join(BASE_DIR, "knowledge_base/data/locations.ttl")
ONTOLOGY_FILE = os.path.join(BASE_DIR, "knowledge_base/ontology/business_core.ttl")
MMD_FILE = os.path.join(BASE_DIR, "knowledge_base/kg_belgium.mmd")
RATES_FILE = os.path.join(BASE_DIR, "knowledge_base/request_rates.csv")

st.set_page_config(page_title="KG Explorer", page_icon="🕸️", layout="wide")

st.title("🕸️ Knowledge Graph Explorer")
st.markdown("Directly query and visualize the **Agri-Energy Knowledge Graph**.")

# --- Lazy Load Graph ---
@st.cache_resource
def load_graph():
    g = Graph()
    try:
        g.parse(ONTOLOGY_FILE, format="turtle")
        g.parse(LOCATIONS_FILE, format="turtle")
        if os.path.exists(RULES_BELGIUM):
            g.parse(RULES_BELGIUM, format="turtle")
        if os.path.exists(RULES_FRANCE):
            g.parse(RULES_FRANCE, format="turtle")
    except Exception as e:
        st.error(f"Error loading graph: {e}")
    return g

g = load_graph()
st.caption(f"Loaded {len(g)} triples into memory.")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🔍 Query Opportunities", "📈 Extraction Stats", "🔮 Graph Visualization"])

# --- Tab 1: Query ---
with tab1:
    st.subheader("Bilingual Opportunity Search")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search by keyword (English or French)", "")
    with col2:
        limit = st.number_input("Limit", value=20, min_value=1, max_value=100)
    
    # Dynamic Query - Inject LIMIT directly as SPARQL requires integer literal
    query = f"""
    PREFIX core: <http://example.org/agri-energy/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?opp ?label ?desc ?doc
    WHERE {{
        ?opp a core:Opportunity ;
             rdfs:label ?label .
        OPTIONAL {{ ?opp core:description ?desc }}
        OPTIONAL {{ ?opp core:definedBy ?doc }}
        
        FILTER (regex(?label, ?keyword, "i") || regex(?desc, ?keyword, "i"))
    }}
    LIMIT {limit}
    """
    
    if st.button("Run SPARQL Query"):
        q = prepareQuery(query)
        # Bind literal for keyword
        results = g.query(q, initBindings={'keyword': Literal(search_term)})
        
        data = []
        for row in results:
            data.append({
                "Label": str(row.label),
                "Description": str(row.desc) if row.desc else "",
                "Source Document": str(row.doc).split('/')[-1] if row.doc else "Unknown",
                "URI": str(row.opp)
            })
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No results found.")

# --- Tab 2: Stats ---
with tab2:
    st.subheader("LLM Extraction Performance")
    if os.path.exists(RATES_FILE):
        df_rates = pd.read_csv(RATES_FILE)
        st.dataframe(df_rates, use_container_width=True)
        
        st.metric("Total API Requests", len(df_rates))
        st.metric("Total Opportunities Extracted", df_rates['OppsFound'].sum())
        
        # Simple Chart
        st.bar_chart(df_rates, x="Filename", y="TimeSeconds")
    else:
        st.warning("No request rate logs found yet.")

# --- Tab 3: Visualization ---
with tab3:
    st.subheader("Belgium Rules Structure")
    if os.path.exists(MMD_FILE):
        with open(MMD_FILE, "r") as f:
            mmd_content = f.read()
            
            st.markdown("### Diagram Render")
            st.markdown(f"""
            ```mermaid
            {mmd_content}
            ```
            """)
            
            with st.expander("View Source Code"):
                st.code(mmd_content, language="mermaid")
    else:
        st.warning("KG Visualization file (kg_belgium.mmd) not found.")
