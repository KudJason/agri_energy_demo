import streamlit as st
import sys
import os
import pandas as pd

# Add scripts directory to path to allow import
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

try:
    from match_opportunities import find_matching_opportunities, get_available_tags
except ImportError as e:
    st.error(f"Failed to import semantic matcher: {e}")

# --- Configuration & Styling ---
st.set_page_config(page_title="Agri-Energy Intelligence", page_icon="🤖", layout="wide")

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .revenue-badge {
        background-color: #f0fdf4;
        color: #166534;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        border: 1px solid #bbf7d0;
    }
    .source-tag {
        font-size: 0.75rem;
        color: #94a3b8;
        font-style: italic;
    }
    .metric-card {
        background: linear-gradient(135deg, #166534 0%, #15803d 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Fetch tags for UI
available_tags = []
try:
    available_tags = get_available_tags()
except Exception as e:
    print(f"Loading tags failed (ignore if first run): {e}")

# Merge with standard core tags if available_tags is small or empty
base_certs = ["Organic (AB)", "Young Farmer"]
ui_tags = sorted(list(set(base_certs + available_tags)))

st.markdown('<div class="main-header">🤖 Semantic Knowledge Graph Matcher</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Bridge the gap between policy complexity and farm reality using RDF Reasoning.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ System Status")
    st.success("Knowledge Graph: Online")
    st.info("Rules loaded from `rules_combined.ttl`")
    st.divider()
    st.markdown("### 📄 Policy Upload")
    st.caption("Upload a new policy (PDF) to automatically extend the Knowledge Graph.")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_file:
        st.warning("Auto-extraction running in background (Simulation)")

# --- Farm Profile Input ---
with st.container():
    st.markdown("#### 🚜 Farm Profile & Operational Context")
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        region = st.selectbox("Operating Region", ["France", "Belgium (Flanders)", "Belgium (Wallonia)"])
        crop = st.selectbox("Primary Crop Category", ["Wheat", "Corn", "Pasture", "Vineyard", "Orchards"])
    with col2:
        size = st.number_input("Effective Area (ha)", value=50, step=1)
        # Empty space for alignment
    with col3:
        certs = st.multiselect("Certifications, Traits & Constraints", ui_tags, help="Select all that apply to your current operation.")

# Construct simple profile dict to pass to matcher
farm_profile = {
    "region": region,
    "crop": crop,
    "size": size,
    "certs": certs
}

st.divider()

if st.button("Query Knowledge Graph for Opportunities 🔍", use_container_width=True):
    with st.spinner("Traversing Knowledge Graph relationships..."):
        try:
            results = find_matching_opportunities(farm_profile)
            
            if not results:
                st.warning("### No direct matches found.")
                st.info("The semantic engine didn't find specific subsidies matching your exact profile. Consider relaxing constraints or checking the KG Explorer.")
            else:
                # --- Summary Metrics ---
                total_opps = len(results)
                # Try to calculate total revenue if rates are numeric
                total_est_revenue = 0
                for r in results:
                    if r.get('payment_rate'):
                        try:
                            total_est_revenue += float(r['payment_rate']) * size
                        except:
                            pass
                
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Matching Opportunities</div>
                        <div class="metric-value">{total_opps}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Estimated Annual Impact</div>
                        <div class="metric-value">€{total_est_revenue:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Data Confidence</div>
                        <div class="metric-value">High</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.write("")
                st.markdown("### 🎯 Best Revenue Stacking Opportunities")
                
                for r in results:
                    with st.container():
                        st.markdown(f"""
                        <div class="card">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <h3 style="margin: 0; color: #1e293b;">📄 {r['name']}</h3>
                                    <span class="source-tag">Source: {r['source']}</span>
                                </div>
                                <div class="revenue-badge">
                                    {f"€{r['payment_rate']} /{r['payment_unit']}" if r.get('payment_rate') else r.get('benefit_amount', 'See Details')}
                                </div>
                            </div>
                            <p style="margin-top: 1rem; color: #475569;">{r['description']}</p>
                            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                                <div style="flex: 1; padding: 0.75rem; background-color: #f8fafc; border-radius: 8px;">
                                    <small style="color: #64748b; font-weight: 600;">CALCULATION LOGIC</small><br/>
                                    <span style="font-size: 0.9rem;">{r.get('calculation_logic', 'Standard per-hectare formula')}</span>
                                </div>
                                <div style="flex: 1; padding: 0.75rem; background-color: #fef2f2; border-radius: 8px;">
                                    <small style="color: #991b1b; font-weight: 600;">DEADLINE</small><br/>
                                    <span style="font-size: 0.9rem; color: #b91c1c;">{r.get('app_end_date', 'N/A')}</span>
                                </div>
                            </div>
                            <div style="margin-top: 1rem;">
                                <small style="color: #94a3b8;">Matched against {r['criteria_count']} semantic criteria</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
        except Exception as e:
            st.error(f"### ❌ Semantic Matching Engine Error")
            st.exception(e)
