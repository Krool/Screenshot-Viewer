import requests
from typing import Optional
from pathlib import Path

STEAM_API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
STORE_API_URL = "https://store.steampowered.com/api/appdetails"

def fetch_steam_app_list() -> Optional[dict]:
    """Fetch the complete Steam app list from their API."""
    try:
        response = requests.get(STEAM_API_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        logging.error(f"Steam API request failed: {e}")
    return None

def fetch_app_details(app_id: str) -> Optional[dict]:
    """Fetch details for a specific Steam app."""
    try:
        url = f"{STORE_API_URL}?appids={app_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        logging.error(f"Steam Store API request failed: {e}")
    return None 