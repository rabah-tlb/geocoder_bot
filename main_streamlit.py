import streamlit as st
import pandas as pd
import math
import re
from src.ingestion import read_file
from src.geocoding import geocode_dataframe, clean_address

# Configuration
st.set_page_config(page_title="Robot de Géocodage", layout="wide")
st.title("📍 Robot de Géocodage")

# Initialisation des états
if "df" not in st.session_state:
    st.session_state.df = None

if "last_selected_enriched_df" not in st.session_state:
    st.session_state.last_selected_enriched_df = None

if "enriched_df" not in st.session_state:
    st.session_state.enriched_df = None

if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None

if "batch_results" not in st.session_state:
    st.session_state.batch_results = []

if "modified_rows" not in st.session_state:
    st.session_state.modified_rows = set()

# ========== UPLOAD ET LECTURE ==========
st.subheader("📁 Chargement du fichier")

uploaded_file = st.file_uploader("Dépose un fichier CSV ou TXT", type=["csv", "txt"])

# Gestion de la réinitialisation lorsque le fichier est retiré
if uploaded_file is None:
    st.session_state.df = None
    st.session_state.enriched_df = None
    st.session_state.cleaned_df = None
    st.session_state.batch_results = []
    st.session_state.modified_rows = set()
    st.session_state.mapping_config = {
        "fields": {},
        "attribute_selected": None
    }

# Détection de changement de fichier pour reset automatique
current_filename = uploaded_file.name if uploaded_file else None
previous_filename = st.session_state.get("previous_filename", None)

if uploaded_file and current_filename != previous_filename:
    # Réinitialiser tous les états liés au précédent fichier
    st.session_state.df = None
    st.session_state.enriched_df = None
    st.session_state.cleaned_df = None
    st.session_state.batch_results = []
    st.session_state.modified_rows = set()
    st.session_state.mapping_config = {
        "fields": {},
        "attribute_selected": None
    }
    st.session_state.previous_filename = current_filename  # Sauvegarder le nouveau nom

if uploaded_file and st.session_state.df is None:
    df = read_file(uploaded_file, sep=None)

    if not df.empty:
        st.session_state.df = df
    else:
        st.error("❌ Erreur de lecture du fichier.")

if st.session_state.df is not None:
    st.success("✅ Fichier chargé avec succès !")
    st.dataframe(st.session_state.df.head())

# ========== MAPPING ==========
df = st.session_state.df

if df is not None:
    st.subheader("🧩 Mapping des Colonnes")

    possible_fields = ['name', 'street', 'postal_code', 'city', 'governorate', 'country', 'complement']

    if "mapping_config" not in st.session_state:
        st.session_state.mapping_config = {
            "fields": {}
        }

    mapping_config = st.session_state.mapping_config
    current_mapping = {}

    for field in possible_fields:
        current_mapping[field] = st.selectbox(
            f"Colonne pour {field}",
            options=["-- Aucun --"] + list(df.columns),
            index=(["-- Aucun --"] + list(df.columns)).index(mapping_config["fields"].get(field, "-- Aucun --"))
            if "fields" in mapping_config and field in mapping_config["fields"] else 0,
            key=f"mapping_{field}"
        )

    mapped_fields = {k: v for k, v in current_mapping.items() if v != "-- Aucun --"}
    st.session_state.mapping_config["fields"] = mapped_fields

    # Génération automatique de la colonne 'full_address'
    if mapped_fields:
        full_address_parts = []

        if "name" in mapped_fields:
            full_address_parts.append(df[mapped_fields["name"]].astype(str))

        for key in ['street', 'postal_code', 'city', 'governorate', 'country', 'complement']:
            if key in mapped_fields:
                full_address_parts.append(df[mapped_fields[key]].astype(str))

        if full_address_parts:
            df["full_address"] = full_address_parts[0]
            for part in full_address_parts[1:]:
                df["full_address"] += ", " + part

            st.success("✅ Colonne 'full_address' générée automatiquement !")
            #st.dataframe(df.head())
            st.dataframe(st.session_state.df.head())
        else:
            st.warning("⚠️ Aucun champ mappé pour générer 'full_address'.")

