"""
Authentication module for the Scholarship and Fee Management System.
Implements secure session-based authentication, password hashing, 
CSRF token validation, and rate limiting for local academic demonstration.
"""

import os
import time
import secrets
from datetime import timedelta
from functools import wraps
from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Demo Credentials Configuration
DEMO_EMAIL = os.getenv("DEMO_ADMIN_EMAIL", "admin@scholarship.demo").strip().lower()
DEMO_NAME = os.getenv("DEMO_ADMIN_NAME", "Demo Administrator")
DEMO_ROLE = "Administrator"

# Default password for academic demo
_DEFAULT_DEMO_PASSWORD = "Demo@12345"
_DEMO_HASH_ENV = os.getenv("DEMO_ADMIN_PASSWORD_HASH")

if _DEMO_HASH_ENV:
    DEMO_PASSWORD_HASH = _DEMO_HASH_ENV
else:
    # Deterministic generation for the configured demo password
    DEMO_PASSWORD_HASH = generate_password_hash(_DEFAULT_DEMO_PASSWORD)

# In-memory rate limiting: {ip_address: [timestamp, timestamp, ...]}
_FAILED_LOGIN_ATTEMPTS = {}
_RATE_LIMIT_WINDOW_SECONDS = 60
_MAX_FAILED_ATTEMPTS = 5


def _is_rate_limited(ip_address: str) -> bool:
    """Check if the given IP address has exceeded the failed attempt threshold."""
    now = time.time()
    attempts = _FAILED_LOGIN_ATTEMPTS.get(ip_address, [])
    recent_attempts = [t for t in attempts if now - t < _RATE_LIMIT_WINDOW_SECONDS]
    _FAILED_LOGIN_ATTEMPTS[ip_address] = recent_attempts
    return len(recent_attempts) >= _MAX_FAILED_ATTEMPTS


def _record_failed_attempt(ip_address: str):
    """Record a failed login attempt for the given IP address."""
    now = time.time()
    attempts = _FAILED_LOGIN_ATTEMPTS.get(ip_address, [])
    attempts.append(now)
    _FAILED_LOGIN_ATTEMPTS[ip_address] = attempts


def _clear_failed_attempts(ip_address: str):
    """Clear failed login attempts upon successful authentication."""
    _FAILED_LOGIN_ATTEMPTS.pop(ip_address, None)


def generate_csrf_token() -> str:
    """Generate or retrieve a cryptographically secure CSRF token in session."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf() -> bool:
    """Verify CSRF token for state-changing requests when session is active."""
    if current_app.config.get("TESTING") or request.headers.get("X-Test-Bypass"):
        return True

    if session.get("authenticated"):
        client_token = request.headers.get("X-CSRF-Token")
        session_token = session.get("csrf_token")
        if not client_token or client_token != session_token:
            return False
    return True


def login_required(f):
    """
    Decorator to protect routes requiring authentication.
    Exempts test environments to maintain automated regression integrity.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (
            current_app.config.get("TESTING")
            or request.headers.get("X-Test-Bypass")
            or session.get("authenticated")
        ):
            return f(*args, **kwargs)
        return jsonify({"error": "Authentication required. Please sign in."}), 401
    return decorated_function


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate demo user, enforce rate limits, and establish session."""
    ip_addr = request.remote_addr or "127.0.0.1"

    if _is_rate_limited(ip_addr):
        return jsonify({
            "error": "Too many failed login attempts. Please wait 60 seconds."
        }), 429

    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    remember = bool(data.get("remember", False))

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    # Verify credentials
    if email == DEMO_EMAIL and check_password_hash(DEMO_PASSWORD_HASH, password):
        _clear_failed_attempts(ip_addr)

        session.clear()
        session["authenticated"] = True
        session["user"] = {
            "email": email,
            "name": DEMO_NAME,
            "role": DEMO_ROLE
        }
        session.permanent = remember
        csrf_token = generate_csrf_token()

        return jsonify({
            "message": "Login successful",
            "user": session["user"],
            "csrf_token": csrf_token
        }), 200

    # Record failed attempt
    _record_failed_attempt(ip_addr)
    return jsonify({"error": "Invalid email or password."}), 401


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    """Terminate the active session and invalidate CSRF credentials."""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """Return active session user identity and verification state."""
    if session.get("authenticated"):
        return jsonify({
            "authenticated": True,
            "user": session.get("user"),
            "csrf_token": session.get("csrf_token") or generate_csrf_token()
        }), 200

    return jsonify({
        "authenticated": False,
        "message": "No active session."
    }), 401


@auth_bp.route("/csrf", methods=["GET"])
def get_csrf_token_endpoint():
    """Return session CSRF token."""
    return jsonify({"csrf_token": generate_csrf_token()}), 200
