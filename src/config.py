from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OSM_EMAIL = os.getenv("OSM_EMAIL")
HERE_API_KEY = os.getenv("HERE_API_KEY")