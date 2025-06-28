import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def run_analytics_page():
    st.header("📊 Analyse des Résultats de Géocodage")

    uploaded_file = st.file_uploader("📥 Glisse un fichier de géocodage enrichi (CSV)", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"❌ Erreur de lecture du fichier : {e}")
            return

        if "status" not in df.columns or "precision_level" not in df.columns:
            st.error("❌ Le fichier ne contient pas les colonnes nécessaires : `status` et `precision_level`.")
            return

        st.success("✅ Fichier chargé avec succès.")
        st.dataframe(df.head())

        st.subheader("📌 Statistiques Générales")

        total_rows = len(df)
        total_success = (df["status"] == "OK").sum()
        total_failed = total_rows - total_success
        success_rate = round((total_success / total_rows) * 100, 2) if total_rows else 0

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"- 🔢 Lignes totales : **{total_rows}**")
            st.markdown(f"- ✅ Succès : **{total_success}**")
            st.markdown(f"- ❌ Échecs : **{total_failed}**")
            st.markdown(f"- 🎯 Taux de réussite : **{success_rate}%**")

        with col2:
            precision_counts = df["precision_level"].value_counts()
            st.markdown("#### 🎯 Niveaux de précision")
            for level, count in precision_counts.items():
                st.markdown(f"- `{level}` : {count}")

        st.subheader("📈 Graphiques")

        # Camembert des statuts
        status_counts = df["status"].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

        # Bar chart pour précision
        fig2, ax2 = plt.subplots()
        precision_counts.plot(kind="bar", ax=ax2)
        ax2.set_ylabel("Nombre de lignes")
        ax2.set_xlabel("Niveau de précision")
        ax2.set_title("Distribution des précisions")
        st.pyplot(fig2)

        # API utilisées
        if "api_used" in df.columns:
            api_counts = df["api_used"].value_counts()
            fig3, ax3 = plt.subplots()
            api_counts.plot(kind="barh", ax=ax3)
            ax3.set_xlabel("Nombre de lignes")
            ax3.set_title("Répartition par API utilisée")
            st.pyplot(fig3)
        else:
            st.info("ℹ️ Colonne 'api_used' non trouvée pour les statistiques par API.")
