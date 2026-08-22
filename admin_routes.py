from flask import Blueprint, jsonify
from sqlalchemy import func

from setup import db, User, Trip, City, Stop, Activity, ItineraryActivity
from auth_utils import token_required, admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/stats", methods=["GET"])
@token_required
@admin_required
def get_admin_stats():
    total_users = db.session.query(func.count(User.user_id)).scalar() or 0
    total_trips = db.session.query(func.count(Trip.trip_id)).scalar() or 0
    public_trips = db.session.query(func.count(Trip.trip_id)).filter(Trip.is_public.is_(True)).scalar() or 0

    # Top cities by how many trip stops reference them
    top_cities_q = (
        db.session.query(City.city_name, City.country, func.count(Stop.stop_id).label("visits"))
        .join(Stop, Stop.city_id == City.city_id)
        .group_by(City.city_id)
        .order_by(func.count(Stop.stop_id).desc())
        .limit(10)
        .all()
    )
    top_cities = [
        {"city_name": name, "country": country, "trip_stops": visits}
        for name, country, visits in top_cities_q
    ]

    # Top activities by how many times they're added to itineraries
    top_activities_q = (
        db.session.query(Activity.title, Activity.category, func.count(ItineraryActivity.itinerary_activity_id).label("uses"))
        .join(ItineraryActivity, ItineraryActivity.activity_id == Activity.activity_id)
        .group_by(Activity.activity_id)
        .order_by(func.count(ItineraryActivity.itinerary_activity_id).desc())
        .limit(10)
        .all()
    )
    top_activities = [
        {"title": title, "category": category, "times_added": uses}
        for title, category, uses in top_activities_q
    ]

    return jsonify({
        "total_users": total_users,
        "total_trips": total_trips,
        "public_trips": public_trips,
        "top_cities": top_cities,
        "top_activities": top_activities,
    }), 200


@admin_bp.route("/users", methods=["GET"])
@token_required
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_public_dict() for u in users]}), 200
