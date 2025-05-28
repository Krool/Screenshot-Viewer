#!/usr/bin/env python3
"""
Debug wrapper for the Steam Screenshots Viewer.
"""

import sys
import traceback
from steam_viewer import main

def debug_main():
    try:
        main()
    except Exception as e:
        print("\nError occurred:", str(e))
        print("\nFull traceback:")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    debug_main() 