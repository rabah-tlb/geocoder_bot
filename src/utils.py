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
