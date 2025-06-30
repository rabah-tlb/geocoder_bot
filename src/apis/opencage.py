import requests
import os

OPEN_CAGE_KEY = os.getenv("OPEN_CAGE_KEY")

def geocode_with_opencage(address):
    if not OPEN_CAGE_KEY:
        return None
    url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={OPEN_CAGE_KEY}&language=fr&countrycode=tn"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data['results']:
            result = data['results'][0]
            return {
                "latitude": result['geometry']['lat'],
                "longitude": result['geometry']['lng'],
                "formatted_address": result['formatted'],
                "precision_level": result['components'].get("_type", "UNKNOWN"),
                "status": "OK",
                "api_used": "OpenCage"
            }
        return {"status": "ZERO_RESULTS", "api_used": "OpenCage"}
    except Exception as e:
        return {"status": "ERROR", "error_message": str(e), "api_used": "OpenCage"}
