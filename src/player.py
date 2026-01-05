import os
import subprocess
import tempfile
import requests
from .ui import console

from .config import load_config

def play_video(url, referer, user_agent, subtitle_url=None):
    """Launches player (VLC on PC, Intent on Android)."""
    
    # 1. Android (Termux)
    if os.path.exists("/storage/emulated/0/Download"): 
        console.print(f"\n[bold green]📱 Launching Android Player...[/]")
        
        config = load_config()
        player_pkg = config.get("player_package", "com.appnix.playify") # Default
        
        # Construct the "Pipes" format that some players (MX, NS Player) support
        # Format: url|key=value&key2=value2
        final_data_uri = f"{url}|Referer={referer}&User-Agent={user_agent}"
        
        # AM Command (Termux)
        # -a android.intent.action.VIEW
        # -d "{DATA_URI}"
        # -t "video/*"
        cmd = [
            "am", "start",
            "--user", "0",
            "-a", "android.intent.action.VIEW",
            "-d", final_data_uri,
            "-t", "video/*",
            "-p", player_pkg
        ]
        
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print(f"[dim]Intent sent to '{player_pkg}'.[/]")
        except FileNotFoundError:
            console.print("[bold red]❌ Error: 'am' command not found (Not in Termux?).[/]")

    # 2. PC (Windows/Linux/Mac)
    else:
        console.print(f"\n[bold green]▶️  Launching VLC (PC)...[/]")
        cmd = [
            "vlc",
            url,
            f"--http-referrer={referer}",
            f"--http-user-agent={user_agent}",
            "--meta-title=MovieBox Stream" 
        ]
        if subtitle_url:
            # VLC on Windows often fails with remote subtitle URLs (file:// mixing).
            # We must download it to a temp file.
            try:
                
                console.print("[dim]⏳ Downloading subtitles for VLC...[/]")
                r = requests.get(subtitle_url)
                # Create temp file, but we need to keep the path to pass to VLC.
                # standard NamedTemporaryFile auto-deletes on close in Python < 3.12 on Windows? 
                # Actually, delete=False is safer, checking OS.
                # We'll put it in the same temp folder but not auto delete immediately to ensure VLC acts on it.
                # Or just use delete=False and rely on OS cleanup or let it persist in temp.
                tf = tempfile.NamedTemporaryFile(delete=False, suffix=".srt")
                tf.write(r.content)
                tf.close()
                
                cmd.append(f"--sub-file={tf.name}")
            except Exception as e:
                console.print(f"[dim red]⚠️ Failed to load subs: {e}[/]")

        try:
            subprocess.run(cmd) 
        except FileNotFoundError:
            console.print("[bold red]❌ Error: 'vlc' not found.[/]")
            console.print("Ensure VLC is installed and in your PATH.")
