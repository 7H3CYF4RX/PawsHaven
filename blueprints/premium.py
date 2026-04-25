"""
Premium Blueprint — Premium Membership & Theme Customization
Vulnerability: Client-Side Access Control Bypass (#37)
  - Theme toggle buttons are disabled via HTML 'disabled' attribute for non-subscribers.
  - The /api/premium/apply-theme endpoint ONLY checks the 'theme' parameter, not subscription status.
  - An attacker can remove the 'disabled' attribute in DevTools and apply any theme for free.
  - The server trusts the client's ability to click the button, not the subscription state.
"""
from flask import Blueprint, request, jsonify, g, render_template
from middleware.auth_middleware import require_auth, optional_auth
from utils import database as db

premium_bp = Blueprint('premium', __name__)

VALID_THEMES = ['default', 'dark', 'galaxy']


@premium_bp.route('/premium')
@optional_auth
def premium_page():
    """Render the premium membership page."""
    return render_template('premium/index.html', user=g.current_user)


@premium_bp.route('/api/premium/subscribe', methods=['POST'])
@require_auth
def subscribe():
    """
    Process premium membership purchase.
    VULN #37 (partial): No payment gateway validation — card details are accepted as-is.
    REVISION: This feature is intentionally disabled to force users to find the bypass.
    """
    return jsonify({
        'success': False,
        'error': 'This Feature is Currently Not available for you'
    }), 403


@premium_bp.route('/api/premium/apply-theme', methods=['POST'])
@require_auth
def apply_theme():
    """
    VULN #37: Client-Side Access Control Bypass.
    This endpoint applies a colour theme but NEVER checks if the user is_premium.
    The only restriction is the disabled HTML button on the frontend.
    An attacker can:
      1. Open DevTools → Inspector
      2. Find the theme button and remove the 'disabled' attribute
      3. Click the button — it calls this endpoint which happily applies the theme
    The server-side check is completely missing — the 'lock' only exists in the DOM.
    """
    data = request.get_json()
    theme = data.get('theme', '').strip().lower()

    if theme not in VALID_THEMES:
        return jsonify({'error': 'Invalid theme selected.'}), 400

    user_id = g.current_user.get('user_id')
    sandbox_id = g.sandbox_id

    # VULN: No premium check here! Anyone who reaches this endpoint can apply themes.
    # The only guard is the disabled attribute on the button in the HTML.
    try:
        db.execute(sandbox_id,
            "UPDATE users SET active_theme = ? WHERE id = ?",
            [theme, user_id]
        )
    except Exception:
        pass  # Column might not exist; theme is stored in cookie as fallback

    return jsonify({
        'success': True,
        'theme': theme,
        'message': f'Theme "{theme}" applied successfully!'
    })


@premium_bp.route('/api/premium/status', methods=['GET'])
@require_auth
def premium_status():
    """Returns the current user's premium subscription status."""
    user_id = g.current_user.get('user_id')
    sandbox_id = g.sandbox_id

    user = db.query_one(sandbox_id, "SELECT is_premium, active_theme FROM users WHERE id = ?", [user_id])
    is_premium = bool(user.get('is_premium', 0)) if user else False
    active_theme = user.get('active_theme', 'default') if user else 'default'

    return jsonify({
        'is_premium': is_premium,
        'active_theme': active_theme or 'default'
    })
