import streamlit as st
import pandas as pd
from src.geocoding_retry import retry_geocode_row
from datetime import datetime


def initialize_retry_state():
    """Initialise les variables de session pour la persistance."""
    if 'retry_df' not in st.session_state:
        st.session_state.retry_df = None
    if 'retry_filename' not in st.session_state:
        st.session_state.retry_filename = None
    if 'retry_results' not in st.session_state:
        st.session_state.retry_results = None
    if 'retry_updated_df' not in st.session_state:
        st.session_state.retry_updated_df = None


def render_file_upload():
    """Section de chargement de fichier avec persistance."""
    with st.expander("📂 Chargement du fichier", expanded=(st.session_state.retry_df is None)):
        uploaded_retry_file = st.file_uploader(
            "Déposez un fichier déjà géocodé (CSV)", 
            type=["csv"],
            key="retry_file_uploader"
        )
        
        # Si aucun fichier uploadé mais il y a un fichier en mémoire
        if uploaded_retry_file is None:
            if st.session_state.retry_df is not None:
                st.info(f"📂 Fichier en mémoire: **{st.session_state.retry_filename}** ({len(st.session_state.retry_df):,} lignes)")
                
                # Afficher les métriques même sans upload
                df = st.session_state.retry_df
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Lignes totales", f"{len(df):,}")
                with col2:
                    if "status" in df.columns:
                        failed = (df["status"] != "OK").sum()
                        st.metric("❌ Échecs", f"{failed:,}")
                with col3:
                    if "precision_level" in df.columns:
                        approx = (df["precision_level"] == "APPROXIMATE").sum()
                        st.metric("🎯 APPROXIMATE", f"{approx:,}")
                
                st.dataframe(df.head(5), use_container_width=True)
                return True  # ✅ CONTINUER même sans upload
            else:
                st.warning("📭 Aucun fichier de relance sélectionné.")
                return False
        
        current_filename = uploaded_retry_file.name
        
        # Charger uniquement si nouveau fichier
        if current_filename != st.session_state.retry_filename:
            try:
                df = pd.read_csv(uploaded_retry_file)
                st.session_state.retry_df = df
                st.session_state.retry_filename = current_filename
                st.session_state.last_selected_enriched_df = df
                st.session_state.enriched_df = df.copy()
                st.session_state.retry_results = None  # Reset résultats
                st.success(f"✅ Fichier **{current_filename}** chargé avec succès !")
                
                # Aperçu compact
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Lignes totales", f"{len(df):,}")
                with col2:
                    if "status" in df.columns:
                        failed = (df["status"] != "OK").sum()
                        st.metric("❌ Échecs", f"{failed:,}")
                with col3:
                    if "precision_level" in df.columns:
                        approx = (df["precision_level"] == "APPROXIMATE").sum()
                        st.metric("🎯 APPROXIMATE", f"{approx:,}")
                
                st.dataframe(df.head(5), use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Erreur de lecture: {e}")
                return False
        else:
            st.success(f"✅ Fichier **{current_filename}** déjà chargé.")
            
            # Afficher métriques
            df = st.session_state.retry_df
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Lignes totales", f"{len(df):,}")
            with col2:
                if "status" in df.columns:
                    failed = (df["status"] != "OK").sum()
                    st.metric("❌ Échecs", f"{failed:,}")
            with col3:
                if "precision_level" in df.columns:
                    approx = (df["precision_level"] == "APPROXIMATE").sum()
                    st.metric("🎯 APPROXIMATE", f"{approx:,}")
    
    return True


def render_filters():
    """Section de filtres de sélection."""
    df = st.session_state.retry_df
    
    if df is None or df.empty:
        st.error("❌ Le fichier est vide ou invalide.")
        return None
    
    with st.expander("🎯 Critères de Sélection", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📌 Statuts à relancer")
            available_status = df["status"].dropna().unique().tolist() if "status" in df.columns else []
            default_status = [s for s in ["ERROR", "ZERO_RESULTS", "OVER_QUERY_LIMIT"] if s in available_status]
            status_filter = st.multiselect(
                "Sélectionnez les statuts",
                options=available_status,
                default=default_status,
                key="status_filter",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("##### 🎯 Précisions à améliorer")
            precision_options = df["precision_level"].dropna().unique().tolist() if "precision_level" in df.columns else []
            default_precisions = [p for p in ["APPROXIMATE", "GEOMETRIC_CENTER"] if p in precision_options]
            precision_filter = st.multiselect(
                "Sélectionnez les précisions",
                options=precision_options,
                default=default_precisions,
                key="precision_filter",
                help="Niveaux de précision à améliorer",
                label_visibility="collapsed"
            )
        
        # Identifiant unique
        st.markdown("##### 🆔 Colonne identifiant")
        id_col = st.selectbox(
            "Colonne pour déduplication",
            options=["-- Aucun --"] + list(df.columns),
            key="id_col",
            label_visibility="collapsed"
        )
        
        # Appliquer les filtres
        df_filtered_status = df[df["status"].isin(status_filter)] if status_filter and "status" in df.columns else pd.DataFrame()
        df_filtered_precision = df[df["precision_level"].isin(precision_filter)] if precision_filter and "precision_level" in df.columns else pd.DataFrame()
        df_combined = pd.concat([df_filtered_status, df_filtered_precision], ignore_index=True)
        
        # Déduplication
        dedup_key = "full_address"
        if id_col != "-- Aucun --" and id_col in df_combined.columns:
            dedup_key = id_col
        
        if not df_combined.empty:
            df_combined = df_combined.drop_duplicates(subset=dedup_key)
        
        # Afficher le nombre de lignes sélectionnées
        st.success(f"🔎 **{len(df_combined):,} lignes** sélectionnées pour relance")
        
        # Aperçu des lignes
        if not df_combined.empty and len(df_combined) > 0:
            with st.expander("👀 Aperçu des lignes sélectionnées", expanded=False):
                display_cols = ["full_address", "status", "precision_level", "api_used"]
                available_cols = [col for col in display_cols if col in df_combined.columns]
                st.dataframe(df_combined[available_cols].head(20), use_container_width=True)
        
        return df_combined, id_col


def render_retry_config():
    """Section de configuration de la relance."""
    with st.expander("🔧 Configuration de la Relance", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🎯 Objectif de précision")
            target_precision = st.radio(
                "Niveau cible",
                options=["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER"],
                index=0,
                key="target_precision",
                help="Niveau de précision à atteindre au minimum",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("##### 🧠 Stratégie")
            st.info("""
            **Relance intelligente activée**
            
            ✅ Toutes les APIs testées
            ✅ Variantes d'adresse générées
            ✅ Meilleur résultat retourné
            ✅ APIs déjà testées évitées
            """)
        
        return target_precision


def render_retry_button(df_combined, id_col):
    """Bouton de lancement de la relance."""
    if df_combined is None or df_combined.empty:
        st.warning("⚠️ Aucune ligne sélectionnée. Ajustez les filtres.")
        return
    
    if st.button("🚀 Lancer la Relance Intelligente", type="primary", use_container_width=True):
        launch_retry(df_combined, id_col)


def launch_retry(df_combined, id_col):
    """Lance la relance intelligente."""
    # Nettoyage des colonnes
    geo_cols_to_clean = [
        'latitude', 'longitude', 'formatted_address', 'address_reformatted',
        'status', 'error_message', 'api_used',
        'precision_level', 'timestamp', 'address_variant', 'improved'
    ]
    df_combined = df_combined.drop(
        columns=[col for col in geo_cols_to_clean if col in df_combined.columns],
        errors="ignore"
    )
    
    if "full_address" not in df_combined.columns:
        st.error("❌ La colonne 'full_address' est requise.")
        return
    
    # Progress bar
    st.markdown("### 🚀 Relance en cours...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    completed = [0]
    total = len(df_combined)
    
    def update_progress():
        completed[0] += 1
        progress_bar.progress(completed[0] / total)
        status_text.text(f"Traitement: {completed[0]}/{total} lignes...")
    
    # Lancement
    with st.spinner("🔄 Géocodage en cours..."):
        retried_df = retry_geocode_row(
            df_combined,
            address_column="full_address",
            max_workers=10,
            progress_callback=update_progress
        )
    
    st.session_state.retry_results = retried_df
    st.success("✅ Géocodage terminé !")
    
    # Mise à jour du dataframe principal
    df = st.session_state.retry_df
    if id_col != "-- Aucun --" and id_col in df.columns and id_col in retried_df.columns:
        failed_ids = retried_df[id_col].unique()
        enriched_df_cleaned = df[~df[id_col].isin(failed_ids)]
        updated_df = pd.concat([enriched_df_cleaned, retried_df], ignore_index=True)
        updated_df = updated_df.sort_values(by=id_col).reset_index(drop=True)
    else:
        updated_df = pd.concat([df, retried_df], ignore_index=True).drop_duplicates(
            subset=["full_address"],
            keep="last"
        )
    
    st.session_state.retry_updated_df = updated_df
    st.session_state.enriched_df = updated_df
    st.session_state.last_selected_enriched_df = updated_df


def render_results():
    """Section d'affichage des résultats."""
    if st.session_state.retry_results is None:
        return
    
    retried_df = st.session_state.retry_results
    
    with st.expander("📊 Résultats de la Relance", expanded=True):
        # Métriques principales
        total_success = (retried_df["status"] == "OK").sum()
        total_failed = len(retried_df) - total_success
        success_rate = round(total_success / len(retried_df) * 100, 1) if len(retried_df) > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Traitées", f"{len(retried_df):,}")
        
        with col2:
            st.metric("✅ Succès", f"{total_success:,}", delta=f"{success_rate}%")
        
        with col3:
            st.metric("❌ Échecs", f"{total_failed:,}", delta=f"{100-success_rate:.1f}%", delta_color="inverse")
        
        with col4:
            if "improved" in retried_df.columns:
                improved = retried_df["improved"].sum() if retried_df["improved"].dtype == bool else 0
                st.metric("🎉 Améliorées", f"{improved:,}")
        
        # Détails
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("##### 🎯 Précision")
            if "precision_level" in retried_df.columns:
                precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
                precision_counts = retried_df["precision_level"].value_counts().to_dict()
                
                for level in precision_order:
                    if level in precision_counts:
                        icon = "🎯" if level == "ROOFTOP" else "📍" if level == "RANGE_INTERPOLATED" else "📌"
                        pct = round(precision_counts[level] / total_success * 100, 1) if total_success > 0 else 0
                        st.markdown(f"{icon} `{level}`: **{precision_counts[level]}** ({pct}%)")
        
        with col_right:
            st.markdown("##### 🔌 APIs")
            if "api_used" in retried_df.columns:
                api_counts = retried_df["api_used"].value_counts().to_dict()
                
                for api, count in api_counts.items():
                    icon = "🗺️" if api == "here" else "🌍" if api == "google" else "🌐" if api == "osm" else "❓"
                    pct = round(count / len(retried_df) * 100, 1)
                    st.markdown(f"{icon} `{api}`: **{count}** ({pct}%)")
        
        # Tabs pour les résultats
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["📋 Tous", "✅ Succès", "❌ Échecs"])
        
        with tab1:
            st.dataframe(retried_df, use_container_width=True, height=400)
        
        with tab2:
            success_df = retried_df[retried_df["status"] == "OK"]
            st.markdown(f"**{len(success_df):,} lignes géocodées avec succès**")
            if not success_df.empty:
                st.dataframe(success_df, use_container_width=True, height=400)
        
        with tab3:
            failed_df = retried_df[retried_df["status"] != "OK"]
            st.markdown(f"**{len(failed_df):,} lignes en échec**")
            if not failed_df.empty:
                st.dataframe(failed_df, use_container_width=True, height=400)
            else:
                st.success("🎉 Aucun échec !")


def render_export():
    """Section d'export des résultats."""
    if st.session_state.retry_results is None:
        return
    
    with st.expander("📥 Export des Résultats", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📄 Résultats de la relance")
            csv_retry = st.session_state.retry_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Télécharger CSV (relance)",
                data=csv_retry,
                file_name=f"retry_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            if st.session_state.retry_updated_df is not None:
                st.markdown("##### 📦 Fichier complet mis à jour")
                csv_full = st.session_state.retry_updated_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Télécharger CSV (complet)",
                    data=csv_full,
                    file_name=f"complete_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )


def run_retry_page():
    """Point d'entrée principal de la page."""
    initialize_retry_state()
    
    st.subheader("🔁 Relance Intelligente de Géocodage")
    
    # Indicateur de fichier chargé (toujours visible si fichier existe)
    if st.session_state.retry_df is not None:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.success(f"📂 **{st.session_state.retry_filename}** | {len(st.session_state.retry_df):,} lignes")
        with col2:
            if st.session_state.retry_results is not None:
                success = (st.session_state.retry_results["status"] == "OK").sum()
                st.info(f"✅ {success:,} améliorées")
        with col3:
            if st.session_state.retry_df is not None:
                failed = (st.session_state.retry_df["status"] != "OK").sum()
                st.warning(f"❌ {failed:,} échecs")
    
    # Sections - CONTINUER même si fichier en mémoire
    file_loaded = render_file_upload()
    
    # Arrêter seulement si vraiment aucun fichier
    if not file_loaded:
        return
    
    # ✅ Continuer avec les filtres même si fichier déjà en mémoire
    filter_result = render_filters()
    if filter_result is None:
        return
    
    df_combined, id_col = filter_result
    
    render_retry_config()
    render_retry_button(df_combined, id_col)
    render_results()
    render_export()