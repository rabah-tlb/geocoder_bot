import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
from custom_style import apply_custom_style  # Import du style

# Appliquer le style
apply_custom_style()

# Configuration du style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 10)


def initialize_analytics_state():
    """Initialise les variables de session pour la persistance."""
    if 'analytics_df' not in st.session_state:
        st.session_state.analytics_df = None
    if 'analytics_filename' not in st.session_state:
        st.session_state.analytics_filename = None
    if 'analytics_fig' not in st.session_state:
        st.session_state.analytics_fig = None


def create_analytics_plots(df):
    """
    Crée une figure avec 4 subplots pour l'analyse des résultats.
    
    Returns:
        fig: Figure matplotlib avec les 4 graphiques
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('📊 Analyse des Résultats de Géocodage', fontsize=16, fontweight='bold')
    
    # 1. Camembert des statuts (en haut à gauche)
    status_counts = df["status"].value_counts()
    colors_status = ['#28a745', '#dc3545', '#ffc107', '#6c757d']
    axes[0, 0].pie(
        status_counts, 
        labels=status_counts.index, 
        autopct='%1.1f%%', 
        startangle=90,
        colors=colors_status[:len(status_counts)]
    )
    axes[0, 0].set_title('Distribution des Statuts', fontsize=12, fontweight='bold')
    
    # 2. Bar chart des niveaux de précision (en haut à droite)
    precision_counts = df["precision_level"].value_counts()
    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
    precision_sorted = precision_counts.reindex([p for p in precision_order if p in precision_counts.index], fill_value=0)
    
    colors_precision = ['#28a745', '#17a2b8', '#ffc107', '#dc3545']
    bars = axes[0, 1].bar(
        range(len(precision_sorted)), 
        precision_sorted.values,
        color=colors_precision[:len(precision_sorted)]
    )
    axes[0, 1].set_xticks(range(len(precision_sorted)))
    axes[0, 1].set_xticklabels(precision_sorted.index, rotation=45, ha='right')
    axes[0, 1].set_ylabel('Nombre de lignes', fontsize=10)
    axes[0, 1].set_title('Niveaux de Précision', fontsize=12, fontweight='bold')
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Ajouter les valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            axes[0, 1].text(
                bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=9
            )
    
    # 3. APIs utilisées (en bas à gauche)
    if "api_used" in df.columns:
        api_counts = df["api_used"].value_counts()
        colors_api = ['#007bff', '#28a745', '#17a2b8', '#6c757d']
        bars_api = axes[1, 0].barh(
            range(len(api_counts)), 
            api_counts.values,
            color=colors_api[:len(api_counts)]
        )
        axes[1, 0].set_yticks(range(len(api_counts)))
        axes[1, 0].set_yticklabels(api_counts.index)
        axes[1, 0].set_xlabel('Nombre de lignes', fontsize=10)
        axes[1, 0].set_title('Répartition par API', fontsize=12, fontweight='bold')
        axes[1, 0].grid(axis='x', alpha=0.3)
        
        # Ajouter les valeurs
        for i, bar in enumerate(bars_api):
            width = bar.get_width()
            if width > 0:
                axes[1, 0].text(
                    width, bar.get_y() + bar.get_height()/2.,
                    f' {int(width)}',
                    ha='left', va='center', fontsize=9
                )
    else:
        axes[1, 0].text(0.5, 0.5, 'API non disponible', 
                       ha='center', va='center', fontsize=12)
        axes[1, 0].set_xlim(0, 1)
        axes[1, 0].set_ylim(0, 1)
        axes[1, 0].axis('off')
    
    # 4. Taux de succès (en bas à droite)
    total_rows = len(df)
    total_success = (df["status"] == "OK").sum()
    total_failed = total_rows - total_success
    success_rate = (total_success / total_rows) * 100 if total_rows > 0 else 0
    
    # Graphique en anneau (donut)
    sizes = [total_success, total_failed]
    labels = ['Succès', 'Échecs']
    colors_donut = ['#28a745', '#dc3545']
    
    wedges, texts, autotexts = axes[1, 1].pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_donut,
        wedgeprops=dict(width=0.5)
    )
    
    # Ajouter le taux au centre
    axes[1, 1].text(0, 0, f'{success_rate:.1f}%\nRéussite', 
                   ha='center', va='center', fontsize=14, fontweight='bold')
    axes[1, 1].set_title('Taux de Réussite Global', fontsize=12, fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    return fig


def generate_pdf_report(df, fig, stats):
    """
    Génère un rapport PDF avec statistiques et graphiques.
    
    Args:
        df: DataFrame avec les données
        fig: Figure matplotlib avec les graphiques
        stats: Dictionnaire avec les statistiques
    
    Returns:
        BytesIO: Buffer contenant le PDF
    """
    buffer = BytesIO()
    
    with PdfPages(buffer) as pdf:
        # Page 1 : Graphiques
        pdf.savefig(fig, bbox_inches='tight')
        
        # Page 2 : Statistiques détaillées
        fig_stats = plt.figure(figsize=(8.5, 11))
        ax = fig_stats.add_subplot(111)
        ax.axis('off')
        
        # Titre
        title_text = f"Rapport d'Analyse de Géocodage\n{datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ax.text(0.5, 0.95, title_text, ha='center', va='top', 
               fontsize=16, fontweight='bold', transform=ax.transAxes)
        
        # Statistiques générales
        stats_text = f"""
