# SDL2 ESPHome UI Tester - Architecture Documentation

## Overview

This application provides a web-based interface for testing ESPHome configurations on the SDL2 platform. It allows developers to quickly iterate on display designs without needing to flash physical hardware.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           UI (HTML + Tailwind + Alpine.js)             │ │
│  │  - File Upload                                         │ │
│  │  - Compatibility Checker Display                       │ │
│  │  - Action Buttons (Validate, Compile, Run)             │ │
│  │  - Terminal Output                                     │ │
│  │  - Backup Management                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST API
┌───────────────────────────┴─────────────────────────────────┐
│                    FastAPI Application                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   API Endpoints                        │ │
│  │  /api/upload     - Upload YAML config                 │ │
│  │  /api/auto-fix   - Auto-fix compatibility issues      │ │
│  │  /api/validate   - Validate config                    │ │
│  │  /api/compile    - Compile config                     │ │
│  │  /api/run        - Run SDL2 display                   │ │
│  │  /api/stop       - Stop SDL2 process                  │ │
│  │  /api/backups    - List/restore backups               │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                │
│  ┌─────────────────────────┴──────────────────────────────┐ │
│  │              Backend Modules                           │ │
│  │                                                        │ │
│  │  ┌─────────────────┐  ┌──────────────────────────┐    │ │
│  │  │  YAML Parser    │  │  SDL2 Compatibility      │    │ │
│  │  │  - Load/Save    │  │  - Check Issues          │    │ │
│  │  │  - Validate     │  │  - Auto-Fix Rules        │    │ │
│  │  └─────────────────┘  └──────────────────────────┘    │ │
│  │                                                        │ │
│  │  ┌─────────────────┐  ┌──────────────────────────┐    │ │
│  │  │ Backup Manager  │  │  ESPHome CLI Wrapper     │    │ │
│  │  │  - Create       │  │  - Validate              │    │ │
│  │  │  - Restore      │  │  - Compile               │    │ │
│  │  │  - List         │  │  - Run                   │    │ │
│  │  └─────────────────┘  └──────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                    System Layer                             │
│  ┌────────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ File System    │  │  ESPHome    │  │  SDL2 Library   │  │
│  │ - Configs      │  │  - Validate │  │  - Display      │  │
│  │ - Backups      │  │  - Compile  │  │  - Touchscreen  │  │
│  │ - Logs         │  │  - Run      │  │  - Input        │  │
│  └────────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend (templates/index.html)

**Technology**: HTML5, Tailwind CSS, Alpine.js

**Responsibilities**:
- File upload UI with drag-and-drop
- Display compatibility issues and modifications
- Action buttons for ESPHome commands
- Terminal output display
- Backup management interface

**Key Features**:
- Reactive state management with Alpine.js
- Modern, responsive design
- Real-time status updates
- Dark theme optimized for developer use

### Backend API (main.py)

**Technology**: FastAPI, Python 3

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve web UI |
| `/api/upload` | POST | Upload and analyze YAML config |
| `/api/auto-fix/{filename}` | POST | Auto-fix SDL2 compatibility issues |
| `/api/validate/{filename}` | POST | Validate config with ESPHome |
| `/api/compile/{filename}` | POST | Compile config |
| `/api/run/{filename}` | POST | Run SDL2 display |
| `/api/stop` | POST | Stop running SDL2 process |
| `/api/backups` | GET | List all backups |
| `/api/restore/{backup}/{target}` | POST | Restore backup |
| `/api/configs` | GET | List uploaded configs |
| `/api/version` | GET | Get ESPHome version |

### Core Modules

#### 1. YAML Parser (backend/yaml_parser.py)

**Purpose**: Handle YAML file operations

**Key Methods**:
- `load_yaml()`: Load and parse YAML file
- `save_yaml()`: Save config with proper formatting
- `validate_structure()`: Check required fields
- `get_display_config()`: Extract display configuration
- `extract_components()`: Get all ESPHome components

