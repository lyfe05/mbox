from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from rich.text import Text

# --- Initialize Rich Console ---
console = Console()

def print_banner():
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(
        Panel(
            Text("MOVIEBOX CLI", justify="center", style="bold cyan") + 
            Text("\nBy Triton 🔱", justify="center", style="yellow italic"),
            style="bold blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )
    )
    console.print(grid)

def display_content_table(content_list, page=None):
    title_str = "🎬 Content List"
    if page is not None:
        title_str += f" (Page {page})"
        
    table = Table(title=title_str, box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", justify="right", width=4)
    table.add_column("Title", style="white", ratio=3)
    table.add_column("Year", style="green", width=10)
    table.add_column("Type", style="yellow", width=10)

    for idx, item in enumerate(content_list):
        title = item.get('title', 'Unknown')
        try:
            clean_title = str(title).encode('ascii', 'ignore').decode('ascii')
        except:
            clean_title = "Unknown"
        
        date = item.get('releaseDate', 'N/A')
        stype = "Movie" if item.get("subjectType") == 1 else "Series"
        
        table.add_row(str(idx + 1), clean_title, str(date), stype)

    console.print(table)

def ask_with_back(prompt_text, type='str', default=None, choices=None):
    """
    Unified prompt that handles 'b' or '0' for Back.
    Returns: None (if back), or valid value.
    """
    p_text = f"{prompt_text} [dim](b/0 to back)[/]"
    while True:
        try:
            # We do NOT pass choices to Prompt.ask because it prevents entering 'b' if not in choices
            val = Prompt.ask(p_text, default=default)
            if val.lower() in ['b', '0']: return None
            
            if choices and val not in choices:
                console.print(f"[red]Please select one of: {', '.join(choices)}[/]")
                continue

            if type == 'int':
                return int(val)
            return val
        except ValueError:
            console.print("[red]Invalid input.[/]")
            continue
