"""Setup sys.path for CLI to import addon modules."""
import sys
from pathlib import Path

# Add addon directory to path
addon_path = Path(__file__).parent.parent / "addon"
sys.path.insert(0, str(addon_path))
