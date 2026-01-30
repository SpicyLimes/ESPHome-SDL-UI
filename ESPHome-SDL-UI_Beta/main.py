from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pathlib import Path
import aiofiles
from datetime import datetime

from backend.config import CONFIG_DIR, BACKUP_DIR, BASE_DIR
from backend.logger import setup_logger
from backend.yaml_parser import YAMLParser
from backend.sdl2_compatibility import SDL2CompatibilityChecker
from backend.backup_manager import BackupManager
from backend.esphome_cli import ESPHomeCLI

logger = setup_logger(__name__)

app = FastAPI(title="SDL2 UI Project", version="1.0.0")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

yaml_parser = YAMLParser()
sdl2_checker = SDL2CompatibilityChecker()
backup_manager = BackupManager()
esphome_cli = ESPHomeCLI()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/upload")
async def upload_config(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.yaml'):
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
        file_path = CONFIG_DIR / filename

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
        file_path = CONFIG_DIR / filename

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
        file_path = CONFIG_DIR / filename

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
        file_path = CONFIG_DIR / filename

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
            "success": success,
            "message": "SDL2 display stopped" if success else "No running process"
        })

    except Exception as e:
        logger.error(f"Stop failed: {e}")
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
        backup_path = BACKUP_DIR / backup_name
        target_path = CONFIG_DIR / target_filename

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
        backup_path = BACKUP_DIR / backup_name

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
        from fastapi.responses import FileResponse

        backup_path = BACKUP_DIR / backup_name

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

@app.on_event("startup")
async def startup_event():
    logger.info("SDL2 UI Project started")
    logger.info(f"Config directory: {CONFIG_DIR}")
    logger.info(f"Backup directory: {BACKUP_DIR}")

@app.on_event("shutdown")
async def shutdown_event():
    await esphome_cli.stop_current_process()
    logger.info("SDL2 UI Project stopped")

if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
