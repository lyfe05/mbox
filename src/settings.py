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
        # Removing inner box lines for cleaner look inside Panel
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Option", style="cyan", justify="right")
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
        
        # Use ask_with_back logic if preferred, or just simple Prompt with specific choices
        # The user specifically mentioned 0/b not working in SUB-MENUS.
        # But for this main menu, 0 is listed as 'Back'.
        choice = Prompt.ask("Select Option", choices=["0", "1", "2", "3", "4"], default="0")
        
        if choice == "0":
            break
            
        elif choice == "1":
            if IS_ANDROID:
                data = setup_android_player()
                save_config(data)
            else:
                console.print("[dim]PC Player selection is currently handled by system PATH (VLC).[/]")
                Prompt.ask("Press Enter to continue")
                
        elif choice == "2":
            q_choices = ["1080p", "720p", "480p", "360p", "Ask"]
            console.print("\n[bold]Select Default Quality:[/]")
            for i, q in enumerate(q_choices):
                console.print(f"  {i+1}. {q}")
            
            # Using ask_with_back to allow 'b' or '0'
            # Note: ask_with_back returns None on back
            q_idx = ask_with_back("Choice", type='int', choices=[str(i+1) for i in range(len(q_choices))], default=len(q_choices))
            
            if q_idx is not None:
                 res = q_choices[q_idx-1]
                 save_config({"default_quality": res})
                 console.print(f"[green]Default quality set to: {res}[/]")
                 # time.sleep(0.5)
            
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
