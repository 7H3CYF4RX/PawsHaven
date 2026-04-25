"""
Files Blueprint — Upload, download, serve files
Vulnerabilities: LFI (#12), RFI (#13), Path traversal (#24), Unrestricted file upload (#28)
"""
import os
from flask import Blueprint, request, jsonify, g, send_file, render_template_string
from middleware.auth_middleware import require_auth
from config import Config
import requests as http_requests

files_bp = Blueprint('files', __name__)


@files_bp.route('/api/upload/avatar', methods=['POST'])
@require_auth
def upload_avatar():
    """
    VULN #28: Unrestricted file upload — no file type validation.
    Accepts .html, .svg (XSS), .php, .py, .exe — anything.
    Also no filename sanitization — path traversal in filename.
    """
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400

    file = request.files['avatar']
    if not file.filename:
        return jsonify({'error': 'No file selected.'}), 400

    # VULN: No validation on file type or filename!
    filename = file.filename  # No sanitization
    save_dir = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'uploads', 'avatars')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    file.save(save_path)

    return jsonify({
        'message': 'Avatar uploaded successfully!',
        'url': f'/api/files/download?path=uploads/avatars/{filename}'
    })


@files_bp.route('/api/files/download', methods=['GET'])
@require_auth
def serve_file():
    """
    VULN #12: LFI — no path sanitization, allows ../../ traversal via path parameter.
    VULN #24: Path traversal — can read /etc/passwd, config files, etc.
    Attack: GET /api/files/download?path=../../../../../../etc/passwd
    """
    filepath = request.args.get('path', '')
    if not filepath:
        return jsonify({'error': 'Path parameter is required.'}), 400

    base_dir = os.path.join(Config.SANDBOX_DIR, g.sandbox_id)
    full_path = os.path.join(base_dir, filepath)

    # VULN: No protection against ../ traversal!
    try:
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_file(full_path)
    except Exception:
        pass

    return jsonify({'error': 'File not found.'}), 404


@files_bp.route('/api/files/remote', methods=['GET'])
@require_auth
def remote_file():
    """
    VULN #13: RFI — fetches a remote URL and renders it as Jinja2 template.
    Chains RFI + SSTI if remote content contains {{ }}.
    """
    url = request.args.get('url', '')

    if not url:
        return jsonify({'error': 'URL parameter is required.'}), 400

    try:
        resp = http_requests.get(url, timeout=5)
        content = resp.text

        # VULN: Renders remote content as Jinja2 template!
        rendered = render_template_string(content)
        return rendered, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        return jsonify({'error': f'Failed to fetch remote file: {str(e)}'}), 500
