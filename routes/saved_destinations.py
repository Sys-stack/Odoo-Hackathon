from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import SavedDestination, City

saved_bp = Blueprint("saved_destinations", __name__)


@saved_bp.get("")
@jwt_required()
def list_saved():
    saved = SavedDestination.query.filter_by(user_id=int(get_jwt_identity())).all()
    return jsonify({"saved_destinations": [s.to_dict() for s in saved]})


@saved_bp.post("")
@jwt_required()
def save_destination():
    data = request.get_json(silent=True) or {}
    city_id = data.get("city_id")
    city = City.query.get(city_id)
    if not city:
        return jsonify({"message": "Unknown city_id."}), 400

    user_id = int(get_jwt_identity())
    existing = SavedDestination.query.get((user_id, city_id))
    if existing:
        return jsonify({"saved_destination": existing.to_dict()}), 200

    saved = SavedDestination(user_id=user_id, city_id=city_id)
    db.session.add(saved)
    db.session.commit()
    return jsonify({"saved_destination": saved.to_dict()}), 201


@saved_bp.delete("/<int:city_id>")
@jwt_required()
def unsave_destination(city_id):
    user_id = int(get_jwt_identity())
    saved = SavedDestination.query.get_or_404((user_id, city_id))
    db.session.delete(saved)
    db.session.commit()
    return jsonify({"message": "Removed from saved destinations."})
