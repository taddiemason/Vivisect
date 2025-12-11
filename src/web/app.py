"""Flask application for Vivisect Web GUI"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Config, ForensicsLogger, ReportGenerator
from modules import (
    DiskImaging,
    FileAnalysis,
    NetworkForensics,
    MemoryAnalysis,
    ArtifactExtraction,
    USBGadget
)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize Vivisect components
    config = Config()
    logger = ForensicsLogger(config.get('log_dir'))
    report_gen = ReportGenerator(config.get('output_dir'))

    # Initialize modules
    disk_imaging = DiskImaging(logger, config)
    file_analysis = FileAnalysis(logger, config)
    network_forensics = NetworkForensics(logger, config)
    memory_analysis = MemoryAnalysis(logger, config)
    artifact_extraction = ArtifactExtraction(logger, config)
    usb_gadget = USBGadget(logger, config)

    # Store active tasks
    active_tasks = {}

    # Routes
    @app.route('/')
    def index():
        """Main dashboard"""
        return render_template('index.html')

    @app.route('/api/status')
    def get_status():
        """Get system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'vivisect_version': '1.0.0',
                'modules': {
                    'disk_imaging': config.get('modules.disk_imaging.enabled', True),
                    'file_analysis': config.get('modules.file_analysis.enabled', True),
                    'network_forensics': config.get('modules.network_forensics.enabled', True),
                    'memory_analysis': config.get('modules.memory_analysis.enabled', True),
                    'artifact_extraction': config.get('modules.artifact_extraction.enabled', True),
                    'usb_gadget': config.get('modules.usb_gadget.enabled', True)
                },
                'active_tasks': len(active_tasks),
                'output_dir': config.get('output_dir'),
                'log_dir': config.get('log_dir'),
                'usb_connected': usb_gadget.is_connected_to_host()
            }
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/disk/devices')
    def list_devices():
        """List available disk devices"""
        try:
            devices = disk_imaging.list_devices()
            return jsonify({'devices': devices})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/disk/image', methods=['POST'])
    def create_disk_image():
        """Create disk image"""
        try:
            data = request.json
            device = data.get('device')
            output = data.get('output')
            method = data.get('method', 'dd')

            def run_imaging():
                if method == 'dd':
                    result = disk_imaging.create_image_dd(device, output)
                else:
                    result = disk_imaging.create_image_dcfldd(device, output)

                socketio.emit('task_complete', {
                    'task': 'disk_image',
                    'result': result
                })

            task_id = f"disk_image_{datetime.now().timestamp()}"
            active_tasks[task_id] = threading.Thread(target=run_imaging)
            active_tasks[task_id].start()

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/interfaces')
    def list_interfaces():
        """List network interfaces"""
        try:
            interfaces = network_forensics.list_interfaces()
            return jsonify({'interfaces': interfaces})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/network/capture', methods=['POST'])
    def start_capture():
        """Start network capture"""
        try:
            data = request.json
            interface = data.get('interface')
            output = data.get('output')
            duration = data.get('duration', 60)

            def run_capture():
                result = network_forensics.capture_traffic(
                    interface, output, duration=duration
                )
                socketio.emit('task_complete', {
                    'task': 'network_capture',
                    'result': result
                })

            task_id = f"capture_{datetime.now().timestamp()}"
            active_tasks[task_id] = threading.Thread(target=run_capture)
            active_tasks[task_id].start()

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/memory/live')
    def analyze_memory_live():
        """Analyze running system"""
        try:
            result = memory_analysis.analyze_running_system()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/memory/dump', methods=['POST'])
    def create_memory_dump():
        """Create memory dump"""
        try:
            data = request.json
            output = data.get('output')
            method = data.get('method', 'auto')

            def run_dump():
                result = memory_analysis.create_memory_dump(output, method)
                socketio.emit('task_complete', {
                    'task': 'memory_dump',
                    'result': result
                })

            task_id = f"memory_dump_{datetime.now().timestamp()}"
            active_tasks[task_id] = threading.Thread(target=run_dump)
            active_tasks[task_id].start()

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/artifacts/browser')
    def extract_browser():
        """Extract browser artifacts"""
        try:
            result = artifact_extraction.extract_browser_history()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/artifacts/logs')
    def extract_logs():
        """Extract system logs"""
        try:
            result = artifact_extraction.extract_system_logs()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/artifacts/persistence')
    def extract_persistence():
        """Extract persistence mechanisms"""
        try:
            result = artifact_extraction.extract_persistence_mechanisms()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/file/hash', methods=['POST'])
    def calculate_hash():
        """Calculate file hash"""
        try:
            data = request.json
            filepath = data.get('filepath')
            hashes = file_analysis.calculate_hashes(filepath)
            return jsonify({'hashes': hashes})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/file/metadata', methods=['POST'])
    def get_metadata():
        """Get file metadata"""
        try:
            data = request.json
            filepath = data.get('filepath')
            metadata = file_analysis.get_file_metadata(filepath)
            return jsonify(metadata)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/collect', methods=['POST'])
    def run_collection():
        """Run full forensics collection"""
        try:
            data = request.json
            case_id = data.get('case_id', f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

            def run_full_collection():
                report = report_gen.create_report(case_id)

                # Memory analysis
                socketio.emit('progress', {'step': 'memory', 'status': 'running'})
                memory_data = memory_analysis.analyze_running_system()
                report_gen.add_finding(report, 'memory', {
                    'type': 'live_analysis',
                    'data': memory_data
                })

                # Browser artifacts
                socketio.emit('progress', {'step': 'browser', 'status': 'running'})
                browser_data = artifact_extraction.extract_browser_history()
                report_gen.add_finding(report, 'artifacts', {
                    'type': 'browser',
                    'data': browser_data
                })

                # System logs
                socketio.emit('progress', {'step': 'logs', 'status': 'running'})
                logs_data = artifact_extraction.extract_system_logs()
                report_gen.add_finding(report, 'artifacts', {
                    'type': 'logs',
                    'data': logs_data
                })

                # Persistence
                socketio.emit('progress', {'step': 'persistence', 'status': 'running'})
                persist_data = artifact_extraction.extract_persistence_mechanisms()
                report_gen.add_finding(report, 'artifacts', {
                    'type': 'persistence',
                    'data': persist_data
                })

                # Save reports
                json_report = report_gen.save_report(report, 'json')
                html_report = report_gen.save_report(report, 'html')

                socketio.emit('task_complete', {
                    'task': 'collection',
                    'result': {
                        'case_id': case_id,
                        'json_report': json_report,
                        'html_report': html_report
                    }
                })

            task_id = f"collection_{datetime.now().timestamp()}"
            active_tasks[task_id] = threading.Thread(target=run_full_collection)
            active_tasks[task_id].start()

            return jsonify({'task_id': task_id, 'case_id': case_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/reports')
    def list_reports():
        """List available reports"""
        try:
            output_dir = config.get('output_dir')
            reports = []

            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    filepath = os.path.join(output_dir, filename)
                    if os.path.isfile(filepath):
                        reports.append({
                            'filename': filename,
                            'path': filepath,
                            'size': os.path.getsize(filepath),
                            'modified': datetime.fromtimestamp(
                                os.path.getmtime(filepath)
                            ).isoformat()
                        })

            reports.sort(key=lambda x: x['modified'], reverse=True)
            return jsonify({'reports': reports})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/reports/<path:filename>')
    def download_report(filename):
        """Download a report"""
        try:
            output_dir = config.get('output_dir')
            filepath = os.path.join(output_dir, filename)

            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
            else:
                return jsonify({'error': 'Report not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/logs/<module>')
    def get_logs(module):
        """Get logs for a specific module"""
        try:
            log_dir = config.get('log_dir')
            log_file = os.path.join(log_dir, f"{module}.log")

            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    # Get last 100 lines
                    lines = f.readlines()[-100:]
                    return jsonify({'logs': lines})
            else:
                return jsonify({'logs': []})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/status')
    def usb_gadget_status():
        """Get USB gadget connection status"""
        try:
            status = usb_gadget.get_gadget_status()
            connection_info = usb_gadget.get_connection_info()
            return jsonify({
                'status': status,
                'connection': connection_info
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/configure', methods=['POST'])
    def configure_usb_network():
        """Configure USB network interface"""
        try:
            result = usb_gadget.configure_network()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/capture', methods=['POST'])
    def start_usb_capture():
        """Start packet capture on USB interface"""
        try:
            data = request.json or {}
            output_file = data.get('output_file')

            def run_capture():
                result = usb_gadget.start_packet_capture(output_file)
                socketio.emit('task_complete', {
                    'task': 'usb_capture',
                    'result': result
                })

            task_id = f"usb_capture_{datetime.now().timestamp()}"
            active_tasks[task_id] = threading.Thread(target=run_capture)
            active_tasks[task_id].start()

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/auto-collect', methods=['POST'])
    def start_auto_collection():
        """Start automatic collection on USB connection"""
        try:
            def run_auto_collect():
                result = usb_gadget.auto_collect_on_connection()
                socketio.emit('task_complete', {
                    'task': 'usb_auto_collect',
                    'result': result
                })

            task_id = f"usb_auto_collect_{datetime.now().timestamp()}"
            active_tasks[task_id] = threading.Thread(target=run_auto_collect)
            active_tasks[task_id].start()

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        emit('connected', {'status': 'connected'})

    @socketio.on('ping')
    def handle_ping():
        """Handle ping from client"""
        emit('pong', {'timestamp': datetime.now().isoformat()})

    return app, socketio


def main():
    """Run the web application"""
    app, socketio = create_app()

    # Run on all interfaces so it's accessible on the device screen
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
