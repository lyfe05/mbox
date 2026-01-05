import sys
import os
import json
import ctypes
from pathlib import Path
from rich.prompt import Prompt
from rich.table import Table
from rich import box
from .ui import console, print_banner
from .config import CONFIG_FILE, ANDROID_PLAYERS, save_config

# --- Windows / VLC Logic (Adapted from file.py) ---

def is_admin() -> bool:
    """Return True if the current process has admin rights."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except: return False

def get_user_path() -> str:
    """Return the current user PATH string."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
        return winreg.QueryValueEx(key, "PATH")[0]

def set_user_path(new_path: str) -> None:
    """Write a new PATH string to the user environment."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)

def broadcast_environment_changed() -> None:
    """Send WM_SETTINGCHANGE so new consoles see the updated PATH."""
    try:
        from ctypes import wintypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            5000,
            ctypes.byref(wintypes.DWORD()),
        )
        console.print("[dim green]Environment broadcast sent.[/]")
    except Exception as e:
        console.print(f"[dim red]Broadcast failed: {e}[/]")

def append_to_path(folder: str) -> bool:
    """Add *folder* to the user PATH. Returns True if successful or already exists."""
    try:
        folder_clean = folder.rstrip("\\")
        raw_path = get_user_path()
        parts = [p.rstrip("\\") for p in raw_path.split(";") if p.strip()]

        if folder_clean.lower() in (p.lower() for p in parts):
            console.print(f"[dim]Folder already in PATH: {folder_clean}[/]")
            return True

        parts.append(folder_clean)
        new_path = ";".join(parts) + ";"
        set_user_path(new_path)
        console.print(f"[bold green]Added to user PATH: {folder_clean}[/]")
        broadcast_environment_changed()
        return True
    except Exception as e:
        console.print(f"[bold red]Failed to update PATH: {e}[/]")
        return False

def check_vlc_pc():
    """Checks for VLC in PATH or common locations. Tries to add to PATH if found."""
    # 1. Check if 'vlc' is already runnable
    import shutil
    if shutil.which("vlc"):
        console.print("[bold green]✅ VLC found in PATH.[/]")
        return True

    console.print("[yellow]⚠️  VLC not found in PATH. Searching common locations...[/]")
    
    # 2. Search common locations
    possible_paths = [
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "VideoLAN", "VLC"),
        os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "VideoLAN", "VLC")
    ]
    
    found_path = None
    for p in possible_paths:
        if os.path.exists(p) and os.path.isdir(p):
            found_path = p
            break
            
    if found_path:
        console.print(f"[green]Found VLC at: {found_path}[/]")
        # 3. Add to PATH
        # Note: 'file.py' has self-elevation logic. Here we just try, or warn.
        # Modifying HKCU Environment usually doesn't require full Admin for the *current user*,
        # but sometimes it might.
        if append_to_path(found_path):
            console.print("[bold green]✅ VLC added to PATH![/]")
            console.print("[dim]You may need to restart the terminal for changes to take effect.[/]")
            return True
        else:
            console.print("[bold red]❌ Failed to add VLC to PATH automatically.[/]")
            return False
    else:
        console.print("[bold red]❌ VLC not found on this system.[/]")
        console.print("Please install VLC Media Player and add it to your PATH.")
        return False

# --- Android Logic ---

def setup_android_player():
    """Prompts user to select a default Android player."""
    console.print("\n[bold cyan]🤖 Android Player Setup[/]")
    
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Player Name", style="white")
    table.add_column("Package Name", style="dim")
    
    players_list = list(ANDROID_PLAYERS.items()) # [(Name, Package), ...]
    
    for idx, (name, pkg) in enumerate(players_list):
        table.add_row(str(idx + 1), name, pkg)
        
    console.print(table)
    
    choice = Prompt.ask("Select Default Player", choices=[str(i+1) for i in range(len(players_list))], default="1")
    selected_name, selected_pkg = players_list[int(choice)-1]
    
    return {"player_name": selected_name, "player_package": selected_pkg}

# --- Main Setup ---

def run_setup():
    print_banner()
    console.print("[bold yellow]⚙️  First Run Setup[/]\n")
    
    config_data = {}
    
    # PC or Android?
    if os.path.exists("/storage/emulated/0/Download"):
        # Android
        console.print("[dim]Detected: Android Environment[/]")
        data = setup_android_player()
        config_data.update(data)
    else:
        # PC
        console.print("[dim]Detected: PC (Windows/Linux/Mac)[/]")
        if os.name == 'nt':
            check_vlc_pc()
        else:
             import shutil
             if shutil.which("vlc"):
                 console.print("[bold green]✅ VLC found.[/]")
             else:
                 console.print("[yellow]⚠️  VLC not found. Please install it.[/]")
                 
    # Save Config
    save_config(config_data)
    console.print("\n[bold green]✅ Setup Complete![/]")
    console.print("[dim]Configuration saved to config.json[/]\n")
    # Prompt.ask("Press Enter to continue to Main Menu")

