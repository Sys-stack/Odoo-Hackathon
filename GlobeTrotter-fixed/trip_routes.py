from datetime import datetime

from flask import Blueprint, request, jsonify

from setup import db, Trip, Stop, ItineraryActivity, City, Activity
from auth_utils import token_required

trips_bp = Blueprint("trips", __name__, url_prefix="/api")


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------
def parse_date(value, field_name):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid date (YYYY-MM-DD).")


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise ValueError("start_time must be in HH:MM format.")


def get_owned_trip(trip_id, user):
    trip = Trip.query.get(trip_id)
    if trip is None:
        return None, (jsonify({"message": "Trip not found."}), 404)
    if trip.user_id != user.user_id:
        return None, (jsonify({"message": "You don't have access to this trip."}), 403)
    return trip, None


def get_owned_stop(stop_id, user):
    stop = Stop.query.get(stop_id)
    if stop is None:
        return None, (jsonify({"message": "Stop not found."}), 404)
    if stop.trip.user_id != user.user_id:
        return None, (jsonify({"message": "You don't have access to this stop."}), 403)
    return stop, None


# ---------------------------------------------------------------------
# Trips
# ---------------------------------------------------------------------
@trips_bp.route("/trips", methods=["GET"])
@token_required
def list_trips():
    trips = (
        Trip.query.filter_by(user_id=request.current_user.user_id)
        .order_by(Trip.start_date.asc())
        .all()
    )
    return jsonify({"trips": [t.to_summary_dict() for t in trips]}), 200


