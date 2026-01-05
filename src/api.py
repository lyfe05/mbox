from .config import API_HOST, CONTENT_HOST, BASE_HEADERS, CONTENT_HEADERS, INITIAL_COOKIES
from .ui import console

def parse_operating_list(data):
    """Parses the 'operatingList' from API response into section dicts."""
    sections = []
    if "data" in data and "operatingList" in data["data"]:
        for op in data["data"]["operatingList"]:
            # We map types to our structure
            stype = op.get("type")
            title = op.get("title", f"Section {op.get('position', '?')}")
            
            # Exclusion List (as per user request)
            if title in ["Get the VIP!", "Popular cartoon characters"]:
                continue

            items = []

            if stype == "BANNER":
                if "banner" in op and "items" in op["banner"]:
                    items = op["banner"]["items"]
            elif stype == "SUBJECTS_MOVIE":
                if "subjects" in op:
                    items = op["subjects"]
            
            # Generic fallback for CUSTOM or other types
            # Check for 'items' or 'subjects' directly or in customData
            elif op.get("customData") and "items" in op["customData"]:
                items = op["customData"]["items"]
            elif "items" in op:
                items = op["items"]
            elif "subjects" in op:
                items = op["subjects"]
            
            # Normalize items: If an item wraps the real content in 'subject', unwrap it.
            # This fixes empty titles in CUSTOM sections.
            normalized_items = []
            for it in items:
                if not it.get("title") and "subject" in it:
                    normalized_items.append(it["subject"])
                else:
                    normalized_items.append(it)
            items = normalized_items

            if items:
                 sections.append({
                     "title": title,
                     "type": stype,
                     "items": items
                 })
    return sections

def get_home_data(session, token):
    """Returns a list of section dicts: {title, type, items}"""
    headers = BASE_HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    with console.status("[bold cyan]🏠 Fetching Home Sections...", spinner="earth"):
        try:
            resp = session.get(f"https://{API_HOST}/wefeed-h5api-bff/home?host=moviebox.ph", headers=headers)
            return parse_operating_list(resp.json())
        except Exception as e:
            console.print(f"[red]Error fetching home: {e}[/]")
            return []

def get_trending_content(session, token, page=0, per_page=30):
    params = {"page": page, "perPage": per_page}
    headers = BASE_HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    with console.status(f"[bold yellow]🔥 Fetching Trending (Page {page})...", spinner="dots"):
        try:
            resp = session.get(f"https://{API_HOST}/wefeed-h5api-bff/subject/trending", headers=headers, params=params)
            data = resp.json().get("data", {})
            items = data.get("subjectList", [])
            has_more = data.get("pager", {}).get("hasMore", False)
            return items, has_more
        except: return [], False

def get_movie_tab_data(session, token):
    """Returns a list of section dicts for Movie Tab."""
    headers = BASE_HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    with console.status("[bold magenta]🎬 Fetching Movie Sections...", spinner="dots"):
        try:
            params = {"tabId": "ONEROOM_MOVIE", "host": "moviebox.ph"}
            resp = session.get(f"https://{API_HOST}/wefeed-h5api-bff/tab-operating", headers=headers, params=params)
            return parse_operating_list(resp.json())
        except Exception as e:
            console.print(f"[red]Error fetching movies: {e}[/]")
            return []

def get_tv_show_content(session, token, page=1, per_page=28):
    headers = BASE_HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    # Channel ID fixed to 2 as per request
    payload = {"page": page, "perPage": per_page, "channelId": 2}
    with console.status(f"[bold magenta]📺 Fetching TV Shows (Page {page})...", spinner="dots"):
        try:
            resp = session.post(f"https://{API_HOST}/wefeed-h5api-bff/subject/filter", headers=headers, json=payload)
            data = resp.json().get("data", {})
            items = data.get("items", []) or data.get("subjectList", [])
            has_more = data.get("pager", {}).get("hasMore", False)
            return items, has_more
        except: return [], False

