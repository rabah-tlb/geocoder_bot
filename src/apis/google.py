import requests
import time
from datetime import datetime
from src.config import GOOGLE_API_KEY
from src.logger import log_api_call


def get_place_id_with_google(query: str) -> str:
    """
    Recherche un place_id Google à partir d'une requête textuelle.
    
    Args:
        query: Texte de recherche (ex: nom + ville)
    
    Returns:
        place_id si trouvé, None sinon
    """
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


def geocode_with_google(address: str = None, components_dict: dict = None, place_id: str = None) -> dict:
    """
    Géocode une adresse via l'API Google Maps.
    
    Args:
        address: Adresse à géocoder
        components_dict: Dictionnaire contenant postal_code, city, governorate
        place_id: ID Google d'un lieu spécifique
    
    Returns:
        Dictionnaire avec latitude, longitude, adresse formatée, status, etc.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "key": GOOGLE_API_KEY,
        "region": "tn"
    }

    # Si on a un place_id, l'utiliser directement
    if place_id:
        params["place_id"] = place_id
    else:
        # Construire les composants pour la Tunisie
        components_parts = ["country:TN"]
        if components_dict:
            if components_dict.get("postal_code"):
                components_parts.append(f"postal_code:{components_dict['postal_code']}")
            if components_dict.get("city"):
                components_parts.append(f"locality:{components_dict['city']}")
            if components_dict.get("governorate"):
                components_parts.append(f"administrative_area_level_1:{components_dict['governorate']}")
        
        params["components"] = "|".join(components_parts)
        if address:
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
                "precision_level_raw": result["geometry"].get("location_type", None),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                "precision_level_raw": None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
            "precision_level_raw": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


def geocode_with_google_simple(address: str) -> dict:
    """
    Version simplifiée pour géocoder uniquement avec une adresse string.
    Utile pour le fallback après HERE.
    
    Args:
        address: Adresse complète à géocoder
    
    Returns:
        Dictionnaire avec les résultats du géocodage
    """
    return geocode_with_google(address=address, components_dict={"country": "TN"})


def geocode_with_google_components(address: str, postal_code: str = None, 
                                   city: str = None, governorate: str = None) -> dict:
    """
    Géocode avec des composants d'adresse séparés pour plus de précision.
    
    Args:
        address: Adresse (rue)
        postal_code: Code postal
        city: Ville
        governorate: Gouvernorat
    
    Returns:
        Dictionnaire avec les résultats du géocodage
    """
    components_dict = {
        "postal_code": postal_code,
        "city": city,
        "governorate": governorate
    }
    return geocode_with_google(address=address, components_dict=components_dict)


def geocode_with_google_place(name: str, city: str = None, country: str = "Tunisia") -> dict:
    """
    Géocode un lieu par son nom (entreprise, monument, etc.).
    
    Args:
        name: Nom du lieu
        city: Ville (optionnel)
        country: Pays (par défaut Tunisia)
    
    Returns:
        Dictionnaire avec les résultats du géocodage
    """
    # Construire la requête
    query_parts = [name]
    if city:
        query_parts.append(city)
    if country:
        query_parts.append(country)
    query = " ".join(query_parts)
    
    # Obtenir le place_id
    place_id = get_place_id_with_google(query)
    
    if place_id:
        return geocode_with_google(place_id=place_id)
    else:
        # Fallback sur géocodage classique
        return geocode_with_google(address=query)