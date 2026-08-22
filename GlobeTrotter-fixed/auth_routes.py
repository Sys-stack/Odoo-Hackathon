import re

from flask import Blueprint, request, jsonify

from setup import db, User
from auth_utils import generate_token, token_required

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not full_name:
        return jsonify({"message": "Full name is required."}), 400

    if not email or not EMAIL_RE.match(email):
        return jsonify({"message": "Enter a valid email address."}), 400

    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters."}), 400

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"message": "That email is already registered."}), 409

    user = User(email=email, full_name=full_name)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = generate_token(user)
    return jsonify({"token": token, "user": user.to_public_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"message": "Invalid email or password."}), 401

    token = generate_token(user)
    return jsonify({"token": token, "user": user.to_public_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def api_me():
    return jsonify({"user": request.current_user.to_public_dict()}), 200


@auth_bp.route("/me", methods=["PUT"])
@token_required
def update_me():
    """Update editable profile fields (Screen 12: User Profile / Settings)."""
    user = request.current_user
    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        full_name = (data.get("full_name") or "").strip()
        if not full_name:
            return jsonify({"message": "Full name cannot be empty."}), 400
        user.full_name = full_name

    if "email" in data:
        email = (data.get("email") or "").strip().lower()
        if not email or not EMAIL_RE.match(email):
            return jsonify({"message": "Enter a valid email address."}), 400
        existing = User.query.filter_by(email=email).first()
        if existing is not None and existing.user_id != user.user_id:
            return jsonify({"message": "That email is already registered."}), 409
        user.email = email

    if "profile_picture_url" in data:
        user.profile_picture_url = (data.get("profile_picture_url") or "").strip() or None

    if "language_preference" in data:
        lang = (data.get("language_preference") or "").strip()
        user.language_preference = lang or "en"

    if "password" in data and data.get("password"):
        if len(data["password"]) < 8:
            return jsonify({"message": "Password must be at least 8 characters."}), 400
        user.set_password(data["password"])

    db.session.commit()
    return jsonify({"user": user.to_public_dict()}), 200


@auth_bp.route("/me", methods=["DELETE"])
@token_required
def delete_me():
    """Delete the current user's account and all owned trips (cascades)."""
    user = request.current_user
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Account deleted."}), 200
