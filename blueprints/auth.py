"""
Auth Blueprint — Registration, Login, Password Reset
Vulnerabilities: Weak password policy (#8), JWT alg:none (#21), 
Host header injection (#26), Predictable reset token (#29), Missing rate limit (#18)
"""
import time
import base64
import os
import random
from flask import Blueprint, request, jsonify, render_template, make_response
from utils.password_utils import hash_password, check_password
from utils.jwt_handler import create_token
from utils.sandbox_manager import create_sandbox
from utils import database as db
from config import Config
from utils.email_manager import send_real_email
from middleware.auth_middleware import require_auth
from flask import g

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """
    VULN #8: Weak password policy — accepts any password including '1' or '123456'.
    No complexity requirements at all.
    """
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400

    if len(password) < 1:
        return jsonify({'error': 'Password cannot be empty.'}), 400

    if email.lower() in ['admin@pawshaven.org', 'hello@pawshaven.org']:
        return jsonify({'error': 'account already exist with that email'}), 400

    for sandbox_id in os.listdir(Config.SANDBOX_DIR):
        sandbox_path = os.path.join(Config.SANDBOX_DIR, sandbox_id, 'db.sqlite')
        if not os.path.exists(sandbox_path):
            continue
        existing = db.query_one(sandbox_id, "SELECT id FROM users WHERE email = ?", [email])
        if existing:
            return jsonify({'error': 'account already exist with that email'}), 400

    pw_hash = hash_password(password)

    # Create sandbox for this user
    user_data = {'name': name, 'email': email, 'password_hash': pw_hash}
    try:
        sandbox_id = create_sandbox(user_data)
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

    # Get the created user from sandbox DB
    user = db.query_one(sandbox_id, "SELECT * FROM users WHERE email = ?", [email])
    if not user:
        return jsonify({'error': 'Registration failed.'}), 500

    # Create JWT
    token = create_token(user)

    # Send Welcome Email
    welcome_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9fafb; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #059669; margin: 0; font-size: 24px;">🐾 PawsHaven</h1>
        </div>
        <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h2 style="margin-top: 0; color: #111827; font-size: 20px;">Welcome, {user['name']}!</h2>
            <p style="color: #4b5563; font-size: 16px; line-height: 1.5;">
                Thank you for joining PawsHaven. We're thrilled to have you in our community!
            </p>
        </div>
    </div>
    """
    send_real_email(
        to_email=user['email'],
        subject="🐾 Welcome to PawsHaven!",
        body_html=welcome_html,
        sandbox_id=sandbox_id
    )

    resp = jsonify({
        'message': 'Account created successfully! Welcome to PawsHaven.',
        'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']}
    })
    resp.set_cookie('token', token, httponly=False, samesite='Lax', max_age=86400)
    return resp, 201


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    VULN #18: No rate limiting — can be brute-forced indefinitely.
    VULN #21: JWT alg:none accepted (in jwt_handler.py).
    """
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    # Search all sandboxes for this email
    from config import Config
    import os
    for sandbox_id in os.listdir(Config.SANDBOX_DIR):
        sandbox_path = os.path.join(Config.SANDBOX_DIR, sandbox_id, 'db.sqlite')
        if not os.path.exists(sandbox_path):
            continue

        user = db.query_one(sandbox_id, "SELECT * FROM users WHERE email = ?", [email])
        if user and check_password(password, user['password_hash']):
            token = create_token(user)
            uses_2fa = bool(user.get('two_factor_enabled', 0))

            if uses_2fa:
                otp = str(random.randint(100000, 999999))
                db.execute(sandbox_id, "UPDATE users SET otp_code = ? WHERE id = ?", [otp, user['id']])
                
                html_body = f"""
                <div style="font-family:Arial; padding:20px;">
                    <h2 style="color:#059669;">Your PawsHaven Security Code</h2>
                    <p>Use the following 6-digit code to complete your login:</p>
                    <h1 style="letter-spacing:5px; background:#f3f4f6; padding:10px; display:inline-block; border-radius:5px;">{otp}</h1>
                    <p><small>If you did not attempt to sign in, please ignore this.</small></p>
                </div>
                """
                send_real_email(user['email'], "PawsHaven 2FA Code", html_body, sandbox_id=sandbox_id)

                return jsonify({
                    'message': 'Please enter your 2FA OTP sent to your email.',
                    'requires_2fa': True,
                    'token': token  # VULN: The token is sent to the client even before 2FA verification!
                })
            else:
                resp = jsonify({
                    'message': 'Login successful!',
                    'requires_2fa': False,
                    'token': token,
                    'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']}
                })
                # Set cookie server-side for standard login, though the UI will set it manually if 2FA response is manipulated
                resp.set_cookie('token', token, httponly=False, samesite='Lax', max_age=86400)
                return resp

    return jsonify({'error': 'Invalid email or password. Please try again.'}), 401


