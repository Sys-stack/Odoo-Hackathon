from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, current_app

from setup import User


def generate_token(user):
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "role": user.role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=current_app.config["JWT_EXP_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def token_required(f):
    """Decorator for routes that require a valid Bearer token.
    Attaches the authenticated User to `request.current_user`.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Missing or invalid Authorization header."}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Session expired. Please sign in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid authentication token."}), 401

        user = User.query.get(payload.get("sub"))
        if user is None:
            return jsonify({"message": "User no longer exists."}), 401

        request.current_user = user
        return f(*args, **kwargs)

    return wrapper
