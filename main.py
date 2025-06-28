import streamlit as st
from streamlit_option_menu import option_menu
from app.page_geocoding import run_geocoding_page
from app.page_retry import run_retry_page
from app.page_analytics import run_analytics_page

# Configuration de la page principale
st.set_page_config(page_title=" Dashboard Géocodage", layout="wide")

# Titre principal
st.title("📍 Robot de Géocodage Multi-API")

# Initialisation des états globaux
session_defaults = {
    "df": None,
    "last_selected_enriched_df": None,
    "enriched_df": None,
    "cleaned_df": None,
    "batch_results": [],
    "modified_rows": set(),
    "mapping_config": {"fields": {}, "attribute_selected": None},
    "job_history": [],
    "active_page": "Géocodage",
    "geocoding_in_progress": False
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# === Navigation (désactivée pendant le géocodage) ===
with st.sidebar:
    st.markdown("###  Navigation")
    if st.session_state.get("geocoding_in_progress", False):
        st.warning("⏳ Géocodage en cours... navigation désactivée.")
        selected = st.session_state.active_page
    else:
        selected = option_menu(
            "Navigation",
            ["Géocodage", "Relance", "Analytiques"],
            icons=["map", "arrow-repeat", "bar-chart-line"],
            menu_icon="cast",
            default_index=["Géocodage", "Relance", "Analytiques"].index(st.session_state.active_page),
            orientation="vertical"
        )
        st.session_state.active_page = selected

# === Routage des pages ===
if selected == "Géocodage":
    run_geocoding_page()
elif selected == "Relance":
    run_retry_page()
elif selected == "Analytiques":
    run_analytics_page()
    