"""
Vet Tools Blueprint — Diagnostic tool
Vulnerability: Command Injection (#5)
"""
import subprocess
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth

vet_tools_bp = Blueprint('vet_tools', __name__)


@vet_tools_bp.route('/api/vet/diagnose', methods=['POST'])
@require_auth
def diagnose():
    """
    VULN #5: Command injection — user input concatenated into shell command.
    
    Feature: "Microchip Scanner" — checks a device/network identifier.
    Payload: 127.0.0.1; cat /etc/passwd
    Payload: 127.0.0.1 && whoami
    Payload: 127.0.0.1 | id
    """
    data = request.get_json()
    device_id = data.get('device_id', '').strip()

    if not device_id:
        return jsonify({'error': 'Device or chip identifier is required.'}), 400

    try:
        # VULN: User input directly in shell command!
        result = subprocess.run(
            f'echo "Scanning device: {device_id}" && ping -c 1 -W 2 {device_id}',
            shell=True, capture_output=True, text=True, timeout=10
        )

        return jsonify({
            'status': 'scan_complete',
            'device_id': device_id,
            'output': result.stdout,
            'errors': result.stderr,
            'exit_code': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Scan timed out. Device may be unreachable.'}), 408
    except Exception as e:
        return jsonify({'error': f'Scan failed: {str(e)}'}), 500
