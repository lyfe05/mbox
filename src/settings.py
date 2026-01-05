from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from .ui import console, ask_with_back
from .config import load_config, save_config, ANDROID_PLAYERS, IS_ANDROID
from .setup import setup_android_player

def settings_menu():
    """Displays the settings menu and handles configuration updates."""
    while True:
        config = load_config()
        
        # Load current values
        curr_player = config.get("player_name", "Unknown")
        curr_quality = config.get("default_quality", "Ask")
        curr_path = config.get("download_path", "Default")
        curr_update = config.get("auto_update", True)
        
        console.print("\n")
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Option", style="cyan")
        table.add_column("Setting", style="white")
        table.add_column("Current Value", style="yellow")
        
        if IS_ANDROID:
            table.add_row("1", "🤖 Android Player", curr_player)
        else:
            table.add_row("1", "🖥️  PC Player", "VLC (System Default)")
            
        table.add_row("2", "📺 Default Quality", curr_quality)
        table.add_row("3", "📂 Download Path", curr_path)
        table.add_row("4", "🔄 Auto Update", "On" if curr_update else "Off")
        table.add_row("0", "🔙 Back to Main Menu", "")
        
        console.print(Panel(table, title="[bold]⚙️  Settings[/]", border_style="blue"))
        
        choice = Prompt.ask("Select Option", choices=["0", "1", "2", "3", "4"], default="0")
        
        if choice == "0":
            break
            
        elif choice == "1":
            if IS_ANDROID:
                data = setup_android_player()
                save_config(data)
            else:
                console.print("[dim]PC Player selection is currently handled by system PATH (VLC).[/]")
                # Future: Allow setting custom path for mpv/potplayer here
                Prompt.ask("Press Enter to continue")
                
        elif choice == "2":
            q_choices = ["1080p", "720p", "480p", "360p", "Ask"]
            console.print("\n[bold]Select Default Quality:[/]")
            for i, q in enumerate(q_choices):
                console.print(f"  {i+1}. {q}")
            
            q_idx = Prompt.ask("Choice", choices=[str(i+1) for i in range(len(q_choices))], default="5")
            res = q_choices[int(q_idx)-1]
            save_config({"default_quality": res})
            
        elif choice == "3":
            new_path = Prompt.ask("Enter new download path (leave empty to reset to default)")
            if new_path.strip():
                save_config({"download_path": new_path.strip()})
            else:
                # Remove key to revert to config.py default logic
                # We can't easy 'remove' with save_config merge logic, so we set to None or empty 
                # and handle in code, or just ignore. 
                # Let's clean the key manually.
                import json
                from .config import CONFIG_FILE
                try:
                    with open(CONFIG_FILE, 'r') as f:
                        data = json.load(f)
                    if "download_path" in data:
                        del data["download_path"]
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(data, f, indent=4)
                    console.print("[green]Reset to default path.[/]")
                except: pass

        elif choice == "4":
            new_val = not curr_update
            save_config({"auto_update": new_val})
            console.print(f"[green]Auto-Update set to: {'On' if new_val else 'Off'}[/]")
