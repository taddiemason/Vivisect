"""Report generation for forensics analysis"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class ReportGenerator:
    """Generates forensics reports in various formats"""

    def __init__(self, output_dir: str = '/var/lib/vivisect/output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_report(self, case_id: str, report_type: str = 'json') -> Dict[str, Any]:
        """Create a new forensics report"""
        report = {
            'case_id': case_id,
            'timestamp': datetime.now().isoformat(),
            'hostname': os.uname().nodename,
            'vivisect_version': '1.0.0',
            'modules': {},
            'findings': [],
            'artifacts': [],
            'timeline': []
        }
        return report

    def add_finding(self, report: Dict[str, Any], module: str, finding: Dict[str, Any]) -> None:
        """Add a finding to the report"""
        finding['module'] = module
        finding['timestamp'] = datetime.now().isoformat()
        report['findings'].append(finding)

    def add_artifact(self, report: Dict[str, Any], artifact: Dict[str, Any]) -> None:
        """Add an artifact to the report"""
        artifact['timestamp'] = datetime.now().isoformat()
        report['artifacts'].append(artifact)

    def add_timeline_event(self, report: Dict[str, Any], event: Dict[str, Any]) -> None:
        """Add an event to the timeline"""
        if 'timestamp' not in event:
            event['timestamp'] = datetime.now().isoformat()
        report['timeline'].append(event)

    def save_report(self, report: Dict[str, Any], format_type: str = 'json') -> str:
        """Save report to file"""
        case_id = report.get('case_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if format_type == 'json':
            filename = f"{case_id}_{timestamp}_report.json"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=4)

        elif format_type == 'html':
            filename = f"{case_id}_{timestamp}_report.html"
            filepath = os.path.join(self.output_dir, filename)
            html_content = self._generate_html_report(report)
            with open(filepath, 'w') as f:
                f.write(html_content)

        elif format_type == 'txt':
            filename = f"{case_id}_{timestamp}_report.txt"
            filepath = os.path.join(self.output_dir, filename)
            text_content = self._generate_text_report(report)
            with open(filepath, 'w') as f:
                f.write(text_content)

        return filepath

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML formatted report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Vivisect Forensics Report - {report['case_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        .metadata {{ background-color: #ecf0f1; padding: 15px; margin: 20px 0; }}
        .finding {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .artifact {{ background-color: #d1ecf1; padding: 10px; margin: 10px 0; border-left: 4px solid #17a2b8; }}
    </style>
</head>
<body>
    <h1>Vivisect Digital Forensics Report</h1>
    <div class="metadata">
        <p><strong>Case ID:</strong> {report['case_id']}</p>
        <p><strong>Timestamp:</strong> {report['timestamp']}</p>
        <p><strong>Hostname:</strong> {report['hostname']}</p>
        <p><strong>Version:</strong> {report['vivisect_version']}</p>
    </div>

    <h2>Findings ({len(report['findings'])})</h2>
"""
        for finding in report['findings']:
            html += f"""
    <div class="finding">
        <p><strong>Module:</strong> {finding.get('module', 'Unknown')}</p>
        <p><strong>Type:</strong> {finding.get('type', 'General')}</p>
        <p><strong>Description:</strong> {finding.get('description', 'N/A')}</p>
        <p><strong>Severity:</strong> {finding.get('severity', 'Info')}</p>
    </div>
"""

        html += f"""
    <h2>Artifacts ({len(report['artifacts'])})</h2>
"""
        for artifact in report['artifacts']:
            html += f"""
    <div class="artifact">
        <p><strong>Type:</strong> {artifact.get('type', 'Unknown')}</p>
        <p><strong>Path:</strong> {artifact.get('path', 'N/A')}</p>
        <p><strong>Hash:</strong> {artifact.get('hash', 'N/A')}</p>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

    def _generate_text_report(self, report: Dict[str, Any]) -> str:
        """Generate plain text formatted report"""
        text = f"""
{'='*80}
VIVISECT DIGITAL FORENSICS REPORT
{'='*80}

Case ID: {report['case_id']}
Timestamp: {report['timestamp']}
Hostname: {report['hostname']}
Version: {report['vivisect_version']}

{'='*80}
FINDINGS ({len(report['findings'])})
{'='*80}

"""
        for i, finding in enumerate(report['findings'], 1):
            text += f"""
Finding #{i}:
  Module: {finding.get('module', 'Unknown')}
  Type: {finding.get('type', 'General')}
  Description: {finding.get('description', 'N/A')}
  Severity: {finding.get('severity', 'Info')}

"""

        text += f"""
{'='*80}
ARTIFACTS ({len(report['artifacts'])})
{'='*80}

"""
        for i, artifact in enumerate(report['artifacts'], 1):
            text += f"""
Artifact #{i}:
  Type: {artifact.get('type', 'Unknown')}
  Path: {artifact.get('path', 'N/A')}
  Hash: {artifact.get('hash', 'N/A')}

"""

        return text
