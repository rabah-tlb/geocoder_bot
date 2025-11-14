import requests
import time
from datetime import datetime
from src.config import HERE_API_KEY
from src.logger import log_api_call

def determine_here_precision(match_level: str) -> str:
    if not match_level:
        return "UNKNOWN"
    match_level = match_level.lower()
    if match_level == "housenumber":
        return "ROOFTOP"
    elif match_level in ["intersection", "street"]:
        return "RANGE_INTERPOLATED"
    elif match_level == "postalcode":
        return "GEOMETRIC_CENTER"
    elif match_level in [
        "city", "locality", "district", "county", "state",
        "place", "country", "administrativearea"
    ]:
        return "APPROXIMATE"
    else:
        return "UNKNOWN"

def geocode_with_here(address: str) -> dict:
    url = "https://geocode.search.hereapi.com/v1/geocode"
    params = {
        "q": address,
        "apiKey": HERE_API_KEY,
        "in": "countryCode:TUN"
    }

    start_time = time.time()

    try:
        response = requests.get(url, params=params, timeout=10)
        duration = time.time() - start_time
        data = response.json()
        items = data.get("items", [])
        
        log_api_call("here", response.url, "OK" if items else "ZERO_RESULTS", duration, response=data)

        if items:
            result = items[0]
            raw_type = result.get("resultType")
            return {
                "latitude": result["position"].get("lat"),
                "longitude": result["position"].get("lng"),
                "formatted_address": result.get("address", {}).get("label", ""),
                "status": "OK",
                "error_message": None,
                "api_used": "here",
                "precision_level": determine_here_precision(raw_type),
                "precision_level_raw": raw_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                "precision_level_raw": None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    except Exception as e:
        duration = time.time() - start_time
        log_api_call("here", url, "ERROR", duration, error=str(e))
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "status": "ERROR",
            "error_message": str(e),
            "api_used": "here",
            "precision_level": None,
            "precision_level_raw": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
