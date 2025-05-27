import streamlit as st
import pandas as pd
from src.ingestion import read_file

st.set_page_config(page_title="Robot de Géocodage", layout="wide")

st.title("🗺️ Robot de Géocodage - Ingestion de Fichier")

# Upload du fichier
uploaded_file = st.file_uploader("Dépose ton fichier CSV ou TXT", type=["csv", "txt"])

if uploaded_file is not None:
    # Choix du séparateur
    separator = st.selectbox("Séparateur", [",", ";", "|", "\\t"], index=0)
    if separator == "\\t":
        separator = "\t"

    df = read_file(uploaded_file, sep=separator)

    if df is not None and len(df.columns) > 0:
        st.success("✅ Fichier chargé avec succès !")
        st.subheader("Aperçu des premières lignes")
        st.dataframe(df.head())

        st.subheader("🧩 Mapping des Colonnes")

        possible_fields = ['street', 'postal_code', 'city', 'country', 'governorate', 'name', 'complement']

        mapping = {}
        for field in possible_fields:
            mapping[field] = st.selectbox(
                f"Colonne pour {field}",
                options=["-- Aucun --"] + list(df.columns),
                index=0
            )

        # Filtrer les champs réellement mappés
        mapped_fields = {k: v for k, v in mapping.items() if v != "-- Aucun --"}

        # Bouton pour générer l'adresse complète
        if st.button("➡️ Générer la colonne 'full_address'"):
            if all(k in mapped_fields for k in ["street", "city", "postal_code"]):
                df["full_address"] = df[mapped_fields["street"]].astype(str) + ", " + \
                                     df[mapped_fields["postal_code"]].astype(str) + " " + \
                                     df[mapped_fields["city"]].astype(str)
                st.success("✅ Colonne 'full_address' générée !")
                st.dataframe(df[["full_address"]].head())
            else:
                st.warning("⚠️ Tu dois mapper au moins les champs 'street', 'postal_code' et 'city'.")

