import streamlit as st
import pandas as pd
from src.geocoding import parallel_geocode_row
from datetime import datetime
from src.geocoding import parallel_geocode_row

def run_retry_page():
    st.subheader("🔁 Relance de géocodage sur un fichier existant")

    uploaded_retry_file = st.file_uploader("📂 Déposez un fichier déjà géocodé", type=["csv"])
    if uploaded_retry_file:
        df = pd.read_csv(uploaded_retry_file)
        st.session_state.last_selected_enriched_df = df
        st.session_state.enriched_df = df.copy()
        st.success("✅ Fichier chargé avec succès !")
        st.dataframe(df)
    else:
        st.warning("📭 Aucun fichier de relance sélectionné.")
        return

    df = st.session_state.last_selected_enriched_df
    if df is None or df.empty:
        st.error("❌ Le fichier est vide ou invalide.")
        return

    st.markdown("### 🎯 Critères de sélection pour relance")

    # Sélection des statuts
    available_status = df["status"].dropna().unique().tolist()
    default_status = [s for s in ["ERROR", "ZERO_RESULTS", "OVER_QUERY_LIMIT"] if s in available_status]
    status_filter = st.multiselect("📌 Statuts à relancer", options=available_status, default=default_status)

    # Sélection des niveaux de précision
    precision_options = df["precision_level"].dropna().unique().tolist()
    default_precisions = [p for p in ["APPROXIMATE"] if p in precision_options]
    precision_filter = st.multiselect("🎯 Niveaux de précision à relancer", options=precision_options, default=default_precisions)

    # Identifiant
    id_col = st.selectbox("🆔 Colonne identifiant unique (facultatif)", options=["-- Aucun --"] + list(df.columns))

    # === Filtrage combiné (union) ===
    df_filtered_status = df[df["status"].isin(status_filter)] if status_filter else pd.DataFrame()
    df_filtered_precision = df[df["precision_level"].isin(precision_filter)] if precision_filter else pd.DataFrame()
    df_combined = pd.concat([df_filtered_status, df_filtered_precision], ignore_index=True)

    # Déduplication
    dedup_key = "full_address"
    if id_col != "-- Aucun --" and id_col in df_combined.columns:
        dedup_key = id_col
    df_combined = df_combined.drop_duplicates(subset=dedup_key)

    st.info(f"🔎 {len(df_combined)} lignes sélectionnées pour relance.")

    # === Bouton de relance ===
    if st.button("🔁 Lancer la relance"):
        if df_combined.empty:
            st.error("❌ Aucun enregistrement ne correspond aux critères sélectionnés.")
            return

        # Nettoyage des anciennes colonnes
        geo_cols = [
            'latitude', 'longitude', 'formatted_address', 'address_reformtted',
            'status', 'error_message', 'api_used',
            'precision_level', 'timestamp'
        ]
        df_combined = df_combined.drop(columns=[col for col in geo_cols if col in df_combined.columns], errors="ignore")

        if "full_address" not in df_combined.columns:
            st.error("❌ La colonne 'full_address' est requise.")
            return

        st.markdown("### 🚀 Relance en cours...")

        # Progress bar
        progress_bar = st.progress(0)
        completed = [0]
        total = len(df_combined)

        def update_progress():
            completed[0] += 1
            progress_bar.progress(completed[0] / total)

        renamed_df = df_combined.rename(columns={v: k for k, v in st.session_state.mapping_config.get("fields", {}).items()})
        retried_df = parallel_geocode_row(renamed_df, address_column="full_address", max_workers=10, progress_callback=update_progress)

        # retried_df = parallel_geocode_row(renamed_df, address_column="full_address", max_workers=10, progress_callback=update_progress)
        st.success("✅ Géocodage terminé")

        # Affichage des résultats
        st.markdown("### 📈 Statistiques de la relance")
        col1, col2 = st.columns(2)

        with col1:
            total_success = (retried_df["status"] == "OK").sum()
            total_failed = len(retried_df) - total_success
            rate = round(total_success / len(retried_df) * 100, 2)
            st.markdown(f"- Lignes traitées : `{len(retried_df)}`")
            st.markdown(f"- Succès : ✅ `{total_success}`")
            st.markdown(f"- Échecs : ❌ `{total_failed}`")
            st.markdown(f"- Taux de réussite : **{rate}%**")

        with col2:
            if "precision_level" in retried_df.columns:
                st.markdown("#### 🎯 Précision :")
                precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
                precision_counts = retried_df["precision_level"].value_counts().to_dict()

                for level in precision_order:
                    if level in precision_counts:
                        st.markdown(f"- `{level}` : {precision_counts[level]}")

                for level, count in precision_counts.items():
                    if level not in precision_order:
                        st.markdown(f"- `{level}` : {count}")

        st.dataframe(retried_df)

        # Mise à jour
        if id_col != "-- Aucun --" and id_col in df.columns:
            failed_ids = retried_df[id_col].unique()
            enriched_df_cleaned = df[~df[id_col].isin(failed_ids)]
            updated_df = pd.concat([enriched_df_cleaned, retried_df], ignore_index=True)
            updated_df = updated_df.sort_values(by=id_col).reset_index(drop=True)
        else:
            updated_df = pd.concat([df, retried_df], ignore_index=True).drop_duplicates(subset=["full_address"], keep="last")

        st.session_state.enriched_df = updated_df
        st.session_state.last_selected_enriched_df = updated_df
        st.success("📦 Mise à jour de l'enriched_df terminée avec succès.")
