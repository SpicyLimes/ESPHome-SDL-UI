# SDL2 ESPHome UI Tester - Version 1

A modern web-based UI tool for testing ESPHome configurations on the SDL2 platform. This tool allows you to upload ESPHome YAML configs, automatically convert them for SDL2 compatibility, and run them with a sleek interface.

## Features

- **File Upload**: Drag-and-drop or click to upload ESPHome YAML configs
- **Automatic Backup**: Creates backups before modifying any files
- **SDL2 Compatibility Checker**: Identifies incompatible components and configurations
- **Auto-Fix**: Automatically converts configs for SDL2 compatibility
- **ESPHome CLI Integration**: Validate, compile, and run configs directly
- **Real-time Preview**: Run SDL2 display in real-time
- **Backup Management**: View and restore previous backups
- **Modern UI**: Sleek, responsive interface with dark mode

## Technology Stack

- **Backend**: Python 3, FastAPI
- **Frontend**: HTML, Tailwind CSS, Alpine.js
- **Config Parser**: PyYAML
- **SDL2**: System SDL2 installation
- **ESPHome**: Via existing venv

## Installation

### 1. Install Dependencies

```bash
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with your ESPHome venv path. Adjust if needed:

```bash
ESPHOME_VENV_PATH=/home/devin/Documents/ESP Documents/ESPHome Projects/venv
BACKUP_DIR=./backups
CONFIG_DIR=./configs
LOG_DIR=./logs
HOST=127.0.0.1
PORT=8000
```

### 3. Verify SDL2 Installation

```bash
sdl2-config --version
```

Should show: 2.30.0

### 4. Verify ESPHome Installation

```bash
source "/home/devin/Documents/ESP Documents/ESPHome Projects/venv/bin/activate"
esphome version
deactivate
```

Should show: Version: 2025.12.5

## Running the Application

### Start the Server

```bash
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"
source venv/bin/activate
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Access the Web UI

Open your browser and navigate to:

```
http://127.0.0.1:8000
```

## Usage

### 1. Upload a Config

- Click the upload area or drag-and-drop your ESPHome YAML file
- The app will automatically analyze it for SDL2 compatibility

### 2. Review Compatibility Issues

- If issues are found, they'll be displayed with severity levels
- Each issue includes the location and a suggested fix

### 3. Auto-Fix Configuration

- Click "Auto-Fix Configuration" to automatically convert the config
- A backup is created before any modifications
- View the applied modifications in the log

### 4. Run Commands

- **Validate**: Check config syntax and structure
- **Compile**: Compile the config (may take a few minutes)
- **Run SDL2**: Launch the SDL2 display window
- **Stop**: Stop the running SDL2 process

### 5. Manage Backups

- View all backups in the Backups section
- Restore any previous version with one click

## Safety Features

1. **Automatic Backups**: Every file modification creates a timestamped backup
2. **Non-destructive**: Original files are never deleted
3. **Sandboxed Execution**: All ESPHome commands run in isolated processes
4. **Error Handling**: Graceful failure with detailed error messages
5. **Logging**: All operations are logged to files for debugging

## Project Structure

```
Version 1/
├── backend/
│   ├── __init__.py
│   ├── backup_manager.py      # Backup creation and restoration
│   ├── config.py               # App configuration
│   ├── esphome_cli.py          # ESPHome CLI wrapper
│   ├── logger.py               # Logging setup
│   ├── sdl2_compatibility.py   # Compatibility checker and auto-fixer
│   └── yaml_parser.py          # YAML parsing and validation
├── templates/
│   └── index.html              # Web UI
├── static/                     # Static assets (currently unused)
├── backups/                    # Config backups (auto-created)
├── configs/                    # Uploaded configs (auto-created)
├── logs/                       # Application logs (auto-created)
├── main.py                     # FastAPI application
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
└── README.md                   # This file
```

## SDL2 Compatibility Rules

The app automatically handles these conversions:

### Platform Changes
- Converts `esp32`, `esp8266`, etc. to `host` platform
- Removes `board` field (not needed for SDL2)

### Display Changes
- Converts hardware displays (ili9341, st7789v, etc.) to `sdl` platform
- Adds required `dimensions` field if missing
- Removes hardware-specific pins (cs_pin, dc_pin, reset_pin)

### Component Removal
- Removes hardware-specific components: `i2c`, `spi`, `uart`
- Warns about network components: `wifi`, `mqtt`, `api`, `ota`, `web_server`

### Touchscreen Support
- SDL touchscreen uses mouse emulation
- No configuration changes needed if already present

### Binary Sensors
- SDL binary sensors use keyboard input
- Requires SDL key codes (e.g., SDLK_a)

## Common Issues

### ESPHome Not Found
If the app can't find ESPHome, verify the path in `.env`:
```bash
source "/home/devin/Documents/ESP Documents/ESPHome Projects/venv/bin/activate"
which esphome
deactivate
```

### SDL2 Display Won't Start
- Ensure SDL2 is installed: `sudo apt install libsdl2-dev`
- Check config is SDL2-compatible (run Auto-Fix)
- Verify no other SDL2 process is running

### Port Already in Use
Change the port in `.env`:
```bash
PORT=8001
```

## Example Configs

See `configs/example.yaml` for a sample SDL2-compatible configuration.

## Development

### Adding New Features

The modular structure makes it easy to extend:

- **New API endpoints**: Add to `main.py`
- **New compatibility rules**: Modify `backend/sdl2_compatibility.py`
- **UI enhancements**: Edit `templates/index.html`

### Debugging

- Check logs in `logs/` directory
- Run with `--reload` flag for auto-reload on code changes
- Use browser developer tools for frontend debugging

## Future Enhancements

Potential features for future versions:

- Real-time log streaming via WebSockets
- Config diff viewer
- Multiple config comparison
- Built-in YAML editor
- Custom component templates
- Export to Docker container
- Remote device deployment
- Config validation rules editor

## License

This project is for personal use. Refer to ESPHome and SDL2 licenses for their respective components.

## Support

For issues related to:
- **This tool**: Check logs in `logs/` directory
- **ESPHome**: https://esphome.io
- **SDL2**: https://www.libsdl.org

## Version History

### Version 1.0.0 (Current)
- Initial release
- Core functionality: upload, auto-fix, validate, compile, run
- Web UI with Tailwind CSS and Alpine.js
- Backup management
- SDL2 compatibility checker
