"""Filesize filtering service."""
def parse_size(size_str):
    if not size_str: return None
    size_str = size_str.strip().lower()
    multipliers = {"b": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}
    for suffix, mult in multipliers.items():
        if size_str.endswith(suffix):
            try: return float(size_str[:-1]) * mult
            except: return None
    try: return float(size_str)
    except: return None

def check_filesize(filesize, min_size=None, max_size=None):
    if min_size and filesize < min_size: return False
    if max_size and filesize > max_size: return False
    return True

def build_filesize_opts(min_size=None, max_size=None):
    """Build yt-dlp-compatible filesize options.

    yt-dlp expects string format like '100M', '1G', '500K'.
    """
    opts = {}
    if min_size:
        parsed = parse_size(min_size)
        if parsed:
            if parsed >= 1024**3: opts["min_filesize"] = f"{parsed / 1024**3:.0f}G"
            elif parsed >= 1024**2: opts["min_filesize"] = f"{parsed / 1024**2:.0f}M"
            elif parsed >= 1024: opts["min_filesize"] = f"{parsed / 1024:.0f}K"
            else: opts["min_filesize"] = f"{parsed:.0f}"
    if max_size:
        parsed = parse_size(max_size)
        if parsed:
            if parsed >= 1024**3: opts["max_filesize"] = f"{parsed / 1024**3:.0f}G"
            elif parsed >= 1024**2: opts["max_filesize"] = f"{parsed / 1024**2:.0f}M"
            elif parsed >= 1024: opts["max_filesize"] = f"{parsed / 1024:.0f}K"
            else: opts["max_filesize"] = f"{parsed:.0f}"
    return opts
