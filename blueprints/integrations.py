"""
Integrations Blueprint — Webhook
Vulnerability: SSRF (#11) — blacklist-based URL filtering (bypassable)
"""
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth
from utils.url_fetcher import fetch_url, is_blacklisted

integrations_bp = Blueprint('integrations', __name__)


@integrations_bp.route('/api/integrations/webhook', methods=['POST'])
@require_auth
def test_webhook():
    """
    VULN #11: SSRF — blacklist check is string-based, no DNS resolution.
    Bypass via: decimal IP (2130706433), hex (0x7f000001), IPv6 ([::1]),
    octal (0177.0.0.1), 127.1, or DNS pointing to internal IPs.
    """
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'Webhook URL is required.'}), 400

    if is_blacklisted(url):
        return jsonify({'error': 'URL points to a restricted address. Please use an external URL.'}), 403

    result = fetch_url(url)

    if not result['success']:
        return jsonify({'error': result['error']}), 400

    return jsonify({
        'message': 'Webhook test successful!',
        'response': {
            'status_code': result['status_code'],
            'body': result['body'][:3000],
            'headers': result['headers']
        }
    })
