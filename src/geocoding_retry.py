import pandas as pd
import re
from datetime import datetime
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

# Import des APIs
from src.apis.here import geocode_with_here
from src.apis.google import (
    geocode_with_google,
    get_place_id_with_google
)
from src.apis.osm import geocode_with_osm, geocode_with_osm_structured


# ========== FONCTIONS UTILITAIRES ==========

def generate_address_without_name(row):
    """Génère une adresse sans le nom de l'établissement."""
    parts = []
    for field in ["street", "postal_code", "city", "governorate", "country"]:
        if field in row and pd.notna(row[field]) and str(row[field]).strip():
            parts.append(str(row[field]).strip())
    return ", ".join(parts)


def generate_reformatted_address(row):
    """Reformate l'adresse pour améliorer la reconnaissance."""
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


def generate_alternative_addresses(row):
    """
    Génère plusieurs variantes d'adresse pour maximiser les chances de succès.
    """
    addresses = []
    
    # 1. Adresse reformatée complète
    addr_reformatted = generate_reformatted_address(row)
    if addr_reformatted:
        addresses.append(("reformatted", addr_reformatted))
    
    # 2. Adresse sans nom (pour éviter la confusion)
    addr_no_name = generate_address_without_name(row)
    if addr_no_name and addr_no_name != addr_reformatted:
        addresses.append(("no_name", addr_no_name))
    
    # 3. Adresse originale si disponible
    if "full_address" in row and pd.notna(row["full_address"]):
        addr_original = str(row["full_address"]).strip()
        if addr_original not in [a[1] for a in addresses]:
            addresses.append(("original", addr_original))
    
    return addresses


def is_better_precision(new_result, current_best):
    """
    Détermine si un nouveau résultat a une meilleure précision.
    """
    if not current_best:
        return True
    
    if new_result.get("status") != "OK":
        return False
    
    precision_order = ["ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"]
    
    new_precision = new_result.get("precision_level")
    current_precision = current_best.get("precision_level")
    
    try:
        return precision_order.index(new_precision) < precision_order.index(current_precision)
    except:
        return False


# ========== STRATÉGIE DE RELANCE INTELLIGENTE ==========

