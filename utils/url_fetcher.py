"""
URL Fetcher — For SSRF vulnerability.
"""
import requests
from urllib.parse import urlparse

BLACKLISTED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '169.254.169.254']
BLACKLISTED_PREFIXES = ['10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.',
                         '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.',
                         '172.28.', '172.29.', '172.30.', '172.31.', '192.168.']


def is_blacklisted(url):
    """
    VULNERABILITY: String-based blacklist — no DNS resolution!
    Bypassable via: decimal IP (2130706433), hex (0x7f000001), IPv6 ([::1]),
    octal (0177.0.0.1), 127.1, or DNS pointing to 127.0.0.1
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or '').lower()
        if not hostname:
            return True
        if parsed.scheme not in ('http', 'https'):
            return True
        for blocked in BLACKLISTED_HOSTS:
            if hostname == blocked:
                return True
        for prefix in BLACKLISTED_PREFIXES:
            if hostname.startswith(prefix):
                return True
        return False
    except Exception:
        return True


def fetch_url(url, timeout=5):
    """Fetch a URL and return the response."""
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        return {'success': True, 'status_code': resp.status_code, 'body': resp.text,
                'headers': dict(resp.headers), 'url': resp.url}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out.'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Could not connect to the specified URL.'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
