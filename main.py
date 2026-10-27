"""Launch the desktop layer. Original V0.2 remains independently runnable."""
import runpy
import sys
from pathlib import Path

if __name__ == '__main__':
    entry = Path(__file__).resolve().parent / 'desktop_v03'
    sys.path.insert(0, str(entry))
    runpy.run_path(str(entry / 'main.py'), run_name='__main__')
