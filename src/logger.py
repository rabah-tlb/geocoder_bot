import json
import os
from datetime import datetime

LOG_FILE = "logs/geocoding_logs.json"

def log_api_call(api_name, url, status, duration, response=None, error=None):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "api": api_name,
        "url": url,
        "status": status,
        "duration": duration,
        "result": response if response else None,
        "error": error if error else None
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