#### 2. SDL2 Compatibility Checker (backend/sdl2_compatibility.py)

**Purpose**: Check and fix SDL2 compatibility issues

**Incompatibility Rules**:

1. **Platform**: Must be `host`, not ESP32/ESP8266
2. **Display**: Must be `sdl` platform, not hardware displays
3. **Components**: Remove hardware-specific (I2C, SPI, UART)
4. **Network**: Warn about WiFi, MQTT, API (optional for SDL2)

**Auto-Fix Actions**:
- Convert platform to `host`
- Remove `board` field
- Convert display platform to `sdl`
- Add `dimensions` if missing
- Remove hardware pins
- Remove incompatible components

**Key Methods**:
- `check_config()`: Analyze config for issues
- `auto_fix_config()`: Apply automatic fixes
- `_check_platform()`: Validate platform settings
- `_check_display()`: Validate display configuration

#### 3. Backup Manager (backend/backup_manager.py)

**Purpose**: Create and restore config backups

**Features**:
- Automatic timestamped backups
- Safe restore with verification
- List all backups with metadata

**Backup Naming**: `{original_name}_{timestamp}.yaml`

**Key Methods**:
- `create_backup()`: Create timestamped backup
- `restore_backup()`: Restore from backup
- `list_backups()`: Get all backups with metadata

#### 4. ESPHome CLI Wrapper (backend/esphome_cli.py)

**Purpose**: Interface with ESPHome command-line tool

**Features**:
- Async subprocess execution
- Process management for running displays
- Clean stdout/stderr capture

**Key Methods**:
- `validate_config()`: Run `esphome config`
- `compile_config()`: Run `esphome compile`
- `run_config()`: Run `esphome run` (launches SDL2)
- `stop_current_process()`: Terminate running process
- `get_version()`: Get ESPHome version
- `clean_build()`: Clean build files

#### 5. Configuration (backend/config.py)

**Purpose**: Centralized configuration management

**Environment Variables**:
- `ESPHOME_VENV_PATH`: Path to ESPHome virtual environment
- `BACKUP_DIR`: Backup storage location
- `CONFIG_DIR`: Uploaded config storage
- `LOG_DIR`: Log file location
- `HOST`: Web server host
- `PORT`: Web server port

#### 6. Logger (backend/logger.py)

**Purpose**: Structured logging

**Features**:
- Daily log rotation
- Console and file output
- Timestamped entries
- Module-level loggers

## Data Flow

### Upload and Auto-Fix Flow

```
1. User uploads YAML file
   ↓
2. Frontend sends to /api/upload
   ↓
3. Save file with timestamp
   ↓
4. YAMLParser.load_yaml()
   ↓
5. SDL2CompatibilityChecker.check_config()
   ↓
6. Return issues to frontend
   ↓
7. User clicks "Auto-Fix"
   ↓
8. Frontend sends to /api/auto-fix
   ↓
9. BackupManager.create_backup()
   ↓
10. SDL2CompatibilityChecker.auto_fix_config()
   ↓
11. YAMLParser.save_yaml()
   ↓
12. Return modifications to frontend
```

### Run SDL2 Display Flow

```
1. User clicks "Run SDL2"
   ↓
2. Frontend sends to /api/run/{filename}
   ↓
3. ESPHomeCLI.run_config()
   ↓
4. Execute: esphome run config.yaml
   ↓
5. SDL2 window opens
   ↓
6. Process runs in background
   ↓
7. User clicks "Stop"
   ↓
8. Frontend sends to /api/stop
   ↓
9. ESPHomeCLI.stop_current_process()
   ↓
10. Terminate SDL2 process
```

## Security Considerations

### File System Safety

1. **Sandboxed Directories**: All file operations confined to:
   - `configs/` - Uploaded configs
   - `backups/` - Backup files
   - `logs/` - Log files

2. **Filename Sanitization**: Timestamps added to prevent conflicts

3. **Backup Before Modify**: Always create backup before changes

### Process Safety

