import pandas as pd
import csv

def detect_separator(file, max_lines=5):
    sample = file.read(2048).decode('utf-8', errors='ignore')
    file.seek(0)
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample)
        return dialect.delimiter
    except csv.Error:
        return ","  # fallback

def read_file(uploaded_file, sep=None):
    if sep is None:
        sep = detect_separator(uploaded_file)
    
    try:
        df = pd.read_csv(uploaded_file, sep=sep, encoding="utf-8")
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=sep, encoding="ISO-8859-1")

    return df
