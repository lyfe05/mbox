import json
import base64
import time
import os
import sys
from .config import CACHE_FILE, API_HOST, BASE_HEADERS
from .ui import console

def is_token_expired(token):
    try:
        parts = token.split('.')
        if len(parts) != 3: return True
        payload = parts[1]
        payload += '=' * (-len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_str = decoded_bytes.decode('utf-8')
        data = json.loads(decoded_str)
        exp_timestamp = data.get('exp', 0)
        return exp_timestamp <= (time.time() + 60)
    except Exception:
        return True

def save_cached_token(token):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({"token": token}, f)
    except Exception as e:
        console.print(f"[dim red]Warning: Could not cache token: {e}[/]")

def load_cached_token():
    if not os.path.exists(CACHE_FILE): return None
    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            return data.get("token")
    except: return None

def get_token(session):
    cached_token = load_cached_token()
    if cached_token:
        if not is_token_expired(cached_token):
            console.print("[bold green]⚡ Using Cached Token[/]")
            return cached_token
        else:
            console.print("[dim yellow]⏰ Cached token expired. Refreshing...[/]")
    
    try:
        with console.status("[bold green]🔐 Authenticating...", spinner="dots"):
            resp = session.get(f"https://{API_HOST}/wefeed-h5api-bff/app/get-latest-app-pkgs?appName=moviebox", headers=BASE_HEADERS)
            resp.raise_for_status()
            user_data = json.loads(resp.headers.get("x-user", "{}"))
            token = user_data.get("token")
            if token:
                save_cached_token(token)
                return token
            raise ValueError("Token not found")
    except Exception as e:
        console.print(f"[bold red]❌ Auth Error: {e}[/]")
        sys.exit(1)
