import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from .config import BACKUP_DIR
from .logger import setup_logger

logger = setup_logger(__name__)

class BackupManager:
    def __init__(self, backup_dir: Path = BACKUP_DIR):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, file_path: Path) -> Optional[Path]:
        try:
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")

            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        try:
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False

            backup_size = backup_path.stat().st_size
            shutil.copy2(backup_path, target_path)

            # Verify the restore was successful
            if not target_path.exists():
                logger.error(f"Restore verification failed - target file not created: {target_path}")
                return False

            target_size = target_path.stat().st_size
            if target_size != backup_size:
                logger.error(f"Restore verification failed - size mismatch: backup={backup_size}, target={target_size}")
                return False

            logger.info(f"Restored backup from {backup_path} to {target_path} (verified)")

            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def list_backups(self) -> list[dict]:
        backups = []
        for backup_file in sorted(self.backup_dir.glob("*.yaml"), reverse=True):
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "created": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            })
        return backups
