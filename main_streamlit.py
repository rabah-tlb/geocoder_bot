import streamlit as st
import pandas as pd
import math
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
        "mode": "Adresse complète",
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
        "mode": "Adresse complète",
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

    possible_fields = ['street', 'postal_code', 'city', 'country', 'governorate', 'name', 'complement']

    if "mapping_config" not in st.session_state:
        st.session_state.mapping_config = {
            "fields": {},
            "mode": "Adresse complète",
            "attribute_selected": None
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

    mode = st.radio("🎯 Mode de géocodage", ["Adresse complète", "Nom + Attribut (flexible)"],
                    index=0 if mapping_config.get("mode") == "Adresse complète" else 1,
                    key="geocode_mode")

    st.session_state.mapping_config["mode"] = mode

    selected_attr = None
    if mode == "Nom + Attribut (flexible)" and "name" in mapped_fields:
        optional_fields = ['street', 'postal_code', 'city', 'country', 'governorate', 'complement']
        attribute_options = [f for f in optional_fields if f in mapped_fields]

        if attribute_options:
            selected_attr = st.selectbox(
                "🧩 Choisir un champ à concaténer avec 'name'",
                options=attribute_options,
                index=attribute_options.index(mapping_config.get("attribute_selected"))
                if mapping_config.get("attribute_selected") in attribute_options else 0,
                key="concat_attr"
            )
            st.session_state.mapping_config["attribute_selected"] = selected_attr

    if st.button("➡️ Générer la colonne 'full_address'"):
        if mode == "Adresse complète":
            required_keys = ["street", "postal_code"]
            optional_keys = ["city", "country", "governorate", "complement"]

            if all(k in mapped_fields for k in required_keys):
                parts = [
                    st.session_state.df[mapped_fields["street"]].astype(str),
                    st.session_state.df[mapped_fields["postal_code"]].astype(str)
                ]
                for key in optional_keys:
                    if key in mapped_fields:
                        parts.append(st.session_state.df[mapped_fields[key]].astype(str))

                st.session_state.df["full_address"] = parts[0]
                for part in parts[1:]:
                    st.session_state.df["full_address"] += ", " + part

                st.success("✅ Colonne 'full_address' générée (adresse complète + champs optionnels) !")
            else:
                st.warning("⚠️ Tu dois mapper les champs : street, postal_code pour ce mode.")
        elif selected_attr and "name" in mapped_fields:
            st.session_state.df["full_address"] = (
                st.session_state.df[mapped_fields["name"]].astype(str) + ", " +
                st.session_state.df[mapped_fields[selected_attr]].astype(str)
            )
            st.success(f"✅ Colonne 'full_address' générée (nom + {selected_attr}) !")

    if "full_address" in st.session_state.df.columns:
        st.dataframe(st.session_state.df[["full_address"]].head())

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

    if st.button("🚀 Lancer le géocodage sur cette plage"):
        batch_results = []

        for i in range(nb_batches_to_run):
            start = i * batch_size
            end = min((i + 1) * batch_size, total_selected)
            batch_df = selected_df.iloc[start:end].copy()

            with st.spinner(f"🔄 Traitement du batch {i+1}/{nb_batches_to_run}..."):
                enriched_batch = geocode_dataframe(batch_df, address_column="full_address")
                batch_results.append(enriched_batch)
                st.success(f"✅ Batch {i+1} traité !")

        st.session_state.batch_results = batch_results

        selected_enriched_df = pd.concat(batch_results, ignore_index=True)
        st.session_state.last_selected_enriched_df = selected_enriched_df

        # Mise à jour uniquement des lignes concernées dans le enriched_df global
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
        st.markdown(f"### 📦 {len(batch_results)} batches traités")
        st.markdown(f"- Taille de batch : `{batch_size}` lignes")
        st.markdown(f"- Lignes traitées : `{len(enriched_df)}`")
        total_success = (enriched_df["status"] == "OK").sum()
        total_failed = len(enriched_df) - total_success
        rate = round(total_success / len(enriched_df) * 100, 2)
        st.markdown(f"- Succès : ✅ `{total_success}`")
        st.markdown(f"- Échecs : ❌ `{total_failed}`")
        st.markdown(f"- Taux de réussite global : **{rate}%**")
        st.dataframe(enriched_df)

    with tabs[1]:
        failed_df = enriched_df[enriched_df["status"] != "OK"]
        st.markdown(f"### ❌ Lignes échouées : {len(failed_df)}")
        st.dataframe(failed_df)

    for i, batch_df in enumerate(batch_results):
        with tabs[i + 2]:
            batch_success = (batch_df["status"] == "OK").sum()
            batch_failed = len(batch_df) - batch_success
            rate = round(batch_success / len(batch_df) * 100, 2)
            st.markdown(f"### 📦 Batch {i+1} – `{len(batch_df)}` lignes")
            st.markdown(f"- Succès : ✅ `{batch_success}`")
            st.markdown(f"- Échecs : ❌ `{batch_failed}`")
            st.markdown(f"- Taux de réussite : **{rate}%**")
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
                retried_df = geocode_dataframe(failed_df, address_column="full_address")

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

# ========== RELANCE DES ADRESSES INVALIDES ==========
if st.session_state.enriched_df is not None:
    enriched_df = st.session_state.last_selected_enriched_df
    invalid_df = enriched_df[(enriched_df["status"] == "OK") & (enriched_df["valid_address"] == False)]

    if not invalid_df.empty:
        st.warning(f"⚠️ {len(invalid_df)} lignes sont valides techniquement mais hors Tunisie.")

        if st.button("🔁 Relancer les adresses invalides (hors Tunisie)"):
            with st.spinner("🔄 Relance des lignes invalides (avec reformulation des adresses)..."):

                mapped_fields = st.session_state.get("mapping_config", {}).get("fields", {})

                def reformat_address(row):
                    parts = []
                    for field in ["street", "postal_code", "city", "governorate", "country", "complement"]:
                        if field in mapped_fields and mapped_fields[field] in row:
                            value = row[mapped_fields[field]]
                            if pd.notna(value):
                                parts.append(str(value))
                    return ", ".join(parts)

                invalid_df = invalid_df.copy()
                invalid_df["full_address"] = invalid_df.apply(reformat_address, axis=1)

                geo_cols = [
                    'latitude', 'longitude', 'formatted_address',
                    'status', 'error_message', 'api_used',
                    'precision_level', 'timestamp', 'valid_address'
                ]
                for col in geo_cols:
                    if col in invalid_df.columns:
                        invalid_df.drop(columns=[col], inplace=True)

                retried_invalid_df = geocode_dataframe(invalid_df, address_column="full_address")

                st.markdown("### ✅ Résultat des adresses relancées")
                st.dataframe(retried_invalid_df)

                if "id" not in enriched_df.columns or "id" not in retried_invalid_df.columns:
                    st.error("❌ Impossible de mettre à jour : colonne 'id' manquante.")
                else:
                    invalid_ids = retried_invalid_df["id"].unique()
                    enriched_df_cleaned = enriched_df[~enriched_df["id"].isin(invalid_ids)]

                    updated_df = pd.concat([enriched_df_cleaned, retried_invalid_df], ignore_index=True)
                    updated_df = updated_df.sort_values(by="id").reset_index(drop=True)

                    st.session_state.enriched_df = updated_df
                    st.session_state.last_selected_enriched_df = updated_df

                    st.success(f"✅ {len(retried_invalid_df)} lignes relancées et mises à jour.")

# ========== EXPORT ==========
if st.session_state.last_selected_enriched_df is not None:
    if st.button("📅 Exporter en CSV"):
        df_export = st.session_state.last_selected_enriched_df
        df_export.to_csv("data/output/geocoded_results_google.csv", index=False)
        st.success(f"📁 {len(df_export)} lignes exportées dans data/output/geocoded_results_google.csv")
