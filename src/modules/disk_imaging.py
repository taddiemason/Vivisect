"""Disk imaging and acquisition module"""

import os
import stat
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from core.result import OperationResult

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

        error = self._validate_source(source_device)
        if error:
            self.logger.error(error)
            return OperationResult.fail(error)

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self._safe_output_path(output_file)
            if output_path is None:
                error = f"Invalid output path '{output_file}' (must stay within {self.output_dir})"
                self.logger.error(error)
                return OperationResult.fail(error)

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

            # Execute dd
            result = subprocess.run(dd_cmd, capture_output=True, text=True, timeout=None)

            if result.returncode != 0:
                raise Exception(f"dd command failed: {result.stderr}")

            # Hash-on-acquire: hash the image and the source and compare so the
            # caller gets a verified copy, not just an unverified hash.
            image_hash, source_hash, verified = self._verify_against_source(
                output_path, source_device)
            if not verified:
                self.logger.warning(
                    f"Image hash does not match source for {source_device} "
                    f"(image={image_hash}, source={source_hash})")

            self.logger.info(f"Imaging completed: {output_path} (verified={verified})")
            return OperationResult.ok({
                'source': source_device,
                'output': output_path,
                'timestamp': timestamp,
                'block_size': block_size,
                'hash': image_hash,
                'source_hash': source_hash,
                'verified': verified,
                'command': ' '.join(dd_cmd),
            })

        except Exception as e:
            self.logger.error(f"Imaging failed: {e}")
            return OperationResult.fail(e)

    def create_image_dcfldd(self, source_device: str, output_file: str,
                           hash_algorithm: str = 'sha256') -> Dict[str, Any]:
        """Create a forensic image using dcfldd with built-in hashing"""
        self.logger.info(f"Starting dcfldd imaging of {source_device}")

        error = self._validate_source(source_device)
        if error:
            self.logger.error(error)
            return OperationResult.fail(error)

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self._safe_output_path(output_file)
            if output_path is None:
                error = f"Invalid output path '{output_file}' (must stay within {self.output_dir})"
                self.logger.error(error)
                return OperationResult.fail(error)
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

            # Execute dcfldd
            result = subprocess.run(dcfldd_cmd, capture_output=True, text=True, timeout=None)

            if result.returncode != 0:
                raise Exception(f"dcfldd command failed: {result.stderr}")

            image_hash, source_hash, verified = self._verify_against_source(
                output_path, source_device, hash_algorithm)
            if not verified:
                self.logger.warning(
                    f"Image hash does not match source for {source_device} "
                    f"(image={image_hash}, source={source_hash})")

            self.logger.info(f"dcfldd imaging completed: {output_path} (verified={verified})")
            return OperationResult.ok({
                'source': source_device,
                'output': output_path,
                'hash_file': hash_file,
                'hash': image_hash,
                'source_hash': source_hash,
                'verified': verified,
                'timestamp': timestamp,
                'command': ' '.join(dcfldd_cmd),
            })

        except Exception as e:
            self.logger.error(f"dcfldd imaging failed: {e}")
            return OperationResult.fail(e)

    def verify_image(self, image_path: str, original_device: str = None) -> Dict[str, Any]:
        """Verify integrity of forensic image"""
        self.logger.info(f"Verifying image: {image_path}")

        if not os.path.exists(image_path):
            return OperationResult.fail('Image file does not exist')

        try:
            # Calculate image hash
            image_hash = self._calculate_file_hash(image_path)

            payload = {
                'image_path': image_path,
                'hash': image_hash,
                'size': os.path.getsize(image_path),
                'timestamp': datetime.now().isoformat()
            }

            # If original device provided, compare hashes
            if original_device and os.path.exists(original_device):
                device_hash = self._calculate_device_hash(original_device)
                payload['device_hash'] = device_hash
                payload['verified'] = (image_hash == device_hash)

            self.logger.info(f"Verification complete: {image_hash}")
            return OperationResult.ok(payload)

        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            return OperationResult.fail(e)

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

    # ── forensic-integrity helpers ────────────────────────────────────────────
    def _validate_source(self, device: str) -> Optional[str]:
        """Return an error string if ``device`` is not a safe imaging source.

        A source must exist and be either a block device (the normal case) or a
        regular file (re-imaging an existing image). This prevents an arbitrary
        path / FIFO / socket from being fed to dd.
        """
        if not os.path.exists(device):
            return f"Source device {device} does not exist"
        try:
            mode = os.stat(device).st_mode
        except OSError as e:
            return f"Cannot stat {device}: {e}"
        if not (stat.S_ISBLK(mode) or stat.S_ISREG(mode)):
            return f"{device} is not a block device or regular file"
        return None

    def _safe_output_path(self, output_file: str) -> Optional[str]:
        """Resolve ``output_file`` inside the output dir, rejecting traversal."""
        base = os.path.realpath(self.output_dir)
        target = os.path.realpath(os.path.join(base, output_file))
        if target == base or target.startswith(base + os.sep):
            return target
        return None

    def _verify_against_source(self, image_path: str, source_device: str,
                               algorithm: str = 'sha256'):
        """Hash the written image and the source, and compare.

        Returns ``(image_hash, source_hash, verified)``. ``verified`` is True
        only when both hashes were computed and match — establishing that the
        acquisition is a faithful copy. A mismatch is expected when dd had to
        pad unreadable sectors (``conv=noerror,sync``) and flags a bad read.
        """
        image_hash = self._calculate_file_hash(image_path, algorithm) \
            if os.path.exists(image_path) else None
        source_hash = self._calculate_device_hash(source_device, algorithm)
        verified = bool(image_hash) and image_hash == source_hash
        return image_hash, source_hash, verified

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

            # Execute split command
            self.logger.info(f"Split command: {' '.join(split_cmd)}")
            result = subprocess.run(split_cmd, capture_output=True, text=True, timeout=None)

            if result.returncode != 0:
                raise Exception(f"split command failed: {result.stderr}")

            self.logger.info("Image split completed successfully")

            return OperationResult.ok({
                'original': image_path,
                'prefix': output_prefix,
                'chunk_size': chunk_size,
            })

        except Exception as e:
            self.logger.error(f"Image splitting failed: {e}")
            return OperationResult.fail(e)

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
