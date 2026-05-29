"""Flask application for Vivisect Web GUI"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask.json.provider import DefaultJSONProvider

from core import Config, TaskState, OperationResult
from core.engine import VivisectEngine


class VivisectJSONProvider(DefaultJSONProvider):
    """Serialise OperationResult transparently so routes can jsonify one."""

    def default(self, o):
        if isinstance(o, OperationResult):
            return o.to_dict()
        return super().default(o)
from web.security import (
    resolve_token,
    install_auth,
    is_loopback,
    token_matches,
    extract_token,
    safe_path,
)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.json = VivisectJSONProvider(app)
    app.config['SECRET_KEY'] = os.urandom(24)

    # Initialize Vivisect components
    config = Config()

    # ── Web security ────────────────────────────────────────────────────────
    # Resolve the API token and lock down CORS/WebSocket origins. The token
    # gates the JSON API for any non-loopback client (see web/security.py).
    auth_token, token_generated = resolve_token(config)
    trust_loopback = bool(config.get('web.trust_loopback', True))
    allowed_origins = config.get('web.allowed_origins') or [
        'http://127.0.0.1:5000', 'http://localhost:5000'
    ]

    app.config['VIVISECT_TOKEN'] = auth_token
    app.config['VIVISECT_TOKEN_GENERATED'] = token_generated
    app.config['VIVISECT_HOST'] = config.get('web.host', '127.0.0.1')
    app.config['VIVISECT_PORT'] = int(config.get('web.port', 5000))
    app.config['VIVISECT_TRUST_LOOPBACK'] = trust_loopback

    socketio = SocketIO(app, cors_allowed_origins=allowed_origins)
    install_auth(app, auth_token, trust_loopback=trust_loopback)

    # Shared composition root: config, logger, report generator, forensic
    # modules, and the background task manager are all owned by the engine,
    # which also defines workflows (collect) shared with the CLI.
    engine = VivisectEngine(config)
    logger = engine.logger
    report_gen = engine.report_gen
    disk_imaging = engine.disk
    file_analysis = engine.file
    network_forensics = engine.network
    memory_analysis = engine.memory
    artifact_extraction = engine.artifacts
    usb_gadget = engine.usb
    task_manager = engine.tasks

    def emit_complete(task_name):
        """Build an on_done callback that emits the legacy 'task_complete' event.

        Preserves the existing client contract: ``result`` is the operation's
        return value on success, or ``{success: False, error}`` on failure.
        """
        def _cb(task):
            if task['state'] == TaskState.DONE.value:
                result = task['result']
            else:
                result = {'success': False, 'error': task.get('error')}
            with app.app_context():
                socketio.emit('task_complete', {
                    'task': task_name,
                    'task_id': task['id'],
                    'state': task['state'],
                    'result': result,
                }, namespace='/')
        return _cb

    # Routes
    @app.route('/')
    def index():
        """Main dashboard.

        The token is embedded in the page only when the requester is already
        trusted (loopback) or has presented a valid token via ``?token=``. A
        remote operator bootstraps the UI by visiting ``/?token=<TOKEN>`` once;
        the page then stores it for subsequent API calls.
        """
        trusted = (trust_loopback and is_loopback(request)) or \
            token_matches(extract_token(request), auth_token)
        return render_template('index.html', auth_token=auth_token if trusted else '')

    @app.route('/api/status')
    def get_status():
        """Get system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'vivisect_version': '1.0.0',
                'modules': engine.module_status(),
                'active_tasks': task_manager.active_count(),
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

            fn = (disk_imaging.create_image_dd if method == 'dd'
                  else disk_imaging.create_image_dcfldd)
            task_id = task_manager.submit(
                'disk_image', fn, device, output,
                on_done=emit_complete('disk_image'))

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

            task_id = task_manager.submit(
                'network_capture', network_forensics.capture_traffic,
                interface, output, duration=duration,
                on_done=emit_complete('network_capture'))

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

            task_id = task_manager.submit(
                'memory_dump', memory_analysis.create_memory_dump, output, method,
                on_done=emit_complete('memory_dump'))

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
            data = request.json or {}
            case_id = data.get('case_id', f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            modules = data.get('modules')  # optional list of step names

            def progress(step, status='running'):
                with app.app_context():
                    socketio.emit('progress', {'step': step, 'status': status},
                                  namespace='/')

            def run_full_collection():
                result = engine.collect(case_id, modules, progress=progress)
                # The in-memory report is not JSON-friendly to ship back; the
                # saved report paths are what the client needs.
                return {k: v for k, v in result.items() if k != 'report'}

            task_id = task_manager.submit(
                'collection', run_full_collection,
                on_done=emit_complete('collection'))

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
            filepath = safe_path(output_dir, filename)
            if filepath is None:
                return jsonify({'error': 'Invalid report path'}), 400

            if os.path.isfile(filepath):
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
            log_file = safe_path(log_dir, f"{module}.log")
            if log_file is None:
                return jsonify({'error': 'Invalid module name'}), 400

            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    # Get last 100 lines
                    lines = f.readlines()[-100:]
                    return jsonify({'logs': lines})
            else:
                return jsonify({'logs': []})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ── Background tasks ─────────────────────────────────────────────────────

    @app.route('/api/tasks')
    def list_tasks():
        """List background tasks and their state (most recent first)."""
        try:
            return jsonify({'tasks': task_manager.list()})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/tasks/<task_id>')
    def get_task(task_id):
        """Fetch a single task's record — lets a client that missed the
        'task_complete' socket event recover the result."""
        task = task_manager.get(task_id)
        if task is None:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(task.to_dict())

    @app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
    def cancel_task(task_id):
        """Request cancellation (effective only for tasks not yet started)."""
        if task_manager.get(task_id) is None:
            return jsonify({'error': 'Task not found'}), 404
        cancel_requested = task_manager.cancel(task_id)
        return jsonify({'task_id': task_id, 'cancel_requested': cancel_requested})

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

    @app.route('/api/usb/multifunction-status')
    def multifunction_status():
        """Get multi-function gadget status (network + storage + serial)"""
        try:
            status = usb_gadget.get_multifunction_status()
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/mass-storage/sync', methods=['POST'])
    def sync_mass_storage():
        """Sync reports to USB mass storage"""
        try:
            task_id = task_manager.submit(
                'mass_storage_sync', usb_gadget.sync_reports_to_storage,
                on_done=emit_complete('mass_storage_sync'))

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/serial-info')
    def serial_console_info():
        """Get serial console information"""
        try:
            info = usb_gadget.get_serial_console_info()
            return jsonify(info)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/mode/switch', methods=['POST'])
    def switch_usb_mode():
        """Switch USB gadget mode"""
        try:
            data = request.json or {}
            mode = data.get('mode')  # 'multi', 'mass_storage', 'ether'
            read_only = data.get('read_only', False)

            if mode == 'multi':
                result = usb_gadget.switch_to_multi_function()
            elif mode == 'mass_storage':
                result = usb_gadget.switch_to_mass_storage_only(read_only=read_only)
            elif mode == 'ether' or mode == 'network':
                result = usb_gadget.switch_to_network_only()
            else:
                return jsonify({'error': f'Invalid mode: {mode}'}), 400

            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/mode/current')
    def get_current_mode():
        """Get current USB gadget mode"""
        try:
            mode = usb_gadget.get_current_mode()
            return jsonify({
                'mode': mode,
                'timestamp': datetime.now().isoformat()
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

            task_id = task_manager.submit(
                'usb_capture', usb_gadget.start_packet_capture, output_file,
                on_done=emit_complete('usb_capture'))

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/auto-collect', methods=['POST'])
    def start_auto_collection():
        """Start automatic collection on USB connection"""
        try:
            task_id = task_manager.submit(
                'usb_auto_collect', usb_gadget.auto_collect_on_connection,
                on_done=emit_complete('usb_auto_collect'))

            return jsonify({'task_id': task_id, 'status': 'started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/hid/status')
    def hid_status():
        """Get HID keyboard status"""
        try:
            available = usb_gadget.is_hid_available()
            return jsonify({
                'available': available,
                'device': '/dev/hidg0' if available else None,
                'warning': 'HID mode requires authorization - use only for legitimate security testing'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/hid/payloads')
    def list_hid_payloads():
        """List available HID payloads"""
        try:
            payloads = usb_gadget._get_hid_payloads()
            return jsonify({
                'payloads': list(payloads.keys()),
                'details': {
                    name: {
                        'description': payload.__doc__.strip() if payload.__doc__ else f'HID payload: {name}',
                        'type': 'function'
                    }
                    for name, payload in payloads.items()
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/hid/send-string', methods=['POST'])
    def send_hid_string():
        """Send a string via HID keyboard"""
        try:
            data = request.json or {}
            text = data.get('text', '')
            delay_ms = data.get('delay_ms', 50)

            if not text:
                return jsonify({'error': 'No text provided'}), 400

            if len(text) > 500:
                return jsonify({'error': 'Text too long (max 500 characters)'}), 400

            task_id = task_manager.submit(
                'hid_send_string', usb_gadget.send_hid_string, text,
                delay_ms=delay_ms, on_done=emit_complete('hid_send_string'))

            return jsonify({
                'task_id': task_id,
                'status': 'started',
                'text_length': len(text)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/hid/execute-payload', methods=['POST'])
    def execute_hid_payload():
        """Execute a pre-built HID payload"""
        try:
            data = request.json or {}
            payload_name = data.get('payload_name')

            if not payload_name:
                return jsonify({'error': 'No payload name provided'}), 400

            task_id = task_manager.submit(
                'hid_execute_payload', usb_gadget.execute_hid_payload, payload_name,
                on_done=emit_complete('hid_execute_payload'))

            return jsonify({
                'task_id': task_id,
                'status': 'started',
                'payload': payload_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usb/hid/mode/switch', methods=['POST'])
    def switch_to_hid():
        """Switch to HID keyboard mode"""
        try:
            result = usb_gadget.switch_to_hid_mode()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @socketio.on('connect')
    def handle_connect(auth=None):
        """Handle client connection.

        Returning False rejects the WebSocket connection. Loopback clients are
        trusted; remote clients must supply the token via ``io({auth:{token}})``.
        """
        if not (trust_loopback and is_loopback(request)):
            provided = auth.get('token') if isinstance(auth, dict) else None
            if not token_matches(provided, auth_token):
                return False
        emit('connected', {'status': 'connected'})

    @socketio.on('ping')
    def handle_ping():
        """Handle ping from client"""
        emit('pong', {'timestamp': datetime.now().isoformat()})

    return app, socketio


def main():
    """Run the web application"""
    app, socketio = create_app()

    host = os.environ.get('VIVISECT_WEB_HOST') or app.config['VIVISECT_HOST']
    port = int(os.environ.get('VIVISECT_WEB_PORT') or app.config['VIVISECT_PORT'])
    socketio.run(app, host=host, port=port, debug=False)


if __name__ == '__main__':
    main()
