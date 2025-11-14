import pandas as pd
import time
import re
from datetime import datetime
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

# Import des APIs séparées
from src.apis.here import geocode_with_here
from src.apis.google import (
    geocode_with_google,
    get_place_id_with_google
)
from src.apis.osm import geocode_with_osm, geocode_with_osm_structured

# Cache pour éviter les appels répétés
@lru_cache(maxsize=None)
def geocode_with_here_cached(address):
    """Version cachée de geocode_with_here"""
    return geocode_with_here(address)


@lru_cache(maxsize=None)
def geocode_with_google_cached(address, postal_code=None, city=None, governorate=None, place_id=None):
    """Version cachée de geocode_with_google"""
    components_dict = {
        "postal_code": postal_code,
        "city": city,
        "governorate": governorate
    }
    return geocode_with_google(address=address, components_dict=components_dict, place_id=place_id)


@lru_cache(maxsize=None)
def geocode_with_osm_cached(address):
    """Version cachée de geocode_with_osm"""
    # IMPORTANT: Respecter la politique d'utilisation de Nominatim (1 req/sec)
    time.sleep(1)
    return geocode_with_osm(address)


def generate_address_without_name(row):
    """Génère une adresse sans le nom de l'établissement."""
    parts = []
    for field in ["street", "postal_code", "city", "governorate", "country"]:
        if field in row:
            val = row[field]
            if pd.notna(val) and str(val).strip() != "":
                parts.append(str(val).strip())
    return ", ".join(parts)


def generate_reformatted_address(row):
    """Reformate l'adresse pour une meilleure reconnaissance par les APIs."""
    def reformat_street(value):
        street = str(value)
        street = re.sub(r"^0{1,3}", "", street)
        street = re.sub(r"0\s+(\d+)", r"\1", street)
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
    
    for field in ["postal_code", "city", "governorate", "country"]:
        if field in row and pd.notna(row[field]):
            parts.append(str(row[field]).strip())
            
    return ", ".join(parts)


def is_better(result, previous):
    """Détermine si un résultat est meilleur qu'un autre basé sur la précision."""
    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
    p1 = result.get("precision_level")
    p2 = previous.get("precision_level")
    try:
        return precision_order.index(p1) < precision_order.index(p2)
    except:
        return False


