from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from setup import City, Activity
from auth_utils import token_required

catalog_bp = Blueprint("catalog", __name__, url_prefix="/api")


@catalog_bp.route("/cities", methods=["GET"])
@token_required
def search_cities():
    q = (request.args.get("q") or "").strip()
    region = (request.args.get("region") or "").strip()
    country = (request.args.get("country") or "").strip()
    try:
        limit = min(int(request.args.get("limit", 20)), 50)
    except ValueError:
        limit = 20
    sort = request.args.get("sort", "popularity")

    query = City.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(City.city_name.ilike(like), City.country.ilike(like)))
    if region:
        query = query.filter(City.region == region)
    if country:
        query = query.filter(City.country == country)

    if sort == "popularity":
        query = query.order_by(City.popularity_score.desc())
    elif sort == "cost":
        query = query.order_by(City.cost_index.asc())
    else:
        query = query.order_by(City.city_name.asc())

    cities = query.limit(limit).all()
    return jsonify({"cities": [c.to_dict() for c in cities]}), 200


@catalog_bp.route("/activities", methods=["GET"])
@token_required
def search_activities():
    city_id = request.args.get("city_id", type=int)
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()

    if not city_id:
        return jsonify({"message": "city_id is required."}), 400

    query = Activity.query.filter_by(city_id=city_id)
    if q:
        query = query.filter(Activity.title.ilike(f"%{q}%"))
    if category:
        query = query.filter(Activity.category == category)

    activities = query.order_by(Activity.title.asc()).all()
    return jsonify({"activities": [a.to_dict() for a in activities]}), 200
