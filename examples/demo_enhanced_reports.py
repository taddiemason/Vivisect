#!/usr/bin/env python3
"""
Demo script for Vivisect Enhanced Reporting with Visualization

This script demonstrates the new enhanced reporting capabilities
including interactive charts, dashboards, and visualizations.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.report import ReportGenerator


def generate_sample_report():
    """Generate a sample forensics report with test data"""

    # Initialize report generator
    reporter = ReportGenerator(output_dir='./demo_output')

    # Create a new report
    case_id = f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    report = reporter.create_report(case_id)

    print(f"🔍 Generating Enhanced Forensics Report: {case_id}")
    print("=" * 60)

    # Add sample findings from different modules
    modules = ['disk_imaging', 'network_forensics', 'memory_analysis',
               'file_analysis', 'artifact_extraction']
    severities = ['Critical', 'High', 'Medium', 'Low', 'Info']

    print("\n📋 Adding Findings...")
    findings_data = [
        {
            'module': 'network_forensics',
            'type': 'Suspicious Connection',
            'description': 'Outbound connection to known C2 server 192.0.2.100:443',
            'severity': 'Critical'
        },
        {
            'module': 'memory_analysis',
            'type': 'Malicious Process',
            'description': 'Process "svchost.exe" found running from unusual location',
            'severity': 'High'
        },
        {
            'module': 'artifact_extraction',
            'type': 'Persistence Mechanism',
            'description': 'Suspicious registry key in HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
            'severity': 'High'
        },
        {
            'module': 'file_analysis',
            'type': 'Suspicious File',
            'description': 'Executable with high entropy detected: /tmp/malware.bin (entropy: 7.9)',
            'severity': 'Critical'
        },
        {
            'module': 'network_forensics',
            'type': 'DNS Query',
            'description': 'DNS query to suspicious domain: malicious-domain.com',
            'severity': 'Medium'
        },
        {
            'module': 'artifact_extraction',
            'type': 'Browser Activity',
            'description': 'User visited phishing website: http://phishing-site.com',
            'severity': 'Medium'
        },
        {
            'module': 'disk_imaging',
            'type': 'Disk Analysis',
            'description': 'Successfully imaged /dev/sdb (500GB) with MD5 verification',
            'severity': 'Info'
        },
        {
            'module': 'memory_analysis',
            'type': 'Network Connection',
            'description': 'Active connection to external IP: 203.0.113.50:8080',
            'severity': 'Low'
        },
        {
            'module': 'file_analysis',
            'type': 'Hash Match',
            'description': 'File hash matched against VirusTotal database',
            'severity': 'Info'
        },
        {
            'module': 'artifact_extraction',
            'type': 'Log Analysis',
            'description': 'Found 15 failed SSH login attempts from IP 198.51.100.42',
            'severity': 'Medium'
        }
    ]

    for finding_data in findings_data:
        reporter.add_finding(report, finding_data['module'], {
            'type': finding_data['type'],
            'description': finding_data['description'],
            'severity': finding_data['severity']
        })
        print(f"  ✓ [{finding_data['severity']:8s}] {finding_data['module']}: {finding_data['type']}")

    # Add sample artifacts
    print("\n📦 Adding Artifacts...")
    artifacts_data = [
        {
            'type': 'Disk Image',
            'path': '/var/lib/vivisect/output/evidence_sdb.img',
            'hash': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
            'size': '500GB'
        },
        {
            'type': 'PCAP File',
            'path': '/var/lib/vivisect/output/network_capture.pcap',
            'hash': '7f8e9d0c1b2a3456789abcdef0123456',
            'size': '2.3GB'
        },
        {
            'type': 'Memory Dump',
            'path': '/var/lib/vivisect/output/memory.raw',
            'hash': '9876543210fedcba0987654321fedcba',
            'size': '16GB'
        },
        {
            'type': 'Browser History',
            'path': '/var/lib/vivisect/output/firefox_history.json',
            'hash': 'abcdef0123456789abcdef0123456789',
            'size': '1.2MB'
        },
        {
            'type': 'System Logs',
            'path': '/var/lib/vivisect/output/syslog_export.tar.gz',
            'hash': '456789abcdef0123456789abcdef0123',
            'size': '45MB'
        },
        {
            'type': 'Registry Hive',
            'path': '/var/lib/vivisect/output/SYSTEM.reg',
            'hash': '123456789abcdef0123456789abcdef0',
            'size': '125MB'
        },
        {
            'type': 'Carved Files',
            'path': '/var/lib/vivisect/output/carved/',
            'hash': 'fedcba9876543210fedcba9876543210',
            'size': '320MB'
        },
        {
            'type': 'Process List',
            'path': '/var/lib/vivisect/output/processes.json',
            'hash': '0123456789abcdef0123456789abcdef',
            'size': '85KB'
        }
    ]

    for artifact_data in artifacts_data:
        reporter.add_artifact(report, artifact_data)
        print(f"  ✓ {artifact_data['type']}: {artifact_data['path']}")

    # Add timeline events
    print("\n⏱️  Adding Timeline Events...")
    base_time = datetime.now() - timedelta(hours=12)

    timeline_events = [
        {'type': 'System Boot', 'description': 'System started', 'offset': 0},
        {'type': 'User Login', 'description': 'User "admin" logged in', 'offset': 30},
        {'type': 'Process Start', 'description': 'Suspicious process started: malware.exe', 'offset': 45},
        {'type': 'Network Activity', 'description': 'First connection to C2 server', 'offset': 50},
        {'type': 'File Created', 'description': 'Malicious file created in /tmp', 'offset': 55},
        {'type': 'Registry Modified', 'description': 'Persistence mechanism installed', 'offset': 60},
        {'type': 'Network Activity', 'description': 'Data exfiltration detected (10MB)', 'offset': 120},
        {'type': 'Process Start', 'description': 'Second-stage payload executed', 'offset': 180},
        {'type': 'File Modified', 'description': 'System file modified: /etc/hosts', 'offset': 240},
        {'type': 'Network Activity', 'description': 'DNS queries to malicious domains', 'offset': 300},
        {'type': 'User Activity', 'description': 'Browser visited phishing site', 'offset': 360},
        {'type': 'Process Terminated', 'description': 'Antivirus process killed', 'offset': 420},
    ]

    for event_data in timeline_events:
        event_time = base_time + timedelta(minutes=event_data['offset'])
        reporter.add_timeline_event(report, {
            'type': event_data['type'],
            'description': event_data['description'],
            'timestamp': event_time.isoformat()
        })
        print(f"  ✓ {event_time.strftime('%H:%M:%S')} - {event_data['type']}: {event_data['description']}")

    return report, reporter


def main():
    """Main demo function"""
    print("\n" + "=" * 60)
    print("🔍 VIVISECT ENHANCED REPORTING DEMO")
    print("=" * 60)

    # Create output directory
    os.makedirs('./demo_output', exist_ok=True)

    # Generate sample report
    report, reporter = generate_sample_report()

    # Save in different formats
    print("\n💾 Saving Reports...")
    print("=" * 60)

    # JSON Report
    json_path = reporter.save_report(report, format_type='json')
    print(f"✓ JSON Report: {json_path}")

    # Enhanced HTML Report with Visualizations
    html_path = reporter.save_report(report, format_type='html')
    print(f"✓ Enhanced HTML Report: {html_path}")
    print(f"\n  📊 Interactive Visualizations Included:")
    print(f"     • Executive Summary Dashboard")
    print(f"     • Findings by Module (Bar Chart)")
    print(f"     • Severity Distribution (Doughnut Chart)")
    print(f"     • Activity Timeline (Line Chart)")
    print(f"     • Artifact Types Distribution (Pie Chart)")
    print(f"     • Detailed Findings with Color-Coded Severity")
    print(f"     • Interactive Hover Effects and Tooltips")

    # Text Report
    text_path = reporter.save_report(report, format_type='txt')
    print(f"✓ Text Report: {text_path}")

    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE!")
    print("=" * 60)
    print(f"\n📂 All reports saved to: ./demo_output/")
    print(f"\n🌐 To view the enhanced HTML report:")
    print(f"   Open the following file in your browser:")
    print(f"   {os.path.abspath(html_path)}")
    print(f"\n💡 Features:")
    print(f"   • Modern, responsive design with gradient backgrounds")
    print(f"   • Interactive Chart.js visualizations")
    print(f"   • Color-coded severity indicators")
    print(f"   • Executive summary dashboard")
    print(f"   • Detailed findings, artifacts, and timeline")
    print(f"   • Print-friendly formatting")
    print(f"   • Mobile-responsive layout")
    print("")


if __name__ == '__main__':
    main()