STATISTIQUES GÉNÉRALES
{'='*50}

📊 Volume de données
  • Lignes totales : {stats['total_rows']}
  • Lignes géocodées : {stats['total_success']}
  • Lignes en échec : {stats['total_failed']}
  • Taux de réussite : {stats['success_rate']:.2f}%

🎯 Précision (lignes réussies uniquement)
"""
        
        # Ajouter les niveaux de précision
        if 'precision_details' in stats:
            for level, count in stats['precision_details'].items():
                percentage = (count / stats['total_success'] * 100) if stats['total_success'] > 0 else 0
                stats_text += f"  • {level}: {count} ({percentage:.1f}%)\n"
        
        # APIs utilisées
        if 'api_details' in stats:
            stats_text += f"\n🔌 APIs utilisées\n"
            for api, count in stats['api_details'].items():
                percentage = (count / stats['total_rows'] * 100) if stats['total_rows'] > 0 else 0
                stats_text += f"  • {api}: {count} ({percentage:.1f}%)\n"
        
        # Ajouter les échecs par type
        if 'failed_by_status' in stats:
            stats_text += f"\n❌ Échecs par type\n"
            for status, count in stats['failed_by_status'].items():
                if status != "OK":
                    percentage = (count / stats['total_failed'] * 100) if stats['total_failed'] > 0 else 0
                    stats_text += f"  • {status}: {count} ({percentage:.1f}%)\n"
        
        ax.text(0.1, 0.85, stats_text, ha='left', va='top', 
               fontsize=10, family='monospace', transform=ax.transAxes)
        
        pdf.savefig(fig_stats, bbox_inches='tight')
        plt.close(fig_stats)
        
        # Métadonnées du PDF
        d = pdf.infodict()
        d['Title'] = 'Rapport d\'Analyse de Géocodage'
        d['Author'] = 'Système de Géocodage'
        d['Subject'] = 'Statistiques et analyse des résultats'
        d['CreationDate'] = datetime.now()
    
    buffer.seek(0)
    return buffer


def render_file_upload():
    """Section de chargement de fichier avec persistance."""
    with st.expander("📂 Chargement du fichier", expanded=(st.session_state.analytics_df is None)):
        uploaded_file = st.file_uploader(
            "Déposez un fichier de géocodage enrichi (CSV)", 
            type=["csv"],
            key="analytics_file_uploader"
        )
        
        current_filename = uploaded_file.name if uploaded_file else None
        
        # Charger uniquement si nouveau fichier
        if uploaded_file and current_filename != st.session_state.analytics_filename:
            try:
                df = pd.read_csv(uploaded_file)
                
                if "status" not in df.columns:
                    st.error("❌ Le fichier ne contient pas la colonne nécessaire : `status`.")
                    return False
                
                st.session_state.analytics_df = df
                st.session_state.analytics_filename = current_filename
                st.session_state.analytics_fig = None  # Reset graphique
                st.success(f"✅ Fichier **{current_filename}** chargé avec succès !")
                
            except Exception as e:
                st.error(f"❌ Erreur de lecture du fichier : {e}")
                return False
        
        # Afficher l'état du fichier (toujours, même sans upload)
        if st.session_state.analytics_df is not None:
            # Message selon le contexte
            if uploaded_file and current_filename == st.session_state.analytics_filename:
                st.success(f"✅ Fichier **{st.session_state.analytics_filename}** déjà chargé.")
            elif not uploaded_file:
                st.info(f"📂 Fichier précédent toujours en mémoire : **{st.session_state.analytics_filename}**")
            
            # Métriques (toujours affichées)
            df = st.session_state.analytics_df
            total_success = (df["status"] == "OK").sum()
            total_failed = len(df) - total_success
            success_rate = (total_success / len(df) * 100) if len(df) > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 Lignes totales", f"{len(df):,}")
            with col2:
                st.metric("✅ Succès", f"{total_success:,}", delta=f"{success_rate:.1f}%")
            with col3:
                st.metric("❌ Échecs", f"{total_failed:,}", delta=f"{100-success_rate:.1f}%", delta_color="inverse")
            with col4:
                if "precision_level" in df.columns:
                    rooftop = (df["precision_level"] == "ROOFTOP").sum()
                    rooftop_rate = (rooftop / total_success * 100) if total_success > 0 else 0
                    st.metric("🎯 ROOFTOP", f"{rooftop:,}", delta=f"{rooftop_rate:.1f}%")
            
            # Aperçu des données (collapsible)
            with st.expander("👀 Aperçu des données", expanded=False):
                st.dataframe(df.head(20), use_container_width=True)
            
            return True
        else:
            st.info("📂 Veuillez charger un fichier CSV pour commencer l'analyse.")
            return False


def render_statistics():
    """Section des statistiques détaillées."""
    if st.session_state.analytics_df is None:
        return
    
    df = st.session_state.analytics_df
    
    with st.expander("📌 Statistiques Détaillées", expanded=True):
        # Détails des précisions et APIs
        col_left, col_right = st.columns(2)
        
        with col_left:
            if "precision_level" in df.columns:
                st.markdown("#### 🎯 Niveaux de précision")
                total_success = (df["status"] == "OK").sum()
                precision_counts = df["precision_level"].value_counts()
                precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
                
                for level in precision_order:
                    if level in precision_counts.index:
                        count = precision_counts[level]
                        percentage = (count / total_success * 100) if total_success > 0 else 0
                        icon = "🎯" if level == "ROOFTOP" else "📍" if level == "RANGE_INTERPOLATED" else "📌"
                        st.markdown(f"{icon} `{level}` : **{count}** ({percentage:.1f}%)")
                
                # Autres niveaux
                for level, count in precision_counts.items():
                    if level not in precision_order and pd.notna(level):
                        percentage = (count / total_success * 100) if total_success > 0 else 0
                        st.markdown(f"• `{level}` : **{count}** ({percentage:.1f}%)")

        with col_right:
            if "api_used" in df.columns:
                st.markdown("#### 🔌 APIs utilisées")
                api_counts = df["api_used"].value_counts()
                
                for api, count in api_counts.items():
                    percentage = (count / len(df) * 100) if len(df) > 0 else 0
                    icon = "🗺️" if api == "here" else "🌍" if api == "google" else "🌐" if api == "osm" else "❓"
                    st.markdown(f"{icon} `{api}` : **{count}** ({percentage:.1f}%)")


def render_visualizations():
    """Section des graphiques."""
    if st.session_state.analytics_df is None:
        return
    
    df = st.session_state.analytics_df
    
    with st.expander("📈 Visualisations", expanded=True):
        if "precision_level" in df.columns:
            # Créer ou récupérer le graphique
            if st.session_state.analytics_fig is None:
                st.session_state.analytics_fig = create_analytics_plots(df)
            
            st.pyplot(st.session_state.analytics_fig)
        else:
            st.warning("⚠️ La colonne 'precision_level' est manquante. Graphiques limités.")
            # Créer un graphique simplifié sans précision
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            status_counts = df["status"].value_counts()
            colors = ['#28a745', '#dc3545', '#ffc107']
            ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', 
                  startangle=90, colors=colors[:len(status_counts)])
            ax.set_title('Distribution des Statuts', fontsize=14, fontweight='bold')
            st.pyplot(fig)


def render_filters_and_download():
    """Section des filtres et téléchargements."""
    if st.session_state.analytics_df is None:
        return
    
    df = st.session_state.analytics_df
    
    with st.expander("📥 Filtres et Téléchargement", expanded=True):
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            # Filtre par statut
            available_status = df["status"].dropna().unique().tolist()
            selected_status = st.multiselect(
                "📌 Filtrer par statut",
                options=available_status,
                default=available_status,
                help="Sélectionnez les statuts à inclure",
                key="filter_status"
            )
        
        with col_filter2:
            # Filtre par précision
            if "precision_level" in df.columns:
                available_precision = df["precision_level"].dropna().unique().tolist()
                selected_precision = st.multiselect(
                    "🎯 Filtrer par précision",
                    options=available_precision,
                    default=available_precision,
                    help="Sélectionnez les niveaux de précision",
                    key="filter_precision"
                )
            else:
                selected_precision = []
        
        with col_filter3:
            # Filtre par API
            if "api_used" in df.columns:
                available_apis = df["api_used"].dropna().unique().tolist()
                selected_apis = st.multiselect(
                    "🔌 Filtrer par API",
                    options=available_apis,
                    default=available_apis,
                    help="Sélectionnez les APIs",
                    key="filter_api"
                )
            else:
                selected_apis = []
        
        # Appliquer les filtres
        df_filtered = df.copy()
        
        if selected_status:
            df_filtered = df_filtered[df_filtered["status"].isin(selected_status)]
        
        if selected_precision and "precision_level" in df.columns:
            df_filtered = df_filtered[df_filtered["precision_level"].isin(selected_precision)]
        
        if selected_apis and "api_used" in df.columns:
            df_filtered = df_filtered[df_filtered["api_used"].isin(selected_apis)]
        
        st.info(f"🔍 **{len(df_filtered):,} lignes** correspondent aux filtres sélectionnés")
        
        # Boutons de téléchargement
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 CSV filtré",
                data=csv,
                file_name=f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_filtered_csv"
            )
        
        with col_dl2:
            csv_full = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 CSV complet",
                data=csv_full,
                file_name=f"full_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_full_csv"
            )
        
        with col_dl3:
            # Préparer les statistiques pour le PDF
            total_rows = len(df)
            total_success = (df["status"] == "OK").sum()
            total_failed = total_rows - total_success
            success_rate = (total_success / total_rows * 100) if total_rows > 0 else 0
            
            stats = {
                'total_rows': total_rows,
                'total_success': total_success,
                'total_failed': total_failed,
                'success_rate': success_rate,
            }
            
            if "precision_level" in df.columns:
                stats['precision_details'] = df[df["status"] == "OK"]["precision_level"].value_counts().to_dict()
            
            if "api_used" in df.columns:
                stats['api_details'] = df["api_used"].value_counts().to_dict()
            
            stats['failed_by_status'] = df[df["status"] != "OK"]["status"].value_counts().to_dict()
            
            # Générer le PDF
            fig = st.session_state.analytics_fig if st.session_state.analytics_fig else create_analytics_plots(df)
            pdf_buffer = generate_pdf_report(df, fig, stats)
            
            st.download_button(
                label="📊 Rapport PDF",
                data=pdf_buffer,
                file_name=f"rapport_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf"
            )
        
        # Aperçu des données filtrées
        if len(df_filtered) > 0:
            with st.expander(f"👀 Aperçu des {len(df_filtered):,} lignes filtrées", expanded=False):
                st.dataframe(df_filtered, use_container_width=True)
        else:
            st.warning("⚠️ Aucune ligne ne correspond aux filtres sélectionnés.")


def run_analytics_page():
    """Point d'entrée principal de la page."""
    initialize_analytics_state()
    
    st.subheader("📊 Analyse des Résultats de Géocodage")
    
    # Indicateur de fichier chargé (toujours visible)
    if st.session_state.analytics_df is not None:
        df = st.session_state.analytics_df
        total_success = (df["status"] == "OK").sum()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.success(f"📂 **{st.session_state.analytics_filename}** | {len(df):,} lignes")
        with col2:
            st.info(f"✅ {total_success:,} succès")
        with col3:
            if "precision_level" in df.columns:
                rooftop = (df["precision_level"] == "ROOFTOP").sum()
                st.info(f"🎯 {rooftop:,} ROOFTOP")
    
    # Sections (affichées selon l'état)
    file_loaded = render_file_upload()
    
    if not file_loaded:
        return
    
    # Sections suivantes (affichées toujours si fichier chargé)
    render_statistics()
    render_visualizations()
    render_filters_and_download()