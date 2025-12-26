"""
Universal Configuration System for EchoOS
Provides dynamic configuration that adapts to any system without hardcoded values
"""

import os
import json
import platform
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

class UniversalConfig:
    """Universal configuration system that adapts to any platform and system"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.system = platform.system().lower()
        self.logger = logging.getLogger(__name__)
        
        # Load or create configuration
        self.config = self._load_or_create_config()
        
        # System-specific settings
        self.system_config = self._get_system_config()
        
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing config or create default universal config"""
        config_file = self.config_dir / "universal_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        # Create default universal config
        default_config = self._create_default_config()
        self._save_config(default_config)
        return default_config
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default universal configuration"""
        return {
            "system": {
                "platform": self.system,
                "auto_detect_apps": True,
                "auto_detect_shortcuts": True,
                "learn_user_preferences": True
            },
            "voice": {
                "wake_words": ["hey echo", "echo os", "wake up"],
                "sleep_words": ["go to sleep", "sleep", "stop listening"],
                "timeout_seconds": 30,
                "confidence_threshold": 0.7
            },
            "ui": {
                "theme": "auto",  # auto, light, dark
                "language": "auto",  # auto-detect or specific language
                "accessibility": {
                    "high_contrast": False,
                    "large_text": False,
                    "screen_reader": False,
                    "voice_speed": 1.0
                }
            },
            "automation": {
                "click_delay": 0.1,
                "type_delay": 0.05,
                "scroll_speed": 3,
                "zoom_speed": 1.2,
                "retry_attempts": 3
            },
            "security": {
                "require_authentication": True,
                "session_timeout_minutes": 30,
                "max_failed_attempts": 3,
                "lockout_duration_minutes": 5
            },
            "discovery": {
                "scan_depth": 3,
                "include_hidden_files": False,
                "max_apps_per_category": 100,
                "exclude_system_apps": True
            },
            "commands": {
                "custom_patterns": {},
                "aliases": {},
                "disabled_commands": []
            }
        }
    
    def _get_system_config(self) -> Dict[str, Any]:
        """Get system-specific configuration"""
        home_dir = Path.home()
        
        system_config = {
            "paths": {
                "home": str(home_dir),
                "config": str(self.config_dir),
                "temp": str(self.config_dir / "temp"),
                "logs": str(self.config_dir / "logs"),
                "cache": str(self.config_dir / "cache")
            },
            "platform": {
                "name": platform.system(),
                "version": platform.version(),
                "architecture": platform.machine(),
                "python_version": platform.python_version()
            }
        }
        
        # Platform-specific paths
        if self.system == "windows":
            system_config["paths"].update({
                "program_files": os.environ.get("ProgramFiles", ""),
                "program_files_x86": os.environ.get("ProgramFiles(x86)", ""),
                "appdata": os.environ.get("APPDATA", ""),
                "localappdata": os.environ.get("LOCALAPPDATA", ""),
                "userprofile": os.environ.get("USERPROFILE", "")
            })
        elif self.system == "darwin":
            system_config["paths"].update({
                "applications": "/Applications",
                "user_applications": str(home_dir / "Applications"),
                "library": str(home_dir / "Library")
            })
        else:  # Linux
            system_config["paths"].update({
                "applications": "/usr/share/applications",
                "user_applications": str(home_dir / ".local" / "share" / "applications"),
                "bin": "/usr/bin",
                "local_bin": str(home_dir / ".local" / "bin")
            })
        
        return system_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            config_file = self.config_dir / "universal_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'voice.timeout_seconds')"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated config
        self._save_config(self.config)
    
    def get_system_path(self, path_type: str) -> str:
        """Get system-specific path"""
        return self.system_config["paths"].get(path_type, "")
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return self.system_config["platform"]
    
    def add_custom_command(self, pattern: str, action: str, context: str = "generic"):
        """Add custom voice command pattern"""
        if "custom_patterns" not in self.config["commands"]:
            self.config["commands"]["custom_patterns"] = {}
        
        if context not in self.config["commands"]["custom_patterns"]:
            self.config["commands"]["custom_patterns"][context] = {}
        
        self.config["commands"]["custom_patterns"][context][pattern] = action
        self._save_config(self.config)
    
    def add_command_alias(self, original: str, alias: str):
        """Add command alias"""
        if "aliases" not in self.config["commands"]:
            self.config["commands"]["aliases"] = {}
        
        self.config["commands"]["aliases"][alias] = original
        self._save_config(self.config)
    
    def disable_command(self, command: str):
        """Disable a command"""
        if "disabled_commands" not in self.config["commands"]:
            self.config["commands"]["disabled_commands"] = []
        
        if command not in self.config["commands"]["disabled_commands"]:
            self.config["commands"]["disabled_commands"].append(command)
            self._save_config(self.config)
    
    def enable_command(self, command: str):
        """Enable a command"""
        if "disabled_commands" in self.config["commands"]:
            if command in self.config["commands"]["disabled_commands"]:
                self.config["commands"]["disabled_commands"].remove(command)
                self._save_config(self.config)
    
    def is_command_enabled(self, command: str) -> bool:
        """Check if a command is enabled"""
        disabled = self.config["commands"].get("disabled_commands", [])
        return command not in disabled
    
    def get_disabled_commands(self) -> List[str]:
        """Get list of disabled commands"""
        return self.config["commands"].get("disabled_commands", [])
    
    def get_custom_patterns(self, context: str = None) -> Dict[str, Any]:
        """Get custom command patterns"""
        patterns = self.config["commands"].get("custom_patterns", {})
        if context:
            return patterns.get(context, {})
        return patterns
    
    def get_command_aliases(self) -> Dict[str, str]:
        """Get command aliases"""
        return self.config["commands"].get("aliases", {})
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self._create_default_config()
        self._save_config(self.config)
    
    def export_config(self, file_path: str):
        """Export configuration to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error exporting config: {e}")
    
    def import_config(self, file_path: str):
        """Import configuration from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge with existing config
            self._merge_config(self.config, imported_config)
            self._save_config(self.config)
        except Exception as e:
            self.logger.error(f"Error importing config: {e}")
    
    def _merge_config(self, base_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Merge new configuration with existing configuration"""
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def get_all_paths(self) -> Dict[str, str]:
        """Get all available paths"""
        return self.system_config["paths"]
    
    def create_directories(self):
        """Create necessary directories"""
        paths = self.system_config["paths"]
        for path_name, path_value in paths.items():
            if path_name in ["temp", "logs", "cache"]:
                Path(path_value).mkdir(parents=True, exist_ok=True)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "system": self.system_config["platform"],
            "paths_count": len(self.system_config["paths"]),
            "custom_patterns": len(self.get_custom_patterns()),
            "disabled_commands": len(self.get_disabled_commands()),
            "command_aliases": len(self.get_command_aliases()),
            "config_version": "1.0"
        }
