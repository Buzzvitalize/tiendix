import os
import sys
from pathlib import Path

PROJECT_ROOT = os.path.dirname(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

archive_root = (os.getenv('PDF_ARCHIVE_ROOT') or '').strip()
if not archive_root:
    archive_root = str(Path(PROJECT_ROOT) / 'generated_docs')
Path(archive_root).mkdir(parents=True, exist_ok=True)

from app import app as application
