"""Network forensics and packet analysis module"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class NetworkForensics:
    """Handles network packet capture and analysis"""

    def __init__(self, logger, config):
        self.logger = logger.get_logger('network_forensics')
        self.config = config
        self.output_dir = config.get('output_dir')

    def list_interfaces(self) -> List[Dict[str, Any]]:
        """List available network interfaces"""
        self.logger.info("Listing network interfaces")

        try:
            result = subprocess.run(
                ['ip', '-j', 'link', 'show'],
                capture_output=True,
                text=True,
                check=True
            )

            interfaces = json.loads(result.stdout)
            interface_list = []

            for iface in interfaces:
                interface_list.append({
                    'name': iface.get('ifname', 'unknown'),
                    'state': iface.get('operstate', 'unknown'),
                    'mac': iface.get('address', 'unknown'),
                    'mtu': iface.get('mtu', 0)
                })

            return interface_list

        except Exception as e:
            self.logger.error(f"Failed to list interfaces: {e}")
            # Fallback method
            try:
                result = subprocess.run(
                    ['ifconfig', '-a'],
                    capture_output=True,
                    text=True
                )
                # Parse ifconfig output (basic)
                return [{'info': result.stdout}]
            except:
                return []

    def capture_traffic(self, interface: str, output_file: str,
                       duration: int = 60, packet_count: int = None,
                       filter_expression: str = None) -> Dict[str, Any]:
        """Capture network traffic to PCAP file"""
        self.logger.info(f"Starting packet capture on {interface}")

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.output_dir, f"{output_file}_{timestamp}.pcap")

            # Build tcpdump command
            tcpdump_cmd = ['tcpdump', '-i', interface, '-w', output_path]

            if packet_count:
                tcpdump_cmd.extend(['-c', str(packet_count)])

            if filter_expression:
                tcpdump_cmd.append(filter_expression)

            self.logger.info(f"Capture command: {' '.join(tcpdump_cmd)}")

            # Execute tcpdump
            # Note: For long captures, this should be run in background
            timeout_duration = duration + 10 if duration else None
            process = subprocess.run(
                tcpdump_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_duration
            )

            if process.returncode != 0:
                raise Exception(f"tcpdump command failed: {process.stderr}")

            self.logger.info(f"Packet capture completed: {output_path}")

            result = {
                'success': True,
                'interface': interface,
                'output_file': output_path,
                'duration': duration,
                'packet_count': packet_count,
                'filter': filter_expression,
                'command': ' '.join(tcpdump_cmd),
                'timestamp': timestamp
            }

            return result

        except Exception as e:
            self.logger.error(f"Packet capture failed: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_pcap(self, pcap_file: str) -> Dict[str, Any]:
        """Analyze PCAP file and extract statistics"""
        self.logger.info(f"Analyzing PCAP file: {pcap_file}")

        if not os.path.exists(pcap_file):
            return {'error': 'PCAP file not found'}

        try:
            analysis = {
                'file': pcap_file,
                'timestamp': datetime.now().isoformat(),
                'statistics': {},
                'protocols': {},
                'conversations': [],
                'suspicious_activity': []
            }

            # Use tshark for detailed analysis
            # Get basic statistics
            stats_cmd = ['capinfos', '-M', pcap_file]
            result = subprocess.run(stats_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                analysis['statistics']['basic'] = result.stdout

            # Get protocol hierarchy
            proto_cmd = [
                'tshark', '-r', pcap_file,
                '-q', '-z', 'io,phs'
            ]
            result = subprocess.run(proto_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                analysis['protocols']['hierarchy'] = result.stdout

            # Get conversations
            conv_cmd = [
                'tshark', '-r', pcap_file,
                '-q', '-z', 'conv,ip'
            ]
            result = subprocess.run(conv_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                analysis['conversations'] = result.stdout

            # Extract HTTP requests
            http_cmd = [
                'tshark', '-r', pcap_file,
                '-Y', 'http.request',
                '-T', 'fields',
                '-e', 'http.host',
                '-e', 'http.request.uri',
                '-e', 'ip.src'
            ]
            result = subprocess.run(http_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout:
                analysis['http_requests'] = result.stdout.strip().split('\n')

            # Look for suspicious patterns
            analysis['suspicious_activity'] = self._detect_suspicious_traffic(pcap_file)

            return analysis

        except Exception as e:
            self.logger.error(f"PCAP analysis failed: {e}")
            return {'error': str(e)}

    def _detect_suspicious_traffic(self, pcap_file: str) -> List[Dict[str, Any]]:
        """Detect potentially suspicious network activity"""
        suspicious = []

        try:
            # Check for port scans
            scan_cmd = [
                'tshark', '-r', pcap_file,
                '-Y', 'tcp.flags.syn==1 and tcp.flags.ack==0',
                '-T', 'fields',
                '-e', 'ip.src',
                '-e', 'tcp.dstport'
            ]
            result = subprocess.run(scan_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 50:  # Threshold for scan detection
                    suspicious.append({
                        'type': 'potential_port_scan',
                        'description': f'Detected {len(lines)} SYN packets',
                        'severity': 'medium'
                    })

            # Check for DNS tunneling (unusually long DNS queries)
            dns_cmd = [
                'tshark', '-r', pcap_file,
                '-Y', 'dns.qry.name',
                '-T', 'fields',
                '-e', 'dns.qry.name'
            ]
            result = subprocess.run(dns_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout:
                for query in result.stdout.strip().split('\n'):
                    if len(query) > 100:
                        suspicious.append({
                            'type': 'suspicious_dns_query',
                            'description': f'Unusually long DNS query: {query[:50]}...',
                            'severity': 'high'
                        })
                        break  # Only report first occurrence

            # Check for unencrypted credentials
            cred_cmd = [
                'tshark', '-r', pcap_file,
                '-Y', 'http.request.method == "POST"',
                '-T', 'fields',
                '-e', 'http.host',
                '-e', 'http.request.uri'
            ]
            result = subprocess.run(cred_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if 'login' in line.lower() or 'password' in line.lower():
                        suspicious.append({
                            'type': 'unencrypted_credentials',
                            'description': 'Potential credentials sent over HTTP',
                            'severity': 'high'
                        })
                        break

        except Exception as e:
            self.logger.error(f"Suspicious traffic detection failed: {e}")

        return suspicious

    def extract_files_from_pcap(self, pcap_file: str, output_dir: str = None) -> Dict[str, Any]:
        """Extract files transferred over network from PCAP"""
        self.logger.info(f"Extracting files from PCAP: {pcap_file}")

        if output_dir is None:
            output_dir = os.path.join(self.output_dir, 'extracted_files')

        os.makedirs(output_dir, exist_ok=True)

        try:
            # Use networkminer or tshark to extract files
            export_cmd = [
                'tshark', '-r', pcap_file,
                '--export-objects', f'http,{output_dir}'
            ]

            self.logger.info(f"Export command: {' '.join(export_cmd)}")

            # Execute tshark export
            process = subprocess.run(
                export_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if process.returncode != 0:
                self.logger.warning(f"tshark export warning: {process.stderr}")

            self.logger.info(f"File extraction completed")

            result = {
                'success': True,
                'pcap_file': pcap_file,
                'output_dir': output_dir,
                'extracted_files': [],
                'command': ' '.join(export_cmd)
            }

            # List extracted files
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    filepath = os.path.join(output_dir, filename)
                    if os.path.isfile(filepath):
                        result['extracted_files'].append({
                            'name': filename,
                            'path': filepath,
                            'size': os.path.getsize(filepath)
                        })

            return result

        except Exception as e:
            self.logger.error(f"File extraction failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_connection_timeline(self, pcap_file: str) -> List[Dict[str, Any]]:
        """Create a timeline of network connections"""
        self.logger.info(f"Creating connection timeline from {pcap_file}")

        try:
            timeline_cmd = [
                'tshark', '-r', pcap_file,
                '-T', 'fields',
                '-e', 'frame.time',
                '-e', 'ip.src',
                '-e', 'ip.dst',
                '-e', 'tcp.srcport',
                '-e', 'tcp.dstport',
                '-e', 'frame.protocols',
                '-E', 'separator=|'
            ]

            result = subprocess.run(
                timeline_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            timeline = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[:1000]:  # Limit to first 1000
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 6:
                            timeline.append({
                                'timestamp': parts[0],
                                'src_ip': parts[1],
                                'dst_ip': parts[2],
                                'src_port': parts[3],
                                'dst_port': parts[4],
                                'protocols': parts[5]
                            })

            return timeline

        except Exception as e:
            self.logger.error(f"Timeline creation failed: {e}")
            return []

    def analyze_dns_queries(self, pcap_file: str) -> Dict[str, Any]:
        """Analyze DNS queries for suspicious activity"""
        self.logger.info(f"Analyzing DNS queries from {pcap_file}")

        try:
            dns_cmd = [
                'tshark', '-r', pcap_file,
                '-Y', 'dns.flags.response == 0',
                '-T', 'fields',
                '-e', 'frame.time',
                '-e', 'ip.src',
                '-e', 'dns.qry.name',
                '-e', 'dns.qry.type',
                '-E', 'separator=|'
            ]

            result = subprocess.run(
                dns_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            dns_analysis = {
                'total_queries': 0,
                'unique_domains': set(),
                'query_types': {},
                'suspicious': [],
                'queries': []
            }

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            domain = parts[2]
                            query_type = parts[3]

                            dns_analysis['total_queries'] += 1
                            dns_analysis['unique_domains'].add(domain)
                            dns_analysis['query_types'][query_type] = \
                                dns_analysis['query_types'].get(query_type, 0) + 1

                            dns_analysis['queries'].append({
                                'timestamp': parts[0],
                                'source': parts[1],
                                'domain': domain,
                                'type': query_type
                            })

            dns_analysis['unique_domains'] = list(dns_analysis['unique_domains'])

            return dns_analysis

        except Exception as e:
            self.logger.error(f"DNS analysis failed: {e}")
            return {'error': str(e)}

    def detect_c2_traffic(self, pcap_file: str) -> Dict[str, Any]:
        """Detect potential Command & Control traffic patterns"""
        self.logger.info(f"Detecting C2 traffic patterns in {pcap_file}")

        indicators = {
            'beaconing': [],
            'suspicious_domains': [],
            'unusual_protocols': []
        }

        try:
            # Look for beaconing (regular intervals)
            # This would require more sophisticated analysis
            # For now, we log the attempt

            # Check for connections to suspicious ports
            suspicious_ports = [4444, 5555, 6666, 7777, 8888, 31337]

            port_cmd = [
                'tshark', '-r', pcap_file,
                '-Y', f'tcp.dstport in {{{",".join(map(str, suspicious_ports))}}}',
                '-T', 'fields',
                '-e', 'ip.dst',
                '-e', 'tcp.dstport'
            ]

            result = subprocess.run(port_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        indicators['unusual_protocols'].append({
                            'description': f'Connection to suspicious port: {line}',
                            'severity': 'high'
                        })

            return indicators

        except Exception as e:
            self.logger.error(f"C2 detection failed: {e}")
            return {'error': str(e)}
