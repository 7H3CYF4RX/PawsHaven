"""
Users Blueprint — Profile management
Vulnerabilities: IDOR (#6), Method tampering/DELETE (#1), Mass assignment (#16), Info disclosure (#9)
"""
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth
from utils.id_encoder import encode_id, decode_id
from utils import database as db

users_bp = Blueprint('users', __name__)


@users_bp.route('/api/users/me', methods=['GET'])
@require_auth
def get_profile():
    """
    VULN #9: Info disclosure — returns too many fields including password_hash.
    """
    user = db.query_one(g.sandbox_id, "SELECT * FROM users WHERE id = ?", [g.current_user['user_id']])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # VULN: Returns ALL fields including sensitive ones
    user['encoded_id'] = encode_id('user', user['id'])
    return jsonify({'user': user})


@users_bp.route('/api/users/me', methods=['PUT'])
@require_auth
def update_profile():
    """
    VULN #16: Mass assignment — blindly updates ALL fields from request body.
    An attacker can add 'role': 'admin' to escalate privileges.
    """
    data = request.get_json()
    user_id = g.current_user['user_id']

    # VULN: No whitelist — ANY field can be updated including 'role'
    for key, value in data.items():
        if key in ('id', 'sandbox_id', 'created_at'):
            continue  # Skip these but allow 'role', 'password_hash', etc.
        try:
            db.execute(g.sandbox_id, f"UPDATE users SET {key} = ? WHERE id = ?", [value, user_id])
        except Exception:
            pass

    user = db.query_one(g.sandbox_id, "SELECT * FROM users WHERE id = ?", [user_id])
    return jsonify({'message': 'Profile updated successfully.', 'user': user})


@users_bp.route('/api/users/<encoded_id>', methods=['GET', 'DELETE'])
@require_auth
def user_by_id(encoded_id):
    """
    VULN #6: IDOR — Base64 encoded IDs can be decoded and incremented.
    VULN #1: Method tampering — GET shows profile, DELETE deletes user without authorization check.
    """
    res_type, res_id = decode_id(encoded_id)
    if res_type != 'user' or res_id is None:
        return jsonify({'error': 'Invalid user ID format.'}), 400

    if request.method == 'DELETE':
        data = request.get_json() or {}
        otp = data.get('otp', '')

        if not otp:
            return jsonify({'error': 'Verification code (OTP) is required to delete account.'}), 400

        # Verify OTP
        # VULN: It checks the OTP against the CURRENT LOGGED IN user, not the target being deleted!
        # An attacker can request an OTP for themselves and use it to delete anyone else (BOLA).
        user = db.query_one(g.sandbox_id, "SELECT id, otp_code FROM users WHERE id = ?", [g.current_user['user_id']])
        if not user or user['otp_code'] != otp:
            return jsonify({'error': 'Invalid or expired verification code.'}), 401

        # VULN: No authorization check! (BOLA)
        db.execute(g.sandbox_id, "DELETE FROM users WHERE id = ?", [res_id])
        return jsonify({'message': 'User account has been deleted.'})

    # GET — return user profile
    user = db.query_one(g.sandbox_id, "SELECT * FROM users WHERE id = ?", [res_id])
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    user['encoded_id'] = encode_id('user', user['id'])
    return jsonify({'user': user})
