import os

# --- Configuration & Constants ---
API_HOST = "h5-api.aoneroom.com"
CONTENT_HOST = "filmboom.top"
CACHE_FILE = "session.json"
CONFIG_FILE = "config.json"

# Base Download Path (Multiplatform)
IS_ANDROID = os.path.exists("/storage/emulated/0/Download")

def get_base_dir():
    # Helper to resolve path (Config > Android Default > PC Default)
    # This involves circular dependency if we import load_config here directly at top level 
    # if load_config uses constants. But load_config is below.
    # We will handle the variable assignment AFTER load_config is defined, or just use a getter.
    # For simplicity, let's keep the default here, but let mbox.py/downloader.py override it 
    # by reading the config themselves. 
    # OR, we move load_config to top or a separate utils?
    # Let's keep it simple: Define DEFAULT, then have a getter that checks config.
    if IS_ANDROID:
        return "/storage/emulated/0/Download/mbox cli"
    else:
        return os.path.join(os.path.expanduser("~"), "Downloads", "mbox cli")

BASE_DOWNLOAD_DIR = get_base_dir()

# Headers
BASE_HEADERS = {
    "host": API_HOST,
    "x-client-info": '{"timezone":"Africa/Nairobi"}',
    "accept": "application/json",
    "x-request-lang": "en",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Linux; Android 13; M2006C3LG Build/TQ3A.230901.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.123 Mobile Safari/537.36",
    "x-client-token": "1767186449,42f9e00068a146a4f07d4873e11cdeb0",
    "origin": "https://moviebox.ph",
    "x-requested-with": "mark.via.gp",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://moviebox.ph/",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9"
}

CONTENT_HEADERS = {
    "host": CONTENT_HOST,
    "x-client-info": '{"timezone":"Africa/Nairobi"}',
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Linux; Android 13; M2006C3LG Build/TQ3A.230901.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.123 Mobile Safari/537.36",
    "x-requested-with": "mark.via.gp",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9"
}

INITIAL_COOKIES = {"uuid": "474de23f-80b9-4f13-9c28-1321a55080b4"}

# --- Config Persistence ---
import json
from .ui import console

CONFIG_FILE = "config.json"

ANDROID_PLAYERS = {
    "Playify": "com.appnix.playify",
    "Network Stream (Video) Player": "com.genuine.leone",
    "MX Player": "com.mxtech.videoplayer.ad",
    "CricfyTV": "com.cricfy.tv",
    "Custom Input": "__CUSTOM__"
}

def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except: return {}

def save_config(data):
    try:
        # Load existing first to merge (if needed), or just overwrite
        current = load_config()
        current.update(data)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current, f, indent=4)
    except Exception as e:
        console.print(f"[red]Error saving config: {e}[/]")
