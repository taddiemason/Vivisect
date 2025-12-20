"""Memory analysis and forensics module"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class MemoryAnalysis:
    """Handles memory dumping and analysis"""

    def __init__(self, logger, config):
        self.logger = logger.get_logger('memory_analysis')
        self.config = config
        self.output_dir = config.get('output_dir')

    def create_memory_dump(self, output_file: str = None, method: str = 'auto') -> Dict[str, Any]:
        """Create a memory dump of the running system"""
        self.logger.info("Creating memory dump")

        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"memory_dump_{timestamp}.raw"

        output_path = os.path.join(self.output_dir, output_file)

        try:
            if method == 'auto' or method == 'lime':
                # Use LiME (Linux Memory Extractor) if available
                result = self._dump_with_lime(output_path)
            elif method == 'dd':
                # Use /dev/mem or /dev/crash
                result = self._dump_with_dd(output_path)
            elif method == 'avml':
                # Use AVML (Acquire Volatile Memory for Linux)
                result = self._dump_with_avml(output_path)
            else:
                return {'success': False, 'error': f'Unknown method: {method}'}

            return result

        except Exception as e:
            self.logger.error(f"Memory dump failed: {e}")
            return {'success': False, 'error': str(e)}

    def _dump_with_lime(self, output_path: str) -> Dict[str, Any]:
        """Create memory dump using LiME"""
        self.logger.info("Attempting memory dump with LiME")

        try:
            # Load LiME module
            insmod_cmd = [
                'insmod',
                '/opt/lime/lime.ko',
                f'path={output_path}',
                'format=raw'
            ]

            self.logger.info(f"LiME command: {' '.join(insmod_cmd)}")

            # Execute insmod command
            result = subprocess.run(insmod_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                raise Exception(f"LiME insmod failed: {result.stderr}")

            self.logger.info(f"Memory dump with LiME completed: {output_path}")

            return {
                'success': True,
                'method': 'lime',
                'output': output_path,
                'command': ' '.join(insmod_cmd),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"LiME dump failed: {e}")
            return {'success': False, 'error': str(e)}

    def _dump_with_dd(self, output_path: str) -> Dict[str, Any]:
        """Create memory dump using dd from /proc/kcore"""
        self.logger.info("Attempting memory dump with dd")

        try:
            dd_cmd = [
                'dd',
                'if=/proc/kcore',
                f'of={output_path}',
                'bs=4M'
            ]

            self.logger.info(f"dd command: {' '.join(dd_cmd)}")

            # Execute dd command
            result = subprocess.run(dd_cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                raise Exception(f"dd command failed: {result.stderr}")

            self.logger.info(f"Memory dump with dd completed: {output_path}")

            return {
                'success': True,
                'method': 'dd',
                'output': output_path,
                'command': ' '.join(dd_cmd),
                'timestamp': datetime.now().isoformat(),
                'note': 'Using /proc/kcore - may not capture all physical memory'
            }

        except Exception as e:
            self.logger.error(f"dd dump failed: {e}")
            return {'success': False, 'error': str(e)}

    def _dump_with_avml(self, output_path: str) -> Dict[str, Any]:
        """Create memory dump using AVML"""
        self.logger.info("Attempting memory dump with AVML")

        try:
            avml_cmd = ['avml', output_path]

            self.logger.info(f"AVML command: {' '.join(avml_cmd)}")

            # Execute AVML command
            result = subprocess.run(avml_cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                raise Exception(f"AVML command failed: {result.stderr}")

            self.logger.info(f"Memory dump with AVML completed: {output_path}")

            return {
                'success': True,
                'method': 'avml',
                'output': output_path,
                'command': ' '.join(avml_cmd),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"AVML dump failed: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_memory_dump(self, dump_file: str, profile: str = None) -> Dict[str, Any]:
        """Analyze memory dump using Volatility"""
        self.logger.info(f"Analyzing memory dump: {dump_file}")

        if not os.path.exists(dump_file):
            return {'error': 'Memory dump file not found'}

        try:
            analysis = {
                'dump_file': dump_file,
                'timestamp': datetime.now().isoformat(),
                'profile': profile,
                'findings': {}
            }

            # Use Volatility 3 for analysis
            if profile is None:
                # Auto-detect profile
                profile = self._detect_profile(dump_file)
                analysis['profile'] = profile

            # Get process list
            analysis['findings']['processes'] = self._get_process_list(dump_file, profile)

            # Get network connections
            analysis['findings']['network'] = self._get_network_connections(dump_file, profile)

            # Get loaded modules
            analysis['findings']['modules'] = self._get_loaded_modules(dump_file, profile)

            # Check for suspicious processes
            analysis['findings']['suspicious'] = self._find_suspicious_processes(
                analysis['findings'].get('processes', [])
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Memory analysis failed: {e}")
            return {'error': str(e)}

    def _detect_profile(self, dump_file: str) -> str:
        """Detect the appropriate Volatility profile"""
        try:
            # Volatility 3 uses automatic profile detection
            vol_cmd = ['vol.py', '-f', dump_file, 'banners.Banners']

            result = subprocess.run(
                vol_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Parse output to determine profile
                return 'Linux'  # Simplified

            return 'LinuxAuto'

        except Exception as e:
            self.logger.error(f"Profile detection failed: {e}")
            return 'LinuxAuto'

    def _get_process_list(self, dump_file: str, profile: str) -> List[Dict[str, Any]]:
        """Extract process list from memory dump"""
        self.logger.info("Extracting process list")

        try:
            vol_cmd = ['vol.py', '-f', dump_file, 'linux.pslist.PsList']

            result = subprocess.run(
                vol_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            processes = []
            if result.returncode == 0:
                # Parse Volatility output
                for line in result.stdout.split('\n')[2:]:  # Skip header
                    if line.strip():
                        # Parse process information
                        # This is simplified - actual parsing would be more complex
                        processes.append({'raw': line.strip()})

            return processes

        except Exception as e:
            self.logger.error(f"Process list extraction failed: {e}")
            return []

    def _get_network_connections(self, dump_file: str, profile: str) -> List[Dict[str, Any]]:
        """Extract network connections from memory dump"""
        self.logger.info("Extracting network connections")

        try:
            vol_cmd = ['vol.py', '-f', dump_file, 'linux.netstat.Netstat']

            result = subprocess.run(
                vol_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            connections = []
            if result.returncode == 0:
                for line in result.stdout.split('\n')[2:]:
                    if line.strip():
                        connections.append({'raw': line.strip()})

            return connections

        except Exception as e:
            self.logger.error(f"Network connection extraction failed: {e}")
            return []

    def _get_loaded_modules(self, dump_file: str, profile: str) -> List[Dict[str, Any]]:
        """Extract loaded kernel modules"""
        self.logger.info("Extracting loaded modules")

        try:
            vol_cmd = ['vol.py', '-f', dump_file, 'linux.lsmod.Lsmod']

            result = subprocess.run(
                vol_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            modules = []
            if result.returncode == 0:
                for line in result.stdout.split('\n')[2:]:
                    if line.strip():
                        modules.append({'raw': line.strip()})

            return modules

        except Exception as e:
            self.logger.error(f"Module extraction failed: {e}")
            return []

    def _find_suspicious_processes(self, processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potentially suspicious processes"""
        suspicious = []

        # Common suspicious process names
        suspicious_names = [
            'netcat', 'nc', 'ncat',
            'cryptominer', 'xmrig',
            'reverse_shell', 'backdoor',
            'rootkit'
        ]

        for proc in processes:
            proc_info = proc.get('raw', '').lower()
            for susp_name in suspicious_names:
                if susp_name in proc_info:
                    suspicious.append({
                        'process': proc,
                        'reason': f'Suspicious process name: {susp_name}',
                        'severity': 'high'
                    })

        return suspicious

    def extract_process_memory(self, dump_file: str, pid: int,
                              output_dir: str = None) -> Dict[str, Any]:
        """Extract memory of a specific process"""
        self.logger.info(f"Extracting memory for PID {pid}")

        if output_dir is None:
            output_dir = os.path.join(self.output_dir, f'process_{pid}')

        os.makedirs(output_dir, exist_ok=True)

        try:
            vol_cmd = [
                'vol.py', '-f', dump_file,
                'linux.proc_dump.ProcDump',
                '--pid', str(pid),
                '--dump-dir', output_dir
            ]

            self.logger.info(f"Extraction command: {' '.join(vol_cmd)}")

            # Execute volatility command
            result = subprocess.run(vol_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                raise Exception(f"Process extraction failed: {result.stderr}")

            self.logger.info(f"Process memory extraction completed for PID {pid}")

            return {
                'success': True,
                'pid': pid,
                'output_dir': output_dir,
                'command': ' '.join(vol_cmd)
            }

        except Exception as e:
            self.logger.error(f"Process memory extraction failed: {e}")
            return {'success': False, 'error': str(e)}

    def scan_for_malware(self, dump_file: str) -> Dict[str, Any]:
        """Scan memory dump for malware signatures"""
        self.logger.info("Scanning for malware in memory dump")

        try:
            findings = {
                'suspicious_strings': [],
                'hidden_processes': [],
                'injected_code': []
            }

            # Use Volatility to detect hidden processes
            vol_cmd = ['vol.py', '-f', dump_file, 'linux.pslist.PsList']
            # Compare with another process listing method to find hidden processes

            # Scan for suspicious strings
            strings_cmd = ['strings', dump_file]
            result = subprocess.run(
                strings_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                suspicious_patterns = [
                    'passwd', 'shadow', 'ssh', 'key',
                    'credit', 'card', 'password',
                    '/bin/bash', '/bin/sh'
                ]

                for line in result.stdout.split('\n')[:10000]:  # Limit
                    for pattern in suspicious_patterns:
                        if pattern in line.lower():
                            findings['suspicious_strings'].append(line[:100])
                            break

            return findings

        except Exception as e:
            self.logger.error(f"Malware scan failed: {e}")
            return {'error': str(e)}

    def get_bash_history_from_memory(self, dump_file: str) -> List[str]:
        """Extract bash history from memory dump"""
        self.logger.info("Extracting bash history from memory")

        try:
            # Use strings and grep to find bash history
            strings_cmd = f'strings {dump_file} | grep -E "^[a-zA-Z0-9_/-]+ "'

            result = subprocess.run(
                strings_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            commands = []
            if result.returncode == 0:
                commands = result.stdout.strip().split('\n')[:1000]  # Limit

            return commands

        except Exception as e:
            self.logger.error(f"Bash history extraction failed: {e}")
            return []

    def analyze_running_system(self) -> Dict[str, Any]:
        """Analyze current running system without creating full dump"""
        self.logger.info("Analyzing running system")

        try:
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'processes': [],
                'network': [],
                'loaded_modules': [],
                'memory_usage': {}
            }

            # Get process list
            ps_cmd = ['ps', 'auxf']
            result = subprocess.run(ps_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                analysis['processes'] = result.stdout.strip().split('\n')

            # Get network connections
            netstat_cmd = ['ss', '-tupan']
            result = subprocess.run(netstat_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                analysis['network'] = result.stdout.strip().split('\n')

            # Get loaded modules
            lsmod_cmd = ['lsmod']
            result = subprocess.run(lsmod_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                analysis['loaded_modules'] = result.stdout.strip().split('\n')

            # Get memory usage
            free_cmd = ['free', '-h']
            result = subprocess.run(free_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                analysis['memory_usage'] = result.stdout

            return analysis

        except Exception as e:
            self.logger.error(f"System analysis failed: {e}")
            return {'error': str(e)}
