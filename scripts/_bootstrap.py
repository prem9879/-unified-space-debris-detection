"""Project path bootstrap for standalone scripts.

Ensures repository-root imports (e.g. ``src.*``) work when scripts are
executed as ``python scripts/<name>.py`` from any current directory.
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
