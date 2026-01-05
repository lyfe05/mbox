import re

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def parse_episode_input(input_str, max_ep):
    """Parses 'all', '1-5', '1,3' into a list of integers."""
    input_str = input_str.lower().strip()
    episodes = set()
    
    if input_str == "all":
        return list(range(1, max_ep + 1))
        
    parts = input_str.split(',')
    for part in parts:
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                episodes.update(range(start, end + 1))
            except ValueError: continue
        else:
            try:
                episodes.add(int(part))
            except ValueError: continue
            
    # Filter valid episodes
    valid_eps = sorted([ep for ep in episodes if 1 <= ep <= max_ep])
    return valid_eps