@trips_bp.route("/trips", methods=["POST"])
@token_required
def create_trip():
    data = request.get_json(silent=True) or {}

    trip_name = (data.get("trip_name") or "").strip()
    description = (data.get("description") or "").strip()
    cover_photo_url = (data.get("cover_photo_url") or "").strip() or None

    if not trip_name:
        return jsonify({"message": "Trip name is required."}), 400

    try:
        start_date = parse_date(data.get("start_date"), "start_date")
        end_date = parse_date(data.get("end_date"), "end_date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if end_date < start_date:
        return jsonify({"message": "End date must be on or after the start date."}), 400

    total_budget = data.get("total_budget")
    if total_budget is not None:
        try:
            total_budget = float(total_budget)
        except (TypeError, ValueError):
            return jsonify({"message": "total_budget must be a number."}), 400

    trip = Trip(
        user_id=request.current_user.user_id,
        trip_name=trip_name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        cover_photo_url=cover_photo_url,
        total_budget=total_budget,
    )
    db.session.add(trip)
    db.session.commit()

    return jsonify({"trip": trip.to_full_dict()}), 201


@trips_bp.route("/trips/<int:trip_id>", methods=["GET"])
@token_required
def get_trip(trip_id):
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err
    return jsonify({"trip": trip.to_full_dict()}), 200


@trips_bp.route("/trips/<int:trip_id>", methods=["PUT"])
@token_required
def update_trip(trip_id):
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}

    if "trip_name" in data:
        trip_name = (data.get("trip_name") or "").strip()
        if not trip_name:
            return jsonify({"message": "Trip name cannot be empty."}), 400
        trip.trip_name = trip_name

    if "description" in data:
        trip.description = (data.get("description") or "").strip()

    if "cover_photo_url" in data:
        trip.cover_photo_url = (data.get("cover_photo_url") or "").strip() or None

    try:
        if "start_date" in data:
            trip.start_date = parse_date(data.get("start_date"), "start_date")
        if "end_date" in data:
            trip.end_date = parse_date(data.get("end_date"), "end_date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if trip.end_date < trip.start_date:
        return jsonify({"message": "End date must be on or after the start date."}), 400

    if "is_public" in data:
        trip.is_public = bool(data.get("is_public"))

    if "total_budget" in data:
        raw = data.get("total_budget")
        if raw in (None, ""):
            trip.total_budget = None
        else:
            try:
                trip.total_budget = float(raw)
            except (TypeError, ValueError):
                return jsonify({"message": "total_budget must be a number."}), 400

    db.session.commit()
    return jsonify({"trip": trip.to_full_dict()}), 200


@trips_bp.route("/trips/<int:trip_id>", methods=["DELETE"])
@token_required
def delete_trip(trip_id):
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err

    db.session.delete(trip)
    db.session.commit()
    return jsonify({"message": "Trip deleted."}), 200


# ---------------------------------------------------------------------
# Stops
# ---------------------------------------------------------------------
@trips_bp.route("/trips/<int:trip_id>/stops", methods=["POST"])
@token_required
def add_stop(trip_id):
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    city_id = data.get("city_id")

    if not city_id or City.query.get(city_id) is None:
        return jsonify({"message": "A valid city_id is required."}), 400

    try:
        arrival_date = parse_date(data.get("arrival_date"), "arrival_date")
        departure_date = parse_date(data.get("departure_date"), "departure_date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if departure_date < arrival_date:
        return jsonify({"message": "Departure date must be on or after arrival."}), 400

    next_order = max([s.sequence_order for s in trip.stops], default=0) + 1

    stop = Stop(
        trip_id=trip.trip_id,
        city_id=city_id,
        sequence_order=next_order,
        arrival_date=arrival_date,
        departure_date=departure_date,
    )
    db.session.add(stop)
    db.session.commit()

    return jsonify({"stop": stop.to_dict()}), 201


@trips_bp.route("/stops/<int:stop_id>", methods=["PUT"])
@token_required
def update_stop(stop_id):
    stop, err = get_owned_stop(stop_id, request.current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}

    try:
        if "arrival_date" in data:
            stop.arrival_date = parse_date(data.get("arrival_date"), "arrival_date")
        if "departure_date" in data:
            stop.departure_date = parse_date(data.get("departure_date"), "departure_date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if stop.departure_date < stop.arrival_date:
        return jsonify({"message": "Departure date must be on or after arrival."}), 400

    if "sequence_order" in data:
        try:
            stop.sequence_order = int(data.get("sequence_order"))
        except (TypeError, ValueError):
            return jsonify({"message": "sequence_order must be an integer."}), 400

    db.session.commit()
    return jsonify({"stop": stop.to_dict()}), 200


@trips_bp.route("/stops/<int:stop_id>/reorder", methods=["POST"])
@token_required
def reorder_stop(stop_id):
    """Swap this stop's sequence_order with the stop in the given direction."""
    stop, err = get_owned_stop(stop_id, request.current_user)
    if err:
        return err

    direction = (request.get_json(silent=True) or {}).get("direction")
    siblings = sorted(stop.trip.stops, key=lambda s: s.sequence_order)
    idx = next((i for i, s in enumerate(siblings) if s.stop_id == stop.stop_id), None)

    if direction == "up" and idx is not None and idx > 0:
        other = siblings[idx - 1]
    elif direction == "down" and idx is not None and idx < len(siblings) - 1:
        other = siblings[idx + 1]
    else:
        return jsonify({"stops": [s.to_dict() for s in siblings]}), 200

    stop.sequence_order, other.sequence_order = other.sequence_order, stop.sequence_order
    db.session.commit()

    siblings = sorted(stop.trip.stops, key=lambda s: s.sequence_order)
    return jsonify({"stops": [s.to_dict() for s in siblings]}), 200


@trips_bp.route("/stops/<int:stop_id>", methods=["DELETE"])
@token_required
def delete_stop(stop_id):
    stop, err = get_owned_stop(stop_id, request.current_user)
    if err:
        return err

    db.session.delete(stop)
    db.session.commit()
    return jsonify({"message": "Stop removed."}), 200


# ---------------------------------------------------------------------
# Itinerary activities
# ---------------------------------------------------------------------
@trips_bp.route("/stops/<int:stop_id>/activities", methods=["POST"])
@token_required
def add_itinerary_activity(stop_id):
    stop, err = get_owned_stop(stop_id, request.current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    activity_id = data.get("activity_id")
    custom_title = (data.get("custom_title") or "").strip() or None
    cost = data.get("cost")

    if not activity_id and not custom_title:
        return jsonify({"message": "Provide either activity_id or custom_title."}), 400

    if activity_id:
        catalog_activity = Activity.query.get(activity_id)
        if catalog_activity is None:
            return jsonify({"message": "Activity not found."}), 400
        if cost is None:
            cost = catalog_activity.estimated_cost

    try:
        scheduled_date = parse_date(data.get("scheduled_date"), "scheduled_date")
        start_time = parse_time(data.get("start_time"))
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if scheduled_date < stop.arrival_date or scheduled_date > stop.departure_date:
        return jsonify({"message": "Activity date must fall within the stop's dates."}), 400

    next_order = max(
        [a.display_order or 0 for a in stop.itinerary_activities], default=0
    ) + 1

    ia = ItineraryActivity(
        stop_id=stop.stop_id,
        activity_id=activity_id,
        custom_title=custom_title,
        scheduled_date=scheduled_date,
        start_time=start_time,
        cost=cost or 0.0,
        display_order=next_order,
    )
    db.session.add(ia)
    db.session.commit()

    return jsonify({"activity": ia.to_dict()}), 201


@trips_bp.route("/itinerary-activities/<int:ia_id>", methods=["PUT"])
@token_required
def update_itinerary_activity(ia_id):
    ia = ItineraryActivity.query.get(ia_id)
    if ia is None:
        return jsonify({"message": "Itinerary activity not found."}), 404
    if ia.stop.trip.user_id != request.current_user.user_id:
        return jsonify({"message": "You don't have access to this item."}), 403

    data = request.get_json(silent=True) or {}

    try:
        if "scheduled_date" in data:
            ia.scheduled_date = parse_date(data.get("scheduled_date"), "scheduled_date")
        if "start_time" in data:
            ia.start_time = parse_time(data.get("start_time"))
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if "cost" in data:
        try:
            ia.cost = float(data.get("cost") or 0)
        except (TypeError, ValueError):
            return jsonify({"message": "cost must be a number."}), 400

    if "custom_title" in data:
        ia.custom_title = (data.get("custom_title") or "").strip() or None

    if "display_order" in data:
        try:
            ia.display_order = int(data.get("display_order"))
        except (TypeError, ValueError):
            return jsonify({"message": "display_order must be an integer."}), 400

    db.session.commit()
    return jsonify({"activity": ia.to_dict()}), 200


@trips_bp.route("/itinerary-activities/<int:ia_id>", methods=["DELETE"])
@token_required
def delete_itinerary_activity(ia_id):
    ia = ItineraryActivity.query.get(ia_id)
    if ia is None:
        return jsonify({"message": "Itinerary activity not found."}), 404
    if ia.stop.trip.user_id != request.current_user.user_id:
        return jsonify({"message": "You don't have access to this item."}), 403

    db.session.delete(ia)
    db.session.commit()
    return jsonify({"message": "Activity removed."}), 200
