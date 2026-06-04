import sys
from pathlib import Path


DESKTOP_DIR = Path(__file__).resolve().parents[1]
if str(DESKTOP_DIR) not in sys.path:
    sys.path.append(str(DESKTOP_DIR))
