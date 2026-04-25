"""
Auth Middleware — Extracts and verifies JWT from requests.
Sets current_user and sandbox_id on flask.g.
"""
from functools import wraps
from flask import request, jsonify, g
from utils.jwt_handler import verify_token
from utils import database as db


def get_token_from_request():
    """Extract JWT from Authorization header or cookie."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return request.cookies.get('token', None)


def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401

        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token. Please log in again.'}), 401

        g.current_user = user_data
        g.sandbox_id = user_data.get('sandbox_id', '')
        
        # Check for Ban
        from config import Config
        import os
        from flask import render_template
        if os.path.exists(os.path.join(Config.SANDBOX_DIR, g.sandbox_id, '.banned')):
            if "text/html" in request.headers.get("Accept", ""):
                return render_template('errors/banned.html'), 403
            return jsonify({'error': 'YOU GOT BANNED, WHY DONT YOU OBEY RULES BRUHHH!!???'}), 403

        # Merge fresh database state (like name, email) but keep JWT claims (like role) for forged tokens
        try:
            db_user = db.query_one(g.sandbox_id, "SELECT id, name, email, role, password_hash, two_factor_enabled FROM users WHERE id = ?", [user_data.get('user_id')])
            if db_user:
                # JWT claims take precedence for role-based vulnerabilities (forgery)
                # We update g.current_user with DB fields but PERSIST the role from JWT if it was manipulated
                jwt_role = user_data.get('role')
                g.current_user.update(db_user)
                if jwt_role == 'admin':
                    g.current_user['role'] = 'admin'
        except Exception:
            return jsonify({'error': 'Sandbox disconnected or deleted. Please log in again.'}), 401
            
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401

        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token. Please log in again.'}), 401

        if user_data.get('role') != 'admin':
            return jsonify({'error': 'Admin privileges required.'}), 403

        g.current_user = user_data
        g.sandbox_id = user_data.get('sandbox_id', '')

        # Check for Ban
        from config import Config
        import os
        from flask import render_template
        if os.path.exists(os.path.join(Config.SANDBOX_DIR, g.sandbox_id, '.banned')):
            if "text/html" in request.headers.get("Accept", ""):
                return render_template('errors/banned.html'), 403
            return jsonify({'error': 'YOU GOT BANNED, WHY DONT YOU OBEY RULES BRUHHH!!???'}), 403

        try:
            db_user = db.query_one(g.sandbox_id, "SELECT id, name, email, role, password_hash, two_factor_enabled FROM users WHERE id = ?", [user_data.get('user_id')])
            if db_user:
                jwt_role = user_data.get('role')
                g.current_user.update(db_user)
                if jwt_role == 'admin':
                    g.current_user['role'] = 'admin'
        except Exception:
            return jsonify({'error': 'Sandbox disconnected or deleted. Please log in again.'}), 401

        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    """Decorator that sets current_user if token exists, but doesn't require it."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if token:
            user_data = verify_token(token)
            if user_data:
                g.current_user = user_data
                g.sandbox_id = user_data.get('sandbox_id', '')
                
                # Check for Ban
                from config import Config
                import os
                from flask import render_template
                if os.path.exists(os.path.join(Config.SANDBOX_DIR, g.sandbox_id, '.banned')):
                    if "text/html" in request.headers.get("Accept", ""):
                        return render_template('errors/banned.html'), 403
                    g.current_user = None
                    g.sandbox_id = ''
                    return f(*args, **kwargs)
                
                try:
                    db_user = db.query_one(g.sandbox_id, "SELECT * FROM users WHERE id = ?", [user_data.get('user_id')])
                    if db_user:
                        g.current_user.update(db_user)
                except Exception:
                    pass
        else:
            g.current_user = None
            g.sandbox_id = ''
        return f(*args, **kwargs)
    return decorated
