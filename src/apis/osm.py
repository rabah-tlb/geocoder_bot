import requests
import os

OSM_EMAIL = os.getenv("OSM_EMAIL")

def geocode_with_osm(address, email={OSM_EMAIL}):
    base_url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": f"GeocoderBot/1.0 ({email})"
    }
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "accept-language": "fr"
    }

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=8)
        data = response.json()

        if data:
            result = data[0]
            return {
                "latitude": float(result["lat"]),
                "longitude": float(result["lon"]),
                "formatted_address": result.get("display_name", address),
                "precision_level": "APPROXIMATE",
                "status": "OK",
                "api_used": "OpenStreetMap"
            }

        return {"status": "ZERO_RESULTS", "api_used": "OpenStreetMap"}
    except Exception as e:
        return {
            "status": "ERROR",
            "error_message": str(e),
            "api_used": "OpenStreetMap"
        }
