import streamlit as st
import pandas as pd
import math
from datetime import datetime
from src.utils import export_job_history_to_pdf, export_enriched_results
from src.ingestion import read_file
from src.geocoding import (
    parallel_geocode_row,
    create_job_entry,
    finalize_job
)


def initialize_session_state():
    """Initialise les variables de session pour la persistance."""
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'enriched_df' not in st.session_state:
        st.session_state.enriched_df = None
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    if 'last_selected_enriched_df' not in st.session_state:
        st.session_state.last_selected_enriched_df = None
    if 'mapping_config' not in st.session_state:
        st.session_state.mapping_config = {"fields": {}}
    if 'job_history' not in st.session_state:
        st.session_state.job_history = []
    if 'geocoding_mode' not in st.session_state:
        st.session_state.geocoding_mode = "HERE uniquement"
    if 'previous_filename' not in st.session_state:
        st.session_state.previous_filename = None


def render_file_upload_section():
    """Section de chargement de fichier."""
    with st.expander("📂 Chargement du fichier", expanded=(st.session_state.df is None)):
        uploaded_file = st.file_uploader(
            "Déposez un fichier CSV ou TXT", 
            type=["csv", "txt"],
            key="file_uploader"
        )
        
        if uploaded_file is None:
            if st.session_state.df is not None:
                st.info("📂 Fichier précédent toujours en mémoire. Chargez un nouveau fichier pour le remplacer.")
                df = st.session_state.df
                
                st.dataframe(df.head(10), use_container_width=True)
                return True  # ✅ CONTINUER même sans upload
            else:
                st.warning("📭 Aucun fichier chargé. Veuillez charger un fichier pour commencer.")
                
            return
        
        current_filename = uploaded_file.name
        previous_filename = st.session_state.get("previous_filename")
        
        # Réinitialiser uniquement si nouveau fichier
        if current_filename != previous_filename:
            df = read_file(uploaded_file, sep=None)
            if not df.empty:
                st.session_state.df = df
                st.session_state.enriched_df = None
                st.session_state.batch_results = []
                st.session_state.last_selected_enriched_df = None
                st.session_state.previous_filename = current_filename
                st.success(f"✅ Fichier **{current_filename}** chargé avec succès !")
                st.dataframe(df.head(10), use_container_width=True)
            else:
                st.error("❌ Erreur de lecture du fichier.")
        else:
            st.success(f"✅ Fichier **{current_filename}** déjà chargé.")
            st.dataframe(st.session_state.df.head(10), use_container_width=True)


def render_mapping_section():
    """Section de mapping des colonnes."""
    if st.session_state.df is None:
        return
    
    df = st.session_state.df
    
    with st.expander("🧩 Mapping des Colonnes", expanded=("full_address" not in df.columns)):
        st.markdown("Mappez les colonnes de votre fichier aux champs requis :")
        
        possible_fields = ['name', 'street', 'postal_code', 'city', 'governorate', 'country', 'complement']
        mapping_config = st.session_state.mapping_config
        
        # Layout en colonnes pour un mapping compact
        col1, col2 = st.columns(2)
        current_mapping = {}
        
        for idx, field in enumerate(possible_fields):
            col = col1 if idx % 2 == 0 else col2
            with col:
                current_value = mapping_config.get("fields", {}).get(field, "-- Aucun --")
                current_mapping[field] = st.selectbox(
                    f"📌 {field.replace('_', ' ').title()}",
                    options=["-- Aucun --"] + list(df.columns),
                    index=(["-- Aucun --"] + list(df.columns)).index(current_value) 
                        if current_value in (["-- Aucun --"] + list(df.columns)) else 0,
                    key=f"mapping_{field}"
                )
        
        mapped_fields = {k: v for k, v in current_mapping.items() if v != "-- Aucun --"}
        st.session_state.mapping_config["fields"] = mapped_fields
        
        if st.button("✅ Valider le mapping", use_container_width=True):
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
                    
                    st.session_state.df = df
                    st.success("✅ Colonne 'full_address' générée !")
                    st.dataframe(df[["full_address"]].head(10), use_container_width=True)
                else:
                    st.warning("⚠️ Aucun champ mappé.")
            else:
                st.warning("⚠️ Veuillez mapper au moins un champ.")


