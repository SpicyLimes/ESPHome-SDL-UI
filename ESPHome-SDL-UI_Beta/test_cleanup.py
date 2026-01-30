#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from backend.yaml_parser import YAMLParser
from backend.sdl2_compatibility import SDL2CompatibilityChecker
from pathlib import Path

# Load test file
parser = YAMLParser()
success, config, error = parser.load_yaml(Path("test/esp32-cyd2usb-2.8in-test1.yaml"))

if not success:
    print(f"Failed to load: {error}")
    sys.exit(1)

print("Original config has rtttl:", 'rtttl' in config)
print("Original config has vibration_sensor with rtttl.play:")
if 'binary_sensor' in config:
    for sensor in config['binary_sensor']:
        if isinstance(sensor, dict) and sensor.get('id') == 'vibration_sensor':
            print(f"  Found vibration_sensor: {sensor.get('on_press')}")

# Auto-fix
checker = SDL2CompatibilityChecker()
fixed_config, modifications = checker.auto_fix_config(config)

print("\nAfter auto-fix:")
print("Fixed config has rtttl:", 'rtttl' in fixed_config)
print("Fixed config has vibration_sensor:")
if 'binary_sensor' in fixed_config:
    for sensor in fixed_config['binary_sensor']:
        if isinstance(sensor, dict) and sensor.get('id') == 'vibration_sensor':
            print(f"  Found vibration_sensor: {sensor.get('on_press')}")

print("\nModifications:")
for i, mod in enumerate(modifications, 1):
    print(f"{i}. [{mod['action'].upper()}] {mod['location']}: {mod['reason']}")
