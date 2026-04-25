"""
Community Blueprint — Comments, Contact
Vulnerabilities: Self XSS (#2), Blind XSS (#4)
"""
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth
from utils import database as db

community_bp = Blueprint('community', __name__)


@community_bp.route('/api/comments', methods=['GET'])
@require_auth
def list_comments():
    """Returns comments — Self XSS payloads render back to the poster."""
    animal_id = request.args.get('animal_id', None)
    if animal_id:
        comments = db.query_all(g.sandbox_id,
            "SELECT c.*, u.name as author FROM comments c LEFT JOIN users u ON c.user_id = u.id WHERE c.animal_id = ? ORDER BY c.created_at DESC",
            [animal_id])
    else:
        comments = db.query_all(g.sandbox_id,
            "SELECT c.*, u.name as author FROM comments c LEFT JOIN users u ON c.user_id = u.id ORDER BY c.created_at DESC")
    return jsonify({'comments': comments})


@community_bp.route('/api/comments', methods=['POST'])
@require_auth
def create_comment():
    """
    VULN #2: Self XSS — comment content is stored and rendered back raw.
    Only the poster sees it in their sandbox, but it still executes.
    """
    data = request.get_json()
    content = data.get('content', '')  # No sanitization
    animal_id = data.get('animal_id', None)

    if not content:
        return jsonify({'error': 'Comment cannot be empty.'}), 400

    comment_id = db.execute_returning_id(g.sandbox_id,
        "INSERT INTO comments (user_id, animal_id, content) VALUES (?, ?, ?)",
        [g.current_user['user_id'], animal_id, content])

    return jsonify({'message': 'Comment posted!', 'comment_id': comment_id}), 201


@community_bp.route('/api/contact', methods=['POST'])
def contact_form():
    """
    VULN #4: Blind XSS — message stored raw, renders in admin review panel.
    No authentication required so attacker doesn't need an account.
    """
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '')  # No sanitization!

    if not name or not email or not message:
        return jsonify({'error': 'Name, email, and message are required.'}), 400

    # Store in ALL sandboxes' admin queue (so any logged-in user can see it in their /admin/review)
    from config import Config
    import os
    for sandbox_id in os.listdir(Config.SANDBOX_DIR):
        db_path = os.path.join(Config.SANDBOX_DIR, sandbox_id, 'db.sqlite')
        if os.path.exists(db_path):
            try:
                db.execute(sandbox_id,
                    "INSERT INTO contact_submissions (name, email, subject, message, ip_address) VALUES (?, ?, ?, ?, ?)",
                    [name, email, subject, message, request.remote_addr])
            except:
                pass

    return jsonify({'message': 'Thank you for reaching out! We will get back to you within 24-48 hours.'})
