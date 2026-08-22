from flask import Blueprint, request, jsonify

from models import Activity

activities_bp = Blueprint("activities", __name__)


@activities_bp.get("/cities/<int:city_id>/activities")
def list_activities_for_city(city_id):
    """Powers the 'Suggestions for Places to Visit / Activities to perform' grid."""
    category = request.args.get("category")
    query = Activity.query.filter_by(city_id=city_id)
    if category:
        query = query.filter_by(category=category)
    activities = query.all()
    return jsonify({"activities": [a.to_dict() for a in activities]})


@activities_bp.get("/activities/<int:activity_id>")
def get_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    return jsonify({"activity": activity.to_dict()})
