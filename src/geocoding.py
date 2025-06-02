import requests
import pandas as pd
import time
import streamlit as st
from datetime import datetime
from src.config import GOOGLE_API_KEY, OSM_EMAIL, HERE_API_KEY

def geocode_with_google(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_API_KEY,
        "region": "tn",
        "components": "country:TN" 
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data["status"] == "OK":
            result = data["results"][0]
            formatted_address = result.get("formatted_address", "")

            is_valid = "Tunisie" in formatted_address or "Tunisia" in formatted_address

            location = result["geometry"]["location"]
            return {
                "latitude": location["lat"],
                "longitude": location["lng"],
                "formatted_address": formatted_address,
                "status": data["status"],
                "error_message": None,
                "api_used": "google",
                "precision_level": result["geometry"].get("location_type", None),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid_address": is_valid
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
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid_address": False
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
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "valid_address": False
        }

def geocode_with_osm(address, email):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
        "email": email
    }

    headers = {
        "User-Agent": "GeocoderBot/1.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if len(data) > 0:
            result = data[0]
            return {
                "latitude": result.get("lat"),
                "longitude": result.get("lon"),
                "formatted_address": result.get("display_name"),
                "status": "OK",
                "error_message": None,
                "api_used": "osm",
                "precision_level": result.get("type", None),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid_address": "Tunisie" in result.get("display_name", "") or "Tunisia" in result.get("display_name", "")
            }
        else:
            return {
                "latitude": None,
                "longitude": None,
                "formatted_address": None,
                "status": "ZERO_RESULTS",
                "error_message": "No results from OSM",
                "api_used": "osm",
                "precision_level": None,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid_address": False
            }

    except Exception as e:
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "status": "ERROR",
            "error_message": str(e),
            "api_used": "osm",
            "precision_level": None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "valid_address": False
        }

def geocode_with_here(address):
    url = "https://geocode.search.hereapi.com/v1/geocode"
    params = {
        "q": address,
        "apiKey": HERE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        items = data.get("items", [])

        if items:
            result = items[0]
            position = result["position"]
            formatted = result.get("address", {}).get("label", "")

            return {
                "latitude": position.get("lat"),
                "longitude": position.get("lng"),
                "formatted_address": formatted,
                "status": "OK",
                "error_message": None,
                "api_used": "here",
                "precision_level": result.get("resultType", None),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid_address": "Tunisie" in formatted or "Tunisia" in formatted
            }
        else:
            return {
                "latitude": None,
                "longitude": None,
                "formatted_address": None,
                "status": "ZERO_RESULTS",
                "error_message": "No results from HERE Maps",
                "api_used": "here",
                "precision_level": None,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "valid_address": False
            }

    except Exception as e:
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "status": "ERROR",
            "error_message": str(e),
            "api_used": "here",
            "precision_level": None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "valid_address": False
        }

def clean_address(address):
    address = str(address)
    address = address.replace("é", "e").replace("è", "e").replace("à", "a").strip()
    if "Tunisie" not in address:
        address += ", Tunisie"
    return address

def geocode_dataframe(df, address_column="full_address"):
    results = []
    total = len(df)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, (index, row) in enumerate(df.iterrows()):
        address = row[address_column]

        status_text.markdown(f"⏳ Ligne {idx+1}/{total} – Tentative avec Google Maps...")
        result = geocode_with_google(address)

        if result["status"] != "OK" or result.get("valid_address") is False:
            status_text.markdown(f"⚠️ Google a échoué. Bascule vers OSM...")
            result = geocode_with_osm(address, email=OSM_EMAIL)

        if result["status"] != "OK" or result.get("valid_address") is False:
            status_text.markdown(f"⚠️ OSM a échoué. Bascule vers HERE Maps...")
            result = geocode_with_here(address)

        current_api = result.get("api_used", "inconnue")
        status_text.markdown(f"✅ Ligne {idx+1}/{total} – API utilisée : `{current_api}`")

        result["row_index"] = index
        results.append(result)

        progress_bar.progress((idx + 1) / total)
        time.sleep(0.05)

    results_df = pd.DataFrame(results)
    enriched_df = pd.concat([df.reset_index(drop=True), results_df.reset_index(drop=True)], axis=1)
    enriched_df = enriched_df.loc[:, ~enriched_df.columns.duplicated()]
    return enriched_df
