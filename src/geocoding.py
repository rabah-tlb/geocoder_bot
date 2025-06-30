import requests
import pandas as pd
import time
import streamlit as st
from datetime import datetime
from functools import lru_cache
from src.config import GOOGLE_API_KEY, HERE_API_KEY
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.logger import log_api_call
from src.apis.here import geocode_with_here

def parallel_geocode_row_google_only(df, address_column="full_address", max_workers=10, progress_callback=None):
    from src.geocoding import geocode_row_google_only

    mapped_fields = st.session_state.mapping_config.get("fields", {})

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                geocode_row_google_only,
                row[address_column],
                row.name,
                row,
                mapped_fields
            ): index for index, row in df.iterrows()
        }

        for future in as_completed(futures):
            try:
                geocode_result = future.result()
                index = geocode_result["row_index"]
                original_row = df.loc[index].to_dict()
                merged = {**original_row, **geocode_result}
                results.append(merged)
            except Exception as e:
                results.append({
                    "status": "ERROR",
                    "error_message": str(e),
                    "row_index": futures[future]
                })
            if progress_callback:
                progress_callback()

    result_df = pd.DataFrame(results)

    # Placer address_reformatted juste après full_address
    if "full_address" in result_df.columns and "address_reformatted" in result_df.columns:
        cols = list(result_df.columns)
        cols.remove("address_reformatted")
        fa_index = cols.index("full_address")
        cols.insert(fa_index + 1, "address_reformatted")
        result_df = result_df[cols]

    return result_df

def parallel_geocode_row(df, address_column="full_address", max_workers=10, progress_callback=None):
    from src.geocoding import geocode_row

    mapped_fields = st.session_state.mapping_config.get("fields", {})

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                geocode_row,
                row[address_column],
                row.name,
                row,
                mapped_fields
            ): index for index, row in df.iterrows()
        }

        for future in as_completed(futures):
            try:
                geocode_result = future.result()
                index = geocode_result["row_index"]
                original_row = df.loc[index].to_dict()
                merged = {**original_row, **geocode_result}
                results.append(merged)
            except Exception as e:
                results.append({
                    "status": "ERROR",
                    "error_message": str(e),
                    "row_index": futures[future]
                })
            if progress_callback:
                progress_callback()

    result_df = pd.DataFrame(results)

    if "full_address" in result_df.columns and "address_reformatted" in result_df.columns:
        cols = list(result_df.columns)
        cols.remove("address_reformatted")
        fa_index = cols.index("full_address")
        cols.insert(fa_index + 1, "address_reformatted")
        result_df = result_df[cols]

    return result_df

@lru_cache(maxsize=None)
def geocode_with_here_cached(address):
    return geocode_with_here(address)

@lru_cache(maxsize=None)
def geocode_with_google_cached(address, postal_code=None, city=None, governorate=None, place_id=None):
    components_dict = {
        "postal_code": postal_code,
        "city": city,
        "governorate": governorate
    }
    return geocode_with_google(address=address, components_dict=components_dict, place_id=place_id)

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
    start_time = time.time()
    try:
        response = requests.get(url, params=params, timeout=10)
        duration = time.time() - start_time
        data = response.json()

        log_api_call("google", response.url, data["status"], duration, response=data)

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
        duration = time.time() - start_time
        log_api_call("google", url, "ERROR", duration, error=str(e))
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

def generate_address_without_name(row):
    parts = []
    for field in ["street", "postal_code", "city", "governorate", "country"]:
        if field in row:
            val = row[field]
            if pd.notna(val) and str(val).strip() != "":
                parts.append(str(val).strip())
    return ", ".join(parts)

def generate_reformatted_address(row):
    def reformat_street(value):
        street = str(value)
        street = re.sub(r"^0{1,3}", "", street)
        street = re.sub(r"0\s+(\d+)", r"\1", street)
        street = re.sub(r"\b(IMM?|ILL|IMMB)\b", "Immeuble", street, flags=re.IGNORECASE)
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
    if "street" in row and pd.notna(row["street"]):
        parts.append(reformat_street(row["street"]))
    return ", ".join(parts)

def is_better(result, previous):
    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
    p1 = result.get("precision_level")
    p2 = previous.get("precision_level")
    try:
        return precision_order.index(p1) < precision_order.index(p2)
    except:
        return False

def geocode_row(address, index, row, mapped_fields):
    from src.geocoding import (
        geocode_with_google_cached,
        geocode_with_here_cached,
        generate_reformatted_address,
        is_better
    )

    address_reformatted = generate_reformatted_address(row)

    best_result = None

    result = geocode_with_here_cached(address_reformatted)
    if result and result["status"] == "OK":
        result["address_reformatted"] = address_reformatted
        if result.get("precision_level") == "ROOFTOP":
            result["row_index"] = index
            return result
        best_result = result

    # result = geocode_with_here_cached(address_reformatted)
    # if result and result["status"] == "OK":
    #     result["address_reformatted"] = address_reformatted
    #     if not best_result or is_better(result, best_result):
    #         best_result = result

    if best_result:
        best_result["row_index"] = index
        return best_result
    elif result: 
        result["row_index"] = index
        return result
    else:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "Aucune API n’a retourné de résultat.",
            "api_used": "aucune"
        }

def geocode_row_google_only(address, index, row, mapped_fields):
    from src.geocoding import (
        get_place_id_with_google,
        geocode_with_google,
        generate_address_without_name,
        generate_reformatted_address,
        is_better
    )

    address_reformatted = generate_reformatted_address(row)

    components_dict = {
        "postal_code": row.get("postal_code"),
        "city": row.get("city"),
        "governorate": row.get("governorate")
    }

    best_result = None

    # 1. Google via place_id (nom + ville)
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
                    return best_result

    # 2. Adresse sans nom
    address_no_name = generate_address_without_name(row)
    result = geocode_with_google(address=address_no_name, components_dict=components_dict)
    if result and result["status"] == "OK":
        if not best_result or is_better(result, best_result):
            best_result = result
            if result.get("precision_level") == "ROOFTOP":
                best_result["row_index"] = index
                return best_result

    # 3. Adresse reformatée
    result = geocode_with_google(address=address_reformatted, components_dict=components_dict)
    if result and result["status"] == "OK":
        if not best_result or is_better(result, best_result):
            best_result = result
            best_result["address_reformatted"] = address_reformatted
            if result.get("precision_level") == "ROOFTOP":
                best_result["row_index"] = index
                return best_result

    # Retourner le meilleur si trouvé
    if best_result:
        best_result["row_index"] = index
        return best_result
    elif result:
        result["row_index"] = index
        return result
    else:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "Aucune réponse de Google.",
            "api_used": "google"
        }

def create_job_entry(job_id, total_rows):
    return {
        "job_id": job_id,
        "start_time": datetime.now(),
        "end_time": None,
        "status": "in_progress",
        "total_rows": total_rows,
        "success": 0,
        "failed": 0,
        "precision_counts": {},
        "details_df": None
    }

def finalize_job(job, enriched_df):
    job["end_time"] = datetime.now()
    job["status"] = "success"
    job["success"] = (enriched_df["status"] == "OK").sum()
    job["failed"] = len(enriched_df) - job["success"]
    if "precision_level" in enriched_df.columns:
        job["precision_counts"] = enriched_df["precision_level"].value_counts().to_dict()
    job["details_df"] = enriched_df
    return job