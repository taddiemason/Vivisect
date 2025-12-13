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
        """Generate HTML formatted report with interactive visualizations"""

        # Prepare data for visualizations
        viz_data = self._prepare_visualization_data(report)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Vivisect Forensics Report - {report['case_id']}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary-color: #3498db;
            --success-color: #27ae60;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --info-color: #17a2b8;
            --dark-bg: #1e293b;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #f8fafc;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        .header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, #2980b9 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(52, 152, 219, 0.3);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .metadata-item {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }}

        .metadata-item label {{
            font-size: 0.85em;
            opacity: 0.9;
            display: block;
            margin-bottom: 5px;
        }}

        .metadata-item strong {{
            font-size: 1.1em;
            display: block;
        }}

        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: var(--card-bg);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid var(--primary-color);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        }}

        .metric-card.critical {{
            border-left-color: var(--danger-color);
        }}

        .metric-card.warning {{
            border-left-color: var(--warning-color);
        }}

        .metric-card.success {{
            border-left-color: var(--success-color);
        }}

        .metric-value {{
            font-size: 3em;
            font-weight: 700;
            color: var(--primary-color);
            line-height: 1;
        }}

        .metric-card.critical .metric-value {{
            color: var(--danger-color);
        }}

        .metric-card.warning .metric-value {{
            color: var(--warning-color);
        }}

        .metric-card.success .metric-value {{
            color: var(--success-color);
        }}

        .metric-label {{
            font-size: 0.9em;
            color: var(--text-secondary);
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .chart-container {{
            background: var(--card-bg);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .chart-container h2 {{
            color: var(--text-primary);
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--primary-color);
            font-size: 1.5em;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin-top: 20px;
        }}

        .findings-grid {{
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }}

        .finding {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid var(--warning-color);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }}

        .finding:hover {{
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
            transform: translateX(5px);
        }}

        .finding.critical {{
            border-left-color: var(--danger-color);
            background: #fee;
        }}

        .finding.high {{
            border-left-color: #ff6b6b;
        }}

        .finding.medium {{
            border-left-color: var(--warning-color);
        }}

        .finding.low {{
            border-left-color: var(--info-color);
        }}

        .finding.info {{
            border-left-color: var(--success-color);
        }}

        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .finding-module {{
            font-weight: 600;
            color: var(--primary-color);
        }}

        .severity-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .severity-badge.critical {{
            background: var(--danger-color);
            color: white;
        }}

        .severity-badge.high {{
            background: #ff6b6b;
            color: white;
        }}

        .severity-badge.medium {{
            background: var(--warning-color);
            color: white;
        }}

        .severity-badge.low {{
            background: var(--info-color);
            color: white;
        }}

        .severity-badge.info {{
            background: var(--success-color);
            color: white;
        }}

        .artifact {{
            background: var(--card-bg);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid var(--info-color);
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .artifact-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .timeline-item {{
            background: var(--card-bg);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid var(--primary-color);
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .timeline-time {{
            font-size: 0.85em;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .timeline-description {{
            margin-top: 5px;
            color: var(--text-primary);
        }}

        .section {{
            margin-top: 40px;
        }}

        .section-title {{
            font-size: 2em;
            color: var(--text-primary);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid var(--primary-color);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            background: var(--primary-color);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}

        tr:hover {{
            background: #f8fafc;
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
            font-style: italic;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
            .metric-card, .chart-container {{
                break-inside: avoid;
            }}
        }}

        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            .artifact-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Vivisect Digital Forensics Report</h1>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <label>Case ID</label>
                    <strong>{report['case_id']}</strong>
                </div>
                <div class="metadata-item">
                    <label>Timestamp</label>
                    <strong>{report['timestamp']}</strong>
                </div>
                <div class="metadata-item">
                    <label>Hostname</label>
                    <strong>{report['hostname']}</strong>
                </div>
                <div class="metadata-item">
                    <label>Vivisect Version</label>
                    <strong>{report['vivisect_version']}</strong>
                </div>
            </div>
        </div>

        <!-- Executive Summary Dashboard -->
        <div class="section">
            <h2 class="section-title">📊 Executive Summary</h2>
            <div class="dashboard-grid">
                <div class="metric-card {viz_data['severity_class']}">
                    <div class="metric-value">{len(report['findings'])}</div>
                    <div class="metric-label">Total Findings</div>
                </div>
                <div class="metric-card success">
                    <div class="metric-value">{len(report['artifacts'])}</div>
                    <div class="metric-label">Artifacts Collected</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(report['timeline'])}</div>
                    <div class="metric-label">Timeline Events</div>
                </div>
                <div class="metric-card {viz_data['critical_class']}">
                    <div class="metric-value">{viz_data['critical_findings']}</div>
                    <div class="metric-label">Critical Findings</div>
                </div>
            </div>
        </div>

        <!-- Findings by Module Chart -->
        {self._generate_module_chart(viz_data)}

        <!-- Severity Distribution Chart -->
        {self._generate_severity_chart(viz_data)}

        <!-- Timeline Visualization -->
        {self._generate_timeline_chart(viz_data)}

        <!-- File Type Distribution -->
        {self._generate_file_type_chart(viz_data)}

        <!-- Detailed Findings -->
        <div class="section">
            <h2 class="section-title">🔎 Detailed Findings ({len(report['findings'])})</h2>
            {self._generate_findings_html(report['findings'])}
        </div>

        <!-- Artifacts -->
        <div class="section">
            <h2 class="section-title">📦 Collected Artifacts ({len(report['artifacts'])})</h2>
            {self._generate_artifacts_html(report['artifacts'])}
        </div>

        <!-- Timeline Events -->
        <div class="section">
            <h2 class="section-title">⏱️ Timeline ({len(report['timeline'])})</h2>
            {self._generate_timeline_html(report['timeline'])}
        </div>
    </div>

    <script>
        {self._generate_chart_scripts(viz_data)}
    </script>
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

    def _prepare_visualization_data(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for visualizations"""
        findings = report.get('findings', [])
        artifacts = report.get('artifacts', [])
        timeline = report.get('timeline', [])

        # Count findings by module
        module_counts = {}
        for finding in findings:
            module = finding.get('module', 'Unknown')
            module_counts[module] = module_counts.get(module, 0) + 1

        # Count findings by severity
        severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0}
        for finding in findings:
            severity = finding.get('severity', 'Info')
            if severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts['Info'] += 1

        # Count artifacts by type
        artifact_types = {}
        for artifact in artifacts:
            atype = artifact.get('type', 'Unknown')
            artifact_types[atype] = artifact_types.get(atype, 0) + 1

        # Determine overall severity class
        critical_findings = severity_counts.get('Critical', 0)
        high_findings = severity_counts.get('High', 0)

        if critical_findings > 0:
            severity_class = 'critical'
            critical_class = 'critical'
        elif high_findings > 0:
            severity_class = 'warning'
            critical_class = 'warning'
        else:
            severity_class = 'success'
            critical_class = 'success'

        return {
            'module_counts': module_counts,
            'severity_counts': severity_counts,
            'artifact_types': artifact_types,
            'critical_findings': critical_findings,
            'severity_class': severity_class,
            'critical_class': critical_class,
            'timeline_data': self._prepare_timeline_data(timeline)
        }

    def _prepare_timeline_data(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare timeline data for visualization"""
        sorted_timeline = sorted(timeline, key=lambda x: x.get('timestamp', ''))
        return sorted_timeline

    def _generate_module_chart(self, viz_data: Dict[str, Any]) -> str:
        """Generate findings by module chart HTML"""
        module_counts = viz_data['module_counts']

        if not module_counts:
            return '<div class="chart-container"><p class="no-data">No module data available</p></div>'

        return f'''
        <div class="chart-container">
            <h2>📋 Findings by Module</h2>
            <div class="chart-wrapper">
                <canvas id="moduleChart"></canvas>
            </div>
        </div>
        '''

    def _generate_severity_chart(self, viz_data: Dict[str, Any]) -> str:
        """Generate severity distribution chart HTML"""
        severity_counts = viz_data['severity_counts']

        total = sum(severity_counts.values())
        if total == 0:
            return '<div class="chart-container"><p class="no-data">No severity data available</p></div>'

        return f'''
        <div class="chart-container">
            <h2>⚠️ Findings by Severity</h2>
            <div class="chart-wrapper">
                <canvas id="severityChart"></canvas>
            </div>
        </div>
        '''

    def _generate_timeline_chart(self, viz_data: Dict[str, Any]) -> str:
        """Generate timeline visualization HTML"""
        timeline_data = viz_data['timeline_data']

        if not timeline_data:
            return '<div class="chart-container"><p class="no-data">No timeline data available</p></div>'

        return f'''
        <div class="chart-container">
            <h2>📅 Activity Timeline</h2>
            <div class="chart-wrapper">
                <canvas id="timelineChart"></canvas>
            </div>
        </div>
        '''

    def _generate_file_type_chart(self, viz_data: Dict[str, Any]) -> str:
        """Generate file type distribution chart HTML"""
        artifact_types = viz_data['artifact_types']

        if not artifact_types:
            return '<div class="chart-container"><p class="no-data">No artifact type data available</p></div>'

        return f'''
        <div class="chart-container">
            <h2>📁 Artifact Types Distribution</h2>
            <div class="chart-wrapper">
                <canvas id="fileTypeChart"></canvas>
            </div>
        </div>
        '''

    def _generate_findings_html(self, findings: List[Dict[str, Any]]) -> str:
        """Generate HTML for detailed findings"""
        if not findings:
            return '<p class="no-data">No findings to display</p>'

        html = '<div class="findings-grid">'
        for finding in findings:
            severity = finding.get('severity', 'Info').lower()
            module = finding.get('module', 'Unknown')
            ftype = finding.get('type', 'General')
            description = finding.get('description', 'N/A')
            timestamp = finding.get('timestamp', 'N/A')

            html += f'''
            <div class="finding {severity}">
                <div class="finding-header">
                    <span class="finding-module">{module}</span>
                    <span class="severity-badge {severity}">{severity.upper()}</span>
                </div>
                <p><strong>Type:</strong> {ftype}</p>
                <p><strong>Description:</strong> {description}</p>
                <p style="font-size: 0.85em; color: var(--text-secondary); margin-top: 10px;">
                    <strong>Timestamp:</strong> {timestamp}
                </p>
            </div>
            '''
        html += '</div>'
        return html

    def _generate_artifacts_html(self, artifacts: List[Dict[str, Any]]) -> str:
        """Generate HTML for artifacts"""
        if not artifacts:
            return '<p class="no-data">No artifacts to display</p>'

        html = '<div class="artifact-grid">'
        for artifact in artifacts:
            atype = artifact.get('type', 'Unknown')
            path = artifact.get('path', 'N/A')
            ahash = artifact.get('hash', 'N/A')
            timestamp = artifact.get('timestamp', 'N/A')
            size = artifact.get('size', 'N/A')

            html += f'''
            <div class="artifact">
                <p><strong>Type:</strong> {atype}</p>
                <p><strong>Path:</strong> <code>{path}</code></p>
                <p><strong>Hash:</strong> <code style="font-size: 0.85em;">{ahash}</code></p>
            '''
            if size != 'N/A':
                html += f'<p><strong>Size:</strong> {size}</p>'
            html += f'''
                <p style="font-size: 0.85em; color: var(--text-secondary); margin-top: 10px;">
                    <strong>Timestamp:</strong> {timestamp}
                </p>
            </div>
            '''
        html += '</div>'
        return html

    def _generate_timeline_html(self, timeline: List[Dict[str, Any]]) -> str:
        """Generate HTML for timeline events"""
        if not timeline:
            return '<p class="no-data">No timeline events to display</p>'

        # Sort timeline by timestamp
        sorted_timeline = sorted(timeline, key=lambda x: x.get('timestamp', ''), reverse=True)

        html = '<div class="timeline-grid">'
        for event in sorted_timeline:
            timestamp = event.get('timestamp', 'N/A')
            description = event.get('description', 'N/A')
            event_type = event.get('type', 'Event')

            html += f'''
            <div class="timeline-item">
                <div class="timeline-time">{timestamp}</div>
                <div class="timeline-description">
                    <strong>{event_type}:</strong> {description}
                </div>
            </div>
            '''
        html += '</div>'
        return html

    def _generate_chart_scripts(self, viz_data: Dict[str, Any]) -> str:
        """Generate JavaScript for Chart.js visualizations"""
        module_counts = viz_data['module_counts']
        severity_counts = viz_data['severity_counts']
        artifact_types = viz_data['artifact_types']
        timeline_data = viz_data['timeline_data']

        script = "// Chart.js Configuration\n"
        script += "Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif';\n"
        script += "Chart.defaults.color = '#64748b';\n\n"

        # Module Chart
        if module_counts:
            modules = list(module_counts.keys())
            counts = list(module_counts.values())
            script += f"""
            // Findings by Module Chart
            const moduleCtx = document.getElementById('moduleChart');
            if (moduleCtx) {{
                new Chart(moduleCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(modules)},
                        datasets: [{{
                            label: 'Number of Findings',
                            data: {json.dumps(counts)},
                            backgroundColor: 'rgba(52, 152, 219, 0.7)',
                            borderColor: 'rgba(52, 152, 219, 1)',
                            borderWidth: 2,
                            borderRadius: 8
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: false
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                borderRadius: 8,
                                titleFont: {{ size: 14, weight: 'bold' }},
                                bodyFont: {{ size: 13 }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    precision: 0,
                                    font: {{ size: 12 }}
                                }},
                                grid: {{
                                    color: 'rgba(0, 0, 0, 0.05)'
                                }}
                            }},
                            x: {{
                                ticks: {{
                                    font: {{ size: 12 }}
                                }},
                                grid: {{
                                    display: false
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            """

        # Severity Chart
        if sum(severity_counts.values()) > 0:
            severity_labels = list(severity_counts.keys())
            severity_values = list(severity_counts.values())
            colors = ['#e74c3c', '#ff6b6b', '#f39c12', '#17a2b8', '#27ae60']

            script += f"""
            // Findings by Severity Chart
            const severityCtx = document.getElementById('severityChart');
            if (severityCtx) {{
                new Chart(severityCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: {json.dumps(severity_labels)},
                        datasets: [{{
                            data: {json.dumps(severity_values)},
                            backgroundColor: {json.dumps(colors)},
                            borderWidth: 3,
                            borderColor: '#ffffff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'right',
                                labels: {{
                                    padding: 15,
                                    font: {{ size: 13 }},
                                    generateLabels: function(chart) {{
                                        const data = chart.data;
                                        return data.labels.map((label, i) => ({{
                                            text: label + ': ' + data.datasets[0].data[i],
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            hidden: false,
                                            index: i
                                        }}));
                                    }}
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                borderRadius: 8,
                                callbacks: {{
                                    label: function(context) {{
                                        const label = context.label || '';
                                        const value = context.parsed || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return label + ': ' + value + ' (' + percentage + '%)';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            """

        # Timeline Chart
        if timeline_data:
            # Group timeline events by hour for visualization
            timeline_counts = {}
            for event in timeline_data:
                timestamp = event.get('timestamp', '')
                if timestamp:
                    # Extract hour from timestamp
                    try:
                        hour = timestamp.split('T')[1][:2] if 'T' in timestamp else '00'
                        timeline_counts[hour + ':00'] = timeline_counts.get(hour + ':00', 0) + 1
                    except:
                        pass

            if timeline_counts:
                timeline_labels = sorted(timeline_counts.keys())
                timeline_values = [timeline_counts[label] for label in timeline_labels]

                script += f"""
                // Activity Timeline Chart
                const timelineCtx = document.getElementById('timelineChart');
                if (timelineCtx) {{
                    new Chart(timelineCtx, {{
                        type: 'line',
                        data: {{
                            labels: {json.dumps(timeline_labels)},
                            datasets: [{{
                                label: 'Events',
                                data: {json.dumps(timeline_values)},
                                fill: true,
                                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                                borderColor: 'rgba(52, 152, 219, 1)',
                                borderWidth: 3,
                                tension: 0.4,
                                pointBackgroundColor: 'rgba(52, 152, 219, 1)',
                                pointBorderColor: '#fff',
                                pointBorderWidth: 2,
                                pointRadius: 5,
                                pointHoverRadius: 7
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{
                                    display: false
                                }},
                                tooltip: {{
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    padding: 12,
                                    borderRadius: 8
                                }}
                            }},
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    ticks: {{
                                        precision: 0,
                                        font: {{ size: 12 }}
                                    }},
                                    grid: {{
                                        color: 'rgba(0, 0, 0, 0.05)'
                                    }}
                                }},
                                x: {{
                                    ticks: {{
                                        font: {{ size: 12 }}
                                    }},
                                    grid: {{
                                        display: false
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
                """

        # Artifact Types Chart
        if artifact_types:
            artifact_labels = list(artifact_types.keys())
            artifact_values = list(artifact_types.values())

            script += f"""
            // Artifact Types Chart
            const fileTypeCtx = document.getElementById('fileTypeChart');
            if (fileTypeCtx) {{
                new Chart(fileTypeCtx, {{
                    type: 'pie',
                    data: {{
                        labels: {json.dumps(artifact_labels)},
                        datasets: [{{
                            data: {json.dumps(artifact_values)},
                            backgroundColor: [
                                'rgba(52, 152, 219, 0.8)',
                                'rgba(46, 204, 113, 0.8)',
                                'rgba(155, 89, 182, 0.8)',
                                'rgba(241, 196, 15, 0.8)',
                                'rgba(231, 76, 60, 0.8)',
                                'rgba(26, 188, 156, 0.8)',
                                'rgba(230, 126, 34, 0.8)',
                                'rgba(149, 165, 166, 0.8)'
                            ],
                            borderWidth: 3,
                            borderColor: '#ffffff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'right',
                                labels: {{
                                    padding: 15,
                                    font: {{ size: 13 }},
                                    generateLabels: function(chart) {{
                                        const data = chart.data;
                                        return data.labels.map((label, i) => ({{
                                            text: label + ': ' + data.datasets[0].data[i],
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            hidden: false,
                                            index: i
                                        }}));
                                    }}
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                borderRadius: 8,
                                callbacks: {{
                                    label: function(context) {{
                                        const label = context.label || '';
                                        const value = context.parsed || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return label + ': ' + value + ' (' + percentage + '%)';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            """

        return script
