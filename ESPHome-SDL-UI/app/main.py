from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pathlib import Path
import aiofiles
from datetime import datetime

from backend.config import CONFIG_DIR, BACKUP_DIR, HOST, PORT


def validate_path_within_dir(base_dir: Path, filename: str) -> Path:
    """Validate that filename resolves to a path within base_dir.

    Prevents path traversal attacks by ensuring the resolved path
    stays within the intended directory.
    """
    # Reject obviously malicious filenames
    if '..' in filename or filename.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = (base_dir / filename).resolve()
    base_resolved = base_dir.resolve()

    # Ensure the resolved path is within the base directory
    if not str(file_path).startswith(str(base_resolved) + '/') and file_path != base_resolved:
        raise HTTPException(status_code=400, detail="Invalid filename")

    return file_path


from backend.logger import setup_logger, get_log_files, get_log_content, clear_old_logs
from backend.yaml_parser import YAMLParser
from backend.sdl2_compatibility import SDL2CompatibilityChecker
from backend.backup_manager import BackupManager
from backend.esphome_cli import ESPHomeCLI

logger = setup_logger(__name__)

# Initialize components
yaml_parser = YAMLParser()
sdl2_checker = SDL2CompatibilityChecker()
backup_manager = BackupManager()
esphome_cli = ESPHomeCLI()

# Lifespan context manager (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("ESPHome SDL UI started")
    logger.info(f"Config directory: {CONFIG_DIR}")
    logger.info(f"Backup directory: {BACKUP_DIR}")
    logger.info(f"Listening on: http://{HOST}:{PORT}")
    yield
    # Shutdown
    await esphome_cli.stop_current_process()
    logger.info("ESPHome SDL UI stopped")

app = FastAPI(
    title="ESPHome SDL UI",
    version="2.0.0",
    lifespan=lifespan
)

