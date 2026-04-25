"""
Newsletter Blueprint
Vulnerability: SSTI (#15) — Jinja2 template injection via render_template_string
"""
from flask import Blueprint, request, jsonify, g, render_template_string
from middleware.auth_middleware import optional_auth
from utils import database as db

newsletter_bp = Blueprint('newsletter', __name__)


@newsletter_bp.route('/api/newsletter/subscribe', methods=['POST'])
@optional_auth
def subscribe():
    """
    VULN #15: SSTI — User input (name) injected directly into Jinja2 template string.
    Payload: name={{7*7}} → returns "Welcome to PawsHaven, 49!"
    RCE: name={{config.__class__.__init__.__globals__['os'].popen('id').read()}}
    """
    data = request.get_json()
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()

    if not email:
        return jsonify({'error': 'Email is required.'}), 400

    # VULN: User input directly in Jinja2 template string!
    try:
        welcome = render_template_string(
            f"""<div class="welcome-msg">
                <h3>Welcome to PawsHaven, {name}! 🐾</h3>
                <p>We'll send rescue updates and adoption stories to <strong>{email}</strong>.</p>
                <p>Thank you for being part of our community!</p>
            </div>"""
        )
    except Exception as e:
        welcome = f'<div class="welcome-msg"><h3>Welcome! Error in template: {str(e)}</h3></div>'

    # Store subscription
    if g.current_user and g.sandbox_id:
        db.execute(g.sandbox_id,
            "INSERT INTO newsletter (email, name, template) VALUES (?, ?, ?)",
            [email, name, ''])

    return jsonify({'message': 'Subscribed successfully!', 'welcome_html': welcome})
