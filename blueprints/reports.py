"""
Reports Blueprint — Stray animal reports
Vulnerability: Stored XSS (#3) — description field has a filter that blocks <script> but allows event handlers
"""
import re
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth
from utils import database as db

reports_bp = Blueprint('reports', __name__)


def basic_xss_filter(text):
    """
    VULN #3: Incomplete XSS filter — only blocks <script> tags.
    Allows: <img onerror>, <svg onload>, <details ontoggle>, <input onfocus autofocus> etc.
    """
    text = re.sub(r'<script\b[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<script\b[^>]*/?>', '', text, flags=re.IGNORECASE)
    return text


@reports_bp.route('/api/reports/stray', methods=['POST'])
@require_auth
def create_report():
    """VULN #3: Stored XSS — description passes through weak filter and stored raw."""
    data = request.get_json()
    location = data.get('location', '').strip()
    description = data.get('description', '')
    animal_type = data.get('animal_type', 'unknown')
    urgency = data.get('urgency', 'normal')

    if not location or not description:
        return jsonify({'error': 'Location and description are required.'}), 400

    # Apply weak XSS filter (bypassable!)
    filtered_desc = basic_xss_filter(description)

    report_id = db.execute_returning_id(g.sandbox_id,
        "INSERT INTO stray_reports (reporter_id, location, description, animal_type, urgency, status) VALUES (?, ?, ?, ?, ?, 'pending')",
        [g.current_user['user_id'], location, filtered_desc, animal_type, urgency])

    return jsonify({'message': 'Report submitted. Thank you for caring!', 'report_id': report_id}), 201


@reports_bp.route('/api/reports/stray', methods=['GET'])
@require_auth
def list_reports():
    """Returns stray reports — rendered with |safe in template so XSS executes."""
    reports = db.query_all(g.sandbox_id,
        "SELECT sr.*, u.name as reporter_name FROM stray_reports sr LEFT JOIN users u ON sr.reporter_id = u.id ORDER BY sr.created_at DESC")
    return jsonify({'reports': reports})
