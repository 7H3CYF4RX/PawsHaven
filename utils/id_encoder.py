"""
Base64 ID Encoder/Decoder for IDOR vulnerability.
IDs follow pattern: {type}_{numeric_id}  →  Base64 encoded
"""
import base64


def encode_id(resource_type, resource_id):
    """Encode resource type + ID to Base64. e.g. 'user_3' → 'dXNlcl8z'"""
    plain = f"{resource_type}_{resource_id}"
    return base64.b64encode(plain.encode()).decode()


def decode_id(encoded):
    """Decode Base64 ID back to (type, numeric_id). e.g. 'dXNlcl8z' → ('user', 3)"""
    try:
        padded = encoded + '=' * (4 - len(encoded) % 4)
        plain = base64.b64decode(padded).decode()
        parts = plain.rsplit('_', 1)
        if len(parts) == 2:
            return parts[0], int(parts[1])
        return None, None
    except Exception:
        return None, None


def encode_simple(value):
    """Simple base64 encode for any value."""
    return base64.b64encode(str(value).encode()).decode()


def decode_simple(encoded):
    """Simple base64 decode."""
    try:
        padded = encoded + '=' * (4 - len(encoded) % 4)
        return base64.b64decode(padded).decode()
    except Exception:
        return None
