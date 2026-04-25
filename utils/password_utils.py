"""
Password Utilities — Intentionally uses MD5 (insecure).
"""
import hashlib


def hash_password(password):
    """
    VULNERABILITY: Uses MD5 — fast, unsalted, easily crackable.
    Real apps should use bcrypt/scrypt/argon2 with salt.
    """
    return hashlib.md5(password.encode()).hexdigest()


def check_password(password, stored_hash):
    """Check a password against stored MD5 hash."""
    return hashlib.md5(password.encode()).hexdigest() == stored_hash
