import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF
import pandas as pd
import os

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(40, 40, 40)
        self.set_x(10)
        self.cell(0, 10, "Historique des Jobs de Géocodage", ln=True, align="L")
        self.ln(5)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def table(self, df):
        self.set_font("Arial", "B", 9)
        headers = list(df.columns)

        # Largeurs des colonnes
        col_widths = [40, 28, 28, 12, 12, 12, 45, 20]

        # En-têtes
        self.set_x(10)
        for i, col in enumerate(headers):
            self.cell(col_widths[i], 8, col, border=1, align="C")
        self.ln()

        self.set_font("Arial", "", 8)

        for _, row in df.iterrows():
            y_start = self.get_y()
            x_start = 10

            # Déterminer la hauteur maximale de la ligne
            heights = []
            for i, col in enumerate(headers):
                text = str(row[col])
                lines = self.multi_cell(col_widths[i], 5, text, border=0, align="L", split_only=True)
                heights.append(len(lines) * 5)
            max_height = max(heights)

            self.set_y(y_start)
            self.set_x(x_start)

            for i, col in enumerate(headers):
                text = str(row[col])
                x_current = self.get_x()
                y_current = self.get_y()

                self.multi_cell(col_widths[i], 5, text, border=1, align="L")
                self.set_xy(x_current + col_widths[i], y_current)

            self.set_y(y_start + max_height)

def export_job_history_to_pdf(jobs, output_path="data/output/job_history.pdf"):
    rows = []
    for job in jobs:
        precision_lines = "\n".join([f"{k}: {v}" for k, v in job["precision_counts"].items()])
        rows.append({
            "ID Job": job["job_id"],
            "Début": job["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "Fin": job["end_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "Total": job["total_rows"],
            "Succès": job["success"],
            "Échecs": job["failed"],
            "Précisions": precision_lines,
            "Statut": job["status"]
        })

    df = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

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