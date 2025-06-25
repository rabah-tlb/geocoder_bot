from weasyprint import HTML
import pandas as pd
import os
from datetime import datetime

def export_job_history_to_pdf(jobs, output_path="data/output/job_history.pdf"):
    # Préparer une liste de dictionnaires pour le tableau
    data = []
    for job in jobs:
        data.append({
            "ID Job": job["job_id"],
            "Début": pd.to_datetime(job["start_time"]).strftime("%Y-%m-%d %H:%M:%S"),
            "Fin": pd.to_datetime(job["end_time"]).strftime("%Y-%m-%d %H:%M:%S"),
            "Total": job["total_rows"],
            "Succès": job["success"],
            "Échecs": job["failed"],
            "Précisions": "<br>".join([f"{k}: {v}" for k, v in job["precision_counts"].items()]),
            "Statut": job["status"]
        })

    df = pd.DataFrame(data)

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: sans-serif }}
            h1 {{ color: #2E86C1; }}
            table {{
                width: 120%;
                margin-left:-60px;
                border-collapse: collapse;
                font-size: 10px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 5px;
                text-align: center;
                vertical-align: middle;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            td {{
                line-height: 1em;
            }}
        </style>
    </head>
    <body>
        <h1>Historique des Jobs</h1>
        {df.to_html(index=False, escape=False)}
    </body>
    </html>
    """

    HTML(string=html_content).write_pdf(output_path)
    return output_path

def get_precision_stats(enriched_df):
    if "precision_level" not in enriched_df.columns:
        return []

    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
    precision_counts = enriched_df["precision_level"].value_counts().to_dict()

    stats_lines = []
    for level in precision_order:
        if level in precision_counts:
            stats_lines.append(f"- `{level}` : {precision_counts[level]}")

    for level, count in precision_counts.items():
        if level not in precision_order:
            stats_lines.append(f"- `{level}` : {count}")
    
    return stats_lines

def export_enriched_results(df, export_format="csv", sep=",", line_delimited_json=False):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"geocodage_result_{now}.{export_format}"
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    if export_format == "csv":
        df.to_csv(filepath, index=False, sep=sep)
    elif export_format == "json":
        if line_delimited_json:
            df.to_json(filepath, orient="records", lines=True, force_ascii=False)
        else:
            df.to_json(filepath, orient="records", indent=2, force_ascii=False)
    elif export_format == "txt":
        df.to_csv(filepath, index=False, sep=sep)
    else:
        raise ValueError("Format d'export non supporté.")

    return filepath