# ========== GÉOCODAGE PAR BATCH ==========
if st.session_state.df is not None and "full_address" in st.session_state.df.columns:
    st.subheader("📍 Géocodage Multi-API en Batches")

    total_rows = len(st.session_state.df)
    st.markdown(f"🔢 Nombre total de lignes : **{total_rows}**")

    start_line = st.number_input("📍 Ligne de départ (incluse)", min_value=0, max_value=total_rows - 1, value=0)
    end_line = st.number_input("🏁 Ligne de fin (exclue)", min_value=start_line + 1, max_value=total_rows, value=min(start_line + 100, total_rows))

    batch_size = st.number_input("📦 Taille d’un batch", min_value=10, max_value=1000, value=100, step=10)

    selected_df = st.session_state.df.iloc[start_line:end_line].copy()
    total_selected = len(selected_df)
    total_batches = math.ceil(total_selected / batch_size)

    nb_batches_to_run = st.number_input("🚀 Nombre de batches à exécuter", min_value=1, max_value=total_batches, value=total_batches)

    actual_batches = min(nb_batches_to_run, total_batches)
    actual_rows = min(actual_batches * batch_size, total_selected)
    st.info(f"🧮 {actual_rows} lignes sélectionnées – {actual_batches} batches de {batch_size}")

    # Récupérer les colonnes mappées
    mapped_fields = st.session_state.mapping_config.get("fields", {})
    component_cols = {
        "postal_code": mapped_fields.get("postal_code"),
        "city": mapped_fields.get("city"),
        "governorate": mapped_fields.get("governorate")
    }

    if st.button("🚀 Lancer le géocodage sur cette plage"):
        batch_results = []

        for i in range(nb_batches_to_run):
            start = i * batch_size
            end = min((i + 1) * batch_size, total_selected)
            batch_df = selected_df.iloc[start:end].copy()

            # Générer les components dynamiques pour chaque ligne
            components_list = []
            for _, row in batch_df.iterrows():
                comp = []
                if component_cols["postal_code"] and pd.notna(row[component_cols["postal_code"]]):
                    comp.append(f"postal_code:{row[component_cols['postal_code']]}")
                if component_cols["city"] and pd.notna(row[component_cols["city"]]):
                    comp.append(f"locality:{row[component_cols['city']]}")
                elif component_cols["governorate"] and pd.notna(row[component_cols["governorate"]]):
                    comp.append(f"administrative_area:{row[component_cols['governorate']]}")
                comp.append("country:TN")
                components_list.append("|".join(comp))

            batch_df["components"] = components_list

            with st.spinner(f"🔄 Traitement du batch {i+1}/{nb_batches_to_run}..."):
                renamed_df = batch_df.rename(columns={v: k for k, v in mapped_fields.items()})
                enriched_batch = geocode_dataframe(renamed_df, address_column="full_address")

                #enriched_batch = geocode_dataframe(batch_df, address_column="full_address")
                batch_results.append(enriched_batch)
                st.success(f"✅ Batch {i+1} traité !")

        st.session_state.batch_results = batch_results

        selected_enriched_df = pd.concat(batch_results, ignore_index=True)
        st.session_state.last_selected_enriched_df = selected_enriched_df

        if st.session_state.enriched_df is None:
            st.session_state.enriched_df = st.session_state.df.copy()

        for _, row in selected_enriched_df.iterrows():
            row_index = row.get("row_index", None)
            if row_index is not None:
                for col in selected_enriched_df.columns:
                    if col != "row_index":
                        st.session_state.enriched_df.at[row_index, col] = row[col]

        st.success("🎉 Tous les batches de la plage sélectionnée ont été traités !")

# ========== AFFICHAGE DES TABS APRÈS TRAITEMENT ==========
if st.session_state.batch_results:
    enriched_df = st.session_state.last_selected_enriched_df
    batch_results = st.session_state.batch_results

    tabs = st.tabs(["📊 Total", "❌ Échecs"] + [f"Batch {i+1}" for i in range(len(batch_results))])

    with tabs[0]:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### 📦 {len(batch_results)} batches traités")
            st.markdown(f"- Taille de batch : `{batch_size}` lignes")
            st.markdown(f"- Lignes traitées : `{len(enriched_df)}`")
            total_success = (enriched_df["status"] == "OK").sum()
            total_failed = len(enriched_df) - total_success
            rate = round(total_success / len(enriched_df) * 100, 2)
            st.markdown(f"- Succès : ✅ `{total_success}`")
            st.markdown(f"- Échecs : ❌ `{total_failed}`")
            st.markdown(f"- Taux de réussite global : **{rate}%**")

        # Statistiques des niveaux de précision triés
        with col2:
             if "precision_level" in enriched_df.columns:
                st.markdown("#### 🎯 Niveaux de précision (global) :")
                precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
                precision_counts = enriched_df["precision_level"].value_counts().to_dict()

                for level in precision_order:
                    if level in precision_counts:
                        st.markdown(f"- `{level}` : {precision_counts[level]}")
                # Autres types non standards
                for level, count in precision_counts.items():
                    if level not in precision_order:
                        st.markdown(f"- `{level}` : {count}")

        st.dataframe(enriched_df)

    with tabs[1]:
        failed_df = enriched_df[enriched_df["status"] != "OK"]
        st.markdown(f"### ❌ Lignes échouées : {len(failed_df)}")
        st.dataframe(failed_df)

    for i, batch_df in enumerate(batch_results):
        with tabs[i + 2]:
            col1, col2 = st.columns(2)

            with col1:
                batch_success = (batch_df["status"] == "OK").sum()
                batch_failed = len(batch_df) - batch_success
                rate = round(batch_success / len(batch_df) * 100, 2)
                st.markdown(f"### 📦 Batch {i+1} – `{len(batch_df)}` lignes")
                st.markdown(f"- Succès : ✅ `{batch_success}`")
                st.markdown(f"- Échecs : ❌ `{batch_failed}`")
                st.markdown(f"- Taux de réussite : **{rate}%**")

            with col2:
                if "precision_level" in batch_df.columns:
                    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
                    precision_counts = batch_df["precision_level"].value_counts().to_dict()

                    st.markdown("#### 🎯 Niveaux de précision dans ce batch :")
                    for level in precision_order:
                        if level in precision_counts:
                            st.markdown(f"- `{level}` : {precision_counts[level]}")

                    for level, count in precision_counts.items():
                        if level not in precision_order:
                            st.markdown(f"- `{level}` : {count} ligne(s)")
            
            st.dataframe(batch_df)

