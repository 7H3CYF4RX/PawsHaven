"""
PawsHaven — Veterinary & Animal Rescue Platform
Main Flask Application
"""
import os
import sys
import platform
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g
from middleware.auth_middleware import get_token_from_request, verify_token

start_time = datetime.utcnow()


def create_app():
    app = Flask(__name__)

    from config import Config
    app.config.from_object(Config)

    # Ensure sandbox directory exists
    os.makedirs(Config.SANDBOX_DIR, exist_ok=True)
    os.makedirs(Config.DOCUMENTS_DIR, exist_ok=True)

    from utils.migrations import migrate_sandboxes
    migrate_sandboxes()

    # ── CORS Misconfiguration (Vuln #27) ─────────────────────────
    @app.after_request
    def add_cors_and_headers(response):
        origin = request.headers.get('Origin', '*')
        # VULN: Reflects ANY origin and allows credentials
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        # VULN: No X-Frame-Options or CSP frame-ancestors (Clickjacking)
        return response

    # ── Register Blueprints ──────────────────────────────────────
    from blueprints.auth import auth_bp
    from blueprints.users import users_bp
    from blueprints.animals import animals_bp
    from blueprints.adoptions import adoptions_bp
    from blueprints.appointments import appointments_bp
    from blueprints.reports import reports_bp
    from blueprints.community import community_bp
    from blueprints.donations import donations_bp
    from blueprints.newsletter import newsletter_bp
    from blueprints.files import files_bp
    from blueprints.integrations import integrations_bp
    from blueprints.vet_tools import vet_tools_bp
    from blueprints.data_export import export_bp
    from blueprints.admin import admin_bp
    from blueprints.misc import misc_bp
    from blueprints.pages import pages_bp
    from blueprints.store import store_bp
    from blueprints.premium import premium_bp
    from blueprints.host_admin import host_admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(animals_bp)
    app.register_blueprint(adoptions_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(newsletter_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(vet_tools_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(premium_bp)
    app.register_blueprint(host_admin_bp)

    # ── Verbose Error Handler (Vuln #34) ─────────────────────────
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            'error': 'Internal Server Error',
            'details': str(e),
            'traceback': traceback.format_exc(),
            'server': 'PawsHaven API v2.4.1',
            'python': sys.version,
            'os': platform.platform(),
            'database_hint': 'sqlite3',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404
        
        token = get_token_from_request()
        user_data = verify_token(token) if token else None
        return render_template('errors/404.html', user=user_data), 404

    @app.errorhandler(403)
    def forbidden(e):
        token = get_token_from_request()
        user_data = verify_token(token) if token else None
        return render_template('errors/403.html', user=user_data), 403

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
