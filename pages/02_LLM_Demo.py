import streamlit as st
import sys
import os

# Add scripts directory to path to allow import
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

try:
    from match_opportunities import find_matching_opportunities, get_available_tags
except ImportError as e:
    st.error(f"Failed to import semantic matcher: {e}")

# Fetch tags for UI
available_tags = []
try:
    available_tags = get_available_tags()
except Exception as e:
    print(f"Loading tags failed (ignore if first run): {e}")

# Merge with standard core tags if available_tags is small or empty
base_certs = ["Organic (AB)", "Young Farmer", "HVE Level 3"]
ui_tags = sorted(list(set(base_certs + available_tags)))

st.set_page_config(page_title="LLM Agri-Energy Demo", page_icon="🤖", layout="wide")

st.title("🤖 Semantic Knowledge Graph Demo")
st.markdown("**Powered by LLM Extraction & RDF Reasoning**")

st.info("This demo uses rules extracted *automatically* from PDF documents using Perplexity Sonar and stored in a local Turtle (.ttl) Knowledge Base.")

with st.sidebar:
    st.header("Upload New Policy?")
    st.caption("To add rules, you would upload a PDF here. (Demo mode: uses pre-loaded 'Dossier PAC 2025')")

# --- Farm Profile Input ---
st.subheader("🚜 Farm Profile")

col1, col2 = st.columns(2)
with col1:
    region = st.selectbox("Region", ["France", "Belgium (Flanders)", "Belgium (Wallonia)", "Germany"])
    crop = st.selectbox("Primary Crop", ["Wheat", "Corn", "Pasture", "Vineyard", "Orchards"])
    
with col2:
    size = st.number_input("Farm Size (ha)", value=50)
    certs = st.multiselect("Certifications / Traits", ui_tags)

# Construct simple profile dict to pass to matcher
farm_profile = {
    "region": region,
    "crop": crop,
    "size": size,
    "certs": certs
}

if st.button("Find Opportunities (Semantic Search) 🔍"):
    with st.spinner("Traversing Knowledge Graph..."):
        try:
            results = find_matching_opportunities(farm_profile)
            
            st.divider()
            
            if not results:
                st.warning("No matching opportunities found in the current Knowledge Base.")
            else:
                st.success(f"Found {len(results)} matches based on extracted rules!")
                
                for r in results:
                    with st.expander(f"📄 {r['name']} ({r['revenue_text']})"):
                        st.markdown(f"**Description**: {r['description']}")
                        st.markdown(f"**Source**: {r['uri'].split('/')[-1]}") # Simple slug display
                        st.caption(f"Verified against {r['criteria_count']} logical criteria.")
                        
        except Exception as e:
            st.error(f"An error occurred during matching: {e}")
