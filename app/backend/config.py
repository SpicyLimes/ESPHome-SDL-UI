import os
from pathlib import Path

# Base directory is the app folder's parent (ESPHome-SDL-UI root)
BASE_DIR = Path(__file__).parent.parent.parent

# ESPHome path - can be set via environment variable by launcher
ESPHOME_PATH = os.getenv("ESPHOME_PATH", "esphome")

# Directories
BACKUP_DIR = BASE_DIR / "backups"
CONFIG_DIR = BASE_DIR / "configs"
LOG_DIR = BASE_DIR / "logs"

# Server settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("APP_PORT", "6062"))

# Create directories if they don't exist
BACKUP_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
