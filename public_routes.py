import secrets

from flask import Blueprint, request, jsonify

from setup import db, Trip, Stop, ItineraryActivity
from auth_utils import token_required
from trip_routes import get_owned_trip

public_bp = Blueprint("public", __name__, url_prefix="/api")


# ---------------------------------------------------------------------
# Owner-side: turn sharing on/off
# ---------------------------------------------------------------------
@public_bp.route("/trips/<int:trip_id>/share", methods=["POST"])
@token_required
def share_trip(trip_id):
    """Make a trip public and (re)issue its shareable token."""
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err

    if not trip.shareable_token:
        trip.shareable_token = secrets.token_urlsafe(16)
    trip.is_public = True
    db.session.commit()

    return jsonify({
        "trip_id": trip.trip_id,
        "is_public": trip.is_public,
        "shareable_token": trip.shareable_token,
        "share_path": f"/shared/{trip.shareable_token}",
    }), 200


@public_bp.route("/trips/<int:trip_id>/share", methods=["DELETE"])
@token_required
def unshare_trip(trip_id):
    """Turn off public visibility. The token is kept so re-sharing reuses the same URL."""
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err

    trip.is_public = False
    db.session.commit()

    return jsonify({"trip_id": trip.trip_id, "is_public": trip.is_public}), 200


# ---------------------------------------------------------------------
# Public, unauthenticated read-only view
# ---------------------------------------------------------------------
@public_bp.route("/public/trips/<string:token>", methods=["GET"])
def get_public_trip(token):
    trip = Trip.query.filter_by(shareable_token=token).first()
    if trip is None or not trip.is_public:
        return jsonify({"message": "This trip isn't available or isn't shared publicly."}), 404

    data = trip.to_full_dict()
    data["owner_name"] = trip.owner.full_name
    # Never expose owner internals beyond a display name.
    return jsonify({"trip": data}), 200


# ---------------------------------------------------------------------
# "Copy Trip" — clone a public trip into the current user's account
# ---------------------------------------------------------------------
@public_bp.route("/public/trips/<string:token>/copy", methods=["POST"])
@token_required
def copy_public_trip(token):
    source = Trip.query.filter_by(shareable_token=token).first()
    if source is None or not source.is_public:
        return jsonify({"message": "This trip isn't available or isn't shared publicly."}), 404

    new_trip = Trip(
        user_id=request.current_user.user_id,
        trip_name=f"{source.trip_name} (copy)",
        description=source.description,
        start_date=source.start_date,
        end_date=source.end_date,
        cover_photo_url=source.cover_photo_url,
        total_budget=source.total_budget,
        is_public=False,
    )
    db.session.add(new_trip)
    db.session.flush()  # get new_trip.trip_id before creating children

    for stop in source.stops:
        new_stop = Stop(
            trip_id=new_trip.trip_id,
            city_id=stop.city_id,
            sequence_order=stop.sequence_order,
            arrival_date=stop.arrival_date,
            departure_date=stop.departure_date,
        )
        db.session.add(new_stop)
        db.session.flush()

        for ia in stop.itinerary_activities:
            db.session.add(ItineraryActivity(
                stop_id=new_stop.stop_id,
                activity_id=ia.activity_id,
                custom_title=ia.custom_title,
                scheduled_date=ia.scheduled_date,
                start_time=ia.start_time,
                cost=ia.cost,
                display_order=ia.display_order,
            ))

    db.session.commit()
    return jsonify({"trip": new_trip.to_full_dict()}), 201
