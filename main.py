import streamlit as st
from streamlit_option_menu import option_menu
from app.page_geocoding import run_geocoding_page
from app.page_retry import run_retry_page
from app.page_analytics import run_analytics_page

# Configuration de la page principale
st.set_page_config(page_title="Dashboard Géocodage", layout="wide")

# Titre principal
st.title("📍 Robot de Géocodage Multi-API")


def initialize_global_state():
    """
    Initialise les états de session globaux UNIQUEMENT s'ils n'existent pas.
    Cela permet de préserver l'état lors des changements de page.
    """
    # États globaux partagés entre les pages
    global_defaults = {
        "df": None,
        "last_selected_enriched_df": None,
        "enriched_df": None,
        "cleaned_df": None,
        "batch_results": [],
        "modified_rows": set(),
        "mapping_config": {"fields": {}, "attribute_selected": None},
        "job_history": [],
        "active_page": "Géocodage",
        "geocoding_in_progress": False,
        "previous_filename": None,
        "geocoding_mode": "HERE uniquement",
    }
    
    # États spécifiques à page_retry
    retry_defaults = {
        "retry_df": None,
        "retry_filename": None,
        "retry_results": None,
        "retry_updated_df": None,
    }
    
    # États spécifiques à page_analytics
    analytics_defaults = {
        "analytics_df": None,
        "analytics_filename": None,
    }
    
    # Fusionner tous les defaults
    all_defaults = {**global_defaults, **retry_defaults, **analytics_defaults}
    
    # Initialiser UNIQUEMENT les clés qui n'existent pas encore
    for key, value in all_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Initialiser l'état global
initialize_global_state()

# === Sidebar avec navigation ===
with st.sidebar:
    st.markdown("---")
    
    # Afficher l'état global si des données sont chargées
    if st.session_state.df is not None or st.session_state.retry_df is not None:
        st.markdown("### 📊 État Global")
        
        # Page Géocodage
        if st.session_state.df is not None:
            with st.expander("📍 Géocodage", expanded=False):
                st.markdown(f"**Fichier:** {st.session_state.previous_filename}")
                st.markdown(f"**Lignes:** {len(st.session_state.df):,}")
                if st.session_state.last_selected_enriched_df is not None:
                    success = (st.session_state.last_selected_enriched_df["status"] == "OK").sum()
                    st.markdown(f"**Géocodées:** {success:,}")
        
        # Page Relance
        if st.session_state.retry_df is not None:
            with st.expander("🔁 Relance", expanded=False):
                st.markdown(f"**Fichier:** {st.session_state.retry_filename}")
                st.markdown(f"**Lignes:** {len(st.session_state.retry_df):,}")
                if st.session_state.retry_results is not None:
                    success = (st.session_state.retry_results["status"] == "OK").sum()
                    st.markdown(f"**Améliorées:** {success:,}")
                    
        # Page Analytiques
        if st.session_state.analytics_df is not None:
            with st.expander("📊 Analytiques", expanded=False):
                st.markdown(f"**Fichier:** {st.session_state.analytics_filename}")
                st.markdown(f"**Lignes:** {len(st.session_state.analytics_df):,}")
        
        st.markdown("---")
    
    # Menu de navigation
    if st.session_state.get("geocoding_in_progress", False):
        st.warning("⏳ Géocodage en cours...\nNavigation désactivée.")
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
    
    st.markdown("---")
    
    # Informations système
    with st.expander("ℹ️ Informations", expanded=False):
        st.markdown("""
        **Version:** 2.0
        
        **APIs:**
        - HERE Maps
        - Google Maps
        - OpenStreetMap
        
        **Fonctionnalités:**
        - Géocodage par batch
        - Fallback intelligent
        - Relance optimisée
        - Analytics avancées
        """)
    
    # Bouton de reset (utile pour débogage)
    if st.button("🔄 Réinitialiser tout", use_container_width=True):
        # Garder uniquement active_page
        active = st.session_state.active_page
        for key in list(st.session_state.keys()):
            if key != "active_page":
                del st.session_state[key]
        st.session_state.active_page = active
        st.rerun()

# === Routage des pages ===
if selected == "Géocodage":
    run_geocoding_page()
elif selected == "Relance":
    run_retry_page()
elif selected == "Analytiques":
    run_analytics_page()