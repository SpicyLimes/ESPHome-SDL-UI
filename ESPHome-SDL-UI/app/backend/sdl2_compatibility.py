from typing import Dict, Any, List, Tuple, Union
from copy import deepcopy
from .logger import setup_logger

logger = setup_logger(__name__)

class SDL2CompatibilityChecker:
    INCOMPATIBLE_PLATFORMS = ['esp32', 'esp8266', 'esp32s2', 'esp32s3', 'esp32c3', 'rp2040']
    INCOMPATIBLE_DISPLAYS = ['ili9341', 'st7789v', 'ssd1306', 'waveshare_epaper', 'max7219']
    INCOMPATIBLE_COMPONENTS = ['wifi', 'mqtt', 'api', 'ota', 'web_server', 'i2c', 'spi', 'uart']
    SDL2_CONVERTIBLE_TOUCHSCREENS = ['xpt2046', 'lilygo_t5_47', 'gt911', 'ft5x06', 'ft63x6', 'cst816', 'cst226', 'ektf2232', 'tt21100']

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.modifications: List[Dict[str, Any]] = []

    def check_config(self, config: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        self.issues = []
        self._check_platform(config)
        self._check_display(config)
        self._check_components(config)
        self._check_hardware_sensors(config)
        self._check_esphome_section(config)

        is_compatible = len([i for i in self.issues if i['severity'] == 'error']) == 0

        return is_compatible, self.issues

    def _has_homeassistant_integrations(self, config: Dict[str, Any]) -> bool:
        """Check if config has components that use homeassistant platform"""
        component_types = ['time', 'sensor', 'binary_sensor', 'text_sensor', 'switch', 'number', 'select']

        for component_type in component_types:
            if component_type in config:
                items = config[component_type]
                if not isinstance(items, list):
                    items = [items] if items else []

                for item in items:
                    if isinstance(item, dict) and item.get('platform') == 'homeassistant':
                        return True

        return False

    def _check_platform(self, config: Dict[str, Any]):
        esphome = config.get('esphome', {})

        if 'platform' in esphome or 'board' in esphome:
            platform = esphome.get('platform', 'unknown')
            if platform.lower() in self.INCOMPATIBLE_PLATFORMS:
                self.issues.append({
                    'type': 'platform',
                    'severity': 'error',
                    'message': f"Platform '{platform}' is incompatible with SDL2. Must use 'host' platform.",
                    'location': 'esphome.platform',
                    'suggestion': "Change platform to 'host'"
                })

        for esp_platform in ['esp32', 'esp8266', 'rp2040', 'bk72xx']:
            if esp_platform in config:
                self.issues.append({
                    'type': 'platform_section',
                    'severity': 'error',
                    'message': f"'{esp_platform}' section is incompatible with SDL2. Must remove and use 'host' platform.",
                    'location': esp_platform,
                    'suggestion': f"Remove '{esp_platform}' section and set 'platform: host' in esphome section"
                })

    def _check_esphome_section(self, config: Dict[str, Any]):
        esphome = config.get('esphome', {})

        if not esphome:
            self.issues.append({
                'type': 'missing_section',
                'severity': 'error',
                'message': "Missing 'esphome' section",
                'location': 'root',
                'suggestion': "Add 'esphome' section with 'name' field"
            })

        if 'name' not in esphome:
            self.issues.append({
                'type': 'missing_field',
                'severity': 'error',
                'message': "Missing 'name' field in esphome section",
                'location': 'esphome',
                'suggestion': "Add 'name: sdl_device' to esphome section"
            })

    def _check_display(self, config: Dict[str, Any]):
        display = config.get('display')

        if not display:
            self.issues.append({
                'type': 'missing_component',
                'severity': 'warning',
                'message': "No display component configured",
                'location': 'root',
                'suggestion': "Add SDL2 display component"
            })
            return

        displays = display if isinstance(display, list) else [display]

        for idx, disp in enumerate(displays):
            platform = disp.get('platform', '')

            if platform and platform != 'sdl':
                self.issues.append({
                    'type': 'display_platform',
                    'severity': 'error',
                    'message': f"Display platform '{platform}' is incompatible with SDL2",
                    'location': f'display[{idx}].platform',
                    'suggestion': "Change platform to 'sdl'"
                })

            if 'dimensions' not in disp and platform == 'sdl':
                self.issues.append({
                    'type': 'missing_field',
                    'severity': 'warning',
                    'message': "SDL2 display should specify dimensions",
                    'location': f'display[{idx}]',
                    'suggestion': "Add 'dimensions' with 'width' and 'height'"
                })

    def _check_components(self, config: Dict[str, Any]):
        needs_api = self._has_homeassistant_integrations(config)

        for component in self.INCOMPATIBLE_COMPONENTS:
            if component in config:
                # Skip api warning if Home Assistant integrations exist
                if component == 'api' and needs_api:
                    continue

                severity = 'error' if component in ['i2c', 'spi', 'uart'] else 'warning'
                self.issues.append({
                    'type': 'incompatible_component',
                    'severity': severity,
                    'message': f"Component '{component}' may not work or is unnecessary with SDL2",
                    'location': component,
                    'suggestion': f"Remove or comment out '{component}' section for SDL2 testing"
                })

    def _check_hardware_sensors(self, config: Dict[str, Any]):
        sensors = config.get('sensor', [])
        if not isinstance(sensors, list):
            sensors = [sensors] if sensors else []

        for idx, sensor in enumerate(sensors):
            if isinstance(sensor, dict) and sensor.get('platform') in ['adc', 'pulse_counter', 'rotary_encoder']:
                self.issues.append({
                    'type': 'hardware_sensor',
                    'severity': 'error',
                    'message': f"Sensor platform '{sensor.get('platform')}' requires hardware and won't work with SDL2",
                    'location': f'sensor[{idx}].platform',
                    'suggestion': f"Remove hardware sensor or replace with template/virtual sensor"
                })

    def auto_fix_config(self, config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        modified_config = deepcopy(config)
        self.modifications = []

        self._fix_platform(modified_config)
        self._fix_display(modified_config)
        self._fix_esphome_section(modified_config)
        self._remove_hardware_sensors(modified_config)
        self._remove_hardware_outputs(modified_config)
        self._remove_incompatible_components(modified_config)
        self._remove_wifi_dependent_sensors(modified_config)
        self._cleanup_component_references(modified_config)

        return modified_config, self.modifications

    def _fix_platform(self, config: Dict[str, Any]):
        esphome = config.setdefault('esphome', {})

        for esp_platform in ['esp32', 'esp8266', 'rp2040', 'bk72xx']:
            if esp_platform in config:
                board_info = config[esp_platform].get('board', 'unknown') if isinstance(config[esp_platform], dict) else 'unknown'
                del config[esp_platform]
                self.modifications.append({
                    'action': 'removed',
                    'location': esp_platform,
                    'old_value': f'{esp_platform} (board: {board_info})',
                    'reason': f'SDL2 uses host platform, {esp_platform} section not compatible'
                })

        if 'platform' in esphome:
            old_val = esphome['platform']
            del esphome['platform']
            self.modifications.append({
                'action': 'removed',
                'location': 'esphome.platform',
                'old_value': old_val,
                'reason': 'ESPHome 2025.x uses separate platform component (host:), not platform key'
            })

        if 'board' in esphome:
            old_board = esphome['board']
            del esphome['board']
            self.modifications.append({
                'action': 'removed',
                'location': 'esphome.board',
                'old_value': old_board,
                'reason': 'SDL2 uses host platform, board not needed'
            })

        if 'host' not in config:
            config['host'] = None
            self.modifications.append({
                'action': 'added',
                'location': 'host',
                'new_value': 'host component (empty)',
                'reason': 'ESPHome 2025.x requires host: component for SDL2 platform'
            })

    def _fix_esphome_section(self, config: Dict[str, Any]):
        esphome = config.setdefault('esphome', {})

        if 'name' not in esphome:
            esphome['name'] = 'sdl_device'
            self.modifications.append({
                'action': 'added',
                'location': 'esphome.name',
                'new_value': 'sdl_device',
                'reason': 'Name is required for ESPHome config'
            })

    def _fix_display(self, config: Dict[str, Any]):
        if 'display' not in config:
            config['display'] = [{
                'platform': 'sdl',
                'dimensions': {'width': 320, 'height': 240},
                'show_test_card': True
            }]
            self.modifications.append({
                'action': 'added',
                'location': 'display',
                'new_value': 'SDL2 display with test card',
                'reason': 'Added default SDL2 display configuration'
            })
            return

        displays = config['display'] if isinstance(config['display'], list) else [config['display']]

        for idx, disp in enumerate(displays):
            if disp.get('platform') and disp['platform'] != 'sdl':
                old_platform = disp['platform']
                disp['platform'] = 'sdl'

                if 'dimensions' not in disp:
                    disp['dimensions'] = {'width': 320, 'height': 240}

                disp.pop('model', None)
                disp.pop('cs_pin', None)
                disp.pop('dc_pin', None)
                disp.pop('reset_pin', None)
                disp.pop('spi_id', None)
                disp.pop('rotation', None)
                disp.pop('invert_colors', None)
                disp.pop('color_palette', None)

                self.modifications.append({
                    'action': 'changed',
                    'location': f'display[{idx}].platform',
                    'old_value': old_platform,
                    'new_value': 'sdl',
                    'reason': 'Converted display to SDL2 platform'
                })

        config['display'] = displays if len(displays) > 1 else displays[0]

        # Handle touchscreen conversion (supports both dict and list)
        if 'touchscreen' in config:
            ts = config['touchscreen']
            touchscreens = ts if isinstance(ts, list) else [ts]
            converted_touchscreens = []

            for idx, touchscreen in enumerate(touchscreens):
                if isinstance(touchscreen, dict) and touchscreen.get('platform') in self.SDL2_CONVERTIBLE_TOUCHSCREENS:
                    old_ts_platform = touchscreen['platform']
                    converted_touchscreens.append({'platform': 'sdl'})
                    self.modifications.append({
                        'action': 'changed',
                        'location': f'touchscreen[{idx}].platform' if len(touchscreens) > 1 else 'touchscreen.platform',
                        'old_value': old_ts_platform,
                        'new_value': 'sdl',
                        'reason': 'Converted touchscreen to SDL2 (mouse emulation)'
                    })
                elif isinstance(touchscreen, dict) and touchscreen.get('platform') == 'sdl':
                    converted_touchscreens.append(touchscreen)
                else:
                    converted_touchscreens.append(touchscreen)

            # Set back as single item or list depending on original format
            if len(converted_touchscreens) == 1:
                config['touchscreen'] = converted_touchscreens[0]
            else:
                config['touchscreen'] = converted_touchscreens

    def _remove_hardware_sensors(self, config: Dict[str, Any]):
        if 'sensor' not in config:
            return

        sensors = config['sensor'] if isinstance(config['sensor'], list) else [config['sensor']]
        filtered_sensors = []
        removed_count = 0

        for sensor in sensors:
            if isinstance(sensor, dict) and sensor.get('platform') in ['adc', 'pulse_counter', 'rotary_encoder']:
                sensor_name = sensor.get('name', sensor.get('id', 'unnamed'))
                self.modifications.append({
                    'action': 'removed',
                    'location': f'sensor (platform: {sensor.get("platform")})',
                    'old_value': f'{sensor_name}',
                    'reason': f"Hardware sensor platform '{sensor.get('platform')}' not compatible with SDL2"
                })
                removed_count += 1
            else:
                filtered_sensors.append(sensor)

        if removed_count > 0:
            if len(filtered_sensors) == 0:
                del config['sensor']
            else:
                config['sensor'] = filtered_sensors if len(filtered_sensors) > 1 else filtered_sensors[0]

    def _remove_hardware_outputs(self, config: Dict[str, Any]):
        if 'output' in config:
            outputs = config['output'] if isinstance(config['output'], list) else [config['output']]
            has_ledc = any(isinstance(o, dict) and o.get('platform') == 'ledc' for o in outputs)

            if has_ledc:
                del config['output']
                self.modifications.append({
                    'action': 'removed',
                    'location': 'output',
                    'old_value': 'Hardware outputs (ledc)',
                    'reason': 'Hardware output platforms (ledc, etc.) require ESP32 and are not compatible with SDL2'
                })

        if 'light' in config:
            del config['light']
            self.modifications.append({
                'action': 'removed',
                'location': 'light',
                'old_value': 'Light components',
                'reason': 'Light components depend on hardware outputs which are not available on SDL2'
            })

        if 'rtttl' in config:
            del config['rtttl']
            self.modifications.append({
                'action': 'removed',
                'location': 'rtttl',
                'old_value': 'RTTTL buzzer',
                'reason': 'RTTTL requires hardware output which is not available on SDL2'
            })

    def _remove_incompatible_components(self, config: Dict[str, Any]):
        # Check if Home Assistant integrations exist that require API
        needs_api = self._has_homeassistant_integrations(config)

        for component in self.INCOMPATIBLE_COMPONENTS:
            if component in config:
                # Keep api if Home Assistant integrations exist
                if component == 'api' and needs_api:
                    self.modifications.append({
                        'action': 'kept',
                        'location': 'api',
                        'reason': 'API component kept - required by Home Assistant integrations'
                    })
                    continue

                old_value = str(config[component])[:50]
                del config[component]
                self.modifications.append({
                    'action': 'removed',
                    'location': component,
                    'old_value': old_value,
                    'reason': f"Component '{component}' is incompatible or unnecessary for SDL2"
                })

    def _remove_wifi_dependent_sensors(self, config: Dict[str, Any]):
        """Remove text sensors that depend on wifi (like wifi_info)"""
        if 'wifi' in config:
            return  # WiFi is present, keep wifi-dependent sensors

        if 'text_sensor' not in config:
            return

        text_sensors = config['text_sensor'] if isinstance(config['text_sensor'], list) else [config['text_sensor']]
        filtered_sensors = []
        removed_count = 0

        for sensor in text_sensors:
            if isinstance(sensor, dict) and sensor.get('platform') == 'wifi_info':
                sensor_name = sensor.get('name', sensor.get('id', 'wifi_info'))
                self.modifications.append({
                    'action': 'removed',
                    'location': f'text_sensor (platform: wifi_info)',
                    'old_value': f'{sensor_name}',
                    'reason': "WiFi info sensor requires wifi component which was removed"
                })
                removed_count += 1
            else:
                filtered_sensors.append(sensor)

        if removed_count > 0:
            if len(filtered_sensors) == 0:
                del config['text_sensor']
            else:
                config['text_sensor'] = filtered_sensors if len(filtered_sensors) > 1 else filtered_sensors[0]

    def _cleanup_component_references(self, config: Dict[str, Any]):
        """Remove references to components that were removed"""

        # If rtttl was removed, clean up rtttl.play actions
        if 'rtttl' not in config:
            self._remove_action_references(config, 'rtttl.play', 'RTTTL component was removed')

        # If light was removed, clean up light actions
        if 'light' not in config:
            self._remove_action_references(config, 'light.turn_on', 'Light component was removed')
            self._remove_action_references(config, 'light.turn_off', 'Light component was removed')

    def _filter_actions_from_trigger(self, trigger_config: Any, action_name: str) -> Tuple[Any, int]:
        """Filter out actions matching action_name from a trigger config.
        Returns (filtered_config, removed_count)."""
        removed_count = 0

        if trigger_config is None:
            return trigger_config, 0

        # Handle dict with 'then' key
        if isinstance(trigger_config, dict) and 'then' in trigger_config:
            original_actions = trigger_config['then'] if isinstance(trigger_config['then'], list) else [trigger_config['then']]
            filtered_actions = []

            for action in original_actions:
                if isinstance(action, dict) and action_name in action:
                    removed_count += 1
                else:
                    filtered_actions.append(action)

            if len(filtered_actions) == 0:
                return None, removed_count  # Signal to remove trigger
            else:
                trigger_config['then'] = filtered_actions if len(filtered_actions) > 1 else filtered_actions[0]
                return trigger_config, removed_count

        # Handle direct list of actions
        elif isinstance(trigger_config, list):
            filtered_actions = []
            for action in trigger_config:
                if isinstance(action, dict) and action_name in action:
                    removed_count += 1
                else:
                    filtered_actions.append(action)

            if len(filtered_actions) == 0:
                return None, removed_count
            return filtered_actions, removed_count

        return trigger_config, 0

    def _remove_action_references(self, config: Dict[str, Any], action_name: str, reason: str):
        """Remove actions with a specific name from various components in the config"""
        removed_count = 0

        # Component types and their trigger names
        component_triggers = {
            'binary_sensor': ['on_press', 'on_release', 'on_click', 'on_double_click', 'on_multi_click', 'on_state'],
            'sensor': ['on_value', 'on_value_range', 'on_raw_value'],
            'text_sensor': ['on_value', 'on_raw_value'],
            'switch': ['on_turn_on', 'on_turn_off'],
            'button': ['on_press'],
            'touchscreen': ['on_touch', 'on_release', 'on_update'],
            'time': ['on_time', 'on_time_sync'],
            'interval': ['interval'],
        }

        for component_type, triggers in component_triggers.items():
            if component_type not in config:
                continue

            items = config[component_type] if isinstance(config[component_type], list) else [config[component_type]]

            for item in items:
                if not isinstance(item, dict):
                    continue

                for trigger in triggers:
                    if trigger in item:
                        filtered, count = self._filter_actions_from_trigger(item[trigger], action_name)
                        removed_count += count

                        if filtered is None:
                            del item[trigger]
                        else:
                            item[trigger] = filtered

        # Handle wifi triggers separately (wifi is a single dict, not a list)
        if 'wifi' in config and isinstance(config['wifi'], dict):
            for trigger in ['on_connect', 'on_disconnect']:
                if trigger in config['wifi']:
                    filtered, count = self._filter_actions_from_trigger(config['wifi'][trigger], action_name)
                    removed_count += count

                    if filtered is None:
                        del config['wifi'][trigger]
                    else:
                        config['wifi'][trigger] = filtered

        # Handle esphome on_boot/on_shutdown/on_loop
        if 'esphome' in config and isinstance(config['esphome'], dict):
            for trigger in ['on_boot', 'on_shutdown', 'on_loop']:
                if trigger in config['esphome']:
                    filtered, count = self._filter_actions_from_trigger(config['esphome'][trigger], action_name)
                    removed_count += count

                    if filtered is None:
                        del config['esphome'][trigger]
                    else:
                        config['esphome'][trigger] = filtered

        if removed_count > 0:
            self.modifications.append({
                'action': 'cleaned',
                'location': f'actions using {action_name}',
                'reason': f'Removed {removed_count} {action_name} action(s) - {reason}'
            })
