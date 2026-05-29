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
        'web': {
            # Bind to loopback by default. Set to '0.0.0.0' to expose the GUI on
            # the network — at which point the auth token is enforced for any
            # non-loopback client.
            'host': '127.0.0.1',
            'port': 5000,
            # Leave empty to auto-generate a token at startup (printed to the
            # console). Set explicitly, or via the VIVISECT_AUTH_TOKEN env var,
            # for a stable token.
            'auth_token': '',
            # Origins permitted for CORS / WebSocket. Add the device's own URL
            # here when binding to 0.0.0.0.
            'allowed_origins': ['http://127.0.0.1:5000', 'http://localhost:5000'],
            # Trust requests originating from the local machine without a token
            # (keeps the on-device kiosk UI working). Disable behind a proxy.
            'trust_loopback': True,
        },
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
                    # Deep-merge with defaults so a partial config (e.g. one
                    # that sets a single nested key) does not discard the rest
                    # of the nested defaults.
                    return self._deep_merge(self.DEFAULT_CONFIG, loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self._deep_merge(self.DEFAULT_CONFIG, {})
        return self._deep_merge(self.DEFAULT_CONFIG, {})

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge ``override`` onto a copy of ``base``."""
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

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
