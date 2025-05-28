import requests
from src.config import GOOGLE_API_KEY
from tqdm import tqdm
import pandas as pd
import time


def geocode_with_google(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data["status"] == "OK":
            result = data["results"][0]
            location = result["geometry"]["location"]

            return {
                "latitude": location["lat"],
                "longitude": location["lng"],
                "formatted_address": result.get("formatted_address", None),
                "status": data["status"],
                "error_message": None,
                "api_used": "google",
                "precision_level": result["geometry"].get("location_type", None),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {
                "latitude": None,
                "longitude": None,
                "formatted_address": None,
                "status": data["status"],
                "error_message": data.get("error_message", "No result"),
                "api_used": "google",
                "precision_level": None,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

    except Exception as e:
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "status": "ERROR",
            "error_message": str(e),
            "api_used": "google",
            "precision_level": None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }


def geocode_dataframe(df, address_column="full_address"):
    results = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="⏳ Géocodage en cours"):
        address = row[address_column]
        result = geocode_with_google(address)
        results.append(result)

    results_df = pd.DataFrame(results)
    enriched_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    return enriched_df