def render_geocoding_section():
    """Section de géocodage par batch."""
    if st.session_state.df is None or "full_address" not in st.session_state.df.columns:
        return
    
    with st.expander("📍 Configuration du Géocodage", expanded=True):
        df = st.session_state.df
        total_rows = len(df)
        
        # Métriques compactes
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Total lignes", f"{total_rows:,}")
        with col2:
            start_line = st.number_input("Début", min_value=0, max_value=total_rows-1, value=0, key="start_line")
        with col3:
            end_line = st.number_input("Fin", min_value=start_line+1, max_value=total_rows, 
                                       value=min(start_line+1000, total_rows), key="end_line")
        with col4:
            batch_size = st.number_input("Taille batch", min_value=10, max_value=10000, 
                                        value=1000, step=100, key="batch_size")
        
        selected_df = df.iloc[start_line:end_line].copy()
        total_selected = len(selected_df)
        total_batches = math.ceil(total_selected / batch_size)
        
        col_a, col_b = st.columns(2)
        with col_a:
            nb_batches = st.number_input("Nombre de batches", min_value=1, max_value=total_batches, 
                                        value=min(total_batches, total_batches), key="nb_batches")
        with col_b:
            actual_rows = min(nb_batches * batch_size, total_selected)
            st.info(f"📊 **{actual_rows:,} lignes** sur {nb_batches} batch(es)")
        
        # Mode de géocodage
        st.markdown("### 🔧 Mode de Géocodage")
        geocoding_mode = st.radio(
            "Sélectionnez l'API :",
            options=[
                "HERE uniquement",
                "Google uniquement",
                "OSM uniquement",
                "Multi-API (HERE → Google → OSM)"
            ],
            index=0,
            key="geocoding_mode_main",
            horizontal=True
        )
        st.session_state.geocoding_mode = geocoding_mode
        
        # Bouton de lancement
        if st.button("🚀 Lancer le Géocodage", type="primary", use_container_width=True):
            launch_geocoding(selected_df, nb_batches, batch_size, geocoding_mode)


def launch_geocoding(selected_df, nb_batches, batch_size, geocoding_mode):
    """Lance le processus de géocodage."""
    mapped_fields = st.session_state.mapping_config.get("fields", {})
    batch_results = []
    
    job_id = f"JOB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    actual_rows = min(nb_batches * batch_size, len(selected_df))
    job = create_job_entry(job_id, total_rows=actual_rows)
    
    # Conteneur pour les résultats en temps réel
    result_container = st.container()
    
    with result_container:
        st.markdown(f"### 🔄 Géocodage en cours - Mode: `{geocoding_mode}`")
        
        overall_progress = st.progress(0)
        status_placeholder = st.empty()
        
        # Déterminer le mode API
        api_mode_map = {
            "HERE uniquement": "here",
            "Google uniquement": "google",
            "OSM uniquement": "osm",
            "Multi-API (HERE → Google → OSM)": "multi"
        }
        api_mode = api_mode_map.get(geocoding_mode, "here")
        
        for i in range(nb_batches):
            start = i * batch_size
            end = min((i + 1) * batch_size, len(selected_df))
            batch_df = selected_df.iloc[start:end].copy()
            
            status_placeholder.info(f"📦 Traitement du batch {i+1}/{nb_batches} ({len(batch_df)} lignes)...")
            
            # Progress bar pour ce batch
            batch_progress_bar = st.progress(0)
            completed = [0]
            total = len(batch_df)
            
            def update_progress():
                completed[0] += 1
                batch_progress_bar.progress(completed[0] / total)
            
            # Géocodage
            renamed_df = batch_df.rename(columns={v: k for k, v in mapped_fields.items()})
            enriched_batch = parallel_geocode_row(
                renamed_df,
                address_column="full_address",
                max_workers=10,
                progress_callback=update_progress,
                api_mode=api_mode
            )
            
            batch_results.append(enriched_batch)
            
            # Mise à jour de la progression globale
            overall_progress.progress((i + 1) / nb_batches)
            
            # Stats rapides
            success_count = (enriched_batch["status"] == "OK").sum()
            rate = round(success_count / len(enriched_batch) * 100, 1)
            status_placeholder.success(f"✅ Batch {i+1} terminé : {success_count}/{len(enriched_batch)} succès ({rate}%)")
        
        # Finalisation
        st.session_state.batch_results = batch_results
        selected_enriched_df = pd.concat(batch_results, ignore_index=True)
        st.session_state.last_selected_enriched_df = selected_enriched_df
        
        job = finalize_job(job, selected_enriched_df)
        st.session_state.job_history.append(job)
        
        # Mise à jour du enriched_df
        if st.session_state.enriched_df is None:
            st.session_state.enriched_df = st.session_state.df.copy()
        
        for _, row in selected_enriched_df.iterrows():
            row_index = row.get("row_index")
            if row_index is not None:
                for col in selected_enriched_df.columns:
                    if col != "row_index":
                        if col not in st.session_state.enriched_df.columns:
                            st.session_state.enriched_df[col] = None
                        st.session_state.enriched_df.at[row_index, col] = row[col]
        
        st.success(f"🎉 Géocodage terminé ! {len(selected_enriched_df)} lignes traitées.")


