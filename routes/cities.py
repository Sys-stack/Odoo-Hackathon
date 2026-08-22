from flask import Blueprint, request, jsonify

from models import City

cities_bp = Blueprint("cities", __name__)


@cities_bp.get("")
def list_cities():
    """GET /api/cities?search=lis&limit=10  -> powers the 'Select a Place' autocomplete."""
    search = (request.args.get("search") or "").strip()
    limit = min(int(request.args.get("limit", 20)), 50)

    query = City.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db_or(City.city_name.ilike(like), City.country.ilike(like))
        )

    cities = query.order_by(City.popularity_score.desc().nullslast()).limit(limit).all()
    return jsonify({"cities": [c.to_dict() for c in cities]})


@cities_bp.get("/<int:city_id>")
def get_city(city_id):
    city = City.query.get_or_404(city_id)
    return jsonify({"city": city.to_dict()})


def db_or(*conditions):
    from sqlalchemy import or_
    return or_(*conditions)
