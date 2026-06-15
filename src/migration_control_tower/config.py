"""Application configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DATA_PATH = DATA_DIR / "synthetic" / "subscribers.json"
