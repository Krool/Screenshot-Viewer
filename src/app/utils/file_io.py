import os
from pathlib import Path

def get_config_path(relative_path: str) -> Path:
    """Resolve paths relative to the config directory."""
    base_path = Path(__file__).parent.parent.parent / 'config'
    return base_path / relative_path

def get_steam_screenshot_paths() -> list[Path]:
    """Find all Steam screenshot paths."""
    steam_path = Path(os.path.expandvars(r"%ProgramFiles(x86)%\\Steam"))
    userdata_path = steam_path / "userdata"
    # ... rest of path finding logic ... 