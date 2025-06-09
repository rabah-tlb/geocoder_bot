import requests
import pandas as pd
import time
import streamlit as st
from datetime import datetime
from src.config import GOOGLE_API_KEY, OSM_EMAIL, HERE_API_KEY
import re

def get_place_id_with_google(query):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        print(f"🔍 {query}")
        print(f"📥 Response: {data}")
        if data["status"] == "OK" and data.get("candidates"):
            return data["candidates"][0].get("place_id")
        else:
            print(f"❌ No match or bad status: {data['status']}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

def geocode_with_google(address=None, components_dict=None, place_id=None):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "key": GOOGLE_API_KEY,
        "region": "tn"
    }

    if place_id:
        params["place_id"] = place_id
    else:
        components_parts = ["country:TN"]
        if components_dict:
            if "postal_code" in components_dict and components_dict["postal_code"]:
                components_parts.append(f"postal_code:{components_dict['postal_code']}")
            if "city" in components_dict and components_dict["city"]:
                components_parts.append(f"locality:{components_dict['city']}")
            if "governorate" in components_dict and components_dict["governorate"]:
                components_parts.append(f"administrative_area_level_1:{components_dict['governorate']}")
        params["components"] = "|".join(components_parts)
        params["address"] = address

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data["status"] == "OK":
            result = data["results"][0]
            formatted_address = result.get("formatted_address", "")
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
        }

def map_osm_precision(osm_type: str) -> str:
    if osm_type is None:
        return "UNKNOWN"
    osm_type = osm_type.lower()
    if osm_type in ["building", "house"]:
        return "ROOFTOP"
    elif osm_type in ["residential", "street", "road"]:
        return "RANGE_INTERPOLATED"
    elif osm_type in ["postcode"]:
        return "GEOMETRIC_CENTER"
    elif osm_type in ["village", "suburb", "city", "county", "region", "country"]:
        return "APPROXIMATE"
    else:
        return "UNKNOWN"

