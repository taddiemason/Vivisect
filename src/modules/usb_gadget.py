"""USB Gadget Mode for Vivisect"""

import os
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Optional

class USBGadget:
    """Manages USB gadget mode for forensics collection"""

    def __init__(self, logger, config):
        self.logger = logger.get_logger('usb_gadget')
        self.config = config
        self.output_dir = config.get('output_dir')
        self.gadget_interface = 'usb0'
        self.host_ip = '10.55.0.1'
        self.device_ip = '10.55.0.2'

        # Multi-function mode settings
        self.mass_storage_file = '/var/lib/vivisect/usb_storage.img'
        self.mass_storage_mount = '/mnt/vivisect_usb'
        self.serial_device = '/dev/ttyGS0'
        self.gadget_mode = 'multi'  # 'ether', 'multi', 'serial', 'mass_storage'

    def is_gadget_enabled(self) -> bool:
        """Check if USB gadget mode is enabled"""
        try:
            # Check if g_ether or g_multi module is loaded
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True
            )

            return 'g_ether' in result.stdout or 'g_multi' in result.stdout
        except Exception as e:
            self.logger.error(f"Failed to check gadget status: {e}")
            return False

    def is_connected_to_host(self) -> bool:
        """Check if device is connected to a host PC via USB"""
        try:
            # Check if usb0 interface exists and is up
            result = subprocess.run(
                ['ip', 'link', 'show', self.gadget_interface],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Check if interface is UP
                return 'state UP' in result.stdout or 'UP' in result.stdout

            return False
        except Exception as e:
            self.logger.error(f"Failed to check USB connection: {e}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about USB connection"""
        try:
            info = {
                'connected': self.is_connected_to_host(),
                'gadget_enabled': self.is_gadget_enabled(),
                'interface': self.gadget_interface,
                'device_ip': self.device_ip,
                'host_ip': self.host_ip,
                'timestamp': datetime.now().isoformat()
            }

            if info['connected']:
                # Get interface statistics
                result = subprocess.run(
                    ['ip', '-s', 'link', 'show', self.gadget_interface],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info['interface_stats'] = result.stdout

            return info
        except Exception as e:
            self.logger.error(f"Failed to get connection info: {e}")
            return {'error': str(e)}

    def configure_network(self) -> Dict[str, Any]:
        """Configure USB network interface"""
        self.logger.info("Configuring USB network interface")

        try:
            commands = [
                # Bring up interface
                ['ip', 'link', 'set', self.gadget_interface, 'up'],
                # Set IP address
                ['ip', 'addr', 'add', f'{self.device_ip}/24', 'dev', self.gadget_interface],
                # Add route to host
                ['ip', 'route', 'add', self.host_ip, 'dev', self.gadget_interface],
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Command failed: {' '.join(cmd)}: {result.stderr}")

            # Enable IP forwarding
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('1')

            self.logger.info("USB network configured successfully")

            return {
                'success': True,
                'device_ip': self.device_ip,
                'host_ip': self.host_ip,
                'interface': self.gadget_interface
            }

        except Exception as e:
            self.logger.error(f"Network configuration failed: {e}")
            return {'success': False, 'error': str(e)}

    def start_packet_capture(self, output_file: str = None) -> Dict[str, Any]:
        """Start capturing traffic on USB interface"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"usb_capture_{timestamp}.pcap"

        output_path = os.path.join(self.output_dir, output_file)

        self.logger.info(f"Starting USB packet capture: {output_path}")

        try:
            # Start tcpdump in background
            tcpdump_cmd = [
                'tcpdump',
                '-i', self.gadget_interface,
                '-w', output_path,
                '-n'  # Don't resolve hostnames
            ]

            # This would run in background in production
            self.logger.info(f"Capture command: {' '.join(tcpdump_cmd)}")

            return {
                'success': True,
                'output_file': output_path,
                'interface': self.gadget_interface,
                'command': ' '.join(tcpdump_cmd)
            }

        except Exception as e:
            self.logger.error(f"Packet capture failed: {e}")
            return {'success': False, 'error': str(e)}

    def monitor_host_activity(self) -> Dict[str, Any]:
        """Monitor activity from connected host PC"""
        self.logger.info("Monitoring host PC activity")

        try:
            activity = {
                'timestamp': datetime.now().isoformat(),
                'connections': [],
                'dns_queries': [],
                'http_requests': []
            }

            # Get active connections
            result = subprocess.run(
                ['ss', '-tupn'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                activity['connections'] = result.stdout.strip().split('\n')

            # Monitor ARP table to see host MAC
            result = subprocess.run(
                ['ip', 'neigh', 'show', 'dev', self.gadget_interface],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                activity['arp_table'] = result.stdout.strip().split('\n')

            return activity

        except Exception as e:
            self.logger.error(f"Host monitoring failed: {e}")
            return {'error': str(e)}

    def extract_host_info(self) -> Dict[str, Any]:
        """Extract information about connected host PC"""
        self.logger.info("Extracting host PC information")

        try:
            host_info = {
                'timestamp': datetime.now().isoformat(),
                'host_ip': self.host_ip,
                'detected_services': []
            }

            # Scan host for open ports (quick scan)
            nmap_cmd = [
                'nmap',
                '-F',  # Fast scan
                '-T4', # Aggressive timing
                self.host_ip
            ]

            # Note: This requires nmap to be installed
            # In production, we'd check if available first
            self.logger.info(f"Scanning host: {' '.join(nmap_cmd)}")

            return host_info

        except Exception as e:
            self.logger.error(f"Host info extraction failed: {e}")
            return {'error': str(e)}

    def enable_mitm_mode(self) -> Dict[str, Any]:
        """Enable Man-in-the-Middle mode for deep inspection"""
        self.logger.info("Enabling MITM mode")

        try:
            # Set up iptables for traffic interception
            iptables_rules = [
                # Enable NAT
                ['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', 'wlan0', '-j', 'MASQUERADE'],
                # Redirect HTTP traffic
                ['iptables', '-t', 'nat', '-A', 'PREROUTING', '-i', self.gadget_interface, '-p', 'tcp', '--dport', '80', '-j', 'REDIRECT', '--to-port', '8080'],
                # Redirect HTTPS for inspection (requires SSL interception)
                ['iptables', '-t', 'nat', '-A', 'PREROUTING', '-i', self.gadget_interface, '-p', 'tcp', '--dport', '443', '-j', 'REDIRECT', '--to-port', '8443'],
            ]

            for rule in iptables_rules:
                self.logger.info(f"Applying rule: {' '.join(rule)}")
                # In production, we'd actually execute these

            return {
                'success': True,
                'mode': 'mitm',
                'http_intercept_port': 8080,
                'https_intercept_port': 8443
            }

        except Exception as e:
            self.logger.error(f"MITM mode failed: {e}")
            return {'success': False, 'error': str(e)}

    def auto_collect_on_connection(self) -> Dict[str, Any]:
        """Automatically start collection when host connects"""
        self.logger.info("Starting auto-collection on USB connection")

        try:
            case_id = f"USB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            collection_info = {
                'case_id': case_id,
                'timestamp': datetime.now().isoformat(),
                'tasks': []
            }

            # 1. Configure network
            net_result = self.configure_network()
            collection_info['tasks'].append({
                'task': 'configure_network',
                'result': net_result
            })

            # 2. Start packet capture
            capture_result = self.start_packet_capture()
            collection_info['tasks'].append({
                'task': 'packet_capture',
                'result': capture_result
            })

            # 3. Monitor host activity
            activity_result = self.monitor_host_activity()
            collection_info['tasks'].append({
                'task': 'host_monitoring',
                'result': activity_result
            })

            self.logger.info(f"Auto-collection started: {case_id}")

            return collection_info

        except Exception as e:
            self.logger.error(f"Auto-collection failed: {e}")
            return {'error': str(e)}

    def get_gadget_status(self) -> Dict[str, Any]:
        """Get comprehensive USB gadget status"""
        try:
            status = {
                'gadget_enabled': self.is_gadget_enabled(),
                'connected': self.is_connected_to_host(),
                'interface': self.gadget_interface,
                'device_ip': self.device_ip,
                'host_ip': self.host_ip,
                'timestamp': datetime.now().isoformat()
            }

            # Check kernel modules
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True
            )

            loaded_modules = []
            for line in result.stdout.split('\n'):
                if 'g_ether' in line or 'g_multi' in line or 'dwc2' in line:
                    loaded_modules.append(line.split()[0])

            status['loaded_modules'] = loaded_modules

            # Check configfs gadget
            gadget_path = '/sys/kernel/config/usb_gadget'
            if os.path.exists(gadget_path):
                status['configfs_available'] = True
                try:
                    gadgets = os.listdir(gadget_path)
                    status['configured_gadgets'] = gadgets
                except:
                    status['configured_gadgets'] = []
            else:
                status['configfs_available'] = False

            return status

        except Exception as e:
            self.logger.error(f"Failed to get gadget status: {e}")
            return {'error': str(e)}

    # ==================== Multi-Function Mode Support ====================

    def is_mass_storage_available(self) -> bool:
        """Check if mass storage gadget is available"""
        try:
            # Check if backing file exists
            if not os.path.exists(self.mass_storage_file):
                return False

            # Check if mass storage is exposed via g_multi or g_mass_storage
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True
            )

            return 'g_multi' in result.stdout or 'g_mass_storage' in result.stdout

        except Exception as e:
            self.logger.error(f"Failed to check mass storage: {e}")
            return False

    def is_serial_available(self) -> bool:
        """Check if serial console is available"""
        try:
            # Check if serial device exists
            return os.path.exists(self.serial_device)
        except Exception as e:
            self.logger.error(f"Failed to check serial console: {e}")
            return False

    def create_mass_storage_image(self, size_mb: int = 512, filesystem: str = 'vfat') -> Dict[str, Any]:
        """Create a mass storage backing file for reports/evidence"""
        self.logger.info(f"Creating {size_mb}MB mass storage image")

        try:
            # Create directory if needed
            storage_dir = os.path.dirname(self.mass_storage_file)
            os.makedirs(storage_dir, exist_ok=True)
            os.makedirs(self.mass_storage_mount, exist_ok=True)

            # Create sparse file
            self.logger.info(f"Creating backing file: {self.mass_storage_file}")
            result = subprocess.run(
                ['dd', 'if=/dev/zero', f'of={self.mass_storage_file}',
                 'bs=1M', f'count={size_mb}', 'status=progress'],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"Failed to create backing file: {result.stderr}")

            # Format with filesystem
            self.logger.info(f"Formatting with {filesystem}")
            if filesystem == 'vfat':
                mkfs_cmd = ['mkfs.vfat', '-n', 'VIVISECT', self.mass_storage_file]
            elif filesystem == 'ext4':
                mkfs_cmd = ['mkfs.ext4', '-L', 'VIVISECT', '-F', self.mass_storage_file]
            else:
                raise Exception(f"Unsupported filesystem: {filesystem}")

            result = subprocess.run(mkfs_cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise Exception(f"Failed to format: {result.stderr}")

            self.logger.info("Mass storage image created successfully")

            return {
                'success': True,
                'file': self.mass_storage_file,
                'size_mb': size_mb,
                'filesystem': filesystem,
                'mount_point': self.mass_storage_mount
            }

        except Exception as e:
            self.logger.error(f"Mass storage creation failed: {e}")
            return {'success': False, 'error': str(e)}

    def mount_mass_storage(self) -> Dict[str, Any]:
        """Mount mass storage image for writing reports"""
        self.logger.info("Mounting mass storage image")

        try:
            if not os.path.exists(self.mass_storage_file):
                return {'success': False, 'error': 'Mass storage image does not exist'}

            # Create mount point
            os.makedirs(self.mass_storage_mount, exist_ok=True)

            # Mount the image
            result = subprocess.run(
                ['mount', '-o', 'loop', self.mass_storage_file, self.mass_storage_mount],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"Mount failed: {result.stderr}")

            self.logger.info(f"Mounted at {self.mass_storage_mount}")

            return {
                'success': True,
                'mount_point': self.mass_storage_mount,
                'backing_file': self.mass_storage_file
            }

        except Exception as e:
            self.logger.error(f"Mount failed: {e}")
            return {'success': False, 'error': str(e)}

    def unmount_mass_storage(self) -> Dict[str, Any]:
        """Unmount mass storage image"""
        self.logger.info("Unmounting mass storage image")

        try:
            result = subprocess.run(
                ['umount', self.mass_storage_mount],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.logger.warning(f"Unmount warning: {result.stderr}")

            return {'success': True}

        except Exception as e:
            self.logger.error(f"Unmount failed: {e}")
            return {'success': False, 'error': str(e)}

    def sync_reports_to_storage(self) -> Dict[str, Any]:
        """Sync reports and evidence to mass storage"""
        self.logger.info("Syncing reports to USB mass storage")

        try:
            # Mount storage
            mount_result = self.mount_mass_storage()
            if not mount_result.get('success'):
                return mount_result

            # Copy reports
            reports_dir = os.path.join(self.output_dir, 'reports')
            if os.path.exists(reports_dir):
                self.logger.info(f"Copying reports from {reports_dir}")
                result = subprocess.run(
                    ['rsync', '-av', '--update', f'{reports_dir}/',
                     f'{self.mass_storage_mount}/reports/'],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode != 0:
                    self.logger.warning(f"Rsync warning: {result.stderr}")

            # Copy evidence metadata
            evidence_dir = os.path.join(self.output_dir, 'evidence')
            if os.path.exists(evidence_dir):
                self.logger.info(f"Copying evidence metadata from {evidence_dir}")
                result = subprocess.run(
                    ['rsync', '-av', '--update', '--exclude', '*.img', '--exclude', '*.dd',
                     f'{evidence_dir}/', f'{self.mass_storage_mount}/evidence/'],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

            # Sync filesystem
            subprocess.run(['sync'], timeout=30)

            # Unmount
            self.unmount_mass_storage()

            self.logger.info("Reports synced successfully")

            return {
                'success': True,
                'synced_dirs': ['reports', 'evidence'],
                'mount_point': self.mass_storage_mount
            }

        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            # Try to unmount anyway
            try:
                self.unmount_mass_storage()
            except:
                pass
            return {'success': False, 'error': str(e)}

    def get_serial_console_info(self) -> Dict[str, Any]:
        """Get serial console information"""
        try:
            info = {
                'available': self.is_serial_available(),
                'device': self.serial_device,
                'baud_rate': 115200
            }

            if info['available']:
                # Check if anything is connected
                result = subprocess.run(
                    ['stty', '-F', self.serial_device],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info['settings'] = result.stdout.strip()

            return info

        except Exception as e:
            self.logger.error(f"Failed to get serial info: {e}")
            return {'error': str(e)}

    def get_multifunction_status(self) -> Dict[str, Any]:
        """Get comprehensive multi-function gadget status"""
        try:
            status = {
                'mode': self.gadget_mode,
                'timestamp': datetime.now().isoformat(),
                'functions': {
                    'network': {
                        'enabled': self.is_gadget_enabled(),
                        'connected': self.is_connected_to_host(),
                        'interface': self.gadget_interface,
                        'device_ip': self.device_ip,
                        'host_ip': self.host_ip
                    },
                    'mass_storage': {
                        'available': self.is_mass_storage_available(),
                        'backing_file': self.mass_storage_file,
                        'backing_file_exists': os.path.exists(self.mass_storage_file),
                        'mount_point': self.mass_storage_mount
                    },
                    'serial': {
                        'available': self.is_serial_available(),
                        'device': self.serial_device
                    }
                }
            }

            # Get backing file size if it exists
            if status['functions']['mass_storage']['backing_file_exists']:
                try:
                    size_bytes = os.path.getsize(self.mass_storage_file)
                    status['functions']['mass_storage']['size_mb'] = size_bytes // (1024 * 1024)
                except:
                    pass

            # Check what's actually loaded
            result = subprocess.run(['lsmod'], capture_output=True, text=True)
            loaded_modules = []
            for line in result.stdout.split('\n'):
                if any(mod in line for mod in ['g_ether', 'g_multi', 'g_serial', 'g_mass_storage', 'usb_f_', 'dwc2']):
                    loaded_modules.append(line.split()[0])

            status['loaded_modules'] = loaded_modules

            # Determine actual mode based on loaded modules
            if 'g_multi' in loaded_modules:
                status['active_mode'] = 'multi-function'
            elif 'g_ether' in loaded_modules:
                status['active_mode'] = 'network-only'
            elif 'g_serial' in loaded_modules:
                status['active_mode'] = 'serial-only'
            elif 'g_mass_storage' in loaded_modules:
                status['active_mode'] = 'mass-storage-only'
            else:
                status['active_mode'] = 'none'

            return status

        except Exception as e:
            self.logger.error(f"Failed to get multi-function status: {e}")
            return {'error': str(e)}
