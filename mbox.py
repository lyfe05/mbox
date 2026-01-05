import sys
import os
import subprocess
import time

# --- Auto-Install Dependencies ---
def install_dependencies():
    # 1. Python Libraries
    required = ["requests", "rich"]
    installed = False
    for package in required:
        try:
            __import__(package)
        except ImportError:
            print(f"Package '{package}' not found. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                installed = True
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}. Please install manually.")
                sys.exit(1)
    
    # 2. Aria2 (External Tool)
    # Improved Check:
    # - Android: Check 'aria2c -v'
    # - PC: Check 'pip show aria2' (since pip install doesn't always add bin to PATH)
    is_android = os.path.exists("/storage/emulated/0/Download")
    aria2_present = False

    if is_android:
        try:
            # Check if running aria2c works
            subprocess.check_call(["aria2c", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            aria2_present = True
        except:
            aria2_present = False
            
        if not aria2_present:
            print("Aria2c not found. Installing via pkg...")
            try:
                subprocess.check_call(["pkg", "install", "aria2", "-y"])
                print("Aria2 installed via pkg.")
            except Exception as e:
                print(f"Failed to install aria2 via pkg: {e}")
    else:
        # PC / Python Environment
        try:
            # Check if pip package is installed
            subprocess.check_call([sys.executable, "-m", "pip", "show", "aria2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            aria2_present = True
        except:
            aria2_present = False
            
        if not aria2_present:
            print("Aria2 not found. Installing via pip...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "aria2"])
                print("Aria2 installed via pip.")
            except Exception as e:
                 print(f"Failed to install aria2 via pip: {e}")

    return installed # Only return True if Python libs were installed (needing restart)

def check_for_updates():
    """Checks for git updates and pulls them."""
    import json
    try:
        if os.path.exists("config.json"):
            with open("config.json", 'r') as f:
                 data = json.load(f)
                 if not data.get("auto_update", True):
                     return False
    except: pass

    import shutil
    if not shutil.which("git"): return False

    print("Checking for updates...")
    try:
        subprocess.check_call(["git", "fetch", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
             output = subprocess.check_output(["git", "status", "-uno"], text=True)
             if "behind" in output:
                 print("Update available. Pulling...")
                 subprocess.check_call(["git", "pull"]) 
                 print("Updated! Restarting...")
                 return True
        except: pass
    except Exception as e:
        print(f"Update check failed: {e}")
    return False

# Run Checks
updated = check_for_updates()
installed = install_dependencies()

if updated or installed:
    time.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

import requests
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from rich.rule import Rule

from src.ui import console, print_banner, display_content_table, ask_with_back
from src.auth import get_token
from src.api import (
    get_home_data, get_trending_content, search_content,
    get_movie_tab_data, get_tv_show_content, get_animation_content,
    get_trending_now_content, get_detail_data, get_play_streams,
    get_captions
)
from src.utils import clean_filename, parse_episode_input
from src.player import play_video
from src.downloader import run_aria2_download
from src.config import BASE_DOWNLOAD_DIR, CONTENT_HOST, CONTENT_HEADERS, CONFIG_FILE, IS_ANDROID
from src.setup import run_setup

# --- Main Application ---
def main():
    if not os.path.exists(CONFIG_FILE):
        run_setup()

    print_banner()
    session = requests.Session()
    token = get_token(session)
    if not token: return

    while True:
        menu_table = Table(show_header=False, box=box.SIMPLE)
        menu_table.add_column("Option", style="cyan")
        menu_table.add_column("Description", style="white")
        menu_table.add_row("1", "🏠 Homepage")
        menu_table.add_row("2", "🔥 Trending")
        menu_table.add_row("3", "🔍 Search")
        menu_table.add_row("4", "🎬 Movie")
        menu_table.add_row("5", "📺 Tv Show")
        menu_table.add_row("6", "🎨 Animation")
        menu_table.add_row("7", "🚀 Trending Now")
        menu_table.add_row("8", "⚙️  Settings")
        console.print(Panel(menu_table, title="[bold]Main Menu[/]", border_style="green"))

        menu_choice = Prompt.ask("Select Option", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="1")
        current_page = 0 # Start at page 0 (internal logic)
        content_list = []
        home_sections = [] # Cache for home sections
        current_home_section = None # The selected section object 
        movie_sections = [] # Cache for movie sections
        current_movie_section = None 
        search_keyword = None # Cache for search keyword

        while True:
            # --- HOMEPAGE LOGIC ---
            if menu_choice == "1":
                if not home_sections:
                     home_sections = get_home_data(session, token)
                
                # If we haven't selected a section yet, show Section Menu
                if not current_home_section:
                    sec_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
                    sec_table.add_column("#", justify="right", style="cyan")
                    sec_table.add_column("Section", style="white")
                    sec_table.add_column("Type", style="dim")
                    
                    for i, sec in enumerate(home_sections):
                        sec_table.add_row(str(i+1), sec['title'], sec['type'])
                        
                    console.print(Panel(sec_table, title="[bold]🏠 Home Sections[/]", border_style="green"))
                    console.print("[dim]Enter [bold green]Number[/] to Select | [bold yellow]B[/]ack to Main Menu[/dim]")
                    
                    inp = ask_with_back("Select Section", type='int')
                    if inp is None: break # Back to Main
                    
                    if inp > 0 and inp <= len(home_sections):
                        current_home_section = home_sections[inp-1]
                        current_page = 0 # Reset page for new section
                        # Fall through to 'content_list' population logic below
                    else:
                        console.print("[red]Invalid Section[/]")
                        continue
                
                # We have a section, populate content_list (paginated)
                # Client-Side Pagination (50 per page)
                full_items = current_home_section['items']
                start = current_page * 50
                end = start + 50
                content_list = full_items[start:end]
                has_more = end < len(full_items) # Client-side check
                
            # --- TRENDING LOGIC ---
            elif menu_choice == "2":
                content_list, has_more = get_trending_content(session, token, current_page)
            
            # --- SEARCH LOGIC ---
            elif menu_choice == "3":
                if not search_keyword:
                    search_keyword = Prompt.ask("[bold yellow]Enter Search Keyword[/]")
                
                content_list, has_more = search_content(session, token, search_keyword, current_page)
            
            # --- MOVIE LOGIC (SECTIONS) ---
            elif menu_choice == "4":
                if not movie_sections:
                     movie_sections = get_movie_tab_data(session, token)
                
                # If we haven't selected a section yet, show Section Menu
                if not current_movie_section:
                    sec_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
                    sec_table.add_column("#", justify="right", style="cyan")
                    sec_table.add_column("Movie Section", style="white")
                    sec_table.add_column("Type", style="dim")
                    
                    for i, sec in enumerate(movie_sections):
                        sec_table.add_row(str(i+1), sec['title'], sec['type'])
                        
                    console.print(Panel(sec_table, title="[bold]🎬 Movie Sections[/]", border_style="green"))
                    console.print("[dim]Enter [bold green]Number[/] to Select | [bold yellow]B[/]ack to Main Menu[/dim]")
                    
                    inp = ask_with_back("Select Section", type='int')
                    if inp is None: break # Back to Main
                    
                    if inp > 0 and inp <= len(movie_sections):
                        current_movie_section = movie_sections[inp-1]
                        current_page = 0 # Reset page for new section
                    else:
                        console.print("[red]Invalid Section[/]")
                        continue
                
                # We have a section, populate content_list (paginated)
                # Client-Side Pagination (50 per page)
                full_items = current_movie_section['items']
                start = current_page * 50
                end = start + 50
                content_list = full_items[start:end]
                has_more = end < len(full_items)
            
            # --- TV SHOW LOGIC ---
            elif menu_choice == "5":
                content_list, has_more = get_tv_show_content(session, token, current_page + 1) # API uses 1-based paging
            
            # --- ANIMATION LOGIC ---
            elif menu_choice == "6":
                content_list, has_more = get_animation_content(session, token, current_page + 1) # API uses 1-based paging

            # --- TRENDING NOW LOGIC ---
            elif menu_choice == "7":
                # API uses 1-based paging
                content_list, has_more = get_trending_now_content(session, token, current_page + 1)

            else: return

            # --- EMPTY CHECK ---
            if not content_list:
                console.print("[bold red]🚫 No content found (or end of list).[/]")
                if (menu_choice in ["2", "5", "6", "7"] or (menu_choice == "1" and current_home_section) or (menu_choice == "4" and current_movie_section)) and current_page > 0:
                    current_page -= 1
                    continue
                
                if menu_choice == "1":
                     # Empty section? Go back to section list
                     current_home_section = None
                     continue
                if menu_choice == "4":
                     current_movie_section = None
                     continue 
                
                if menu_choice not in ["2", "5", "6", "7"]: # Search case mostly
                     return 

            display_content_table(content_list, page=current_page if menu_choice in ["1", "2", "4", "5", "6", "7"] else None)

            # --- NAVIGATION / SELECTION ---
            if menu_choice in ["1", "2", "4", "5", "6", "7"]:
                nav_text = "[dim]Navigation: "
                if has_more:
                    nav_text += "[bold cyan]N[/]ext Page | "
                if current_page > 0:
                    nav_text += "[bold cyan]P[/]revious Page | "
                nav_text += "Enter [bold green]Number[/] to Select | [bold yellow]B[/]ack[/dim]"
                
                console.print(nav_text)
                user_input = Prompt.ask("Choice").strip().lower()
                
                if user_input == 'n': 
                    if has_more:
                         current_page += 1
                    else:
                         console.print("[dim yellow]End of list.[/]")
                    continue
                elif user_input == 'p': 
                    if current_page > 0: current_page -= 1
                    continue
                elif user_input == 'b': 
                    if menu_choice == "1":
                        current_home_section = None # Back to Section List
                        continue
                    elif menu_choice == "4":
                         current_movie_section = None
                         continue
                    else:
                        break # Back to Main Menu
            else:
                user_input = ask_with_back("Select # to watch")
                if user_input is None: break

            try:
                choice = int(user_input) - 1
                if choice < 0 or choice >= len(content_list): raise ValueError
                selected = content_list[choice]
            except (ValueError, TypeError):
                console.print("[red]Invalid selection.[/]")
                continue

            # --- Detail / Season / Action Loop ---
            while True:
                
                raw_title = selected.get('title', 'Unknown')
                s_id = selected.get('subjectId')
                d_path = selected.get('detailPath')

                detail_data = get_detail_data(session, s_id, d_path)
                if not detail_data: break

                resource = detail_data.get('resource', {})
                seasons_list = resource.get('seasons', [])
                
                # Logic: Type Detection
                # Helper to find key in multiple dicts taking nested 'subject' into account
                def find_meta(key, *sources):
                    for src in sources:
                        if not src: continue
                        if key in src and src[key]: return src[key]
                        if 'subject' in src and isinstance(src['subject'], dict):
                            sub = src['subject']
                            if key in sub and sub[key]: return sub[key]
                    return None

                description = find_meta('description', detail_data, selected) or 'No description available.'
                rating = find_meta('imdbRatingValue', detail_data, selected) or 'N/A'
                duration_val = find_meta('duration', detail_data, selected)
                
                formatted_duration = "N/A"
                if duration_val:
                    try:
                        d = int(duration_val)
                        if d > 0:
                            m, s = divmod(d, 60)
                            h, m = divmod(m, 60)
                            formatted_duration = f"{h:02d}:{m:02d}:{s:02d}"
                    except: pass
                
                info_text = f"[bold white]{raw_title}[/]\n"
                info_text += f"[dim]Rating: ⭐ {rating} | Duration: ⏳ {formatted_duration}[/]\n"
                info_text += f"[cyan]{description}[/]"

                if len(seasons_list) == 1 and seasons_list[0]['se'] == 0:
                    is_movie = True
                    console.print(Panel(info_text, title="[bold green]🎬 MOVIE DETAIL[/]", border_style="green"))
                else:
                    is_movie = False
                    console.print(Panel(info_text, title="[bold green]📺 SERIES DETAIL[/]", border_style="green"))
                    s_table = Table(box=box.SIMPLE_HEAD)
                    s_table.add_column("Season", style="cyan")
                    s_table.add_column("Episodes", style="magenta")
                    for s in seasons_list: s_table.add_row(f"Season {s['se']}", str(s.get('maxEp', 0)))
                    console.print(s_table)

                # --- Series / Movie Logic ---
                selected_eps = []
                selected_se = 0
                
                if is_movie:
                    pass 
                else:
                    try:
                        selected_se = ask_with_back("Enter Season Number", type='int')
                        if selected_se is None: break # Back to List
                        
                        season_data = next((item for item in seasons_list if item["se"] == selected_se), None)
                        if not season_data: 
                            console.print("[red]Invalid Season[/]")
                            continue
                            
                        max_ep = season_data.get('maxEp', 0)
                        
                        ep_input = ask_with_back(f"Enter Episode(s) (e.g. 1, 1-5, all) [Max: {max_ep}]")
                        if ep_input is None: continue # Back to Season input (actually restarts loop 3)

                        selected_eps = parse_episode_input(ep_input, max_ep)
                        if not selected_eps:
                            console.print("[red]No valid episodes selected.[/]")
                            continue
                    except: continue

                # --- Pre-flight Stream Fetching ---
                streams_map = {}
                valid_eps_ordered = []
                
                with console.status("[bold cyan]🚀 Pre-fetching stream info...", spinner="earth"):
                    to_fetch = selected_eps if selected_eps else ([0] if is_movie else [])
                    for ep_num in to_fetch:
                        se = selected_se if not is_movie else 0
                        ep = ep_num if not is_movie else 0
                        s_list = get_play_streams(session, s_id, d_path, se, ep)
                        if s_list:
                            streams_map[ep_num] = s_list
                            valid_eps_ordered.append(ep_num)
                        else:
                            console.print(f"[dim red]Warning: No streams found for Ep {ep_num}[/]")

                if not valid_eps_ordered:
                    console.print("[bold red]❌ No streams found.[/]")
                    continue # Restart Loop 3 (Select again)

                # Use first valid episode to show Quality Options
                first_ep = valid_eps_ordered[0]
                base_streams = streams_map[first_ep]

                # --- Quality Selection Logic ---
                import json
                default_q = "Ask"
                try:
                    if os.path.exists("config.json"):
                        with open("config.json", 'r') as f:
                            data = json.load(f)
                            default_q = data.get("default_quality", "Ask")
                except: pass

                target_res = None
                
                if default_q != "Ask":
                    # Try to find default_q (e.g., "1080p")
                    target_res_int = int(default_q.replace("p", ""))
                    
                    # Sort streams by resolution descending
                    base_streams_sorted = sorted(base_streams, key=lambda x: int(x.get('resolutions', 0)), reverse=True)
                    
                    # 1. Exact Match
                    match = next((s for s in base_streams_sorted if int(s.get('resolutions')) == target_res_int), None)
                    
                    # 2. Fallback (first one that is smaller or equal, or just the best one available)
                    if not match:
                        console.print(f"[bold yellow]⚠️  Preferred quality {default_q} not found. Falling back to best available.[/]")
                        match = base_streams_sorted[0] # Pick the highest available
                        
                    target_res = match.get('resolutions')
                    console.print(f"[green]✅ Auto-selected Quality: {target_res}p[/]")
                
                else:
                    # Manual Selection
                    q_title = "Available Qualities" if is_movie else f"Available Qualities (Based on Ep {first_ep})"
                    q_table = Table(title=q_title, box=box.ROUNDED)
                    q_table.add_column("#", justify="right", style="cyan")
                    q_table.add_column("Resolution", style="green")
                    q_table.add_column("Size (Approx)", style="yellow")
                    for idx, stream in enumerate(base_streams):
                        size_mb = f"{int(stream.get('size', 0)) / (1024 * 1024):.2f} MB"
                        q_table.add_row(str(idx + 1), f"{stream.get('resolutions')}p", size_mb)
                    console.print(q_table)

                    target_res_val = None
                    q_idx_val = ask_with_back("Select Quality", type='int', default=1)
                    if q_idx_val is None: break 
                    
                    try:
                        q_idx = q_idx_val - 1
                        if q_idx < 0 or q_idx >= len(base_streams): raise ValueError
                        target_res = base_streams[q_idx].get('resolutions')
                    except: continue

                # --- Verify Quality Availability ---
                episode_quality_map = {}
                limit_quality_map = {}
                missing_eps = []

                for ep_num in valid_eps_ordered:
                    s_list = streams_map[ep_num]
                    match = next((s for s in s_list if str(s.get('resolutions')) == str(target_res)), None)
                    if match:
                        episode_quality_map[ep_num] = match.get('url')
                        limit_quality_map[ep_num] = match.get('resolutions')
                    else:
                        missing_eps.append(ep_num)

                # Handle Mismatches
                if missing_eps:
                    console.print(f"\n[bold yellow]⚠️  Quality '{target_res}p' is missing for {len(missing_eps)} episodes.[/]")
                    console.print("Fallback required for specific episodes.")
                    
                    abort_mismatch = False
                    for miss_ep in missing_eps:
                         s_list = streams_map[miss_ep]
                         console.print(f"\n[bold]Episode {miss_ep} Options:[/]")
                         for i, s in enumerate(s_list):
                             console.print(f"  {i+1}. {s.get('resolutions')}p ({int(s.get('size',0))/1048576:.0f}MB)")
                         
                         sel = ask_with_back(f"Select quality for Ep {miss_ep}", type='int', default=1)
                         if sel is None: 
                             abort_mismatch = True
                             break
                         
                         sel_idx = sel - 1
                         if sel_idx < 0 or sel_idx >= len(s_list): sel_idx = 0
                         chosen = s_list[sel_idx]
                         episode_quality_map[miss_ep] = chosen.get('url')
                         limit_quality_map[miss_ep] = chosen.get('resolutions')
                    
                    if abort_mismatch: continue

                # --- Subtitle Logic ---
                episode_subtitle_map = {} # Map: ep_num -> subtitle_url
                
                if valid_eps_ordered:
                     # We need to determine the user's preferred language using the first available episode
                     first_ep_num = valid_eps_ordered[0]
                     first_streams = streams_map.get(first_ep_num, [])
                     first_id = s_id
                     if first_streams: first_id = first_streams[0].get("id", s_id)
                     
                     # Fetch first to ask user
                     first_captions = get_captions(session, s_id, d_path, first_id)
                     
                     selected_lan_name = None # For matching others
                     
                     if first_captions and not IS_ANDROID:
                         console.print(f"\n[bold cyan]Select Subtitle ({'Movie' if is_movie else 'Series Batch'}):[/]")
                         
                         eng_idx = 1
                         for i, cap in enumerate(first_captions):
                             lang = cap.get('lanName', 'Unknown')
                             is_default = "en" in cap.get('lan', '').lower()
                             style = "green" if is_default else "white"
                             prefix = "✅ " if is_default else "   "
                             console.print(f"  {i+1}. {prefix}{lang}")
                             if is_default: eng_idx = i + 1
                         
                         none_idx = len(first_captions) + 1
                         console.print(f"  {none_idx}. None")
                         
                         choice = ask_with_back("Select Subtitle", type='int', default=eng_idx)
                         if choice is None: continue # Back logic might be tricky here, effectively skips subs
                         
                         if choice > 0 and choice <= len(first_captions):
                             target_cap = first_captions[choice-1]
                             selected_lan_name = target_cap.get('lanName')
                             console.print(f"[dim green]Selected Language: {selected_lan_name}[/]")
                             
                             # Assign for first episode
                             episode_subtitle_map[first_ep_num] = target_cap.get('url')
                         elif choice == none_idx:
                             console.print("[dim]No subtitles selected.[/]")
                             selected_lan_name = "NONE" 
                         else:
                             console.print("[red]Invalid selection.[/]")
                             # Continue without subs? or retry? let's continue without
                     
                     # If we have a selection (and it's not None), fetch for the rest
                     if selected_lan_name and selected_lan_name != "NONE":
                         remaining_eps = valid_eps_ordered[1:]
                         if remaining_eps:
                             with console.status(f"[bold yellow]📜 Matching subtitles for {len(remaining_eps)} episodes...", spinner="dots"):
                                 for ep_num in remaining_eps:
                                     streams = streams_map.get(ep_num, [])
                                     cur_id = s_id
                                     if streams: cur_id = streams[0].get("id", s_id)
                                     
                                     caps = get_captions(session, s_id, d_path, cur_id)
                                     # Find match
                                     match = next((c for c in caps if c.get('lanName') == selected_lan_name), None)
                                     if match:
                                         episode_subtitle_map[ep_num] = match.get('url')
                                     else:
                                         # Fallback to English? Or just None?
                                         # Let's try English fallback if exact match fails
                                         fallback = next((c for c in caps if "en" in c.get('lan', '').lower()), None)
                                         if fallback:
                                              episode_subtitle_map[ep_num] = fallback.get('url')


                # --- Action Menu ---
                console.print("\n")
                action_table = Table(show_header=False, box=box.SIMPLE)
                action_table.add_column("Option", style="cyan")
                action_table.add_column("Action", style="white")
                action_table.add_row("1", "▶️  Play")
                action_table.add_row("2", "⬇️  Download")
                
                console.print(Panel(action_table, title="[bold]Select Action[/]", border_style="blue"))
                action = ask_with_back("Choice", choices=["1", "2"], default="1")
                if action is None: continue

                # --- Execution Loop ---
                for current_ep in valid_eps_ordered:
                    real_se = selected_se if not is_movie else 0
                    real_ep = current_ep if not is_movie else 0
                    
                    video_url = episode_quality_map.get(current_ep)
                    res_label = limit_quality_map.get(current_ep)
                    if not video_url: continue 

                    final_referer = f"https://{CONTENT_HOST}/spa/videoPlayPage/movies/{d_path}?id={s_id}&type=/movie/detail&detailSe=&detailEp=&lang=en"
                    # Use CONTENT_HEADERS user-agent as default logic or from config
                    final_ua = CONTENT_HEADERS['user-agent']
                    
                    sub_url_for_ep = episode_subtitle_map.get(current_ep)
                    
                    if action == "1":
                        link_label = f"PLAYABLE LINK ({res_label}p)" if is_movie else f"PLAYABLE LINK (Ep {real_ep} - {res_label}p)"
                        console.print(f"\n[bold green]✅ {link_label}[/]")
                        play_video(video_url, final_referer, final_ua, sub_url_for_ep)
                        console.print(Rule(style="dim"))
                    elif action == "2":
                        safe_title = clean_filename(raw_title)
                        if is_movie:
                            # User requested subfolder for each movie: Movies/Title/Title.mp4
                            final_folder = os.path.join(BASE_DOWNLOAD_DIR, "Movies", safe_title)
                            filename = f"{safe_title}_{res_label}p.mp4"
                        else:
                            season_folder = f"S{real_se:02d}"
                            final_folder = os.path.join(BASE_DOWNLOAD_DIR, "Series", safe_title, season_folder)
                            filename = f"{safe_title}_S{real_se:02d}E{real_ep:02d}_{res_label}p.mp4"
                            
                        run_aria2_download(video_url, filename, final_folder, final_referer, final_ua, sub_url_for_ep)

                # --- Post-Action Menu ---
                console.print("\n[bold green]Done![/]")
                if is_movie:
                    Prompt.ask("[dim]Press Enter to return to Menu[/]")
                    break # Break Loop 3 -> Loop 2 (List)
                else:
                    pa_choice = Prompt.ask("Actions: [bold white]Enter[/] (Menu) | [bold yellow]s[/] (Seasons)", default="")
                    if pa_choice.lower() == 's':
                        continue # Restart Loop 3 (Season Selection)
                    else:
                        break # Break Loop 3 -> Loop 2 (List)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Exiting... Goodbye![/]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected Error: {e}[/]")
        sys.exit(1)