import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Dict, Optional
from .config import LOG_DIR

# Track which loggers have been configured to prevent handler duplication
_configured_loggers = set()

# Maximum log file size (5 MB) and number of backup files to keep
MAX_LOG_SIZE = 5 * 1024 * 1024
BACKUP_COUNT = 5


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels, filter at handler level

    # Check if this logger has already been configured by us
    if name not in _configured_loggers:
        # Clear any existing handlers to prevent duplication on module reload
        if logger.hasHandlers():
            logger.handlers.clear()

        log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"

        # Use RotatingFileHandler for automatic log rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # More detailed format for file logging
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Simpler format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Prevent propagation to root logger to avoid duplicate messages
        logger.propagate = False

        _configured_loggers.add(name)

    return logger


def get_log_files() -> List[Dict[str, any]]:
    """Get list of all log files with metadata."""
    log_files = []
    for log_file in sorted(LOG_DIR.glob("*.log*"), reverse=True):
        try:
            stat = log_file.stat()
            log_files.append({
                "name": log_file.name,
                "path": str(log_file),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        except OSError:
            continue
    return log_files


def get_log_content(filename: str, lines: int = 500, level_filter: Optional[str] = None) -> Dict[str, any]:
    """Read log file content with optional filtering.

    Args:
        filename: Name of the log file
        lines: Maximum number of lines to return (from end of file)
        level_filter: Optional log level to filter by (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Dict with log content and metadata
    """
    log_path = LOG_DIR / filename

    # Security check - ensure the file is within LOG_DIR
    if '..' in filename or filename.startswith('/'):
        return {"success": False, "error": "Invalid filename"}

    resolved_path = log_path.resolve()
    if not str(resolved_path).startswith(str(LOG_DIR.resolve())):
        return {"success": False, "error": "Invalid filename"}

    if not log_path.exists():
        return {"success": False, "error": "Log file not found"}

    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()

        # Filter by level if specified
        if level_filter:
            level_filter = level_filter.upper()
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if level_filter in valid_levels:
                all_lines = [line for line in all_lines if f' - {level_filter} - ' in line]

        # Return last N lines
        content_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "success": True,
            "filename": filename,
            "total_lines": len(all_lines),
            "returned_lines": len(content_lines),
            "content": ''.join(content_lines)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def clear_old_logs(days: int = 30) -> int:
    """Remove log files older than specified days.

    Args:
        days: Number of days to keep logs

    Returns:
        Number of files deleted
    """
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=days)
    deleted = 0

    for log_file in LOG_DIR.glob("*.log*"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                log_file.unlink()
                deleted += 1
        except OSError:
            continue

    return deleted
