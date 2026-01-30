import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from .logger import setup_logger

logger = setup_logger(__name__)


class ESPHomeYAMLLoader(yaml.SafeLoader):
    """Custom YAML loader for ESPHome configs with !secret tag support."""
    pass


def _secret_constructor(loader, node):
    """Handle !secret tags by replacing with placeholder."""
    secret_name = loader.construct_scalar(node)
    return f"SECRET_{secret_name}"


# Register the !secret constructor on our custom loader class (not global SafeLoader)
ESPHomeYAMLLoader.add_constructor('!secret', _secret_constructor)


class YAMLParser:
    def __init__(self):
        self.config_data: Optional[Dict[str, Any]] = None
        self.file_path: Optional[Path] = None

    def _merge_duplicate_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge duplicate substitutions sections that may exist in ESPHome configs"""
        return data

    def load_yaml(self, file_path: Path) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            lines = content.split('\n')
            substitutions_sections = []
            current_section = None
            section_indent = None

            for i, line in enumerate(lines):
                if line.strip().startswith('substitutions:'):
                    if current_section is not None:
                        substitutions_sections.append(current_section)
                    current_section = {'start': i, 'content': {}}
                    section_indent = len(line) - len(line.lstrip())
                elif current_section is not None:
                    if line.strip() and not line.startswith('#'):
                        line_indent = len(line) - len(line.lstrip())
                        if line_indent <= section_indent and line.strip():
                            substitutions_sections.append(current_section)
                            current_section = None

            if current_section is not None:
                substitutions_sections.append(current_section)

            if len(substitutions_sections) > 1:
                logger.warning(f"Found {len(substitutions_sections)} substitutions sections, will merge them")

                merged_content = content
                for section in reversed(substitutions_sections[1:]):
                    start_line = section['start']
                    lines_to_remove = []
                    for j in range(start_line, len(lines)):
                        if lines[j].strip().startswith('substitutions:'):
                            lines_to_remove.append(j)
                        elif j > start_line and lines[j].strip() and not lines[j].startswith('#'):
                            line_indent = len(lines[j]) - len(lines[j].lstrip())
                            if line_indent > 0:
                                lines_to_remove.append(j)
                            else:
                                break
                        elif lines[j].strip().startswith('#') or not lines[j].strip():
                            lines_to_remove.append(j)
                        else:
                            break

                    for j in reversed(lines_to_remove):
                        del lines[j]

                merged_content = '\n'.join(lines)
                self.config_data = yaml.load(merged_content, Loader=ESPHomeYAMLLoader)
            else:
                self.config_data = yaml.load(content, Loader=ESPHomeYAMLLoader)

            self.file_path = file_path
            logger.info(f"Successfully loaded YAML: {file_path}")
            return True, self.config_data, None
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {e}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Failed to load file: {e}"
            logger.error(error_msg)
            return False, None, error_msg

    def save_yaml(self, file_path: Path, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            logger.info(f"Successfully saved YAML: {file_path}")
            return True, None
        except Exception as e:
            error_msg = f"Failed to save file: {e}"
            logger.error(error_msg)
            return False, error_msg

    def validate_structure(self) -> Tuple[bool, List[str]]:
        errors = []

        if not self.config_data:
            errors.append("No config data loaded")
            return False, errors

        required_keys = ['esphome']
        for key in required_keys:
            if key not in self.config_data:
                errors.append(f"Missing required key: {key}")

        return len(errors) == 0, errors

    def get_platform(self) -> Optional[str]:
        if not self.config_data:
            return None

        esphome_config = self.config_data.get('esphome', {})
        if isinstance(esphome_config, dict):
            return esphome_config.get('platform')
        return None

    def has_display(self) -> bool:
        if not self.config_data:
            return False
        return 'display' in self.config_data

    def get_display_config(self) -> Optional[List[Dict[str, Any]]]:
        if not self.config_data:
            return None

        display = self.config_data.get('display')
        if isinstance(display, list):
            return display
        elif isinstance(display, dict):
            return [display]
        return None

    def extract_components(self) -> Dict[str, Any]:
        if not self.config_data:
            return {}

        components = {
            'display': self.config_data.get('display'),
            'touchscreen': self.config_data.get('touchscreen'),
            'binary_sensor': self.config_data.get('binary_sensor'),
            'sensor': self.config_data.get('sensor'),
            'text_sensor': self.config_data.get('text_sensor'),
            'switch': self.config_data.get('switch'),
            'button': self.config_data.get('button'),
            'light': self.config_data.get('light'),
            'climate': self.config_data.get('climate'),
            'cover': self.config_data.get('cover'),
            'fan': self.config_data.get('fan'),
        }

        return {k: v for k, v in components.items() if v is not None}
