from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from src.apis.opencage import geocode_with_opencage
from src.apis.geocodexyz import geocode_with_geocodexyz
from src.apis.osm import geocode_with_osm

def fallback_geocode(address, index):
    for geocode_func in [
        geocode_with_opencage,
        geocode_with_geocodexyz,
        geocode_with_osm
    ]:
        try:
            result = geocode_func(address)
            if result and result.get("status") == "OK":
                result["row_index"] = index
                return result
        except Exception:
            continue
    return {
        "row_index": index,
        "status": "ERROR",
        "error_message": "Aucune API n’a retourné de résultat.",
        "api_used": "aucune"
    }

def retry_geocode_row(df, address_column="full_address", max_workers=10, progress_callback=None):
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fallback_geocode, row[address_column], row.name): row.name
            for _, row in df.iterrows()
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "row_index": futures[future],
                    "status": "ERROR",
                    "error_message": str(e),
                    "api_used": "aucune"
                })
            if progress_callback:
                progress_callback()

    return pd.DataFrame(results)
