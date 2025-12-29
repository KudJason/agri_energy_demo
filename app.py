import streamlit as st

st.set_page_config(page_title="Agri-Energy Bridge", page_icon="🌱", layout="wide")

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
    }
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 1rem;
    }
    .hero-section {
        background: linear-gradient(135deg, #166534 0%, #15803d 100%);
        color: white;
        padding: 4rem 2rem;
        border-radius: 20px;
        margin-bottom: 3rem;
        text-align: center;
    }
    .card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        height: 100%;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 1rem;
    }
    .card-text {
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .btn {
        display: inline-block;
        background-color: #166534;
        color: white !important;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-section">
    <h1 style="color: white; margin-bottom: 1rem;">🌱 Agri-Energy Intelligence Platform</h1>
    <p style="font-size: 1.25rem; opacity: 0.9; max-width: 800px; margin: 0 auto;">
        Bridging the gap between complex agricultural regulations and renewable energy opportunities 
        using Knowledge Graphs and Generative AI.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">🚜 Strategic Farm Matcher</div>
        <p class="card-text">
            Our <b>LLM-powered</b> engine extracts rules directly from official policy PDFs and 
            maps them to your farm's unique profile using a <b>Semantic Knowledge Graph</b>.
        </p>
        <p style="font-size: 0.875rem; color: #94a3b8; margin-bottom: 1rem;">
            ✓ Real-time Eligibility Checks<br/>
            ✓ Automated Revenue Stacking<br/>
            ✓ Knowledge Graph Powered
        </p>
        <a href="/LLM_Demo" class="btn">Explore Real Data Demo</a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">🕸️ KG Explorer</div>
        <p class="card-text">
            Deep dive into the <b>Agricultural Knowledge Base</b>. Directly query the RDF triples, 
            visualize relationships, and inspect the original source documents.
        </p>
        <p style="font-size: 0.875rem; color: #94a3b8; margin-bottom: 1rem;">
            ✓ SPARQL Direct Query<br/>
            ✓ Mermaid Graph Visuals<br/>
            ✓ Transparent Provenance
        </p>
        <a href="/KG_Explorer" class="btn">Open Explorer</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/><br/>", unsafe_allow_html=True)
st.divider()
st.caption("Developed by the Agri-Energy DeepMind Team • Powered by Semantic Web & LLMs")
