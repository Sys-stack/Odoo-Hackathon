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