@auth_bp.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email', '')
    otp = data.get('otp', '')

    for sandbox_id in os.listdir(Config.SANDBOX_DIR):
        sandbox_path = os.path.join(Config.SANDBOX_DIR, sandbox_id, 'db.sqlite')
        if not os.path.exists(sandbox_path):
            continue
        user = db.query_one(sandbox_id, "SELECT * FROM users WHERE email = ? AND otp_code = ?", [email, otp])
        if user:
            # Clear OTP after use
            db.execute(sandbox_id, "UPDATE users SET otp_code = '' WHERE id = ?", [user['id']])
            return jsonify({'success': True, 'message': 'OTP verification successful.'})

    return jsonify({'error': 'Invalid 2FA code.'}), 401

@auth_bp.route('/api/auth/request-otp', methods=['POST'])
@require_auth
def request_otp():
    """
    Requested dynamically by the frontend when a user wants to execute a sensitive action (like disabling 2FA).
    """
    user_id = g.current_user.get('user_id')
    user_email = g.current_user.get('email')
    sandbox_id = g.sandbox_id

    otp = str(random.randint(100000, 999999))
    db.execute(sandbox_id, "UPDATE users SET otp_code = ? WHERE id = ?", [otp, user_id])

    html_body = f"""
    <div style="font-family: Arial, sans-serif; text-align: center; color: #333;">
        <h2>Action Verification</h2>
        <p>You have requested a verification code to authorize a sensitive account action.</p>
        <h1 style="background: #f4f4f4; padding: 15px; border-radius: 8px; letter-spacing: 5px; color: #007bff;">{otp}</h1>
        <p><small>If you did not request this, please ignore this email.</small></p>
    </div>
    """
    send_real_email(user_email, "PawsHaven Auth Request", html_body, sandbox_id=sandbox_id)

    return jsonify({'success': True, 'message': 'OTP sent successfully'})


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    VULN #26: Host header injection — uses Host header in reset link.
    VULN #29: Predictable reset token — based on user_id + timestamp.
    """
    data = request.get_json()
    email = data.get('email', '').strip()

    # VULN: Uses Host header to build reset link
    host = request.headers.get('Host', 'localhost:5000')

    for sandbox_id in os.listdir(Config.SANDBOX_DIR):
        sandbox_path = os.path.join(Config.SANDBOX_DIR, sandbox_id, 'db.sqlite')
        if not os.path.exists(sandbox_path):
            continue
        user = db.query_one(sandbox_id, "SELECT * FROM users WHERE email = ?", [email])
        if user:
            # VULN: Predictable token = base64(user_id_timestamp)
            timestamp = int(time.time())
            raw_token = f"{user['id']}_{timestamp}"
            token = base64.b64encode(raw_token.encode()).decode()

            db.execute(sandbox_id,
                "INSERT INTO password_reset_tokens (user_id, token) VALUES (?, ?)",
                [user['id'], token])

            reset_link = f"http://{host}/reset-password?token={token}"

            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9fafb; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h1 style="color: #059669; margin: 0; font-size: 24px;">🐾 PawsHaven</h1>
                </div>
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h2 style="margin-top: 0; color: #111827; font-size: 20px;">Password Reset Request</h2>
                    <p style="color: #4b5563; font-size: 16px; line-height: 1.5;">
                        We received a request to reset the password for your PawsHaven account. If you made this request, please click the button below to securely set a new password:
                    </p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #059669; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Reset My Password</a>
                    </div>
                    <p style="color: #6b7280; font-size: 14px; line-height: 1.5;">
                        <strong style="color:#d97706;">Security Token:</strong> <code style="background:#f3f4f6; padding: 2px 6px; border-radius: 4px;">{token}</code>
                    </p>
                    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                    <p style="color: #9ca3af; font-size: 12px; margin: 0; text-align: center;">
                        If you did not request a password reset, you can safely ignore this email. Your password will not be changed.
                    </p>
                </div>
            </div>
            """
            
            send_real_email(
                to_email=email,
                subject="🔑 PawsHaven Password Reset Link",
                body_html=html_body,
                sandbox_id=sandbox_id
            )

            return jsonify({
                'message': 'If an account exists with that email, a password reset link has been sent.'
            })

    return jsonify({'message': 'If an account exists with that email, a password reset link has been sent.'})


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token."""
    data = request.get_json()
    token = data.get('token', '')
    new_password = data.get('password', '')

    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required.'}), 400

    from config import Config
    import os
    for sandbox_id in os.listdir(Config.SANDBOX_DIR):
        sandbox_path = os.path.join(Config.SANDBOX_DIR, sandbox_id, 'db.sqlite')
        if not os.path.exists(sandbox_path):
            continue
        reset = db.query_one(sandbox_id,
            "SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0", [token])
        if reset:
            pw_hash = hash_password(new_password)
            db.execute(sandbox_id, "UPDATE users SET password_hash = ? WHERE id = ?",
                      [pw_hash, reset['user_id']])
            db.execute(sandbox_id, "UPDATE password_reset_tokens SET used = 1 WHERE id = ?",
                      [reset['id']])
            return jsonify({'message': 'Password has been reset successfully.'})

    return jsonify({'error': 'Invalid or expired reset token.'}), 400


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    resp = jsonify({'message': 'Logged out successfully.'})
    resp.delete_cookie('token')
    return resp
