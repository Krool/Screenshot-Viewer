import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Set

class SteamGameDatabase:
    def __init__(self):
        self.logger = logging.getLogger('SteamGameDatabase')
        self.games: Dict[str, str] = {}
        self.custom_games: Dict[str, str] = {}
        self.pending_updates: Set[str] = set()
        
        if getattr(sys, 'frozen', False):
            self.base_path = Path(sys.executable).parent
        else:
            self.base_path = Path(__file__).parent.parent.parent
        
        self.cache_file = self.base_path / "config" / "game_cache" / "steam_games.json"
        self.custom_cache_file = self.base_path / "config" / "game_cache" / "custom_games.json"
        
        self.load_cache()
    
    # ... rest of SteamGameDatabase methods ... 