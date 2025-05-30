import os
import sys
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for the application."""
    log_dir = Path(os.getenv('APPDATA')) / 'Game Screenshot Viewer' / 'Logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_dir / 'debug.log')]
    )
    
    if getattr(sys, 'frozen', False):
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                root_logger.removeHandler(handler) 