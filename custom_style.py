"""
Styles personnalisés pour l'application Geocoder Bot
"""

import streamlit as st

# Couleurs de l'application
PRIMARY_COLOR = "#485093"  # Bleu principal
SECONDARY_COLOR = "#A23B72"  # Rose/Magenta
ACCENT_COLOR = "#F18F01"  # Orange
ROBOT_COLOR = "#4A5568"  # Gris foncé


def apply_custom_style():
    """
    Applique le style CSS personnalisé à l'application Streamlit.
    Remplace toutes les couleurs rouges/roses de Streamlit par la couleur primaire.
    """
    
    custom_css = f"""
    <style>
        /* ========== VARIABLES CSS ========== */
        :root {{
            --primary-color: {PRIMARY_COLOR};
            --primary-hover: {PRIMARY_COLOR}CC;
            --primary-light: {PRIMARY_COLOR}33;
            --primary-dark: #1F5A75;
        }}

        /* ========== BOUTONS ========== */
        .stButton>button {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}

        .stButton>button:hover {{
            background-color: {PRIMARY_COLOR}CC !important;
            color: white !important;
        }}

        .stButton>button:active {{
            background-color: #1F5A75 !important;
            transform: translateY(0px);
        }}

        .stButton>button:disabled {{
            background-color: #CCCCCC !important;
            color: #666666 !important;
            cursor: not-allowed !important;
        }}

        .stDownloadButton>button {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
        }}

        .stDownloadButton>button:hover {{
            background-color: {PRIMARY_COLOR}CC !important;
        }}

        /* ========== RADIO BUTTONS ========== */
        div[role="radiogroup"] {{
            gap: 8px;
        }}

        div[role="radiogroup"] label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
            cursor: pointer !important;
        }}

        div[role="radiogroup"] input[type="radio"] {{
            accent-color: {PRIMARY_COLOR} !important;
            cursor: pointer !important;
        }}

        div[role="radiogroup"] label:hover {{
            color: #1F5A75 !important;
        }}

        div[role="radiogroup"] input[type="radio"]:checked {{
            background-color: {PRIMARY_COLOR} !important;
            border-color: {PRIMARY_COLOR} !important;
        }}

        /* ========== CHECKBOX ========== */
        div[data-testid="stCheckbox"] {{
            color: {PRIMARY_COLOR} !important;
        }}

        input[type="checkbox"] {{
            accent-color: {PRIMARY_COLOR} !important;
            cursor: pointer !important;
        }}

        div[data-testid="stCheckbox"] label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        input[type="checkbox"]:checked {{
            background-color: {PRIMARY_COLOR} !important;
            border-color: {PRIMARY_COLOR} !important;
        }}

        /* ========== EXPANDERS ========== */
        .streamlit-expanderHeader {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 700 !important;
            font-size: 18px !important;
            border-radius: 8px !important;
        }}

        .streamlit-expanderHeader:hover {{
            color: #1F5A75 !important;
            background-color: {PRIMARY_COLOR}33 !important;
        }}

        .streamlit-expanderHeader svg {{
            fill: {PRIMARY_COLOR} !important;
        }}

        .streamlit-expanderContent {{
            border-left: 3px solid {PRIMARY_COLOR} !important;
            padding-left: 16px !important;
        }}

        /* ========== TABS ========== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            border-bottom: 2px solid #E0E0E0;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: #666666 !important;
            font-weight: 600 !important;
            border-radius: 8px 8px 0 0 !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            color: {PRIMARY_COLOR} !important;
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 700 !important;
        }}

        /* ========== SELECT BOX / MULTISELECT ========== */
        .stSelectbox label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        .stSelectbox > div > div {{
            border-color: {PRIMARY_COLOR} !important;
        }}

        .stMultiSelect {{
            border-color: {PRIMARY_COLOR} !important;
        }}
        
        .stMultiSelect [data-baseweb="tag"] {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
        }}

        .stMultiSelect [data-baseweb="tag"] svg {{
            fill: white !important;
        }}

        .stMultiSelect label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        /* ========== SLIDER ========== */
        .stSlider label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        .stSlider [data-baseweb="slider"] [role="slider"] {{
            background-color: {PRIMARY_COLOR} !important;
        }}

        .stSlider [data-baseweb="slider"] > div > div {{
            background-color: {PRIMARY_COLOR} !important;
        }}

        .stSlider [data-baseweb="slider"] > div > div > div {{
            background-color: {PRIMARY_COLOR} !important;
        }}

        /* ========== NUMBER INPUT ========== */
        .stNumberInput label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        .stNumberInput input:focus {{
            border-color: {PRIMARY_COLOR} !important;
            box-shadow: 0 0 0 1px {PRIMARY_COLOR} !important;
        }}

        .stNumberInput button {{
            color: {PRIMARY_COLOR} !important;
        }}

        .stNumberInput button:hover {{
            background-color: {PRIMARY_COLOR}33 !important;
        }}

        /* ========== TEXT INPUT ========== */
        .stTextInput label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        .stTextInput input:focus {{
            border-color: {PRIMARY_COLOR} !important;
            box-shadow: 0 0 0 1px {PRIMARY_COLOR} !important;
        }}

        /* ========== TEXT AREA ========== */
        .stTextArea label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        .stTextArea textarea:focus {{
            border-color: {PRIMARY_COLOR} !important;
            box-shadow: 0 0 0 1px {PRIMARY_COLOR} !important;
        }}

        /* ========== FILE UPLOADER ========== */

        .stFileUploader label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        .stFileUploader section {{
            border-color: {PRIMARY_COLOR} !important;
        }}

        .stFileUploader button {{
            color: {PRIMARY_COLOR} !important;
            border-color: {PRIMARY_COLOR} !important;
        }}

        .stFileUploader button:hover {{
            background-color: {PRIMARY_COLOR}33 !important;
        }}

        /* ========== PROGRESS BAR ========== */
        .stProgress > div > div {{
            background-color: {PRIMARY_COLOR} !important;
        }}

        .stProgress > div {{
            background-color: {PRIMARY_COLOR}33 !important;
        }}

        /* ========== SPINNER ========== */
        .stSpinner > div {{
            border-top-color: {PRIMARY_COLOR} !important;
        }}

        /* ========== METRICS ========== */
        [data-testid="stMetricDelta"] svg[fill="#09ab3b"] {{
            fill: {PRIMARY_COLOR} !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        /* ========== DATAFRAME / TABLE ========== */
        .stDataFrame thead tr th {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
            font-weight: 700 !important;
        }}

        .stDataFrame tbody tr:hover {{
            background-color: {PRIMARY_COLOR}33 !important;
        }}

        /* ========== LINKS ========== */
        a {{
            color: {PRIMARY_COLOR} !important;
            text-decoration: none !important;
        }}

        a:hover {{
            color: #1F5A75 !important;
            text-decoration: underline !important;
        }}

        /* ========== SIDEBAR ========== */
        .css-1d391kg, .css-1dp5vir {{
            background-color: {PRIMARY_COLOR}33 !important;
            color: {PRIMARY_COLOR} !important;
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background-color: {PRIMARY_COLOR}33 !important;
            color: {PRIMARY_COLOR} !important;
            border-left: 4px solid {PRIMARY_COLOR} !important;
            font-weight: 700 !important;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            background-color: {PRIMARY_COLOR}33 !important;
            color: {PRIMARY_COLOR} !important;
        }}

        /* ========== ALERTS / INFO BOXES ========== */
        .stAlert[data-baseweb="notification"] {{
            border-left: 4px solid {PRIMARY_COLOR} !important;
        }}

        .stSuccess {{
            background-color: {PRIMARY_COLOR}33 !important;
            border-left: 4px solid {PRIMARY_COLOR} !important;
        }}

        /* ========== DIVIDER ========== */
        hr {{
            border-color: {PRIMARY_COLOR} !important;
            opacity: 0.3;
        }}

        /* ========== CODE BLOCK ========== */
        code {{
            color: {PRIMARY_COLOR} !important;
            background-color: {PRIMARY_COLOR}33 !important;
            border-radius: 4px !important;
            padding: 2px 6px !important;
        }}

        /* ========== MARKDOWN HEADINGS ========== */
        h1, h2, h3 {{
            color: {PRIMARY_COLOR} !important;
        }}

        /* ========== SCROLLBAR ========== */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 10px;
        }}

        ::-webkit-scrollbar-thumb {{
            background: {PRIMARY_COLOR};
            border-radius: 10px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #1F5A75;
        }}

        /* ========== TOOLTIP ========== */
        [data-baseweb="tooltip"] {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
        }}

        /* ========== DATE INPUT ========== */
        .stDateInput label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        .stDateInput [data-baseweb="calendar"] button[aria-pressed="true"] {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
        }}

        /* ========== TIME INPUT ========== */
        .stTimeInput label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        /* ========== COLOR PICKER ========== */
        .stColorPicker label {{
            color: {PRIMARY_COLOR} !important;
            font-weight: 600 !important;
        }}

        /* ========== FORM SUBMIT BUTTON ========== */
        .stForm button[type="submit"] {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
        }}

        .stForm button[type="submit"]:hover {{
            background-color: {PRIMARY_COLOR}CC !important;
            box-shadow: 0 4px 12px rgba(46, 134, 171, 0.3) !important;
        }}

        /* ========== ANIMATIONS ========== */
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        @keyframes slideIn {{
            from {{
                transform: translateX(100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}

        /* ========== RESPONSIVE ========== */
        @media (max-width: 768px) {{
            .stButton>button {{
                width: 100%;
                margin: 4px 0;
            }}
            
            .stTabs [data-baseweb="tab"] {{
                padding: 8px 12px !important;
                font-size: 14px !important;
            }}
        }}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)


def apply_logo_and_style():
    """
    Applique le logo et le style personnalisé à l'application.
    À appeler au début de chaque page.
    """
    
    # Configuration de la page
    st.set_page_config(
        page_title="Geocoder Bot",
        page_icon="🗺️",  # ou le chemin vers ton favicon
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Appliquer le style CSS
    apply_custom_style()
    
    # Logo dans la sidebar (optionnel)
    # st.sidebar.image("path/to/geocoder_bot_icon.png", width=150)


# Fonction utilitaire pour créer des boutons avec icônes
def custom_button(label, icon="", key=None, help=None, disabled=False):
    """
    Crée un bouton personnalisé avec icône.
    
    Args:
        label (str): Texte du bouton
        icon (str): Emoji ou icône
        key (str): Clé unique du bouton
        help (str): Tooltip au survol
        disabled (bool): Bouton désactivé
    
    Returns:
        bool: True si le bouton est cliqué
    """
    button_label = f"{icon} {label}" if icon else label
    return st.button(button_label, key=key, help=help, disabled=disabled)


# Fonction utilitaire pour créer des metrics colorés
def custom_metric(label, value, delta=None, delta_color="normal"):
    """
    Crée une métrique personnalisée.
    
    Args:
        label (str): Label de la métrique
        value (str/int): Valeur principale
        delta (str/int): Variation
        delta_color (str): "normal", "inverse", ou "off"
    """
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


if __name__ == "__main__":
    # Exemple d'utilisation
    apply_custom_style()
    
    st.title("🗺️ Geocoder Bot")
    st.subheader("Test du style personnalisé")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.button("Bouton Standard")
        st.download_button("Télécharger", data="test", file_name="test.txt")
    
    with col2:
        st.radio("Mode API", ["HERE", "Google", "OSM"])
        st.checkbox("Option activée")
    
    with col3:
        st.selectbox("Sélectionner", ["Option 1", "Option 2"])
        st.multiselect("Multi-sélection", ["A", "B", "C"])
    
    with st.expander("📋 Voir les détails"):
        st.write("Contenu de l'expander")
    
    tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])
    
    with tab1:
        st.write("Contenu tab 1")
    
    st.slider("Slider", 0, 100, 50)
    st.progress(0.7)
    
    st.metric("Total lignes", "10,000", delta="1,000")