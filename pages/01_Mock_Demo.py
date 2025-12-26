import streamlit as st

# --- Configuration & Styling ---
st.set_page_config(page_title="Agri-Energy Bridge", page_icon="🌱", layout="wide")

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .big-font { font-size: 20px !important; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    .success-card { padding: 20px; border-radius: 10px; background-color: #e8f5e9; border: 1px solid #c8e6c9; }
</style>
""", unsafe_allow_html=True)

st.title("🌱 Agri-Energy Strategic Partner")
st.markdown("### 1. Farm Diagnostics & Data Ingestion")
st.markdown("Please provide your farm's operating profile to unlock revenue stacking opportunities.")

# --- MOCK DATA STORE ---
# This simulates what the RDF Knowledge Graph WOULD return
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
    },
    {
        "id": "opp_be_1",
        "name": "🇧🇪 Ecoregeling: Ecologisch Graslandbeheer",
        "type": "Subsidy",
        "revenue_per_ha": 300,
        "description": "Vergoeding voor extensief graslandgebruik zonder gewasbescherming.",
        "requirements": ["Region: Flanders", "Crop: Pasture"]
    },
    {
        "id": "opp_be_2",
        "name": "⚡ VLIF Innovatie: Agri-PV",
        "type": "Investment Support",
        "revenue_per_ha": 4200,
        "description": "Investeringssteun (40%) voor innovatieve zonnepanelen boven teelten.",
        "requirements": ["Region: Flanders", "Innovative Project"]
    }
]

# --- UI: The Survey Form ---
with st.sidebar:
    st.header("Platform Status")
    st.info("System: Online")
    st.info("Regulations Loaded: 3 (Mocked)")
    st.info("Country Focus: France")

with st.form("ingestion_survey"):
    # Section 1: General Info
    st.subheader("📍 Geography & Scope")
    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox("Operating Region", ["France", "Germany", "Netherlands", "Belgium (Flanders)", "Belgium (Wallonia)"])
        size_ha = st.number_input("Total Farm Area (Hectares)", min_value=1.0, value=75.0, step=0.1)
    with col2:
        soil_type = st.selectbox("Dominant Soil Type", ["Clay", "Sandy", "Loam", "Peat"])
        slope_pct = st.slider("Average Land Slope (%)", 0, 30, 2, help="Vital for PV feasibility")

    # Section 2: Production
    st.subheader("🌾 Production Profile")
    col3, col4 = st.columns(2)
    with col3:
        primary_crop = st.selectbox("Primary Crop / Activity", ["Wheat", "Corn", "Pasture (Cattle)", "Orchards"])
        energy_bill = st.number_input("Annual Energy Bill (€)", min_value=0, value=12000)
    with col4:
        grid_dist = st.slider("Distance to Electrical Substation (km)", 0.0, 20.0, 1.5, help="Determines grid connection cost")
    
    # Section 3: Compliance & Certifications
    st.subheader("📜 Compliance")
    certs = st.multiselect("Active Certifications", ["Organic (AB)", "HVE Level 3", "GlobalGAP", "None"])
    
    # Submission
    st.markdown("---")
    submitted = st.form_submit_button("Analysing Strategic Opportunities 🚀")

# --- UI: Results Display (Mock Logic) ---
if submitted:
    st.divider()
    st.markdown("## 📊 Strategic Roadmap")
    
    # 1. Mock "Thinking" Process
    st.spinner("Querying EU Regulatory Database...")
    st.spinner("Calculating Solar Irradiance...")
    
    # 2. Simple Logic to Filter Mock Data
    valid_matches = []
    
    # Logic for Mock Opp 1: Agrivoltaics
    if region == "France" and primary_crop == "Pasture (Cattle)" and slope_pct < 10:
        valid_matches.append(MOCK_OPPORTUNITIES[0])
        
    # Logic for Mock Opp 2: Organic
    if "Organic (AB)" in certs:
        valid_matches.append(MOCK_OPPORTUNITIES[1])
        
    # Logic for Mock Opp 3: Energy Hub
    if grid_dist < 3.0:
        valid_matches.append(MOCK_OPPORTUNITIES[2])

    # Logic for Flanders Opp 1: Grassland
    if region == "Belgium (Flanders)" and primary_crop == "Pasture (Cattle)":
        valid_matches.append(MOCK_OPPORTUNITIES[3])

    # Logic for Flanders Opp 2: VLIF Agri-PV
    # Assuming valid if size is sufficient for "Innovation" investment
    if region == "Belgium (Flanders)" and size_ha > 5.0:
        valid_matches.append(MOCK_OPPORTUNITIES[4])
    
    # 3. Display Logic
    if not valid_matches:
        st.warning("Based on the provided profile, no high-confidence standard opportunities were found. A bespoke audit is recommended.")
    else:
        # Calculate Totals
        total_est_rev = sum([m['revenue_per_ha'] for m in valid_matches]) * size_ha
        
        # Summary Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Identified Opportunities", f"{len(valid_matches)}")
        m2.metric("Est. Annual Uplift", f"€{total_est_rev:,.0f}")
        m3.metric("Land Efficiency Score", "High")
        
        # List Details
        for match in valid_matches:
            with st.expander(f"{match['name']}  --  Est. €{match['revenue_per_ha'] * size_ha:,.0f}/yr", expanded=True):
                st.markdown(f"**Description**: {match['description']}")
                st.markdown(f"**Type**: *{match['type']}*")
                st.caption(f"Matched Criteria: {', '.join(match['requirements'])}")
