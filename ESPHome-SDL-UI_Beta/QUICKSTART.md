# Quick Start Guide - SDL2 ESPHome UI Tester

Get up and running in 5 minutes!

## Prerequisites Check

Run these commands to verify your system is ready:

```bash
# Check SDL2 installation
sdl2-config --version
# Should output: 2.30.0

# Check ESPHome installation
source "/home/devin/Documents/ESP Documents/ESPHome Projects/venv/bin/activate"
esphome version
deactivate
# Should output: Version: 2025.12.5

# Check Python 3
python3 --version
# Should be 3.11 or higher
```

## Installation (One-Time Setup)

```bash
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"

# Create virtual environment
python3 -m venv venv

# Install dependencies
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

### Option 1: Using the Startup Script (Recommended)

```bash
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"
./start.sh
```

### Option 2: Manual Start

```bash
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"
source venv/bin/activate
python main.py
```

### Option 3: Using Uvicorn with Hot Reload

```bash
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Access the Web Interface

Once the server is running, open your browser:

```
http://127.0.0.1:8000
```

## First-Time Usage

### Step 1: Upload a Config

1. **Option A**: Upload your own ESPHome YAML file
   - Click the upload area or drag-and-drop
   - The file will be analyzed automatically

2. **Option B**: Use the test files
   - `configs/example.yaml` - SDL2-ready config
   - `configs/test_esp32.yaml` - Needs conversion

### Step 2: Review Compatibility

- Green badge: SDL2 compatible, ready to run
- Yellow badge: Needs fixes

If issues are found:
- Review the compatibility issues list
- Each issue shows location and suggested fix

### Step 3: Auto-Fix (if needed)

1. Click **"Auto-Fix Configuration"** button
2. A backup is created automatically
3. View the applied modifications
4. Config is now SDL2-compatible

### Step 4: Validate

Click **"Validate"** to check config syntax:
- Terminal output shows ESPHome validation results
- Green output = success
- Red output = errors to fix

### Step 5: Compile (Optional)

Click **"Compile"** to build the config:
- First compile takes longer (downloads dependencies)
- Subsequent compiles are faster
- Watch terminal output for progress

### Step 6: Run SDL2 Display

Click **"Run SDL2"**:
- SDL2 window opens with your display
- Process runs in background
- Test touchscreen with mouse clicks
- Test keyboard with configured keys

### Step 7: Stop Display

Click **"Stop"** when done:
- Cleanly terminates SDL2 process
- Window closes

## Example Workflow

Here's a complete example using the test ESP32 config:

```bash
# 1. Start the server
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"
./start.sh

# 2. Open browser to http://127.0.0.1:8000

# 3. In the browser:
#    - Upload configs/test_esp32.yaml
#    - See incompatibility issues detected
#    - Click "Auto-Fix Configuration"
#    - See modifications applied
#    - Click "Validate" to verify syntax
#    - Click "Compile" to build (optional)
#    - Click "Run SDL2" to see display
#    - Interact with the SDL2 window
#    - Click "Stop" when done
```

## Testing SDL2 Features

### Display

The SDL2 window shows your display output:
- Text rendering
- Graphics (shapes, lines, circles)
- Images (if configured)
- Animations

### Touchscreen

Mouse acts as touchscreen:
- Click anywhere in SDL2 window
- Triggers touchscreen events
- Configure in YAML with `touchscreen: sdl`

### Keyboard Input

Press keys configured as binary sensors:
```yaml
binary_sensor:
  - platform: sdl
    id: key_a
    key: SDLK_a
```

Common SDL key codes:
- Letters: `SDLK_a`, `SDLK_b`, etc.
- Numbers: `SDLK_0`, `SDLK_1`, etc.
- Special: `SDLK_SPACE`, `SDLK_RETURN`, `SDLK_ESCAPE`
- Arrows: `SDLK_UP`, `SDLK_DOWN`, `SDLK_LEFT`, `SDLK_RIGHT`

## Backup Management

### Viewing Backups