def geocode_with_osm(address, email):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
        "email": email
    }
    headers = {"User-Agent": "GeocoderBot/1.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if len(data) > 0:
            result = data[0]
            formatted = result.get("display_name", "")
            osm_type = result.get("type", None)
            precision = map_osm_precision(osm_type)
            return {
                "latitude": result.get("lat"),
                "longitude": result.get("lon"),
                "formatted_address": formatted,
                "status": "OK",
                "error_message": None,
                "api_used": "osm",
                "precision_level": precision,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
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
        }

def map_here_precision(match_level: str) -> str:
    if match_level is None:
        return "UNKNOWN"
    match_level = match_level.lower()
    if match_level == "housenumber":
        return "ROOFTOP"
    elif match_level in ["intersection", "street"]:
        return "RANGE_INTERPOLATED"
    elif match_level == "postalcode":
        return "GEOMETRIC_CENTER"
    elif match_level in ["city", "locality", "district", "county", "state", "place", "country"]:
        return "APPROXIMATE"
    else:
        return "UNKNOWN"

def geocode_with_here(address):
    url = "https://geocode.search.hereapi.com/v1/geocode"
    params = {
        "q": address,
        "apiKey": HERE_API_KEY,
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
        }

def clean_address(address):
    address = str(address)
    address = address.replace("é", "e").replace("è", "e").replace("à", "a").strip()
    if "Tunisie" not in address:
        address += ", Tunisie"
    return address

def generate_address_without_name(row, mapped_fields):
    parts = []
    for field in ["street", "postal_code", "city", "governorate", "country"]:
        if field in mapped_fields and mapped_fields[field] in row:
            val = row[mapped_fields[field]]
            if pd.notna(val):
                parts.append(str(val))
    return ", ".join(parts)

def generate_reformatted_address(row, mapped_fields):
    def reformat_street(value):
        street = str(value)
        street = re.sub(r"^0{1,3}", "", street)
        street = re.sub(r"\b0\s+(\d+)", r"\1", street)
        street = re.sub(r"\b(IMM?|ILL)\b", "Immeuble", street, flags=re.IGNORECASE)
        street = re.sub(r"\b(RES|RS)\b", "Résidence", street, flags=re.IGNORECASE)
        match = re.match(r"^(\d{1,4})(\s*)(.*)", street)
        if match:
            num, space, rest = match.groups()
            if not re.search(r"\b(Rue|Avenue|Av|Boulevard|Blvd|Résidence|Immeuble)\b", rest, flags=re.IGNORECASE):
                return f"{num}{space}Rue {rest}".strip()
        if not re.search(r"\b(Rue|Avenue|Av|Boulevard|Blvd|Résidence|Immeuble)\b", street, flags=re.IGNORECASE):
            return "Rue " + street
        return street.strip()

    parts = []
    if "street" in mapped_fields and mapped_fields["street"] in row:
        val = row[mapped_fields["street"]]
        if pd.notna(val):
            parts.append(reformat_street(val))
    for field in ["postal_code", "city", "governorate", "country"]:
        if field in mapped_fields and mapped_fields[field] in row:
            val = row[mapped_fields[field]]
            if pd.notna(val):
                parts.append(str(val))
    return ", ".join(parts)

def is_better(result, previous):
    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
    p1 = result.get("precision_level")
    p2 = previous.get("precision_level")
    try:
        return precision_order.index(p1) < precision_order.index(p2)
    except:
        return False

def geocode_dataframe(df, address_column="full_address"):
    results = []
    total = len(df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    mapped_fields = st.session_state.mapping_config.get("fields", {})

    for idx, (index, row) in enumerate(df.iterrows()):
        raw_address = row[address_column]
        address = clean_address(raw_address)

        components_dict = {
            "postal_code": row.get("postal_code"),
            "city": row.get("city"),
            "governorate": row.get("governorate")
        }

        status_text.markdown(f"⏳ Ligne {idx+1}/{total} – Test avec Google Maps...")

        result = None
        best_result = None

        # Étape 1 : place_id (name + city/country)
        if "name" in row and pd.notna(row["name"]):
            query = str(row["name"])
            if "city" in row and pd.notna(row["city"]):
                query += " " + str(row["city"])
            elif "country" in row and pd.notna(row["country"]):
                query += " " + str(row["country"])
            place_id = get_place_id_with_google(query)
            if place_id:
                result = geocode_with_google(place_id=place_id)
                if result and result["status"] == "OK":
                    best_result = result
                    if result.get("precision_level") == "ROOFTOP":
                        best_result["row_index"] = index
                        results.append(best_result)
                        progress_bar.progress(min((idx + 1) / total, 1.0))
                        continue

        # Étape 2 : sans name
        address_no_name = generate_address_without_name(row, mapped_fields)
        result = geocode_with_google(address=address_no_name, components_dict=components_dict)
        if result and result["status"] == "OK":
            if not best_result or is_better(result, best_result):
                best_result = result
                if result.get("precision_level") == "ROOFTOP":
                    best_result["row_index"] = index
                    results.append(best_result)
                    progress_bar.progress(min((idx + 1) / total, 1.0))
                    continue

        # Étape 3 : adresse reformattée
        address_reformatted = generate_reformatted_address(row, mapped_fields)
        result = geocode_with_google(address=address_reformatted, components_dict=components_dict)
        if result and result["status"] == "OK":
            if not best_result or is_better(result, best_result):
                best_result = result
                if result.get("precision_level") == "ROOFTOP":
                    best_result["row_index"] = index
                    results.append(best_result)
                    progress_bar.progress(min((idx + 1) / total, 1.0))
                    continue

        # Fallback vers OSM
        if not best_result:
            status_text.markdown("⚠️ Google KO – tentative avec OSM...")
            result = geocode_with_osm(address, email=OSM_EMAIL)
            if result and result["status"] == "OK":
                best_result = result
                best_result["row_index"] = index
                results.append(best_result)
                progress_bar.progress(min((idx + 1) / total, 1.0))
                continue

        # Fallback vers HERE
        if not best_result:
            status_text.markdown("⚠️ OSM KO – tentative avec HERE Maps...")
            result = geocode_with_here(address)
            best_result = result  # que le résultat soit OK ou non, on le garde

        if best_result:
            best_result["row_index"] = index
            results.append(best_result)
        else:
            results.append({
                "row_index": index,
                "status": "ERROR",
                "error_message": "Aucune API n’a retourné de résultat.",
                "api_used": "aucune"
            })

        current_api = best_result.get("api_used", "inconnue") if best_result else "aucune"
        status_text.markdown(f"✅ Ligne {idx+1}/{total} – API utilisée : `{current_api}`")

        progress_bar.progress(min((idx + 1) / total, 1.0))
        time.sleep(0.05)

    results_df = pd.DataFrame(results)
    enriched_df = pd.concat([df.reset_index(drop=True), results_df.reset_index(drop=True)], axis=1)
    enriched_df = enriched_df.loc[:, ~enriched_df.columns.duplicated()]
    return enriched_df
