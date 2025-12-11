"""Configuration management for Vivisect"""

import os
import json
from pathlib import Path
from typing import Dict, Any

class Config:
    """Manages configuration for the forensics suite"""

    DEFAULT_CONFIG = {
        'output_dir': '/var/lib/vivisect/output',
        'log_dir': '/var/log/vivisect',
        'temp_dir': '/tmp/vivisect',
        'auto_start': True,
        'modules': {
            'disk_imaging': {
                'enabled': True,
                'compression': True,
                'hash_algorithm': 'sha256'
            },
            'file_analysis': {
                'enabled': True,
                'scan_depth': 10,
                'calculate_hashes': True
            },
            'network_forensics': {
                'enabled': True,
                'capture_interface': 'eth0',
                'max_capture_size': '1GB'
            },
            'memory_analysis': {
                'enabled': True,
                'auto_dump': False
            },
            'artifact_extraction': {
                'enabled': True,
                'browser_artifacts': True,
                'registry_artifacts': True,
                'system_logs': True
            }
        }
    }

    def __init__(self, config_path: str = '/etc/vivisect/vivisect.conf'):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    return {**self.DEFAULT_CONFIG, **loaded_config}
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        dirs = [
            self.get('output_dir'),
            self.get('log_dir'),
            self.get('temp_dir')
        ]
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
