"""
Admin Blueprint — Dashboard, Review Queue
Blind XSS renders in review queue.
"""
from flask import Blueprint, request, jsonify, g, render_template
from middleware.auth_middleware import require_admin
from utils import database as db

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/dashboard', methods=['GET'])
@require_admin
def admin_dashboard():
    """VULN: Accessible after mass assignment sets role to 'admin'."""
    users = db.query_all(g.sandbox_id, "SELECT id, name, email, role, created_at FROM users")
    animals = db.query_all(g.sandbox_id, "SELECT COUNT(*) as count FROM animals")
    donations = db.query_all(g.sandbox_id, "SELECT SUM(final_amount) as total FROM donations")

    return jsonify({
        'users': users,
        'total_animals': animals[0]['count'] if animals else 0,
        'total_donations': donations[0]['total'] if donations and donations[0]['total'] else 0,
        'recent_submissions': db.query_all(g.sandbox_id,
            "SELECT * FROM contact_submissions ORDER BY created_at DESC LIMIT 10")
    })


@admin_bp.route('/api/admin/review', methods=['GET'])
@require_admin
def admin_review():
    """
    VULN #4: Blind XSS renders here — contact submissions displayed with raw HTML.
    """
    submissions = db.query_all(g.sandbox_id,
        "SELECT * FROM contact_submissions ORDER BY created_at DESC")
    return jsonify({'submissions': submissions})