# ========== RELANCE DES ÉCHECS ==========
if st.session_state.enriched_df is not None:
    enriched_df = st.session_state.last_selected_enriched_df
    failed_df = enriched_df[enriched_df["status"] != "OK"]

    if not failed_df.empty:
        st.warning(f"⚠️ {len(failed_df)} lignes ont échoué au géocodage.")

        if st.button("🔁 Relancer uniquement les erreurs"):
            with st.spinner("🔄 Relance des lignes échouées (avec reformulation des adresses)..."):

                # Récupérer le mapping sauvegardé
                mapped_fields = st.session_state.get("mapping_config", {}).get("fields", {})

                def reformat_address(row):
                    parts = []
                    for field in ["street", "postal_code", "city", "governorate", "country", "complement"]:
                        if field in mapped_fields and mapped_fields[field] in row:
                            value = row[mapped_fields[field]]
                            if pd.notna(value):
                                parts.append(str(value))
                    return ", ".join(parts)

                # Reformuler les adresses
                failed_df = failed_df.copy()
                failed_df["full_address"] = failed_df.apply(reformat_address, axis=1)

                # Nettoyage des anciennes colonnes de géocodage
                geo_cols = [
                    'latitude', 'longitude', 'formatted_address',
                    'status', 'error_message', 'api_used',
                    'precision_level', 'timestamp'
                ]
                for col in geo_cols:
                    if col in failed_df.columns:
                        failed_df.drop(columns=[col], inplace=True)

                # Re-géocodage complet
                #retried_df = geocode_dataframe(failed_df, address_column="full_address")

                renamed_df = failed_df.rename(columns={v: k for k, v in mapped_fields.items()})
                retried_df = geocode_dataframe(renamed_df, address_column="full_address")

                # Affichage debug
                st.markdown("### ✅ Résultat des lignes relancées")
                st.dataframe(retried_df)

                # Mise à jour du enriched_df
                if "id" not in enriched_df.columns or "id" not in retried_df.columns:
                    st.error("❌ Impossible de mettre à jour : colonne 'id' manquante.")
                else:
                    # Supprimer les lignes échouées avec les mêmes id
                    failed_ids = retried_df["id"].unique()
                    enriched_df_cleaned = enriched_df[~enriched_df["id"].isin(failed_ids)]

                    # Fusionner avec les lignes corrigées
                    updated_df = pd.concat([enriched_df_cleaned, retried_df], ignore_index=True)

                    # Trier si besoin
                    updated_df = updated_df.sort_values(by="id").reset_index(drop=True)

                    # Enregistrer la mise à jour
                    st.session_state.enriched_df = updated_df
                    st.session_state.last_selected_enriched_df = updated_df  # clé ici pour l'export

                    st.success(f"✅ {len(retried_df)} lignes corrigées ! Résultats mis à jour.")

# ========== EXPORT ==========
if st.session_state.last_selected_enriched_df is not None:
    if st.button("📅 Exporter en CSV"):
        df_export = st.session_state.last_selected_enriched_df
        df_export.to_csv("data/output/geocoded_results_google.csv", index=False)
        st.success(f"📁 {len(df_export)} lignes exportées dans data/output/geocoded_results_google.csv")
