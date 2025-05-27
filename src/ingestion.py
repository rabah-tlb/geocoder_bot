import pandas as pd

def load_and_preview(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath, sep=None, engine="python")
        return df
    except Exception as e:
        print(f"Erreur de lecture du fichier : {e}")
        return pd.DataFrame()
