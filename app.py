import streamlit as st

st.set_page_config(page_title="Agri-Energy Bridge", page_icon="🌱", layout="wide")

st.title("🌱 Agri-Energy Strategic Partner")

st.markdown("""
### Welcome to the Agri-Energy Intelligence Platform

This platform demonstrates how Semantic Web technologies and LLMs can bridge the gap between complex regulations and farm realities.

#### Available Demos:

1.  **[Mock Demo (Hardcoded)](/Mock_Demo)**
    *   The original Proof-of-Concept.
    *   Uses hardcoded Python logic (`if/else`) to demonstrate the "Revenue Stacking" user experience.
    *   Fast, but difficult to scale to thousands of new regulations.

2.  **[LLM & Knowledge Graph Demo (Real Data)](/LLM_Demo)**
    *   **Powered by Granite/Perplexity Extraction**: Rules are extracted from *real* PDF policy documents (e.g., French CAP/PAC forms).
    *   **Semantic Matching**: Uses a **Knowledge Graph** to find opportunities.
    *   **Scalable**: To add a new rule, you simply upload a PDF; the code doesn't change.

---
*Select a demo from the sidebar to begin.*
""")
