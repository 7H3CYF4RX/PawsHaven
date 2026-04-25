"""
JWT Handler — Intentionally vulnerable to alg:none attack.
"""
import jwt
import json
import base64
from datetime import datetime, timedelta
from config import Config


def create_token(user_data):
    """Create a signed JWT token."""
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'role': user_data.get('role', 'user'),
        'sandbox_id': user_data.get('sandbox_id', ''),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)


def verify_token(token):
    """
    Verify a JWT token.
    
    VULNERABILITY: Accepts tokens with alg: "none"!
    If the header specifies algorithm "none", signature verification is skipped entirely.
    An attacker can forge any payload (e.g., change role to "admin") and it will be accepted.
    """
    if not token:
        return None

    try:
        # Decode header to check algorithm
        parts = token.split('.')
        if len(parts) < 2:
            return None

        # Pad base64 if needed
        header_b64 = parts[0] + '=' * (4 - len(parts[0]) % 4)
        header = json.loads(base64.b64decode(header_b64))

        alg = header.get('alg', '').lower()

        if alg in ('none', 'NONE', 'None', 'nOnE'):
            # VULN: Skip signature verification for alg:none!
            # Use base64.urlsafe_b64decode and handle padding properly
            payload_b64 = parts[1]
            missing_padding = len(payload_b64) % 4
            if missing_padding:
                payload_b64 += '=' * (4 - missing_padding)
            
            payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
            return payload

        # Normal verification
        return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])

    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None