def render_results_section():
    """Section d'affichage des résultats."""
    if not st.session_state.batch_results:
        return
    
    enriched_df = st.session_state.last_selected_enriched_df
    
    with st.expander("📊 Résultats du Géocodage", expanded=True):
        # Métriques principales
        total_success = (enriched_df["status"] == "OK").sum()
        total_failed = len(enriched_df) - total_success
        success_rate = round(total_success / len(enriched_df) * 100, 1) if len(enriched_df) > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📄 Total", f"{len(enriched_df):,}")
        with col2:
            st.metric("✅ Succès", f"{total_success:,}", delta=f"{success_rate}%")
        with col3:
            st.metric("❌ Échecs", f"{total_failed:,}", delta=f"{100-success_rate:.1f}%", delta_color="inverse")
        with col4:
            if "precision_level" in enriched_df.columns:
                rooftop = (enriched_df["precision_level"] == "ROOFTOP").sum()
                rooftop_rate = round(rooftop / total_success * 100, 1) if total_success > 0 else 0
                st.metric("🎯 ROOFTOP", f"{rooftop:,}", delta=f"{rooftop_rate}%")
        
        # Tabs pour différentes vues
        tab1, tab2, tab3 = st.tabs(["📋 Tous les résultats", "✅ Succès", "❌ Échecs"])
        
        with tab1:
            # Statistiques détaillées
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 🎯 Précision")
                if "precision_level" in enriched_df.columns:
                    precision_counts = enriched_df["precision_level"].value_counts()
                    for level, count in precision_counts.items():
                        if pd.notna(level):
                            pct = round(count / total_success * 100, 1) if total_success > 0 else 0
                            st.markdown(f"• `{level}`: **{count}** ({pct}%)")
            
            with col_right:
                st.markdown("#### 🔌 APIs")
                if "api_used" in enriched_df.columns:
                    api_counts = enriched_df["api_used"].value_counts()
                    for api, count in api_counts.items():
                        pct = round(count / len(enriched_df) * 100, 1)
                        st.markdown(f"• `{api}`: **{count}** ({pct}%)")
            
            st.dataframe(enriched_df, use_container_width=True, height=400)
        
        with tab2:
            success_df = enriched_df[enriched_df["status"] == "OK"]
            st.markdown(f"**{len(success_df)} lignes géocodées avec succès**")
            st.dataframe(success_df, use_container_width=True, height=400)
        
        with tab3:
            failed_df = enriched_df[enriched_df["status"] != "OK"]
            st.markdown(f"**{len(failed_df)} lignes en échec**")
            if not failed_df.empty:
                st.dataframe(failed_df, use_container_width=True, height=400)
            else:
                st.success("🎉 Aucun échec !")


def render_retry_section():
    """Section de relance des échecs."""
    if st.session_state.last_selected_enriched_df is None:
        return
    
    enriched_df = st.session_state.last_selected_enriched_df
    failed_df = enriched_df[enriched_df["status"] != "OK"]
    
    if failed_df.empty:
        return
    
    with st.expander(f"🔁 Relancer les Échecs ({len(failed_df)} lignes)", expanded=False):
        st.warning(f"⚠️ {len(failed_df)} lignes ont échoué.")
        
        # Mode de relance
        retry_mode = st.radio(
            "Mode de géocodage pour la relance :",
            options=[
                "Multi-API (HERE → Google → OSM)",
                "HERE uniquement",
                "Google uniquement",
                "OSM uniquement"
            ],
            index=0,
            key="retry_mode",
            horizontal=True
        )
        
        if st.button("🔄 Relancer les échecs", type="primary", use_container_width=True):
            with st.spinner(f"🔄 Relance avec {retry_mode}..."):
                # Préparation
                mapped_fields = st.session_state.mapping_config.get("fields", {})
                
                def reformat_address(row):
                    parts = []
                    for field in ["street", "postal_code", "city", "governorate", "country", "complement"]:
                        if field in mapped_fields and mapped_fields[field] in row:
                            value = row[mapped_fields[field]]
                            if pd.notna(value):
                                parts.append(str(value))
                    return ", ".join(parts)
                
                failed_df = failed_df.copy()
                failed_df["full_address"] = failed_df.apply(reformat_address, axis=1)
                
                # Nettoyage
                geo_cols = ['latitude', 'longitude', 'formatted_address', 'status', 
                           'error_message', 'api_used', 'precision_level', 'timestamp']
                for col in geo_cols:
                    if col in failed_df.columns:
                        failed_df.drop(columns=[col], inplace=True)
                
                # Déterminer le mode API
                api_mode_map = {
                    "Multi-API (HERE → Google → OSM)": "multi",
                    "HERE uniquement": "here",
                    "Google uniquement": "google",
                    "OSM uniquement": "osm"
                }
                api_mode = api_mode_map.get(retry_mode, "multi")
                
                # Re-géocodage
                renamed_df = failed_df.rename(columns={v: k for k, v in mapped_fields.items()})
                retried_df = parallel_geocode_row(
                    renamed_df,
                    address_column="full_address",
                    max_workers=10,
                    api_mode=api_mode
                )
                
                # Stats
                retry_success = (retried_df["status"] == "OK").sum()
                retry_rate = round(retry_success / len(retried_df) * 100, 1)
                
                st.success(f"✅ Relance terminée : {retry_success}/{len(retried_df)} succès ({retry_rate}%)")
                st.dataframe(retried_df, use_container_width=True)
                
                # Mise à jour
                st.session_state.last_selected_enriched_df = pd.concat(
                    [enriched_df[enriched_df["status"] == "OK"], retried_df],
                    ignore_index=True
                )


