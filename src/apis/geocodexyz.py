import requests
import os

GEOCODEXYZ_KEY = os.getenv("GEOCODEXYZ_KEY")

def geocode_with_geocodexyz(address):
    base_url = "https://geocode.xyz"
    params = {
        "locate": address,
        "json": 1
    }
    if GEOCODEXYZ_KEY:
        params["auth"] = GEOCODEXYZ_KEY

    try:
        response = requests.get(base_url, params=params, timeout=8)
        data = response.json()

        if 'error' in data:
            return {
                "status": "ERROR",
                "error_message": data['error'].get('description', 'unknown'),
                "api_used": "Geocode.xyz"
            }

        if 'latt' in data and 'longt' in data:
            return {
                "latitude": float(data['latt']),
                "longitude": float(data['longt']),
                "formatted_address": data.get('standard', {}).get('addresst', address),
                "precision_level": "APPROXIMATE",
                "status": "OK",
                "api_used": "Geocode.xyz"
            }

        return {"status": "ZERO_RESULTS", "api_used": "Geocode.xyz"}
    except Exception as e:
        return {
            "status": "ERROR",
            "error_message": str(e),
            "api_used": "Geocode.xyz"
        }
