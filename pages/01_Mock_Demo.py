import streamlit as st

# --- Configuration & Styling ---
st.set_page_config(page_title="Agri-Energy Bridge", page_icon="🌱", layout="wide")

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
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
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

st.markdown('<div class="main-header">🌱 Mock Strategic Roadmap</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Diagnostic simulation of farm operations and revenue stacking.</div>', unsafe_allow_html=True)

# --- MOCK DATA STORE ---
MOCK_OPPORTUNITIES = [
    {
        "id": "opp_1",
        "name": "⚡ Agrivoltaics (France Decree 2024-318)",
        "type": "Energy",
        "revenue_per_ha": 3500,
        "description": "Installation of vertical bifacial solar panels on pasture land. Must ensure <10% yield loss.",
        "requirements": ["Region: France", "Crop: Pasture", "Slope < 10%"]
    },
    {
        "id": "opp_2",
        "name": "💶 CAP Eco-Scheme: Organic Farming",
        "type": "Subsidy",
        "revenue_per_ha": 110,
        "description": "Annual direct payment for certified organic production.",
        "requirements": ["Certification: Organic"]
    },
    {
        "id": "opp_3",
        "name": "🧱 Energy Hub Optimization",
        "type": "Innovation",
        "revenue_per_ha": 500, 
        "description": "Grid congestion relief payment via local flexible electricity trading.",
        "requirements": ["Distance to Substation < 3km"]
    }
]

# --- UI: The Survey Form ---
with st.sidebar:
    st.header("⚙️ Platform Status")
    st.info("Mode: Simulation (Mock)")
    st.info("System: Online")

with st.form("ingestion_survey"):
    st.subheader("📍 Geography & Operational Scope")
    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox("Operating Region", ["France", "Netherlands", "Belgium (Flanders)", "Belgium (Wallonia)"])
        size_ha = st.number_input("Total Farm Area (Hectares)", min_value=1.0, value=75.0, step=0.1)
    with col2:
        soil_type = st.selectbox("Dominant Soil Type", ["Clay", "Sandy", "Loam", "Peat"])
        slope_pct = st.slider("Average Land Slope (%)", 0, 30, 2)

    st.subheader("🌾 Production Profile")
    col3, col4 = st.columns(2)
    with col3:
        primary_crop = st.selectbox("Primary Crop / Activity", ["Wheat", "Corn", "Pasture (Cattle)", "Orchards"])
        energy_bill = st.number_input("Annual Energy Bill (€)", min_value=0, value=12000)
    with col4:
        grid_dist = st.slider("Distance to Electrical Substation (km)", 0.0, 20.0, 1.5)
    
    st.subheader("📜 Compliance")
    certs = st.multiselect("Active Certifications", ["Organic (AB)", "HVE Level 3", "GlobalGAP", "None"])
    
    submitted = st.form_submit_button("Run Diagnostic Analysis 🚀", use_container_width=True)

# --- UI: Results Display ---
if submitted:
    st.divider()
    st.markdown("## 📊 Strategic Roadmap Analysis")
    
    with st.status("Analyzing farm profile..."):
        st.write("Querying regulatory database...")
        st.write("Calculating solar potential...")
        st.write("Matching eligibility criteria...")
    
    valid_matches = []
    if region == "France" and primary_crop == "Pasture (Cattle)" and slope_pct < 10:
        valid_matches.append(MOCK_OPPORTUNITIES[0])
    if "Organic (AB)" in certs:
        valid_matches.append(MOCK_OPPORTUNITIES[1])
    if grid_dist < 3.0:
        valid_matches.append(MOCK_OPPORTUNITIES[2])

    if not valid_matches:
        st.warning("No high-confidence opportunities found based on current profile.")
    else:
        total_est_rev = sum([m['revenue_per_ha'] for m in valid_matches]) * size_ha
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Opportunities</div><div class="metric-value">{len(valid_matches)}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Est. Annual Uplift</div><div class="metric-value">€{total_est_rev:,.0f}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Efficiency</div><div class="metric-value">Optimal</div></div>', unsafe_allow_html=True)
        
        st.write("")
        for match in valid_matches:
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <h3 style="margin: 0; color: #1e293b;">{match['name']}</h3>
                    <div class="revenue-badge">Est. €{match['revenue_per_ha'] * size_ha:,.0f}/yr</div>
                </div>
                <p style="margin-top: 1rem; color: #475569;">{match['description']}</p>
                <div style="margin-top: 0.5rem;">
                    <small style="color: #94a3b8;"><b>Requirements:</b> {', '.join(match['requirements'])}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
