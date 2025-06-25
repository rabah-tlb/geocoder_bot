import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Historique des Jobs", ln=True, align="C")

    def table(self, df):
        self.set_font("Arial", "B", 10)
        col_widths = [25, 35, 35, 15, 15, 15, 40, 20]
        headers = list(df.columns)
        for i, col in enumerate(headers):
            self.cell(col_widths[i], 8, col, border=1, align="C")
        self.ln()

        self.set_font("Arial", "", 9)
        for _, row in df.iterrows():
            for i, col in enumerate(headers):
                value = str(row[col])
                self.cell(col_widths[i], 8, value[:40], border=1)
            self.ln()

def export_job_history_to_pdf(jobs, output_path="data/output/job_history.pdf"):
    import pandas as pd

    rows = []
    for job in jobs:
        rows.append({
            "ID Job": job["job_id"],
            "Début": job["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "Fin": job["end_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "Total": job["total_rows"],
            "Succès": job["success"],
            "Échecs": job["failed"],
            "Précisions": ", ".join([f"{k}: {v}" for k, v in job["precision_counts"].items()]),
            "Statut": job["status"]
        })

    df = pd.DataFrame(rows)

    pdf = PDF()
    pdf.add_page()
    pdf.table(df)
    pdf.output(output_path)

    return output_path

def get_precision_stats(enriched_df):
    if "precision_level" not in enriched_df.columns:
        return []

    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
    precision_counts = enriched_df["precision_level"].value_counts().to_dict()

    stats_lines = []
    for level in precision_order:
        if level in precision_counts:
            stats_lines.append(f"- ⁠ {level} ⁠ : {precision_counts[level]}")

    for level, count in precision_counts.items():
        if level not in precision_order:
            stats_lines.append(f"- ⁠ {level} ⁠ : {count}")
    
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