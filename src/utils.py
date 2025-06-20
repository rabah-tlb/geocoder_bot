from weasyprint import HTML
import pandas as pd

def export_job_history_to_pdf(jobs, output_path="job_history.pdf"):
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
            body {{ font-family: sans-serif; padding: 20px; }}
            h1 {{ color: #2E86C1; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 12px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px;
                text-align: center;
                vertical-align: middle;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            td {{
                line-height: 1.4em;
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
