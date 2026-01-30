import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
ESPHOME_VENV_PATH = os.getenv("ESPHOME_VENV_PATH", "/home/devin/Documents/ESP Documents/ESPHome Projects/venv")
BACKUP_DIR = BASE_DIR / os.getenv("BACKUP_DIR", "backups")
CONFIG_DIR = BASE_DIR / os.getenv("CONFIG_DIR", "configs")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

BACKUP_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
