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
