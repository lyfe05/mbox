import os

# --- Configuration & Constants ---
API_HOST = "h5-api.aoneroom.com"
CONTENT_HOST = "filmboom.top"
CACHE_FILE = "session.json"
CONFIG_FILE = "config.json"

# Base Download Path (Multiplatform)
if os.path.exists("/storage/emulated/0/Download"):
    # Android / Termux
    BASE_DOWNLOAD_DIR = "/storage/emulated/0/Download/mbox cli"
else:
    # Windows / Linux / Mac
    BASE_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "mbox cli")

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
    "Playify (Default)": "com.appnix.playify",
    "VLC for Android": "org.videolan.vlc",
    "MX Player": "com.mxtech.videoplayer.ad",
    "MX Player Pro": "com.mxtech.videoplayer.pro",
    "Next Player": "dev.anilbeesetti.nextplayer",
    "Just (Video) Player": "com.brouken.player"
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