1. **Process Isolation**: ESPHome runs in separate subprocess
2. **Termination Control**: Clean process shutdown
3. **Resource Limits**: Subprocess timeout controls

### Input Validation

1. **File Type Check**: Only `.yaml` files accepted
2. **YAML Parsing**: Validate before processing
3. **Path Validation**: Check file existence

## Error Handling

### Logging Levels

- **INFO**: Normal operations (upload, compile, run)
- **WARNING**: Recoverable issues (validation failures)
- **ERROR**: Critical failures (backup failure, file errors)

### User Feedback

- Success messages (green)
- Warning messages (yellow)
- Error messages (red)
- Terminal output for detailed info

## Performance Considerations

### Async Operations

- All ESPHome CLI operations are async
- Non-blocking UI during long operations
- Background process management

### File Handling

- Efficient YAML parsing with PyYAML
- Streaming file uploads
- Minimal memory footprint

## Extensibility

### Adding New Compatibility Rules

Edit `backend/sdl2_compatibility.py`:

```python
def _check_new_component(self, config: Dict[str, Any]):
    if 'new_component' in config:
        self.issues.append({
            'type': 'incompatible_component',
            'severity': 'error',
            'message': 'New component not supported',
            'location': 'new_component',
            'suggestion': 'Remove new_component'
        })
```

### Adding New API Endpoints

Edit `main.py`:

```python
@app.post("/api/new-endpoint/{filename}")
async def new_endpoint(filename: str):
    # Implementation
    return JSONResponse(content={"success": True})
```

### Adding Frontend Features

Edit `templates/index.html`:

```javascript
async newFeature() {
    this.loading = true;
    try {
        const response = await fetch('/api/new-endpoint');
        // Handle response
    } finally {
        this.loading = false;
    }
}
```

## Dependencies

### Python Packages

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pyyaml**: YAML parsing
- **aiofiles**: Async file operations
- **pydantic**: Data validation
- **jinja2**: Template rendering
- **python-dotenv**: Environment config

### System Dependencies

- **SDL2**: Display library (libsdl2-dev)
- **ESPHome**: Platform framework
- **Python 3.11+**: Runtime environment

## Testing Strategy

### Manual Testing

1. Upload ESP32 config (test_esp32.yaml)
2. Verify compatibility issues detected
3. Run auto-fix
4. Verify backup created
5. Validate config
6. Compile config
7. Run SDL2 display
8. Test stop functionality
9. Restore backup

### Future Automated Testing

- Unit tests for each backend module
- Integration tests for API endpoints
- End-to-end UI tests with Playwright

## Deployment

### Development

```bash
./start.sh
```

### Production Considerations

1. **Reverse Proxy**: Use nginx/Apache
2. **HTTPS**: Add SSL certificate
3. **Authentication**: Add user authentication
4. **Rate Limiting**: Prevent abuse
5. **Resource Limits**: Docker containerization

## Future Enhancements

### Short Term

1. WebSocket support for real-time logs
2. Config diff viewer
3. Multiple file upload
4. Built-in YAML editor

### Medium Term

1. Custom component templates
2. Display preview without running
3. Config sharing/export
4. Dark/light theme toggle

### Long Term

1. Multi-user support
2. Cloud deployment option
3. CI/CD integration
4. Plugin system
5. ESPHome version management

## Troubleshooting

### Common Issues

**SDL2 not found**:
```bash
sudo apt install libsdl2-dev libsodium-dev
```

**ESPHome not found**:
- Check `.env` ESPHOME_VENV_PATH
- Verify venv exists and has esphome installed

**Port already in use**:
- Change PORT in `.env`
- Kill existing process: `lsof -ti:8000 | xargs kill -9`

**Permission denied**:
- Check directory permissions
- Ensure write access to configs/, backups/, logs/

## Contributing

When modifying this project:

1. Update this documentation
2. Test all affected features
3. Follow existing code style
4. Add logging for new operations
5. Update README.md if needed

## License

This project is for personal use. ESPHome and SDL2 have their own licenses.