def intelligent_retry_geocode(row, index, target_precision="ROOFTOP"):
    """
    Stratégie intelligente de relance avec plusieurs APIs et variantes d'adresse.
    
    Stratégie :
    1. Si la ligne a déjà un résultat OK mais précision faible → tenter d'améliorer
    2. Si la ligne a échoué → essayer toutes les APIs avec toutes les variantes
    3. Retourner le meilleur résultat trouvé
    
    Args:
        row: Ligne du DataFrame
        index: Index de la ligne
        target_precision: Niveau de précision cible (par défaut ROOFTOP)
    
    Returns:
        dict: Meilleur résultat trouvé
    """
    best_result = None
    current_status = row.get("status")
    current_precision = row.get("precision_level")
    current_api = row.get("api_used")
    
    # Générer toutes les variantes d'adresse
    address_variants = generate_alternative_addresses(row)
    
    if not address_variants:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "Impossible de générer des adresses valides",
            "api_used": "none",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # Ordre des APIs à essayer (en fonction de ce qui a déjà été tenté)
    api_order = []
    
    if current_api == "here":
        api_order = ["google", "osm", "here"]
    elif current_api == "google":
        api_order = ["here", "osm", "google"]
    elif current_api == "osm":
        api_order = ["here", "google", "osm"]
    else:
        api_order = ["here", "google", "osm"]
    
    # ========== ESSAYER CHAQUE API AVEC CHAQUE VARIANTE ==========
    
    for api_name in api_order:
        
        # Arrêter si on a déjà ROOFTOP
        if best_result and best_result.get("precision_level") == "ROOFTOP":
            break
        
        if api_name == "here":
            for variant_type, address in address_variants:
                result = geocode_with_here(address)
                if result and result["status"] == "OK":
                    result["address_variant"] = variant_type
                    if not best_result or is_better_precision(result, best_result):
                        best_result = result
                        if result.get("precision_level") == "ROOFTOP":
                            break
        
        elif api_name == "google":
            # Stratégie Google : place_id + adresses variantes + composants structurés
            
            # 1. Essayer avec place_id si on a un nom
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
                        result["address_variant"] = "place_id"
                        if not best_result or is_better_precision(result, best_result):
                            best_result = result
                            if result.get("precision_level") == "ROOFTOP":
                                continue
            
            # 2. Essayer avec chaque variante d'adresse
            components_dict = {
                "postal_code": row.get("postal_code"),
                "city": row.get("city"),
                "governorate": row.get("governorate")
            }
            
            for variant_type, address in address_variants:
                result = geocode_with_google(address=address, components_dict=components_dict)
                if result and result["status"] == "OK":
                    result["address_variant"] = variant_type
                    if not best_result or is_better_precision(result, best_result):
                        best_result = result
                        if result.get("precision_level") == "ROOFTOP":
                            break
        
        elif api_name == "osm":
            # Stratégie OSM : adresses variantes + recherche structurée
            
            # 1. Essayer avec chaque variante
            for variant_type, address in address_variants:
                result = geocode_with_osm(address)
                if result and result["status"] == "OK":
                    result["address_variant"] = variant_type
                    if not best_result or is_better_precision(result, best_result):
                        best_result = result
                        if result.get("precision_level") == "ROOFTOP":
                            break
            
            # 2. Essayer avec recherche structurée
            if not best_result or best_result.get("precision_level") != "ROOFTOP":
                result = geocode_with_osm_structured(
                    street=row.get("street"),
                    city=row.get("city"),
                    postal_code=row.get("postal_code"),
                    country=row.get("country")
                )
                if result and result["status"] == "OK":
                    result["address_variant"] = "structured"
                    if not best_result or is_better_precision(result, best_result):
                        best_result = result
    
    # ========== RETOURNER LE MEILLEUR RÉSULTAT ==========
    
    if best_result:
        best_result["row_index"] = index
        best_result["improved"] = (
            current_status != "OK" or 
            is_better_precision(best_result, {"precision_level": current_precision})
        )
        return best_result
    else:
        return {
            "row_index": index,
            "status": "ERROR",
            "error_message": "Aucune API n'a retourné de résultat après relance complète",
            "api_used": "none",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "improved": False,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# ========== FONCTION PARALLÈLE DE RELANCE ==========

def retry_geocode_parallel(df, max_workers=10, progress_callback=None, target_precision="ROOFTOP"):
    """
    Relance le géocodage en parallèle avec stratégie intelligente.
    
    Args:
        df: DataFrame avec les lignes à relancer
        max_workers: Nombre de threads parallèles
        progress_callback: Callback pour mise à jour de la progression
        target_precision: Niveau de précision cible
    
    Returns:
        pd.DataFrame: Résultats de la relance
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                intelligent_retry_geocode,
                row,
                row.name,
                target_precision
            ): index for index, row in df.iterrows()
        }
        
        for future in as_completed(futures):
            try:
                geocode_result = future.result()
                index = geocode_result["row_index"]
                original_row = df.loc[index].to_dict()
                
                # Merger les résultats (en gardant les anciennes colonnes si besoin)
                merged = {**original_row, **geocode_result}
                results.append(merged)
                
            except Exception as e:
                index = futures[future]
                original_row = df.loc[index].to_dict()
                results.append({
                    **original_row,
                    "status": "ERROR",
                    "error_message": str(e),
                    "row_index": index,
                    "improved": False
                })
            
            if progress_callback:
                progress_callback()
    
    result_df = pd.DataFrame(results)
    
    # Réorganiser les colonnes pour mettre les nouvelles colonnes importantes en avant
    important_cols = ["row_index", "status", "improved", "precision_level", "api_used", 
                      "latitude", "longitude", "formatted_address", "address_variant"]
    
    existing_important = [col for col in important_cols if col in result_df.columns]
    other_cols = [col for col in result_df.columns if col not in existing_important]
    
    result_df = result_df[existing_important + other_cols]
    
    return result_df


# ========== FONCTION SIMPLIFIÉE POUR COMPATIBILITÉ ==========

def retry_geocode_row(df, address_column="full_address", max_workers=10, 
                      progress_callback=None, api_mode="multi"):
    """
    Fonction de relance compatible avec l'interface existante.
    
    Args:
        df: DataFrame à relancer
        address_column: Colonne contenant l'adresse (utilisé pour vérification)
        max_workers: Nombre de workers parallèles
        progress_callback: Callback de progression
        api_mode: Mode de l'API (ignoré, utilise toujours la stratégie intelligente)
    
    Returns:
        pd.DataFrame: Résultats enrichis
    """
    return retry_geocode_parallel(
        df, 
        max_workers=max_workers, 
        progress_callback=progress_callback,
        target_precision="ROOFTOP"
    )