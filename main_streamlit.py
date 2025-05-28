import streamlit as st
import pandas as pd
from src.ingestion import read_file
from src.geocoding import geocode_dataframe

# Configuration
st.set_page_config(page_title="Robot de Géocodage", layout="wide")
st.title("🗺️ Robot de Géocodage")

# Initialisation des états
if "df" not in st.session_state:
    st.session_state.df = None

if "enriched_df" not in st.session_state:
    st.session_state.enriched_df = None

# ========== UPLOAD ET LECTURE ==========
st.subheader("📁 Chargement du fichier")

uploaded_file = st.file_uploader("Dépose un fichier CSV ou TXT", type=["csv", "txt"])

if uploaded_file and st.session_state.df is None:
    separator = st.selectbox("Séparateur", [",", ";", "|", "\\t"], index=0)
    if separator == "\\t":
        separator = "\t"

    df = read_file(uploaded_file, sep=separator)
    if not df.empty:
        st.session_state.df = df
        st.success("✅ Fichier chargé avec succès !")
        st.dataframe(df.head())
    else:
        st.error("❌ Erreur de lecture du fichier.")

# ========== MAPPING ==========
df = st.session_state.df

if df is not None:
    st.subheader("🧩 Mapping des Colonnes")

    possible_fields = ['street', 'postal_code', 'city', 'country', 'governorate', 'name', 'complement']
    mapping = {}

    for field in possible_fields:
        mapping[field] = st.selectbox(
            f"Colonne pour {field}",
            options=["-- Aucun --"] + list(df.columns),
            index=0,
            key=f"mapping_{field}"
        )

    mapped_fields = {k: v for k, v in mapping.items() if v != "-- Aucun --"}

    if st.button("➡️ Générer la colonne 'full_address'"):
        if all(k in mapped_fields for k in ["street", "postal_code", "city"]):
            df["full_address"] = df[mapped_fields["street"]].astype(str) + ", " + \
                                 df[mapped_fields["postal_code"]].astype(str) + " " + \
                                 df[mapped_fields["city"]].astype(str)
            st.session_state.df = df.copy()  # 🔥 IMPORTANT : réassigne une copie stable
            st.success("✅ Colonne 'full_address' générée !")
            st.dataframe(df[["full_address"]].head())
        else:
             st.warning("⚠️ Tu dois mapper au moins les champs 'street', 'postal_code' et 'city'.")

# ========== GÉOCODAGE GOOGLE ==========
st.subheader("📍 Géocodage Google Maps")

if st.button("🚀 Lancer le géocodage avec Google Maps"):
    df = st.session_state.get("df", None)

    if df is None:
        st.error("❌ Aucun fichier disponible.")
    elif "full_address" not in df.columns:
        st.error("❌ La colonne 'full_address' est manquante.")
    else:
        with st.spinner("Géocodage en cours..."):
            enriched_df = geocode_dataframe(df, address_column="full_address")
            st.session_state.enriched_df = enriched_df
            st.success("✅ Géocodage terminé")
            st.dataframe(enriched_df.head())

# ========== EXPORT ==========
if st.session_state.enriched_df is not None:
    if st.button("💾 Exporter en CSV"):
        st.session_state.enriched_df.to_csv("data/output/geocoded_results_google.csv", index=False)
        st.success("📁 Fichier exporté dans data/output/geocoded_results_google.csv")