def geocode_row_with_fallback(address, index, row, mapped_fields):
    """Géocode une ligne avec logique de fallback: HERE -> Google -> OSM."""
    address_reformatted = generate_reformatted_address(row)
    best_result = None
    
    # ÉTAPE 1: HERE API
    result = geocode_with_here_cached(address_reformatted)
    if result and result["status"] == "OK":
        result["address_reformatted"] = address_reformatted
        if result.get("precision_level") == "ROOFTOP":
            result["row_index"] = index
            return result
        best_result = result
    
    # ÉTAPE 2: GOOGLE MAPS API
    if not best_result or best_result.get("precision_level") not in ["ROOFTOP", "RANGE_INTERPOLATED"]:
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
                    if not best_result or is_better(result, best_result):
                        best_result = result
                        if result.get("precision_level") == "ROOFTOP":
                            best_result["row_index"] = index
                            return best_result
        
        components_dict = {
            "postal_code": row.get("postal_code"),
            "city": row.get("city"),
            "governorate": row.get("governorate")
        }
        
        address_no_name = generate_address_without_name(row)
        result = geocode_with_google(address=address_no_name, components_dict=components_dict)
        if result and result["status"] == "OK":
            if not best_result or is_better(result, best_result):
                best_result = result
                if result.get("precision_level") == "ROOFTOP":
                    best_result["row_index"] = index
                    return best_result
        
        result = geocode_with_google(address=address_reformatted, components_dict=components_dict)
        if result and result["status"] == "OK":
            result["address_reformatted"] = address_reformatted
            if not best_result or is_better(result, best_result):
                best_result = result
    
    # ÉTAPE 3: OPENSTREETMAP (OSM)
    if not best_result or best_result.get("precision_level") == "APPROXIMATE":
        result = geocode_with_osm_cached(address_reformatted)
        if result and result["status"] == "OK":
            result["address_reformatted"] = address_reformatted
            if not best_result or is_better(result, best_result):
                best_result = result
                if result.get("precision_level") == "ROOFTOP":
                    best_result["row_index"] = index
                    return best_result
        
        if not best_result or best_result.get("precision_level") == "APPROXIMATE":
            address_no_name = generate_address_without_name(row)
            result = geocode_with_osm_cached(address_no_name)
            if result and result["status"] == "OK":
                if not best_result or is_better(result, best_result):
                    best_result = result
        
        if not best_result or best_result.get("precision_level") == "APPROXIMATE":
            result = geocode_with_osm_structured(
                street=row.get("street"),
                city=row.get("city"),
                postal_code=row.get("postal_code"),
                country=row.get("country")
            )
            if result and result["status"] == "OK":
                if not best_result or is_better(result, best_result):
                    best_result = result
    
    if best_result:
        best_result["row_index"] = index
        return best_result
    else:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "Aucune API n'a retourné de résultat (HERE, Google, OSM).",
            "api_used": "none",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def geocode_row_here_only(address, index, row, mapped_fields):
    """Géocode une ligne en utilisant uniquement HERE Maps."""
    address_reformatted = generate_reformatted_address(row)
    result = geocode_with_here_cached(address_reformatted)
    if result and result["status"] == "OK":
        result["address_reformatted"] = address_reformatted
        result["row_index"] = index
        return result
    else:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "HERE n'a pas retourné de résultat.",
            "api_used": "here",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def geocode_row_google_only(address, index, row, mapped_fields):
    """Géocode une ligne en utilisant uniquement Google Maps."""
    address_reformatted = generate_reformatted_address(row)
    components_dict = {
        "postal_code": row.get("postal_code"),
        "city": row.get("city"),
        "governorate": row.get("governorate")
    }
    best_result = None

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

    address_no_name = generate_address_without_name(row)
    result = geocode_with_google(address=address_no_name, components_dict=components_dict)
    if result and result["status"] == "OK":
        if not best_result or is_better(result, best_result):
            best_result = result
            if result.get("precision_level") == "ROOFTOP":
                best_result["row_index"] = index
                return best_result

    result = geocode_with_google(address=address_reformatted, components_dict=components_dict)
    if result and result["status"] == "OK":
        result["address_reformatted"] = address_reformatted
        if not best_result or is_better(result, best_result):
            best_result = result

    if best_result:
        best_result["row_index"] = index
        return best_result
    else:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "Aucune réponse de Google.",
            "api_used": "google",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def geocode_row_osm_only(address, index, row, mapped_fields):
    """Géocode une ligne en utilisant uniquement OpenStreetMap."""
    address_reformatted = generate_reformatted_address(row)
    best_result = None
    
    result = geocode_with_osm_cached(address_reformatted)
    if result and result["status"] == "OK":
        result["address_reformatted"] = address_reformatted
        best_result = result
        if result.get("precision_level") == "ROOFTOP":
            best_result["row_index"] = index
            return best_result
    
    if not best_result:
        address_no_name = generate_address_without_name(row)
        result = geocode_with_osm_cached(address_no_name)
        if result and result["status"] == "OK":
            best_result = result
            if result.get("precision_level") == "ROOFTOP":
                best_result["row_index"] = index
                return best_result
    
    if not best_result:
        result = geocode_with_osm_structured(
            street=row.get("street"),
            city=row.get("city"),
            postal_code=row.get("postal_code"),
            country=row.get("country")
        )
        if result and result["status"] == "OK":
            best_result = result
    
    if best_result:
        best_result["row_index"] = index
        return best_result
    else:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "OSM n'a pas retourné de résultat.",
            "api_used": "osm",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def parallel_geocode_row(df, address_column="full_address", 
                         max_workers=10, progress_callback=None, api_mode="here"):
    """Géocode plusieurs lignes en parallèle avec choix de l'API."""
    mapped_fields = st.session_state.mapping_config.get("fields", {})
    results = []
    
    if api_mode == "multi":
        geocode_func = geocode_row_with_fallback
    elif api_mode == "here":
        geocode_func = geocode_row_here_only
    elif api_mode == "google":
        geocode_func = geocode_row_google_only
    elif api_mode == "osm":
        geocode_func = geocode_row_osm_only
    else:
        geocode_func = geocode_row_here_only

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                geocode_func,
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


def create_job_entry(job_id, total_rows):
    """Crée une entrée de job pour le suivi."""
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
    """Finalise un job de géocodage avec les statistiques."""
    job["end_time"] = datetime.now()
    job["status"] = "success"
    job["success"] = (enriched_df["status"] == "OK").sum()
    job["failed"] = len(enriched_df) - job["success"]
    
    if "precision_level" in enriched_df.columns:
        job["precision_counts"] = enriched_df["precision_level"].value_counts().to_dict()
    
    job["details_df"] = enriched_df
    return job


# Alias pour compatibilité avec l'ancien code
geocode_row = geocode_row_with_fallback