import requests
import time
from datetime import datetime
from src.config import OSM_EMAIL
from src.logger import log_api_call


def geocode_with_osm(address, email=OSM_EMAIL):
    """
    Géocode une adresse avec Nominatim (OpenStreetMap).
    
    Args:
        address: Adresse à géocoder
        email: Email requis par Nominatim (policy d'usage)
    
    Returns:
        dict: Résultat du géocodage avec le format standardisé
    """
    base_url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "email": email  # Requis par la politique d'utilisation de Nominatim
    }
    
    headers = {
        "User-Agent": "GeocodingApp/1.0 (contact via email parameter)"
    }
    
    start_time = time.time()
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                
                # Déterminer le niveau de précision basé sur le type OSM
                precision_level = determine_osm_precision(result)
                
                geocode_result = {
                    "status": "OK",
                    "api_used": "osm",
                    "latitude": float(result.get("lat")),
                    "longitude": float(result.get("lon")),
                    "formatted_address": result.get("display_name"),
                    "precision_level": precision_level,
                    "osm_type": result.get("type"),
                    "osm_class": result.get("class"),
                    "osm_place_id": result.get("place_id"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "response_time": round(response_time, 3)
                }
                
                log_api_call(
                    api_name="osm",
                    url=base_url,
                    status="success",
                    duration=response_time,
                    response=geocode_result
                )
                
                return geocode_result
            else:
                # Aucun résultat trouvé
                log_api_call(
                    api_name="osm",
                    url=base_url,
                    status="no_results",
                    duration=response_time
                )
                
                return {
                    "status": "ZERO_RESULTS",
                    "api_used": "osm",
                    "latitude": None,
                    "longitude": None,
                    "formatted_address": None,
                    "precision_level": None,
                    "error_message": "Aucun résultat trouvé",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "response_time": round(response_time, 3)
                }
        else:
            # Erreur HTTP
            error_msg = f"HTTP {response.status_code}: {response.text}"
            log_api_call(
                api_name="osm",
                url=base_url,
                status="error",
                duration=response_time,
                error=error_msg
            )
            
            return {
                "status": "ERROR",
                "api_used": "osm",
                "latitude": None,
                "longitude": None,
                "formatted_address": None,
                "precision_level": None,
                "error_message": error_msg,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "response_time": round(response_time, 3)
            }
            
    except requests.exceptions.Timeout:
        log_api_call(
            api_name="osm",
            url=base_url,
            status="timeout",
            duration=10.0,
            error="Timeout de la requête"
        )
        
        return {
            "status": "ERROR",
            "api_used": "osm",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "error_message": "Timeout de la requête",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "response_time": 10.0
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        log_api_call(
            api_name="osm",
            url=base_url,
            status="error",
            duration=response_time,
            error=str(e)
        )
        
        return {
            "status": "ERROR",
            "api_used": "osm",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "error_message": f"Erreur: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "response_time": round(response_time, 3)
        }


def determine_osm_precision(result):
    """
    Détermine le niveau de précision basé sur le type et la classe OSM.
    
    Mapping approximatif vers les niveaux Google:
    - ROOFTOP: Adresse précise (house, building)
    - RANGE_INTERPOLATED: Rue avec numéro interpolé
    - GEOMETRIC_CENTER: Rue, quartier
    - APPROXIMATE: Ville, région
    """
    osm_type = result.get("type", "").lower()
    osm_class = result.get("class", "").lower()
    
    # Précision maximale - bâtiment ou adresse exacte
    if osm_type in ["house", "building", "residential", "apartments"]:
        return "ROOFTOP"
    
    # Précision haute - rue avec numéro ou point d'intérêt précis
    if osm_type in ["address", "place", "shop", "amenity", "office"]:
        return "ROOFTOP"
    
    # Précision moyenne - rue ou quartier
    if osm_type in ["road", "street", "path", "footway", "pedestrian"]:
        return "RANGE_INTERPOLATED"
    
    if osm_type in ["neighbourhood", "suburb", "quarter", "district"]:
        return "GEOMETRIC_CENTER"
    
    # Précision basse - ville, région
    if osm_type in ["city", "town", "village", "municipality", "county", "state", "region"]:
        return "APPROXIMATE"
    
    # Par défaut
    return "GEOMETRIC_CENTER"


def geocode_with_osm_structured(street=None, city=None, postal_code=None, 
                                country=None, email=OSM_EMAIL):
    """
    Géocode avec des composants d'adresse structurés.
    
    Args:
        street: Rue
        city: Ville
        postal_code: Code postal
        country: Pays
        email: Email requis par Nominatim
    
    Returns:
        dict: Résultat du géocodage
    """
    base_url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "email": email
    }
    
    # Ajouter les composants structurés
    if street:
        params["street"] = street
    if city:
        params["city"] = city
    if postal_code:
        params["postalcode"] = postal_code
    if country:
        params["country"] = country
    
    headers = {
        "User-Agent": "GeocodingApp/1.0 (contact via email parameter)"
    }
    
    start_time = time.time()
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                precision_level = determine_osm_precision(result)
                
                geocode_result = {
                    "status": "OK",
                    "api_used": "osm",
                    "latitude": float(result.get("lat")),
                    "longitude": float(result.get("lon")),
                    "formatted_address": result.get("display_name"),
                    "precision_level": precision_level,
                    "osm_type": result.get("type"),
                    "osm_class": result.get("class"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "response_time": round(response_time, 3)
                }
                
                log_api_call(
                    api_name="osm",
                    url=base_url,
                    status="success",
                    duration=response_time,
                    response=geocode_result
                )
                
                return geocode_result
            else:
                log_api_call(
                    api_name="osm",
                    url=base_url,
                    status="no_results",
                    duration=response_time
                )
                
                return {
                    "status": "ZERO_RESULTS",
                    "api_used": "osm",
                    "latitude": None,
                    "longitude": None,
                    "formatted_address": None,
                    "precision_level": None,
                    "error_message": "Aucun résultat trouvé",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "response_time": round(response_time, 3)
                }
        else:
            error_msg = f"HTTP {response.status_code}"
            log_api_call(
                api_name="osm",
                url=base_url,
                status="error",
                duration=response_time,
                error=error_msg
            )
            
            return {
                "status": "ERROR",
                "api_used": "osm",
                "latitude": None,
                "longitude": None,
                "formatted_address": None,
                "precision_level": None,
                "error_message": error_msg,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "response_time": round(response_time, 3)
            }
            
    except Exception as e:
        response_time = time.time() - start_time
        log_api_call(
            api_name="osm",
            url=base_url,
            status="error",
            duration=response_time,
            error=str(e)
        )
        
        return {
            "status": "ERROR",
            "api_used": "osm",
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "precision_level": None,
            "error_message": f"Erreur: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "response_time": round(response_time, 3)
        }