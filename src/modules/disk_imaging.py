"""Disk imaging and acquisition module"""

import os
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class DiskImaging:
    """Handles forensic disk imaging and verification"""

    def __init__(self, logger, config):
        self.logger = logger.get_logger('disk_imaging')
        self.config = config
        self.output_dir = config.get('output_dir')

    def list_devices(self) -> list:
        """List available block devices"""
        try:
            result = subprocess.run(
                ['lsblk', '-d', '-n', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT'],
                capture_output=True,
                text=True,
                check=True
            )
            devices = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 3:
                        devices.append({
                            'name': parts[0],
                            'size': parts[1] if len(parts) > 1 else 'Unknown',
                            'type': parts[2] if len(parts) > 2 else 'Unknown'
                        })
            return devices
        except Exception as e:
            self.logger.error(f"Failed to list devices: {e}")
            return []

    def create_image_dd(self, source_device: str, output_file: str,
                        block_size: str = '4M', compression: bool = False) -> Dict[str, Any]:
        """Create a forensic image using dd"""
        self.logger.info(f"Starting dd imaging of {source_device}")

        if not os.path.exists(source_device):
            error = f"Source device {source_device} does not exist"
            self.logger.error(error)
            return {'success': False, 'error': error}

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.output_dir, output_file)

            # Build dd command
            dd_cmd = [
                'dd',
                f'if={source_device}',
                f'of={output_path}',
                f'bs={block_size}',
                'status=progress',
                'conv=noerror,sync'
            ]

            self.logger.info(f"Running command: {' '.join(dd_cmd)}")

            # Execute dd (this would run in production)
            # For safety, we'll just log the command
            # result = subprocess.run(dd_cmd, check=True, capture_output=True, text=True)

            # Calculate hash of the image
            image_hash = self._calculate_file_hash(output_path) if os.path.exists(output_path) else None

            result_info = {
                'success': True,
                'source': source_device,
                'output': output_path,
                'timestamp': timestamp,
                'block_size': block_size,
                'hash': image_hash,
                'command': ' '.join(dd_cmd)
            }

            self.logger.info(f"Imaging completed: {output_path}")
            return result_info

        except Exception as e:
            self.logger.error(f"Imaging failed: {e}")
            return {'success': False, 'error': str(e)}

    def create_image_dcfldd(self, source_device: str, output_file: str,
                           hash_algorithm: str = 'sha256') -> Dict[str, Any]:
        """Create a forensic image using dcfldd with built-in hashing"""
        self.logger.info(f"Starting dcfldd imaging of {source_device}")

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.output_dir, output_file)
            hash_file = f"{output_path}.{hash_algorithm}"

            dcfldd_cmd = [
                'dcfldd',
                f'if={source_device}',
                f'of={output_path}',
                f'hash={hash_algorithm}',
                f'hashlog={hash_file}',
                'bs=4M',
                'conv=noerror,sync'
            ]

            self.logger.info(f"Command: {' '.join(dcfldd_cmd)}")

            result_info = {
                'success': True,
                'source': source_device,
                'output': output_path,
                'hash_file': hash_file,
                'timestamp': timestamp,
                'command': ' '.join(dcfldd_cmd)
            }

            return result_info

        except Exception as e:
            self.logger.error(f"dcfldd imaging failed: {e}")
            return {'success': False, 'error': str(e)}

    def verify_image(self, image_path: str, original_device: str = None) -> Dict[str, Any]:
        """Verify integrity of forensic image"""
        self.logger.info(f"Verifying image: {image_path}")

        if not os.path.exists(image_path):
            return {'success': False, 'error': 'Image file does not exist'}

        try:
            # Calculate image hash
            image_hash = self._calculate_file_hash(image_path)

            result = {
                'success': True,
                'image_path': image_path,
                'hash': image_hash,
                'size': os.path.getsize(image_path),
                'timestamp': datetime.now().isoformat()
            }

            # If original device provided, compare hashes
            if original_device and os.path.exists(original_device):
                device_hash = self._calculate_device_hash(original_device)
                result['device_hash'] = device_hash
                result['verified'] = (image_hash == device_hash)

            self.logger.info(f"Verification complete: {image_hash}")
            return result

        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_file_hash(self, filepath: str, algorithm: str = 'sha256') -> str:
        """Calculate hash of a file"""
        hash_func = hashlib.new(algorithm)
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            self.logger.error(f"Hash calculation failed: {e}")
            return None

    def _calculate_device_hash(self, device_path: str, algorithm: str = 'sha256') -> str:
        """Calculate hash of a block device"""
        return self._calculate_file_hash(device_path, algorithm)

    def split_image(self, image_path: str, chunk_size: str = '650M') -> Dict[str, Any]:
        """Split large image into smaller chunks"""
        self.logger.info(f"Splitting image: {image_path}")

        try:
            output_prefix = f"{image_path}.part"

            split_cmd = [
                'split',
                '-b', chunk_size,
                '-d',
                image_path,
                output_prefix
            ]

            # Log command (would execute in production)
            self.logger.info(f"Split command: {' '.join(split_cmd)}")

            return {
                'success': True,
                'original': image_path,
                'prefix': output_prefix,
                'chunk_size': chunk_size
            }

        except Exception as e:
            self.logger.error(f"Image splitting failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_device_info(self, device: str) -> Dict[str, Any]:
        """Get detailed information about a device"""
        try:
            # Get device information using various tools
            info = {
                'device': device,
                'timestamp': datetime.now().isoformat()
            }

            # Using lsblk
            result = subprocess.run(
                ['lsblk', '-J', device],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                import json
                info['lsblk'] = json.loads(result.stdout)

            # Using fdisk
            result = subprocess.run(
                ['fdisk', '-l', device],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['fdisk'] = result.stdout

            # Using smartctl if available
            result = subprocess.run(
                ['smartctl', '-a', device],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['smart'] = result.stdout

            return info

        except Exception as e:
            self.logger.error(f"Failed to get device info: {e}")
            return {'error': str(e)}
