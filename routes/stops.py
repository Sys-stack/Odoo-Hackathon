from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Stop, ItineraryActivity, Activity
from utils.validation import parse_date

stops_bp = Blueprint("stops", __name__)


def _own_stop_or_403(stop):
    from flask_jwt_extended import get_jwt_identity
    if stop.trip.user_id != int(get_jwt_identity()):
        return jsonify({"message": "You don't have access to this stop."}), 403
    return None


@stops_bp.put("/stops/<int:stop_id>")
@jwt_required()
def update_stop(stop_id):
    stop = Stop.query.get_or_404(stop_id)
    forbidden = _own_stop_or_403(stop)
    if forbidden:
        return forbidden

    data = request.get_json(silent=True) or {}
    try:
        if "arrival_date" in data:
            stop.arrival_date = parse_date(data["arrival_date"], "Start date")
        if "departure_date" in data:
            stop.departure_date = parse_date(data["departure_date"], "End date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if stop.departure_date < stop.arrival_date:
        return jsonify({"message": "End date cannot be before start date."}), 400

    if "sequence_order" in data:
        stop.sequence_order = data["sequence_order"]

    db.session.commit()
    return jsonify({"stop": stop.to_dict()})


@stops_bp.delete("/stops/<int:stop_id>")
@jwt_required()
def delete_stop(stop_id):
    stop = Stop.query.get_or_404(stop_id)
    forbidden = _own_stop_or_403(stop)
    if forbidden:
        return forbidden
    db.session.delete(stop)
    db.session.commit()
    return jsonify({"message": "Stop deleted."})


@stops_bp.post("/stops/<int:stop_id>/activities")
@jwt_required()
def add_itinerary_activity(stop_id):
    """Add a catalog activity (or a custom item) to a stop's schedule."""
    stop = Stop.query.get_or_404(stop_id)
    forbidden = _own_stop_or_403(stop)
    if forbidden:
        return forbidden

    data = request.get_json(silent=True) or {}
    activity_id = data.get("activity_id")
    custom_title = (data.get("custom_title") or "").strip() or None

    if not activity_id and not custom_title:
        return jsonify({"message": "Provide an activity_id or a custom_title."}), 400

    cost = data.get("cost")
    if cost is None and activity_id:
        activity = Activity.query.get(activity_id)
        cost = activity.estimated_cost if activity else 0

    try:
        scheduled_date = parse_date(data.get("scheduled_date"), "Scheduled date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    next_order = (
        max([a.display_order or 0 for a in stop.itinerary_activities], default=0) + 1
    )

    item = ItineraryActivity(
        stop_id=stop.stop_id,
        activity_id=activity_id,
        custom_title=custom_title,
        scheduled_date=scheduled_date,
        start_time=data.get("start_time"),
        cost=cost or 0,
        display_order=next_order,
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"itinerary_activity": item.to_dict()}), 201
