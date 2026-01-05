import os
import subprocess
import requests
from .ui import console

def run_aria2_download(url, filename, folder_path, referer, user_agent, subtitle_url=None):
    """Executes aria2c with organized paths and quiet output."""
    
    # 1. Create directory if not exists
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
            console.print(f"[green]📁 Created directory: {folder_path}[/]")
        except PermissionError:
            console.print("[bold red]❌ Permission Denied![/] Please check directory permissions.")
            if "/storage/emulated/0" in folder_path:
                console.print("On Termux: Run [bold yellow]termux-setup-storage[/] to grant access.")
            return

    # Download Subtitle if available (simple requests)
    if subtitle_url:
        srt_file = os.path.splitext(filename)[0] + ".srt"
        srt_path = os.path.join(folder_path, srt_file)
        try:
            console.print(f"[dim]⬇️  Downloading Subtitle...[/]")
            # Doing a quick fetch
            r = requests.get(subtitle_url)
            with open(srt_path, 'wb') as f:
                f.write(r.content)
            console.print(f"[dim green]✅ Subtitle saved![/]")
        except Exception as e:
            console.print(f"[dim red]⚠️ Failed to download sub: {e}[/]")

    console.print(f"\n[bold green]⬇️  Starting Aria2 Download...[/]")
    console.print(f"[dim]Folder: {folder_path}[/]")
    console.print(f"[dim]File:   {filename}[/]")
    
    # ARIA2C COMMAND (SPAM FREE)
    cmd = [
        "aria2c",
        url,
        "-d", folder_path,
        "-o", filename,
        "-c", # Enable resuming
        "--header", f"Referer: {referer}",
        "--user-agent", user_agent,
        "--file-allocation=none",
        "-x", "16",  # 16 connections
        "-s", "16",  # 16 servers
        "-k", "1M",  # 1MB chunk size
        "--console-log-level=warn", # Only shows errors/warnings
        "--summary-interval=0"      # DISABLES THE SPAMMY SUMMARY BLOCK
    ]
    
    try:
        # Use subprocess to run aria2c. It will show its own progress bar.
        subprocess.run(cmd)
        console.print(f"\n[bold green]✅ Download Complete![/]")
    except FileNotFoundError:
        console.print("[bold red]❌ Error: 'aria2c' not found.[/]")
        console.print("Install Aria2: [yellow]pkg install aria2[/] (Termux) or [yellow]winget install aria2[/] (Windows)[/]")