# Templates directory
APP_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/upload")
async def upload_config(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(('.yaml', '.yml')):
            raise HTTPException(status_code=400, detail="Only YAML files are allowed")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{Path(file.filename).stem}_{timestamp}.yaml"
        file_path = CONFIG_DIR / filename

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        logger.info(f"Uploaded file: {file_path}")

        success, config_data, error = yaml_parser.load_yaml(file_path)

        if not success:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": error}
            )

        is_valid, validation_errors = yaml_parser.validate_structure()

        is_compatible, compatibility_issues = sdl2_checker.check_config(config_data)

        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "file_path": str(file_path),
            "is_valid": is_valid,
            "validation_errors": validation_errors,
            "is_compatible": is_compatible,
            "compatibility_issues": compatibility_issues,
            "config_preview": config_data
        })

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-fix/{filename}")
async def auto_fix_config(filename: str):
    try:
        file_path = validate_path_within_dir(CONFIG_DIR, filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        backup_path = backup_manager.create_backup(file_path)

        if not backup_path:
            raise HTTPException(status_code=500, detail="Failed to create backup")

        success, config_data, error = yaml_parser.load_yaml(file_path)

        if not success:
            raise HTTPException(status_code=400, detail=error)

        modified_config, modifications = sdl2_checker.auto_fix_config(config_data)

        success, error = yaml_parser.save_yaml(file_path, modified_config)

        if not success:
            backup_manager.restore_backup(backup_path, file_path)
            raise HTTPException(status_code=500, detail=f"Failed to save modified config: {error}")

        logger.info(f"Auto-fixed config: {filename}")

        return JSONResponse(content={
            "success": True,
            "backup_path": str(backup_path),
            "modifications": modifications,
            "modified_config": modified_config
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-fix failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate/{filename}")
async def validate_config(filename: str):
    try:
        file_path = validate_path_within_dir(CONFIG_DIR, filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        success, output = await esphome_cli.validate_config(file_path)

        return JSONResponse(content={
            "success": success,
            "output": output
        })

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compile/{filename}")
async def compile_config(filename: str):
    try:
        file_path = validate_path_within_dir(CONFIG_DIR, filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        success, output = await esphome_cli.compile_config(file_path)

        return JSONResponse(content={
            "success": success,
            "output": output
        })

    except Exception as e:
        logger.error(f"Compilation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run/{filename}")
async def run_config(filename: str):
    try:
        file_path = validate_path_within_dir(CONFIG_DIR, filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        success, output = await esphome_cli.run_config(file_path)

        return JSONResponse(content={
            "success": success,
            "output": output
        })

    except Exception as e:
        logger.error(f"Run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def stop_display():
    try:
        success = await esphome_cli.stop_current_process()

        return JSONResponse(content={
            "success": True,  # Always return success since the goal is to stop
            "was_running": success,
            "message": "SDL2 display stopped" if success else "No running process"
        })

    except Exception as e:
        logger.error(f"Stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_sdl_status():
    """Check if the SDL2 process is currently running."""
    try:
        is_running = esphome_cli.is_process_running()

        return JSONResponse(content={
            "success": True,
            "is_running": is_running
        })

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backups")
async def list_backups():
    try:
        backups = backup_manager.list_backups()

        return JSONResponse(content={
            "success": True,
            "backups": backups
        })

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/restore/{backup_name}/{target_filename}")
async def restore_backup(backup_name: str, target_filename: str):
    try:
        backup_path = validate_path_within_dir(BACKUP_DIR, backup_name)
        target_path = validate_path_within_dir(CONFIG_DIR, target_filename)

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        success = backup_manager.restore_backup(backup_path, target_path)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to restore backup")

        return JSONResponse(content={
            "success": True,
            "message": f"Restored {backup_name} to {target_filename}"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/configs")
async def list_configs():
    try:
        configs = []
        for config_file in sorted(CONFIG_DIR.glob("*.yaml"), reverse=True):
            configs.append({
                "name": config_file.name,
                "path": str(config_file),
                "size": config_file.stat().st_size,
                "modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            })

        return JSONResponse(content={
            "success": True,
            "configs": configs
        })

    except Exception as e:
        logger.error(f"Failed to list configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/version")
async def get_esphome_version():
    try:
        success, version = await esphome_cli.get_version()

        return JSONResponse(content={
            "success": success,
            "version": version
        })

    except Exception as e:
        logger.error(f"Failed to get version: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/backups/{backup_name}")
async def delete_backup(backup_name: str):
    try:
        backup_path = validate_path_within_dir(BACKUP_DIR, backup_name)

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        backup_path.unlink()
        logger.info(f"Deleted backup: {backup_name}")

        return JSONResponse(content={
            "success": True,
            "message": f"Deleted {backup_name}"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backups/{backup_name}/download")
async def download_backup(backup_name: str):
    try:
        backup_path = validate_path_within_dir(BACKUP_DIR, backup_name)

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        return FileResponse(
            path=str(backup_path),
            filename=backup_name,
            media_type='application/x-yaml'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Logging API Endpoints - For troubleshooting and support
# ============================================================================

@app.get("/api/logs")
async def list_logs():
    """List all available log files."""
    try:
        logs = get_log_files()
        return JSONResponse(content={
            "success": True,
            "logs": logs
        })
    except Exception as e:
        logger.error(f"Failed to list logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/{filename}")
async def get_log(filename: str, lines: int = 500, level: str = None):
    """Get log file content.

    Args:
        filename: Name of the log file
        lines: Maximum number of lines to return (default 500)
        level: Filter by log level (DEBUG, INFO, WARNING, ERROR)
    """
    try:
        result = get_log_content(filename, lines=lines, level_filter=level)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Log not found"))

        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get log content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/{filename}/download")
async def download_log(filename: str):
    """Download a log file."""
    try:
        from backend.config import LOG_DIR

        # Security validation
        if '..' in filename or filename.startswith('/'):
            raise HTTPException(status_code=400, detail="Invalid filename")

        log_path = (LOG_DIR / filename).resolve()
        if not str(log_path).startswith(str(LOG_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid filename")

        if not log_path.exists():
            raise HTTPException(status_code=404, detail="Log file not found")

        return FileResponse(
            path=str(log_path),
            filename=filename,
            media_type='text/plain'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/logs/cleanup")
async def cleanup_logs(days: int = 30):
    """Delete log files older than specified days.

    Args:
        days: Number of days to keep (default 30)
    """
    try:
        deleted_count = clear_old_logs(days=days)
        logger.info(f"Cleaned up {deleted_count} old log files (older than {days} days)")

        return JSONResponse(content={
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} log files older than {days} days"
        })
    except Exception as e:
        logger.error(f"Failed to cleanup logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
