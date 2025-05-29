import streamlit as st
import pandas as pd
from src.ingestion import read_file
from src.geocoding import geocode_dataframe, clean_address

# Configuration
st.set_page_config(page_title="Robot de Géocodage", layout="wide")
st.title("📍 Robot de Géocodage")

# Initialisation des états
if "df" not in st.session_state:
    st.session_state.df = None

if "enriched_df" not in st.session_state:
    st.session_state.enriched_df = None

if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None

# ========== UPLOAD ET LECTURE ==========
st.subheader("📁 Chargement du fichier")

uploaded_file = st.file_uploader("Dépose un fichier CSV ou TXT", type=["csv", "txt"])

if uploaded_file and st.session_state.df is None:
    detect_auto = st.checkbox("🔍 Détecter automatiquement le séparateur", value=True)

    if detect_auto:
        df = read_file(uploaded_file, sep=None)
    else:
        separator = st.selectbox("Séparateur", [",", ";", "|", "\\t"], index=0)
        if separator == "\\t":
            separator = "\t"
        df = read_file(uploaded_file, sep=separator)

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
            st.session_state.df = df.copy()
            st.success("✅ Colonne 'full_address' générée !")
            st.dataframe(df[["full_address"]].head())
        else:
             st.warning("⚠️ Tu dois mapper au moins les champs 'street', 'postal_code' et 'city'.")

# ========== GÉOCODAGE MULTI-API ==========
st.subheader("📍 Géocodage Multi-API")

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
            st.dataframe(enriched_df)

if st.session_state.enriched_df is not None:
    enriched_df = st.session_state.enriched_df

    total = len(enriched_df)
    failed_df = enriched_df[enriched_df["status"] != "OK"]
    failed_count = len(failed_df)
    success_count = total - failed_count
    rate = round(success_count / total * 100, 2)

    st.subheader("📊 Statistiques de traitement")
    st.markdown(f"- Total lignes traitées : `{total}`")
    st.markdown(f"- Succès : ✅ `{success_count}`")
    st.markdown(f"- Échecs : ❌ `{failed_count}`")
    st.markdown(f"- Taux de réussite : **{rate}%**")

    enriched_df = enriched_df.reset_index(drop=True)
    st.session_state.enriched_df = enriched_df  # mettre à jour

    # Bouton de nettoyage après géocodage
    if st.button("🧹 Nettoyer les adresses géocodées"):
        cleaned_df = enriched_df.copy()
        cleaned_df["full_address"] = cleaned_df["full_address"].apply(clean_address)
        st.session_state.cleaned_df = cleaned_df

        # Affichage de la différence
        st.success("✅ Nettoyage terminé ! Voici un aperçu avant/après :")
        comparison_df = pd.DataFrame({
            "Avant nettoyage": enriched_df["full_address"],
            "Après nettoyage": cleaned_df["full_address"]
        })
        st.dataframe(comparison_df.head())

    # Bloc de relance
    if failed_count > 0:
        st.warning(f"⚠️ {failed_count} lignes ont échoué.")

        if st.button("🔁 Relancer uniquement les erreurs"):
            st.info("🔄 Relance des lignes échouées...")

            # Re-géocoder uniquement les lignes en échec
            retried_df = geocode_dataframe(failed_df, address_column="full_address")

            # Reset index pour éviter tout conflit d’indexation
            enriched_df = enriched_df.reset_index(drop=True)

            # Mise à jour des lignes échouées par les nouvelles valeurs
            for _, row in retried_df.iterrows():
                try:
                    row_index = int(row["row_index"])  # index d’origine
                    for col in retried_df.columns:
                        value = row[col]

                        # Si c’est une Series, on prend le premier élément
                        if isinstance(value, pd.Series):
                            value = value.iloc[0]

                        enriched_df.at[row_index, col] = value

                except Exception as e:
                    st.warning(f"⚠️ Erreur en mettant à jour la ligne {row_index}, colonne '{col}' : {e}")

            # Mise à jour de session
            st.session_state.enriched_df = enriched_df

            st.success("✅ Relance terminée ! Résultats mis à jour.")
            st.dataframe(enriched_df)

# ========== EXPORT ==========
if st.session_state.enriched_df is not None:
    if st.button("📅 Exporter en CSV"):
        st.session_state.enriched_df.to_csv("data/output/geocoded_results_google.csv", index=False)
        st.success("📁 Fichier exporté dans data/output/geocoded_results_google.csv")

if st.session_state.cleaned_df is not None:
    if st.button("📤 Exporter les adresses nettoyées"):
        st.session_state.cleaned_df.to_csv("data/output/geocoded_results_cleaned.csv", index=False)
        st.success("📁 Fichier exporté dans data/output/geocoded_results_cleaned.csv")



git add .
git commit -m "feat: implement fallback geocoding with HERE Maps when OpenStreetMap fails"
git push origin main