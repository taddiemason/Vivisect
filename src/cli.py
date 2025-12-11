"""Command-line interface for Vivisect"""

import argparse
import sys
from datetime import datetime
from core import Config, ForensicsLogger, ReportGenerator
from modules import (
    DiskImaging,
    FileAnalysis,
    NetworkForensics,
    MemoryAnalysis,
    ArtifactExtraction
)

class VivisectCLI:
    """Command-line interface for Vivisect Digital Forensics Suite"""

    def __init__(self):
        self.config = Config()
        self.config.ensure_directories()
        self.logger = ForensicsLogger(self.config.get('log_dir'))
        self.report_gen = ReportGenerator(self.config.get('output_dir'))

        # Initialize modules
        self.disk_imaging = DiskImaging(self.logger, self.config)
        self.file_analysis = FileAnalysis(self.logger, self.config)
        self.network_forensics = NetworkForensics(self.logger, self.config)
        self.memory_analysis = MemoryAnalysis(self.logger, self.config)
        self.artifact_extraction = ArtifactExtraction(self.logger, self.config)

    def create_parser(self):
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='Vivisect - Digital Forensics Suite',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Disk Imaging commands
        disk_parser = subparsers.add_parser('disk', help='Disk imaging operations')
        disk_sub = disk_parser.add_subparsers(dest='disk_command')

        disk_list = disk_sub.add_parser('list', help='List available devices')

        disk_image = disk_sub.add_parser('image', help='Create disk image')
        disk_image.add_argument('device', help='Source device (e.g., /dev/sda)')
        disk_image.add_argument('output', help='Output file name')
        disk_image.add_argument('--method', choices=['dd', 'dcfldd'], default='dd')
        disk_image.add_argument('--compress', action='store_true', help='Compress output')

        disk_verify = disk_sub.add_parser('verify', help='Verify disk image')
        disk_verify.add_argument('image', help='Image file to verify')
        disk_verify.add_argument('--device', help='Original device to compare')

        # File Analysis commands
        file_parser = subparsers.add_parser('file', help='File analysis operations')
        file_sub = file_parser.add_subparsers(dest='file_command')

        file_hash = file_sub.add_parser('hash', help='Calculate file hashes')
        file_hash.add_argument('filepath', help='File to hash')

        file_metadata = file_sub.add_parser('metadata', help='Extract file metadata')
        file_metadata.add_argument('filepath', help='File to analyze')

        file_scan = file_sub.add_parser('scan', help='Scan directory')
        file_scan.add_argument('directory', help='Directory to scan')
        file_scan.add_argument('--recursive', action='store_true', help='Recursive scan')

        file_carve = file_sub.add_parser('carve', help='Carve files from image')
        file_carve.add_argument('source', help='Source image or device')
        file_carve.add_argument('--output', help='Output directory')

        file_entropy = file_sub.add_parser('entropy', help='Calculate file entropy')
        file_entropy.add_argument('filepath', help='File to analyze')

        # Network Forensics commands
        net_parser = subparsers.add_parser('network', help='Network forensics operations')
        net_sub = net_parser.add_subparsers(dest='net_command')

        net_list = net_sub.add_parser('list', help='List network interfaces')

        net_capture = net_sub.add_parser('capture', help='Capture network traffic')
        net_capture.add_argument('interface', help='Network interface')
        net_capture.add_argument('output', help='Output PCAP file')
        net_capture.add_argument('--duration', type=int, default=60, help='Capture duration (seconds)')
        net_capture.add_argument('--filter', help='BPF filter expression')

        net_analyze = net_sub.add_parser('analyze', help='Analyze PCAP file')
        net_analyze.add_argument('pcap', help='PCAP file to analyze')

        net_extract = net_sub.add_parser('extract', help='Extract files from PCAP')
        net_extract.add_argument('pcap', help='PCAP file')
        net_extract.add_argument('--output', help='Output directory')

        # Memory Analysis commands
        mem_parser = subparsers.add_parser('memory', help='Memory analysis operations')
        mem_sub = mem_parser.add_subparsers(dest='mem_command')

        mem_dump = mem_sub.add_parser('dump', help='Create memory dump')
        mem_dump.add_argument('--output', help='Output file name')
        mem_dump.add_argument('--method', choices=['auto', 'lime', 'dd', 'avml'], default='auto')

        mem_analyze = mem_sub.add_parser('analyze', help='Analyze memory dump')
        mem_analyze.add_argument('dump', help='Memory dump file')
        mem_analyze.add_argument('--profile', help='Volatility profile')

        mem_live = mem_sub.add_parser('live', help='Analyze running system')

        # Artifact Extraction commands
        artifact_parser = subparsers.add_parser('artifact', help='Artifact extraction operations')
        artifact_sub = artifact_parser.add_subparsers(dest='artifact_command')

        artifact_browser = artifact_sub.add_parser('browser', help='Extract browser history')
        artifact_browser.add_argument('--user', help='User home directory')

        artifact_logs = artifact_sub.add_parser('logs', help='Extract system logs')
        artifact_logs.add_argument('--logdir', default='/var/log', help='Log directory')

        artifact_user = artifact_sub.add_parser('user', help='Extract user artifacts')
        artifact_user.add_argument('--user', help='User home directory')

        artifact_packages = artifact_sub.add_parser('packages', help='List installed packages')

        artifact_network_config = artifact_sub.add_parser('netconfig', help='Extract network configuration')

        artifact_persistence = artifact_sub.add_parser('persistence', help='Find persistence mechanisms')

        # Full collection command
        collect_parser = subparsers.add_parser('collect', help='Run full forensics collection')
        collect_parser.add_argument('case_id', help='Case identifier')
        collect_parser.add_argument('--modules', nargs='+',
                                   choices=['disk', 'file', 'network', 'memory', 'artifacts'],
                                   help='Specific modules to run')

        # Report commands
        report_parser = subparsers.add_parser('report', help='Generate forensics report')
        report_parser.add_argument('case_id', help='Case identifier')
        report_parser.add_argument('--format', choices=['json', 'html', 'txt'], default='json')

        return parser

    def run(self, args=None):
        """Run the CLI"""
        parser = self.create_parser()
        args = parser.parse_args(args)

        if not args.command:
            parser.print_help()
            return 1

        try:
            if args.command == 'disk':
                return self.handle_disk_commands(args)
            elif args.command == 'file':
                return self.handle_file_commands(args)
            elif args.command == 'network':
                return self.handle_network_commands(args)
            elif args.command == 'memory':
                return self.handle_memory_commands(args)
            elif args.command == 'artifact':
                return self.handle_artifact_commands(args)
            elif args.command == 'collect':
                return self.handle_collect_command(args)
            elif args.command == 'report':
                return self.handle_report_command(args)

        except Exception as e:
            print(f"Error: {e}")
            self.logger.main_logger.error(f"Command failed: {e}", exc_info=True)
            return 1

        return 0

    def handle_disk_commands(self, args):
        """Handle disk imaging commands"""
        if args.disk_command == 'list':
            devices = self.disk_imaging.list_devices()
            print("\nAvailable Devices:")
            print("-" * 60)
            for dev in devices:
                print(f"  {dev['name']:<10} {dev['size']:<10} {dev['type']}")
            print()

        elif args.disk_command == 'image':
            print(f"Creating disk image of {args.device}...")
            if args.method == 'dd':
                result = self.disk_imaging.create_image_dd(
                    args.device, args.output, compression=args.compress
                )
            else:
                result = self.disk_imaging.create_image_dcfldd(args.device, args.output)

            if result.get('success'):
                print(f"✓ Image created: {result['output']}")
                if result.get('hash'):
                    print(f"  Hash: {result['hash']}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.disk_command == 'verify':
            print(f"Verifying image: {args.image}...")
            result = self.disk_imaging.verify_image(args.image, args.device)
            if result.get('success'):
                print(f"✓ Verification complete")
                print(f"  Image hash: {result['hash']}")
                if 'verified' in result:
                    print(f"  Match: {'Yes' if result['verified'] else 'No'}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        return 0

    def handle_file_commands(self, args):
        """Handle file analysis commands"""
        if args.file_command == 'hash':
            hashes = self.file_analysis.calculate_hashes(args.filepath)
            print(f"\nHashes for {args.filepath}:")
            print("-" * 60)
            for algo, hash_val in hashes.items():
                print(f"  {algo.upper():<10} {hash_val}")
            print()

        elif args.file_command == 'metadata':
            metadata = self.file_analysis.get_file_metadata(args.filepath)
            print(f"\nMetadata for {args.filepath}:")
            print("-" * 60)
            for key, value in metadata.items():
                if key != 'hashes':
                    print(f"  {key:<15} {value}")
            print()

        elif args.file_command == 'scan':
            print(f"Scanning directory: {args.directory}...")
            files = self.file_analysis.scan_directory(args.directory, args.recursive)
            print(f"Found {len(files)} files")

        elif args.file_command == 'carve':
            print(f"Carving files from {args.source}...")
            result = self.file_analysis.carve_files(args.source, args.output)
            if result.get('success'):
                print(f"✓ Carved {len(result.get('carved_files', []))} files")
                print(f"  Output: {result['output_dir']}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.file_command == 'entropy':
            result = self.file_analysis.find_entropy(args.filepath)
            print(f"\nEntropy Analysis:")
            print("-" * 60)
            print(f"  Entropy: {result.get('entropy', 'N/A')}")
            print(f"  Assessment: {result.get('assessment', 'N/A')}")
            print()

        return 0

    def handle_network_commands(self, args):
        """Handle network forensics commands"""
        if args.net_command == 'list':
            interfaces = self.network_forensics.list_interfaces()
            print("\nNetwork Interfaces:")
            print("-" * 60)
            for iface in interfaces:
                print(f"  {iface.get('name', 'Unknown'):<15} {iface.get('state', 'Unknown')}")
            print()

        elif args.net_command == 'capture':
            print(f"Capturing traffic on {args.interface}...")
            result = self.network_forensics.capture_traffic(
                args.interface, args.output,
                duration=args.duration, filter_expression=args.filter
            )
            if result.get('success'):
                print(f"✓ Capture saved: {result['output_file']}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.net_command == 'analyze':
            print(f"Analyzing PCAP: {args.pcap}...")
            result = self.network_forensics.analyze_pcap(args.pcap)
            if 'error' not in result:
                print(f"✓ Analysis complete")
                if result.get('suspicious_activity'):
                    print(f"  Suspicious activities found: {len(result['suspicious_activity'])}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.net_command == 'extract':
            print(f"Extracting files from {args.pcap}...")
            result = self.network_forensics.extract_files_from_pcap(args.pcap, args.output)
            if result.get('success'):
                print(f"✓ Extracted {len(result.get('extracted_files', []))} files")
            else:
                print(f"✗ Failed: {result.get('error')}")

        return 0

    def handle_memory_commands(self, args):
        """Handle memory analysis commands"""
        if args.mem_command == 'dump':
            print(f"Creating memory dump...")
            result = self.memory_analysis.create_memory_dump(args.output, args.method)
            if result.get('success'):
                print(f"✓ Memory dump created: {result['output']}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.mem_command == 'analyze':
            print(f"Analyzing memory dump: {args.dump}...")
            result = self.memory_analysis.analyze_memory_dump(args.dump, args.profile)
            if 'error' not in result:
                print(f"✓ Analysis complete")
                findings = result.get('findings', {})
                if findings.get('suspicious'):
                    print(f"  Suspicious items found: {len(findings['suspicious'])}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.mem_command == 'live':
            print(f"Analyzing running system...")
            result = self.memory_analysis.analyze_running_system()
            if 'error' not in result:
                print(f"✓ Live analysis complete")
                print(f"  Processes: {len(result.get('processes', []))}")
                print(f"  Network connections: {len(result.get('network', []))}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        return 0

    def handle_artifact_commands(self, args):
        """Handle artifact extraction commands"""
        if args.artifact_command == 'browser':
            print(f"Extracting browser history...")
            result = self.artifact_extraction.extract_browser_history(args.user)
            if 'error' not in result:
                print(f"✓ Browser history extracted")
                print(f"  Chrome entries: {len(result.get('chrome', []))}")
                print(f"  Firefox entries: {len(result.get('firefox', []))}")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.artifact_command == 'logs':
            print(f"Extracting system logs...")
            result = self.artifact_extraction.extract_system_logs(args.logdir)
            if 'error' not in result:
                print(f"✓ System logs extracted")
                for log_type, entries in result.items():
                    if isinstance(entries, list):
                        print(f"  {log_type}: {len(entries)} entries")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.artifact_command == 'user':
            print(f"Extracting user artifacts...")
            result = self.artifact_extraction.extract_user_artifacts(args.user)
            if 'error' not in result:
                print(f"✓ User artifacts extracted")
                for artifact_type, data in result.items():
                    if isinstance(data, list):
                        print(f"  {artifact_type}: {len(data)} items")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.artifact_command == 'packages':
            print(f"Extracting installed packages...")
            result = self.artifact_extraction.extract_installed_packages()
            if 'error' not in result:
                print(f"✓ Package list extracted")
                for pkg_type, pkgs in result.items():
                    print(f"  {pkg_type}: {len(pkgs)} packages")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.artifact_command == 'netconfig':
            print(f"Extracting network configuration...")
            result = self.artifact_extraction.extract_network_configuration()
            if 'error' not in result:
                print(f"✓ Network configuration extracted")
            else:
                print(f"✗ Failed: {result.get('error')}")

        elif args.artifact_command == 'persistence':
            print(f"Finding persistence mechanisms...")
            result = self.artifact_extraction.extract_persistence_mechanisms()
            if 'error' not in result:
                print(f"✓ Persistence mechanisms found")
                for mech_type, items in result.items():
                    if isinstance(items, list):
                        print(f"  {mech_type}: {len(items)} items")
            else:
                print(f"✗ Failed: {result.get('error')}")

        return 0

    def handle_collect_command(self, args):
        """Handle full forensics collection"""
        print(f"\n{'='*60}")
        print(f"Starting Full Forensics Collection")
        print(f"Case ID: {args.case_id}")
        print(f"{'='*60}\n")

        report = self.report_gen.create_report(args.case_id)

        # Run enabled modules
        modules_to_run = args.modules if args.modules else ['file', 'network', 'memory', 'artifacts']

        for module in modules_to_run:
            print(f"\n[{module.upper()}] Running module...")

            if module == 'memory':
                result = self.memory_analysis.analyze_running_system()
                self.report_gen.add_finding(report, 'memory', {
                    'type': 'live_analysis',
                    'description': 'Live system memory analysis',
                    'data': result
                })

            elif module == 'artifacts':
                browser_data = self.artifact_extraction.extract_browser_history()
                logs_data = self.artifact_extraction.extract_system_logs()
                user_data = self.artifact_extraction.extract_user_artifacts()

                self.report_gen.add_finding(report, 'artifacts', {
                    'type': 'browser_history',
                    'description': 'Browser history extraction',
                    'data': browser_data
                })

                self.report_gen.add_finding(report, 'artifacts', {
                    'type': 'system_logs',
                    'description': 'System logs extraction',
                    'data': logs_data
                })

        # Save report
        report_path = self.report_gen.save_report(report, 'json')
        html_report_path = self.report_gen.save_report(report, 'html')

        print(f"\n{'='*60}")
        print(f"Collection Complete!")
        print(f"  JSON Report: {report_path}")
        print(f"  HTML Report: {html_report_path}")
        print(f"{'='*60}\n")

        return 0

    def handle_report_command(self, args):
        """Handle report generation"""
        print(f"Generating {args.format} report for case {args.case_id}...")
        # This would load existing data and generate a report
        report = self.report_gen.create_report(args.case_id)
        report_path = self.report_gen.save_report(report, args.format)
        print(f"✓ Report saved: {report_path}")
        return 0


def main():
    """Main entry point"""
    cli = VivisectCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())
