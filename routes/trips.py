from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Trip, Stop, City
from utils.validation import parse_date

trips_bp = Blueprint("trips", __name__)


def _current_user_id():
    return int(get_jwt_identity())


@trips_bp.get("")
@jwt_required()
def list_trips():
    trips = (
        Trip.query.filter_by(user_id=_current_user_id())
        .order_by(Trip.start_date.desc())
        .all()
    )
    return jsonify({"trips": [t.to_dict() for t in trips]})


@trips_bp.post("")
@jwt_required()
def create_trip():
    """
    Screen 4 'Create a new Trip'.
    Body: {
      trip_name, description?, start_date, end_date, total_budget?, is_public?,
      stops?: [{ city_id, arrival_date, departure_date }]
    }
    """
    data = request.get_json(silent=True) or {}

    trip_name = (data.get("trip_name") or "").strip()
    if not trip_name:
        return jsonify({"message": "Trip name is required."}), 400

    try:
        start_date = parse_date(data.get("start_date"), "Start date")
        end_date = parse_date(data.get("end_date"), "End date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if end_date < start_date:
        return jsonify({"message": "End date cannot be before start date."}), 400

    trip = Trip(
        user_id=_current_user_id(),
        trip_name=trip_name,
        description=data.get("description"),
        start_date=start_date,
        end_date=end_date,
        total_budget=data.get("total_budget"),
        is_public=bool(data.get("is_public", False)),
    )

    # Optional: allow creating stops inline when the trip is created
    stops_payload = data.get("stops") or []
    for i, stop_data in enumerate(stops_payload):
        city = City.query.get(stop_data.get("city_id"))
        if not city:
            return jsonify({"message": f"Stop {i + 1}: unknown city_id."}), 400
        try:
            arrival = parse_date(stop_data.get("arrival_date"), f"Stop {i + 1} arrival date")
            departure = parse_date(stop_data.get("departure_date"), f"Stop {i + 1} departure date")
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

        trip.stops.append(
            Stop(
                city_id=city.city_id,
                sequence_order=i + 1,
                arrival_date=arrival,
                departure_date=departure,
            )
        )

    db.session.add(trip)
    db.session.commit()

    return jsonify({"trip": trip.to_dict(include_stops=True)}), 201


@trips_bp.get("/<int:trip_id>")
@jwt_required()
def get_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != _current_user_id() and not trip.is_public:
        return jsonify({"message": "You don't have access to this trip."}), 403
    return jsonify({"trip": trip.to_dict(include_stops=True)})


@trips_bp.put("/<int:trip_id>")
@jwt_required()
def update_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != _current_user_id():
        return jsonify({"message": "You don't have access to this trip."}), 403

    data = request.get_json(silent=True) or {}

    if "trip_name" in data:
        if not data["trip_name"].strip():
            return jsonify({"message": "Trip name cannot be empty."}), 400
        trip.trip_name = data["trip_name"].strip()

    if "description" in data:
        trip.description = data["description"]

    if "start_date" in data:
        try:
            trip.start_date = parse_date(data["start_date"], "Start date")
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    if "end_date" in data:
        try:
            trip.end_date = parse_date(data["end_date"], "End date")
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    if trip.end_date < trip.start_date:
        return jsonify({"message": "End date cannot be before start date."}), 400

    if "total_budget" in data:
        trip.total_budget = data["total_budget"]
    if "is_public" in data:
        trip.is_public = bool(data["is_public"])
    if "cover_photo_url" in data:
        trip.cover_photo_url = data["cover_photo_url"]

    db.session.commit()
    return jsonify({"trip": trip.to_dict(include_stops=True)})


@trips_bp.delete("/<int:trip_id>")
@jwt_required()
def delete_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != _current_user_id():
        return jsonify({"message": "You don't have access to this trip."}), 403
    db.session.delete(trip)
    db.session.commit()
    return jsonify({"message": "Trip deleted."})


@trips_bp.post("/<int:trip_id>/share")
@jwt_required()
def create_share_link(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != _current_user_id():
        return jsonify({"message": "You don't have access to this trip."}), 403
    trip.is_public = True
    token = trip.generate_shareable_token()
    db.session.commit()
    return jsonify({"shareable_token": token})


@trips_bp.post("/<int:trip_id>/stops")
@jwt_required()
def add_stop(trip_id):
    """Add a stop to an existing trip (used by the 'Select a Place' row on Screen 4)."""
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != _current_user_id():
        return jsonify({"message": "You don't have access to this trip."}), 403

    data = request.get_json(silent=True) or {}
    city = City.query.get(data.get("city_id"))
    if not city:
        return jsonify({"message": "Select a valid place."}), 400

    try:
        arrival = parse_date(data.get("arrival_date"), "Start date")
        departure = parse_date(data.get("departure_date"), "End date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if departure < arrival:
        return jsonify({"message": "End date cannot be before start date."}), 400

    next_order = (max([s.sequence_order for s in trip.stops], default=0)) + 1
    stop = Stop(
        trip_id=trip.trip_id,
        city_id=city.city_id,
        sequence_order=next_order,
        arrival_date=arrival,
        departure_date=departure,
    )
    db.session.add(stop)
    db.session.commit()

    return jsonify({"stop": stop.to_dict()}), 201
