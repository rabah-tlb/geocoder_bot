import pandas as pd
import chardet

def detect_encoding(file_obj):
    raw_data = file_obj.read(10000)
    file_obj.seek(0)  # Revenir au début du fichier
    result = chardet.detect(raw_data)
    return result['encoding']

def read_file(file_obj, sep: str = ",", encoding: str = None) -> pd.DataFrame:
    try:
        # Détection automatique de l'encodage si non fourni
        if encoding is None:
            encoding = detect_encoding(file_obj)

        # Lire le fichier depuis Streamlit (BytesIO)
        df = pd.read_csv(file_obj, sep=sep, encoding=encoding, engine="python")
        return df
    except Exception as e:
        print(f"Erreur de lecture : {e}")
        return pd.DataFrame()
