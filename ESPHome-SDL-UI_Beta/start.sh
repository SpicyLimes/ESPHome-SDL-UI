#!/bin/bash

# SDL2 ESPHome UI Tester - Startup Script

cd "/home/devin/Documents/Projects/SDL-UI-Project/Version 1"

echo "Starting SDL2 ESPHome UI Tester..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "==============================================="
echo "SDL2 ESPHome UI Tester - Version 1"
echo "==============================================="
echo ""
echo "Server starting on http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==============================================="
echo ""

# Start the application
python main.py