Backups section shows:
- Backup filename (original_timestamp.yaml)
- Creation date/time
- File size

### Restoring Backups

1. Select a backup from the list
2. Click **"Restore"**
3. Confirm the restoration
4. Current config file is overwritten with backup

### Manual Backup Access

Backups are stored in:
```bash
cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1/backups"
ls -lh
```

## Troubleshooting

### Server Won't Start

**Problem**: `Port already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
lsof -ti:8000 | xargs kill -9

# Or change port in .env
nano .env
# Change PORT=8001
```

### Upload Fails

**Problem**: `File upload failed`

**Check**:
- File is `.yaml` extension
- File is valid YAML syntax
- Directory permissions are correct

### SDL2 Won't Run

**Problem**: `SDL2 display failed to start`

**Solution**:
```bash
# Ensure SDL2 is installed
sudo apt update
sudo apt install libsdl2-dev libsodium-dev

# Check display server
echo $DISPLAY
# Should show :0 or :1

# If headless, SDL2 won't work (needs display server)
```

### Validation Errors

**Problem**: Config validation fails after auto-fix

**Common causes**:
- Missing font files
- Missing image files
- Syntax errors in lambda blocks
- Missing component IDs

**Solution**: Review terminal output for specific errors

### ESPHome Not Found

**Problem**: `esphome: command not found`

**Solution**:
```bash
# Check .env file
cat .env | grep ESPHOME_VENV_PATH

# Verify path exists
ls -la "/home/devin/Documents/ESP Documents/ESPHome Projects/venv/bin/esphome"

# If missing, reinstall ESPHome or update path
```

## Tips & Best Practices

### 1. Start Simple

Begin with the example config:
```bash
# Copy example as starting point
cp configs/example.yaml configs/my_display.yaml
# Upload and modify my_display.yaml
```

### 2. Iterate Quickly

SDL2 allows rapid iteration:
1. Edit YAML
2. Upload
3. Run
4. See results immediately
5. Repeat

Much faster than flashing hardware!

### 3. Use Backups

Before major changes:
- Upload current config
- Auto-fix if needed
- Make changes
- Test
- Restore if needed

### 4. Check Logs

If something goes wrong:
```bash
tail -f logs/$(date +%Y%m%d).log
```

### 5. Reference Assets

For fonts and images, use absolute paths or place in config directory:
```yaml
font:
  - file: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    id: my_font
    size: 20
```

## Advanced Usage

### Custom Display Sizes

Edit dimensions in YAML:
```yaml
display:
  - platform: sdl
    dimensions:
      width: 800
      height: 480
```

Common sizes:
- 320x240 (QVGA)
- 480x320 (HVGA)
- 800x480 (WVGA)
- 1024x600 (WSVGA)

### Window Options

Customize SDL2 window:
```yaml
display:
  - platform: sdl
    dimensions:
      width: 480
      height: 320
    window:
      position: {x: 100, y: 100}
      borderless: false
      always_on_top: true
      fullscreen: false
      resizable: true
```

### Multiple Displays

Test multiple displays:
```yaml
display:
  - platform: sdl
    id: display1
    dimensions: {width: 320, height: 240}

  - platform: sdl
    id: display2
    dimensions: {width: 480, height: 320}
```

## Next Steps

After getting comfortable:

1. **Read ARCHITECTURE.md** - Understand how it works
2. **Read README.md** - Full feature documentation
3. **Explore ESPHome docs** - Learn display features
4. **Customize** - Modify the tool for your needs

## Getting Help

- **Application logs**: `logs/` directory
- **ESPHome docs**: https://esphome.io
- **SDL2 docs**: https://www.libsdl.org

## Quick Reference Commands

```bash
# Start server
./start.sh

# Stop server
Ctrl+C

# View logs
tail -f logs/$(date +%Y%m%d).log

# Check server status
curl http://127.0.0.1:8000/api/version

# List configs
ls -lh configs/

# List backups
ls -lh backups/

# Clean build files
rm -rf .esphome/
```

Enjoy testing your ESPHome displays with SDL2!
