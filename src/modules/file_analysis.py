"""File analysis and carving module"""

import os
import hashlib
import magic
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class FileAnalysis:
    """Handles file analysis, carving, and metadata extraction"""

    # Common file signatures for carving
    FILE_SIGNATURES = {
        'jpeg': {'header': b'\xFF\xD8\xFF', 'footer': b'\xFF\xD9', 'extension': '.jpg'},
        'png': {'header': b'\x89\x50\x4E\x47', 'footer': b'\x49\x45\x4E\x44\xAE\x42\x60\x82', 'extension': '.png'},
        'pdf': {'header': b'\x25\x50\x44\x46', 'footer': b'\x25\x25\x45\x4F\x46', 'extension': '.pdf'},
        'zip': {'header': b'\x50\x4B\x03\x04', 'footer': b'\x50\x4B\x05\x06', 'extension': '.zip'},
        'elf': {'header': b'\x7F\x45\x4C\x46', 'footer': None, 'extension': '.elf'},
        'sqlite': {'header': b'\x53\x51\x4C\x69\x74\x65\x20\x66\x6F\x72\x6D\x61\x74\x20\x33', 'footer': None, 'extension': '.db'},
    }

    def __init__(self, logger, config):
        self.logger = logger.get_logger('file_analysis')
        self.config = config
        self.output_dir = config.get('output_dir')

    def calculate_hashes(self, filepath: str, algorithms: List[str] = None) -> Dict[str, str]:
        """Calculate multiple hashes for a file"""
        if algorithms is None:
            algorithms = ['md5', 'sha1', 'sha256']

        self.logger.info(f"Calculating hashes for {filepath}")

        if not os.path.exists(filepath):
            self.logger.error(f"File not found: {filepath}")
            return {}

        hashes = {}
        hash_objects = {algo: hashlib.new(algo) for algo in algorithms}

        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    for hash_obj in hash_objects.values():
                        hash_obj.update(chunk)

            for algo, hash_obj in hash_objects.items():
                hashes[algo] = hash_obj.hexdigest()

            self.logger.info(f"Hashes calculated: {hashes}")
            return hashes

        except Exception as e:
            self.logger.error(f"Hash calculation failed: {e}")
            return {}

    def get_file_metadata(self, filepath: str) -> Dict[str, Any]:
        """Extract comprehensive file metadata"""
        self.logger.info(f"Extracting metadata from {filepath}")

        if not os.path.exists(filepath):
            return {'error': 'File not found'}

        try:
            stat_info = os.stat(filepath)
            metadata = {
                'path': filepath,
                'filename': os.path.basename(filepath),
                'size': stat_info.st_size,
                'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                'permissions': oct(stat_info.st_mode)[-3:],
                'owner_uid': stat_info.st_uid,
                'owner_gid': stat_info.st_gid,
                'inode': stat_info.st_ino,
            }

            # Get file type using libmagic
            try:
                metadata['mime_type'] = magic.from_file(filepath, mime=True)
                metadata['file_type'] = magic.from_file(filepath)
            except Exception as e:
                self.logger.warning(f"Magic library not available: {e}")
                metadata['mime_type'] = 'unknown'
                metadata['file_type'] = 'unknown'

            # Calculate hashes
            metadata['hashes'] = self.calculate_hashes(filepath)

            return metadata

        except Exception as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            return {'error': str(e)}

    def scan_directory(self, directory: str, recursive: bool = True,
                      calculate_hashes: bool = True) -> List[Dict[str, Any]]:
        """Scan directory and collect file information"""
        self.logger.info(f"Scanning directory: {directory}")

        files_info = []

        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        try:
                            if calculate_hashes:
                                info = self.get_file_metadata(filepath)
                            else:
                                stat_info = os.stat(filepath)
                                info = {
                                    'path': filepath,
                                    'size': stat_info.st_size,
                                    'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                                }
                            files_info.append(info)
                        except Exception as e:
                            self.logger.warning(f"Error processing {filepath}: {e}")
            else:
                for entry in os.listdir(directory):
                    filepath = os.path.join(directory, entry)
                    if os.path.isfile(filepath):
                        try:
                            if calculate_hashes:
                                info = self.get_file_metadata(filepath)
                            else:
                                stat_info = os.stat(filepath)
                                info = {
                                    'path': filepath,
                                    'size': stat_info.st_size,
                                    'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                                }
                            files_info.append(info)
                        except Exception as e:
                            self.logger.warning(f"Error processing {filepath}: {e}")

            self.logger.info(f"Scanned {len(files_info)} files")
            return files_info

        except Exception as e:
            self.logger.error(f"Directory scan failed: {e}")
            return []

    def carve_files(self, source: str, output_dir: str = None,
                   file_types: List[str] = None) -> Dict[str, Any]:
        """Carve files from disk image or raw data"""
        self.logger.info(f"Starting file carving from {source}")

        if output_dir is None:
            output_dir = os.path.join(self.output_dir, 'carved_files')

        os.makedirs(output_dir, exist_ok=True)

        if file_types is None:
            file_types = list(self.FILE_SIGNATURES.keys())

        carved_files = []

        try:
            # Use foremost for file carving if available
            foremost_cmd = [
                'foremost',
                '-t', ','.join(file_types),
                '-o', output_dir,
                '-i', source
            ]

            self.logger.info(f"Carving command: {' '.join(foremost_cmd)}")

            # Alternative: use scalpel
            scalpel_cmd = [
                'scalpel',
                source,
                '-o', output_dir
            ]

            result = {
                'success': True,
                'source': source,
                'output_dir': output_dir,
                'file_types': file_types,
                'carved_files': [],
                'command': ' '.join(foremost_cmd)
            }

            # Scan output directory for carved files
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        result['carved_files'].append({
                            'path': filepath,
                            'size': os.path.getsize(filepath),
                            'type': os.path.splitext(filename)[1]
                        })

            self.logger.info(f"Carved {len(result['carved_files'])} files")
            return result

        except Exception as e:
            self.logger.error(f"File carving failed: {e}")
            return {'success': False, 'error': str(e)}

    def search_strings(self, filepath: str, min_length: int = 4,
                      encoding: str = 'ascii') -> List[str]:
        """Extract printable strings from file"""
        self.logger.info(f"Extracting strings from {filepath}")

        try:
            strings_cmd = [
                'strings',
                '-n', str(min_length),
                '-e', encoding,
                filepath
            ]

            result = subprocess.run(
                strings_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                strings_list = result.stdout.strip().split('\n')
                self.logger.info(f"Extracted {len(strings_list)} strings")
                return strings_list
            else:
                self.logger.error(f"Strings extraction failed: {result.stderr}")
                return []

        except Exception as e:
            self.logger.error(f"String extraction failed: {e}")
            return []

    def find_entropy(self, filepath: str) -> Dict[str, Any]:
        """Calculate file entropy (useful for detecting encryption/compression)"""
        self.logger.info(f"Calculating entropy for {filepath}")

        try:
            with open(filepath, 'rb') as f:
                data = f.read()

            if not data:
                return {'entropy': 0, 'size': 0}

            # Calculate byte frequency
            byte_counts = [0] * 256
            for byte in data:
                byte_counts[byte] += 1

            # Calculate entropy
            import math
            entropy = 0
            data_len = len(data)

            for count in byte_counts:
                if count > 0:
                    probability = count / data_len
                    entropy -= probability * math.log2(probability)

            result = {
                'filepath': filepath,
                'entropy': round(entropy, 4),
                'size': data_len,
                'max_entropy': 8.0,
                'percentage': round((entropy / 8.0) * 100, 2),
                'assessment': self._assess_entropy(entropy)
            }

            self.logger.info(f"Entropy: {entropy}")
            return result

        except Exception as e:
            self.logger.error(f"Entropy calculation failed: {e}")
            return {'error': str(e)}

    def _assess_entropy(self, entropy: float) -> str:
        """Assess what entropy level might indicate"""
        if entropy < 1.0:
            return "Very low - likely uniform data"
        elif entropy < 3.0:
            return "Low - likely simple data or text"
        elif entropy < 5.0:
            return "Medium - typical executable or mixed data"
        elif entropy < 7.0:
            return "High - compressed or encrypted data likely"
        else:
            return "Very high - likely encrypted or highly compressed"

    def compare_files(self, file1: str, file2: str) -> Dict[str, Any]:
        """Compare two files for forensic analysis"""
        self.logger.info(f"Comparing {file1} and {file2}")

        try:
            hash1 = self.calculate_hashes(file1)
            hash2 = self.calculate_hashes(file2)

            result = {
                'file1': file1,
                'file2': file2,
                'identical_hashes': hash1 == hash2,
                'file1_hashes': hash1,
                'file2_hashes': hash2,
                'size_match': os.path.getsize(file1) == os.path.getsize(file2)
            }

            return result

        except Exception as e:
            self.logger.error(f"File comparison failed: {e}")
            return {'error': str(e)}

    def find_hidden_data(self, filepath: str) -> Dict[str, Any]:
        """Look for hidden data, alternate data streams, steganography indicators"""
        self.logger.info(f"Searching for hidden data in {filepath}")

        findings = {
            'filepath': filepath,
            'potential_issues': []
        }

        try:
            # Check entropy (high entropy might indicate encryption/steganography)
            entropy_info = self.find_entropy(filepath)
            if entropy_info.get('entropy', 0) > 7.5:
                findings['potential_issues'].append({
                    'type': 'high_entropy',
                    'description': 'Unusually high entropy - possible encryption or steganography',
                    'entropy': entropy_info['entropy']
                })

            # Check for suspicious strings
            strings = self.search_strings(filepath, min_length=8)
            suspicious_keywords = ['password', 'secret', 'key', 'confidential', 'hidden']
            found_keywords = [s for s in strings if any(kw in s.lower() for kw in suspicious_keywords)]

            if found_keywords:
                findings['potential_issues'].append({
                    'type': 'suspicious_strings',
                    'description': 'Found suspicious keywords',
                    'samples': found_keywords[:10]
                })

            return findings

        except Exception as e:
            self.logger.error(f"Hidden data search failed: {e}")
            return {'error': str(e)}