def get_animation_content(session, token, page=1, per_page=28):
    headers = BASE_HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    # Channel ID fixed to 1006 as per request
    payload = {"page": page, "perPage": per_page, "channelId": 1006}
    with console.status(f"[bold yellow]🎨 Fetching Animation (Page {page})...", spinner="dots"):
        try:
            resp = session.post(f"https://{API_HOST}/wefeed-h5api-bff/subject/filter", headers=headers, json=payload)
            data = resp.json().get("data", {})
            items = data.get("items", []) or data.get("subjectList", [])
            has_more = data.get("pager", {}).get("hasMore", False)
            return items, has_more
        except: return [], False

def search_content(session, token, keyword, page=0):
    headers = BASE_HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    payload = {"keyword": keyword, "perPage": 30, "page": page}
    with console.status(f"[bold magenta]🔍 Searching for '{keyword}' (Page {page})...", spinner="dots"):
        try:
            resp = session.post(f"https://{API_HOST}/wefeed-h5api-bff/subject/search", headers=headers, json=payload)
            # Check both locations just in case API varies
            data = resp.json()
            items = data.get("data", {}).get("items", []) or data.get("data", {}).get("subjectList", [])
            # Search usually doesn't have standard pager, but we'll try safe get
            has_more = data.get("data", {}).get("pager", {}).get("hasMore", False)
            return items, has_more
        except: return [], False


def get_detail_data(session, subject_id, detail_path):
    params = {"subjectId": subject_id, "detail_path": detail_path}
    headers = CONTENT_HEADERS.copy()
    headers["referer"] = f"https://{CONTENT_HOST}/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&type=/movie/detail&detailSe=&detailEp=&lang=en"
    with console.status("[bold blue]📋 Fetching Details...", spinner="dots"):
        try:
            resp = session.get(f"https://{CONTENT_HOST}/wefeed-h5-bff/web/subject/detail", headers=headers, params=params, cookies=INITIAL_COOKIES)
            return resp.json().get("data", {})
        except: return {}

def get_play_streams(session, subject_id, detail_path, se, ep):
    params = {"subjectId": subject_id, "se": se, "ep": ep, "detail_path": detail_path}
    headers = CONTENT_HEADERS.copy()
    headers["referer"] = f"https://{CONTENT_HOST}/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&type=/movie/detail&detailSe=&detailEp=&lang=en"
    with console.status("[bold green]🚀 Generating Stream Links...", spinner="runner"):
        try:
            resp = session.get(f"https://{CONTENT_HOST}/wefeed-h5-bff/web/subject/play", headers=headers, params=params, cookies=INITIAL_COOKIES)
            return resp.json().get("data", {}).get("streams", [])
        except: return []

def get_captions(session, subject_id, detail_path, movie_id):
    """Fetches valid subtitles for a movie."""
    params = {
        "format": "MP4",
        "id": movie_id,
        "subjectId": subject_id,
        "detail_path": detail_path
    }
    headers = CONTENT_HEADERS.copy()
    headers["referer"] = f"https://{CONTENT_HOST}/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&type=/movie/detail&detailSe=&detailEp=&lang=en"
    
    with console.status("[bold yellow]📜 Fetching Subtitles...", spinner="dots"):
        try:
            resp = session.get(f"https://{CONTENT_HOST}/wefeed-h5-bff/web/subject/caption", headers=headers, params=params, cookies=INITIAL_COOKIES)
            data = resp.json()
            return data.get("data", {}).get("captions", [])
        except: return []

def get_trending_now_content(session, token, page=1, per_page=20):
    headers = BASE_HEADERS.copy()
    headers["authorization"] = f"Bearer {token}"
    # ID fixed to 1232643093049001320 as per request
    params = {"id": "1232643093049001320", "page": page, "perPage": per_page}
    with console.status(f"[bold red]🚀 Fetching Trending Now (Page {page})...", spinner="dots"):
        try:
            resp = session.get(f"https://{API_HOST}/wefeed-h5api-bff/ranking-list/content", headers=headers, params=params)
            data = resp.json().get("data", {})
            items = data.get("items", []) or data.get("subjectList", []) or data.get("contentList", [])
            has_more = data.get("pager", {}).get("hasMore", False)
            return items, has_more
        except: return [], False
