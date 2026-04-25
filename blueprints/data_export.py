"""
Data Export Blueprint
Vulnerability: Insecure deserialization (#25) — Python pickle
"""
import pickle
import base64
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth

export_bp = Blueprint('export', __name__)


@export_bp.route('/api/export', methods=['POST'])
@require_auth
def handle_export():
    """
    VULN #25: Insecure deserialization — accepts pickled data in 'legacy' format.
    Payload: Create malicious pickle object with os.system() → base64 encode → send.
    """
    data = request.get_json()
    format_type = data.get('format', 'json')
    payload = data.get('data', '')

    if format_type == 'json':
        return jsonify({'message': 'Export ready.', 'data': payload, 'format': 'json'})

    elif format_type == 'legacy':
        # VULN: Deserializes untrusted pickle data!
        if not payload:
            return jsonify({'error': 'No data provided for legacy import.'}), 400

        try:
            raw = base64.b64decode(payload)
            obj = pickle.loads(raw)  # VULN: RCE via pickle
            return jsonify({'message': 'Legacy data imported.', 'result': str(obj)})
        except Exception as e:
            return jsonify({'error': f'Deserialization failed: {str(e)}'}), 400

    else:
        return jsonify({'error': f'Unknown format: {format_type}'}), 400
