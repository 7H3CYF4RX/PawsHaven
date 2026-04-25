"""
Host Admin Blueprint — For CTF Hosters to manage players.
Completely secured using a Master Password.
"""
import os
import shutil
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, g
from config import Config
from utils import database as db

host_admin_bp = Blueprint('host_admin', __name__, template_folder='templates')

def require_host_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_host_admin'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('host_admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@host_admin_bp.route('/host-management-portal/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        import hashlib
        password = request.form.get('password', '')
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if pw_hash == Config.HOST_ADMIN_HASH:
            session['is_host_admin'] = True
            return redirect(url_for('host_admin.dashboard'))
        return render_template('host_admin/login.html', error="Invalid Master Password")
    return render_template('host_admin/login.html')

@host_admin_bp.route('/host-management-portal/logout')
def logout():
    session.pop('is_host_admin', None)
    return redirect(url_for('host_admin.login'))

@host_admin_bp.route('/host-management-portal')
@require_host_admin
def dashboard():
    return render_template('host_admin/dashboard.html')

@host_admin_bp.route('/api/host/players')
@require_host_admin
def list_players():
    players = []
    if os.path.exists(Config.SANDBOX_DIR):
        for sid in os.listdir(Config.SANDBOX_DIR):
            path = os.path.join(Config.SANDBOX_DIR, sid)
            if not os.path.isdir(path): continue
            
            # Metadata
            stats = os.stat(path)
            created_at = datetime.fromtimestamp(stats.st_ctime).isoformat()
            
            # Try to get user info from their DB
            user_info = {"name": "Unknown", "email": "Unknown", "sent_emails": 0}
            db_path = os.path.join(path, 'db.sqlite')
            if os.path.exists(db_path):
                try:
                    # Target the first user (sandbox owner)
                    user = db.query_one(sid, "SELECT name, email, sent_emails FROM users ORDER BY id ASC LIMIT 1")
                    if user: user_info = user
                except: pass
            
            is_banned = os.path.exists(os.path.join(path, '.banned'))
            
            players.append({
                "id": sid,
                "name": user_info['name'],
                "email": user_info['email'],
                "sent_emails": user_info['sent_emails'],
                "created_at": created_at,
                "is_banned": is_banned
            })
    
    return jsonify({"players": players})

@host_admin_bp.route('/api/host/players/<sid>/ban', methods=['POST'])
@require_host_admin
def ban_player(sid):
    path = os.path.join(Config.SANDBOX_DIR, sid)
    if os.path.exists(path) and os.path.isdir(path):
        ban_file = os.path.join(path, '.banned')
        with open(ban_file, 'w') as f:
            f.write(json.dumps({"banned_at": datetime.utcnow().isoformat()}))
        return jsonify({"message": f"Player {sid} banned successfully."})
    return jsonify({"error": "Player not found"}), 404

@host_admin_bp.route('/api/host/players/<sid>/unban', methods=['POST'])
@require_host_admin
def unban_player(sid):
    path = os.path.join(Config.SANDBOX_DIR, sid)
    ban_file = os.path.join(path, '.banned')
    if os.path.exists(ban_file):
        os.remove(ban_file)
        return jsonify({"message": f"Player {sid} unbanned."})
    return jsonify({"error": "Ban not found"}), 404

@host_admin_bp.route('/api/host/players/<sid>', methods=['DELETE'])
@require_host_admin
def delete_player(sid):
    # Sanitize sid to prevent path traversal
    sid = os.path.basename(sid)
    path = os.path.abspath(os.path.join(Config.SANDBOX_DIR, sid))
    
    if not path.startswith(os.path.abspath(Config.SANDBOX_DIR)):
        return jsonify({"error": "Invalid sandbox ID"}), 400

    if os.path.exists(path) and os.path.isdir(path):
        try:
            # 1. Clean up global documents (Receipts) before deleting the DB
            try:
                receipts = db.query_all(sid, "SELECT receipt_path FROM donations WHERE receipt_path IS NOT NULL")
                if receipts:
                    for r in receipts:
                        global_receipt = os.path.join(Config.DOCUMENTS_DIR, 'receipts', r['receipt_path'])
                        if os.path.exists(global_receipt):
                            os.remove(global_receipt)
            except: pass # Sandbox might be corrupted or table missing

            # 2. Force garbage collection to release file handles
            import gc
            gc.collect() 
            
            # 3. Nuke the main sandbox folder (DB, uploads, private files)
            shutil.rmtree(path)
            return jsonify({"message": f"Player {sid} data completely wiped."})
        except Exception as e:
            # Fallback: attempt silent deletion
            try:
                shutil.rmtree(path, ignore_errors=True)
                if not os.path.exists(path):
                    return jsonify({"message": f"Player {sid} wiped (with secondary cleanup)."})
            except: pass
            return jsonify({"error": f"Failed to wipe data: {str(e)}"}), 500
            
    return jsonify({"error": "Player not found"}), 404

@host_admin_bp.route('/api/host/broadcast', methods=['POST'])
@require_host_admin
def broadcast():
    data = request.get_json()
    title = data.get('subject', 'Announcement')
    message = data.get('message', '')
    
    from datetime import timedelta
    broadcast_data = {
        "id": str(int(datetime.utcnow().timestamp())),
        "title": title,
        "message": message,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(seconds=20)).isoformat()
    }
    
    os.makedirs(os.path.join(Config.BASE_DIR, 'data'), exist_ok=True)
    broadcast_file = os.path.join(Config.BASE_DIR, 'data', 'global_broadcast.json')
    
    with open(broadcast_file, 'w') as f:
        json.dump(broadcast_data, f)
                
    return jsonify({"message": "Global broadcast published successfully."})

@host_admin_bp.route('/api/host/players/<sid>/message', methods=['POST'])
@require_host_admin
def send_private_message(sid):
    data = request.get_json()
    title = data.get('subject', 'Private Message')
    message = data.get('message', '')
    
    from datetime import timedelta
    msg_data = {
        "id": "p_" + str(int(datetime.utcnow().timestamp())),
        "title": title,
        "message": message,
        "is_private": True,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(seconds=20)).isoformat()
    }
    
    path = os.path.join(Config.SANDBOX_DIR, sid)
    if os.path.exists(path) and os.path.isdir(path):
        with open(os.path.join(path, 'message.json'), 'w') as f:
            json.dump(msg_data, f)
        return jsonify({"message": f"Private message sent to {sid}."})
    return jsonify({"error": "Player not found"}), 404

@host_admin_bp.route('/api/host/broadcast/clear', methods=['DELETE'])
@require_host_admin
def clear_broadcast():
    broadcast_file = os.path.join(Config.BASE_DIR, 'data', 'global_broadcast.json')
    if os.path.exists(broadcast_file):
        os.remove(broadcast_file)
        return jsonify({"message": "Global broadcast cleared."})
    return jsonify({"message": "No active broadcast found."})

@host_admin_bp.route('/api/host/players/<sid>/message/clear', methods=['DELETE'])
@require_host_admin
def clear_private_message(sid):
    path = os.path.join(Config.SANDBOX_DIR, sid)
    msg_file = os.path.join(path, 'message.json')
    if os.path.exists(msg_file):
        os.remove(msg_file)
        return jsonify({"message": f"Private message for {sid} cleared."})
    return jsonify({"message": "No private message found for this player."})
