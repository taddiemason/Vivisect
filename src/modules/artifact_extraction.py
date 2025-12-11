"""Artifact extraction module for browser history, registry, logs, etc."""

import os
import sqlite3
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class ArtifactExtraction:
    """Extracts forensic artifacts from various sources"""

    def __init__(self, logger, config):
        self.logger = logger.get_logger('artifact_extraction')
        self.config = config
        self.output_dir = config.get('output_dir')

    def extract_browser_history(self, user_home: str = None) -> Dict[str, Any]:
        """Extract browser history from various browsers"""
        self.logger.info("Extracting browser history")

        if user_home is None:
            user_home = os.path.expanduser('~')

        artifacts = {
            'chrome': [],
            'firefox': [],
            'edge': [],
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Chrome/Chromium
            chrome_paths = [
                os.path.join(user_home, '.config/google-chrome/Default/History'),
                os.path.join(user_home, '.config/chromium/Default/History')
            ]
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    artifacts['chrome'].extend(self._extract_chrome_history(chrome_path))

            # Firefox
            firefox_path = os.path.join(user_home, '.mozilla/firefox')
            if os.path.exists(firefox_path):
                artifacts['firefox'].extend(self._extract_firefox_history(firefox_path))

            return artifacts

        except Exception as e:
            self.logger.error(f"Browser history extraction failed: {e}")
            return {'error': str(e)}

    def _extract_chrome_history(self, db_path: str) -> List[Dict[str, Any]]:
        """Extract history from Chrome/Chromium SQLite database"""
        history = []

        try:
            # Copy database to avoid lock issues
            import shutil
            temp_db = '/tmp/chrome_history_temp.db'
            shutil.copy2(db_path, temp_db)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            query = """
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                ORDER BY last_visit_time DESC
                LIMIT 1000
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                # Chrome stores timestamps as microseconds since 1601-01-01
                timestamp = row[3] / 1000000 - 11644473600 if row[3] else 0
                history.append({
                    'url': row[0],
                    'title': row[1],
                    'visit_count': row[2],
                    'last_visit': datetime.fromtimestamp(timestamp).isoformat() if timestamp > 0 else 'N/A'
                })

            conn.close()
            os.remove(temp_db)

        except Exception as e:
            self.logger.error(f"Chrome history extraction failed: {e}")

        return history

    def _extract_firefox_history(self, firefox_dir: str) -> List[Dict[str, Any]]:
        """Extract history from Firefox places.sqlite database"""
        history = []

        try:
            # Find profile directories
            for profile in os.listdir(firefox_dir):
                profile_path = os.path.join(firefox_dir, profile)
                if os.path.isdir(profile_path):
                    places_db = os.path.join(profile_path, 'places.sqlite')
                    if os.path.exists(places_db):
                        import shutil
                        temp_db = '/tmp/firefox_places_temp.db'
                        shutil.copy2(places_db, temp_db)

                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()

                        query = """
                            SELECT url, title, visit_count, last_visit_date
                            FROM moz_places
                            WHERE url IS NOT NULL
                            ORDER BY last_visit_date DESC
                            LIMIT 1000
                        """

                        cursor.execute(query)
                        rows = cursor.fetchall()

                        for row in rows:
                            # Firefox stores timestamps in microseconds
                            timestamp = row[3] / 1000000 if row[3] else 0
                            history.append({
                                'url': row[0],
                                'title': row[1],
                                'visit_count': row[2],
                                'last_visit': datetime.fromtimestamp(timestamp).isoformat() if timestamp > 0 else 'N/A',
                                'profile': profile
                            })

                        conn.close()
                        os.remove(temp_db)

        except Exception as e:
            self.logger.error(f"Firefox history extraction failed: {e}")

        return history

    def extract_system_logs(self, log_dir: str = '/var/log') -> Dict[str, Any]:
        """Extract and analyze system logs"""
        self.logger.info(f"Extracting system logs from {log_dir}")

        logs = {
            'auth_logs': [],
            'syslog': [],
            'kernel_logs': [],
            'application_logs': []
        }

        try:
            # Authentication logs
            auth_log_files = [
                os.path.join(log_dir, 'auth.log'),
                os.path.join(log_dir, 'secure')
            ]
            for log_file in auth_log_files:
                if os.path.exists(log_file):
                    logs['auth_logs'].extend(self._read_log_file(log_file, lines=1000))

            # Syslog
            syslog_file = os.path.join(log_dir, 'syslog')
            if os.path.exists(syslog_file):
                logs['syslog'] = self._read_log_file(syslog_file, lines=1000)

            # Kernel logs
            kern_log = os.path.join(log_dir, 'kern.log')
            if os.path.exists(kern_log):
                logs['kernel_logs'] = self._read_log_file(kern_log, lines=500)

            # Journal logs (systemd)
            try:
                journal_cmd = ['journalctl', '-n', '1000', '--output=json']
                result = subprocess.run(
                    journal_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    logs['systemd_journal'] = result.stdout.strip().split('\n')
            except Exception as e:
                self.logger.warning(f"Journal extraction failed: {e}")

            return logs

        except Exception as e:
            self.logger.error(f"System log extraction failed: {e}")
            return {'error': str(e)}

    def _read_log_file(self, filepath: str, lines: int = 1000) -> List[str]:
        """Read last N lines from a log file"""
        try:
            result = subprocess.run(
                ['tail', '-n', str(lines), filepath],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            return []
        except Exception as e:
            self.logger.error(f"Log file read failed: {e}")
            return []

    def extract_user_artifacts(self, user_home: str = None) -> Dict[str, Any]:
        """Extract user-specific artifacts"""
        self.logger.info("Extracting user artifacts")

        if user_home is None:
            user_home = os.path.expanduser('~')

        artifacts = {
            'bash_history': [],
            'ssh_keys': [],
            'known_hosts': [],
            'downloads': [],
            'recent_files': []
        }

        try:
            # Bash history
            bash_history = os.path.join(user_home, '.bash_history')
            if os.path.exists(bash_history):
                with open(bash_history, 'r', errors='ignore') as f:
                    artifacts['bash_history'] = f.readlines()[:1000]

            # SSH artifacts
            ssh_dir = os.path.join(user_home, '.ssh')
            if os.path.exists(ssh_dir):
                # List SSH keys (not reading private keys for security)
                for item in os.listdir(ssh_dir):
                    item_path = os.path.join(ssh_dir, item)
                    if os.path.isfile(item_path):
                        artifacts['ssh_keys'].append({
                            'filename': item,
                            'size': os.path.getsize(item_path),
                            'modified': datetime.fromtimestamp(
                                os.path.getmtime(item_path)
                            ).isoformat()
                        })

                # Known hosts
                known_hosts = os.path.join(ssh_dir, 'known_hosts')
                if os.path.exists(known_hosts):
                    with open(known_hosts, 'r', errors='ignore') as f:
                        artifacts['known_hosts'] = f.readlines()

            # Recent downloads
            downloads_dir = os.path.join(user_home, 'Downloads')
            if os.path.exists(downloads_dir):
                for item in os.listdir(downloads_dir)[:100]:
                    item_path = os.path.join(downloads_dir, item)
                    if os.path.isfile(item_path):
                        artifacts['downloads'].append({
                            'filename': item,
                            'size': os.path.getsize(item_path),
                            'modified': datetime.fromtimestamp(
                                os.path.getmtime(item_path)
                            ).isoformat()
                        })

            return artifacts

        except Exception as e:
            self.logger.error(f"User artifact extraction failed: {e}")
            return {'error': str(e)}

    def extract_installed_packages(self) -> Dict[str, Any]:
        """Extract list of installed packages"""
        self.logger.info("Extracting installed packages")

        packages = {
            'dpkg': [],
            'snap': [],
            'flatpak': []
        }

        try:
            # Debian packages
            dpkg_cmd = ['dpkg', '-l']
            result = subprocess.run(dpkg_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                packages['dpkg'] = result.stdout.strip().split('\n')

            # Snap packages
            snap_cmd = ['snap', 'list']
            result = subprocess.run(snap_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                packages['snap'] = result.stdout.strip().split('\n')

            # Flatpak packages
            flatpak_cmd = ['flatpak', 'list']
            result = subprocess.run(flatpak_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                packages['flatpak'] = result.stdout.strip().split('\n')

            return packages

        except Exception as e:
            self.logger.error(f"Package extraction failed: {e}")
            return {'error': str(e)}

    def extract_network_configuration(self) -> Dict[str, Any]:
        """Extract network configuration and artifacts"""
        self.logger.info("Extracting network configuration")

        network_info = {
            'interfaces': [],
            'routing_table': [],
            'arp_cache': [],
            'dns_config': [],
            'firewall_rules': []
        }

        try:
            # Network interfaces
            ip_cmd = ['ip', 'addr', 'show']
            result = subprocess.run(ip_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                network_info['interfaces'] = result.stdout.strip().split('\n')

            # Routing table
            route_cmd = ['ip', 'route', 'show']
            result = subprocess.run(route_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                network_info['routing_table'] = result.stdout.strip().split('\n')

            # ARP cache
            arp_cmd = ['ip', 'neigh', 'show']
            result = subprocess.run(arp_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                network_info['arp_cache'] = result.stdout.strip().split('\n')

            # DNS configuration
            resolv_conf = '/etc/resolv.conf'
            if os.path.exists(resolv_conf):
                with open(resolv_conf, 'r') as f:
                    network_info['dns_config'] = f.readlines()

            # Firewall rules (iptables)
            iptables_cmd = ['iptables', '-L', '-n', '-v']
            result = subprocess.run(iptables_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                network_info['firewall_rules'] = result.stdout.strip().split('\n')

            return network_info

        except Exception as e:
            self.logger.error(f"Network configuration extraction failed: {e}")
            return {'error': str(e)}

    def extract_persistence_mechanisms(self) -> Dict[str, Any]:
        """Extract potential persistence mechanisms"""
        self.logger.info("Extracting persistence mechanisms")

        persistence = {
            'cron_jobs': [],
            'systemd_services': [],
            'startup_scripts': [],
            'user_crontabs': []
        }

        try:
            # System cron jobs
            cron_dirs = ['/etc/cron.d', '/etc/cron.daily', '/etc/cron.hourly']
            for cron_dir in cron_dirs:
                if os.path.exists(cron_dir):
                    for item in os.listdir(cron_dir):
                        item_path = os.path.join(cron_dir, item)
                        if os.path.isfile(item_path):
                            persistence['cron_jobs'].append({
                                'location': cron_dir,
                                'filename': item,
                                'path': item_path
                            })

            # Systemd services
            systemctl_cmd = ['systemctl', 'list-unit-files', '--type=service']
            result = subprocess.run(systemctl_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                persistence['systemd_services'] = result.stdout.strip().split('\n')

            # RC scripts
            rc_dirs = ['/etc/rc.local', '/etc/rc*.d']
            for rc_pattern in rc_dirs:
                import glob
                for rc_file in glob.glob(rc_pattern):
                    if os.path.exists(rc_file):
                        persistence['startup_scripts'].append(rc_file)

            # User crontabs
            crontab_cmd = ['crontab', '-l']
            result = subprocess.run(crontab_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                persistence['user_crontabs'] = result.stdout.strip().split('\n')

            return persistence

        except Exception as e:
            self.logger.error(f"Persistence mechanism extraction failed: {e}")
            return {'error': str(e)}

    def extract_timeline_data(self, directory: str) -> List[Dict[str, Any]]:
        """Create timeline of file system changes"""
        self.logger.info(f"Creating timeline for {directory}")

        timeline = []

        try:
            # Use find to get all files with timestamps
            find_cmd = [
                'find', directory,
                '-type', 'f',
                '-printf', '%T@ %p %s\\n'
            ]

            result = subprocess.run(
                find_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[:10000]:  # Limit
                    if line:
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            timestamp = float(parts[0])
                            timeline.append({
                                'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                                'path': parts[1],
                                'size': parts[2] if len(parts) > 2 else '0'
                            })

            # Sort by timestamp
            timeline.sort(key=lambda x: x['timestamp'], reverse=True)

            return timeline

        except Exception as e:
            self.logger.error(f"Timeline creation failed: {e}")
            return []

    def search_for_credentials(self, directory: str) -> List[Dict[str, Any]]:
        """Search for potential credentials in files"""
        self.logger.info(f"Searching for credentials in {directory}")

        findings = []

        try:
            # Search for common credential patterns
            patterns = [
                'password',
                'passwd',
                'api_key',
                'apikey',
                'secret',
                'token',
                'credentials'
            ]

            for pattern in patterns:
                grep_cmd = [
                    'grep', '-r', '-i',
                    '--include=*.txt',
                    '--include=*.conf',
                    '--include=*.cfg',
                    '--include=*.ini',
                    '--include=*.json',
                    '--include=*.xml',
                    pattern,
                    directory
                ]

                result = subprocess.run(
                    grep_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n')[:100]:  # Limit
                        if line:
                            findings.append({
                                'pattern': pattern,
                                'match': line[:200]  # Truncate long lines
                            })

            return findings

        except Exception as e:
            self.logger.error(f"Credential search failed: {e}")
            return []