def render_export_section():
    """Section d'export."""
    if st.session_state.last_selected_enriched_df is None:
        return
    
    with st.expander("📥 Exporter les Résultats", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_format = st.selectbox("Format", ["csv", "json", "txt"], key="export_format")
        
        with col2:
            sep = st.text_input("Séparateur", value=",", key="export_sep")
        
        with col3:
            if export_format == "json":
                line_delimited = st.checkbox("JSON ligne par ligne", value=False, key="line_delimited")
            else:
                line_delimited = False
        
        if st.button("📄 Générer et télécharger", type="primary", use_container_width=True):
            df_export = st.session_state.last_selected_enriched_df
            file_path = export_enriched_results(
                df_export, 
                export_format=export_format, 
                sep=sep, 
                line_delimited_json=line_delimited
            )
            
            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"💾 Télécharger {export_format.upper()}",
                    data=file,
                    file_name=file_path.split("/")[-1],
                    mime="text/plain" if export_format == "txt" else 
                         "application/json" if export_format == "json" else "text/csv",
                    use_container_width=True
                )


def render_history_section():
    """Section d'historique des jobs."""
    if not st.session_state.job_history:
        return
    
    with st.expander("📜 Historique des Jobs", expanded=False):
        # Tableau récapitulatif
        df_jobs = pd.DataFrame([
            {
                "Job ID": job["job_id"],
                "Lignes": job["total_rows"],
                "Succès": job["success"],
                "Échecs": job["failed"],
                "Taux": f"{round(job['success']/job['total_rows']*100, 1)}%",
                "Statut": job["status"]
            }
            for job in st.session_state.job_history
        ])
        st.dataframe(df_jobs, use_container_width=True)
        
        # Bouton de téléchargement PDF
        if st.button("📥 Télécharger l'historique PDF", use_container_width=True):
            pdf_path = export_job_history_to_pdf(st.session_state.job_history)
            with open(pdf_path, "rb") as file:
                st.download_button(
                    label="📄 Télécharger PDF",
                    data=file,
                    file_name="historique_jobs.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        # Détails des jobs
        for job in reversed(st.session_state.job_history[-5:]):  # Limiter aux 5 derniers
            with st.expander(f"🔹 {job['job_id']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"🕒 Début: {job['start_time']}")
                    st.write(f"🏁 Fin: {job['end_time']}")
                with col2:
                    st.write(f"📄 Total: {job['total_rows']}")
                    st.write(f"✅ Succès: {job['success']}")
                
                if "precision_counts" in job and job["precision_counts"]:
                    st.write("🎯 Précisions:", job["precision_counts"])
                
                st.dataframe(job["details_df"].head(5), use_container_width=True)


def run_geocoding_page():
    """Point d'entrée principal de la page."""
    initialize_session_state()
    
    st.subheader("📍 Géocodage Multi-API")
    
    # Indicateur de fichier chargé
    if st.session_state.df is not None:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.success(f"📂 **{st.session_state.previous_filename}** | {len(st.session_state.df):,} lignes")
        with col2:
            if st.session_state.last_selected_enriched_df is not None:
                success = (st.session_state.last_selected_enriched_df["status"] == "OK").sum()
                st.info(f"✅ {success:,} géocodées")
        with col3:
            if st.session_state.job_history:
                st.info(f"📜 {len(st.session_state.job_history)} jobs")
    
    # Sections dans l'ordre
    render_file_upload_section()
    render_mapping_section()
    render_geocoding_section()
    render_results_section()
    render_retry_section()
    render_export_section()
    render_history_section()