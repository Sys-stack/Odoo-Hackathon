"""Screen 14 (new): AI Trip Estimator — calls Google's Gemini API to produce
an approximate distance/cost/travel-info estimate for a route, either loaded
from a saved trip's stops or entered manually (no trip required).

This is intentionally stateless: nothing here is written to the database.
It's a calculator, not a source of truth — the numbers are LLM estimates,
not live pricing or routing data.

Requires GEMINI_API_KEY to be set (see .env.example). Without it, the
endpoint returns a clear 501 rather than failing obscurely.
"""
import json
import os

import requests
from flask import Blueprint, request, jsonify

from setup import Trip
from auth_utils import token_required
from trip_routes import parse_date

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"

# Gemini's structured-output schema (subset of OpenAPI types Gemini supports).
# Forcing this shape means the frontend never has to guess at Gemini's prose.
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "legs": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "from_city": {"type": "STRING"},
                    "to_city": {"type": "STRING"},
                    "distance_km": {"type": "NUMBER"},
                    "typical_transport": {"type": "STRING"},
                },
                "required": ["from_city", "to_city", "distance_km", "typical_transport"],
            },
        },
        "total_distance_km": {"type": "NUMBER"},
        "cost_estimate_usd": {
            "type": "OBJECT",
            "properties": {
                "transport": {"type": "NUMBER"},
                "stay": {"type": "NUMBER"},
                "food": {"type": "NUMBER"},
                "activities": {"type": "NUMBER"},
                "misc": {"type": "NUMBER"},
                "total": {"type": "NUMBER"},
            },
            "required": ["transport", "stay", "food", "activities", "misc", "total"],
        },
        "average_daily_cost_per_traveler_usd": {"type": "NUMBER"},
        "best_time_to_visit": {"type": "STRING"},
        "travel_tips": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": [
        "legs", "total_distance_km", "cost_estimate_usd",
        "average_daily_cost_per_traveler_usd", "best_time_to_visit", "travel_tips",
    ],
}


def build_prompt(city_list, start_date, end_date, num_days, travelers, trip_style):
    route = " → ".join(city_list)
    return (
        "You are a travel-planning assistant giving approximate, ballpark figures "
        "(not live prices) for a multi-city trip.\n\n"
        f"Travelers: {travelers}\n"
        f"Trip style/budget level: {trip_style}\n"
        f"Dates: {start_date} to {end_date} ({num_days} day{'s' if num_days != 1 else ''})\n"
        f"Route in order: {route}\n\n"
        "For each consecutive pair of cities in the route, estimate the typical "
        "one-way travel distance in kilometers and the most common way to cover "
        "it (flight, train, bus, car, etc). Then estimate a total cost breakdown "
        "in USD for the WHOLE trip across all travelers combined, covering "
        "transport, accommodation (stay), food, activities, and miscellaneous. "
        "Also give the average daily cost per traveler in USD, a one-line note "
        "on the best time of year to visit this route, and 3-5 short practical "
        "travel tips specific to this route. Use your general knowledge of "
        "these destinations to produce realistic, well-reasoned estimates."
    )


def call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, (
            "AI estimates aren't configured on this server — set GEMINI_API_KEY "
            "in your .env file (see .env.example) and restart."
        ), 501

    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    url = GEMINI_API_URL.format(model=model)

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.4,
        },
    }

    try:
        resp = requests.post(
            url, params={"key": api_key}, json=body, timeout=30,
        )
    except requests.RequestException as e:
        return None, f"Couldn't reach the Gemini API: {e}", 502

    if resp.status_code != 200:
        # Gemini's error payloads are JSON with an {"error": {"message": ...}} shape.
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except ValueError:
            detail = resp.text
        return None, f"Gemini API error ({resp.status_code}): {detail}", 502

    try:
        payload = resp.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, ValueError, TypeError) as e:
        return None, f"Gemini returned an unexpected response shape: {e}", 502

    return result, None, 200


@ai_bp.route("/estimate", methods=["POST"])
@token_required
def estimate_trip():
    data = request.get_json(silent=True) or {}

    travelers = data.get("travelers", 1)
    try:
        travelers = max(1, int(travelers))
    except (TypeError, ValueError):
        return jsonify({"message": "travelers must be an integer."}), 400

    trip_style = (data.get("trip_style") or "mid-range").strip()

    trip_id = data.get("trip_id")
    if trip_id:
        trip = Trip.query.get(trip_id)
        if trip is None or trip.user_id != request.current_user.user_id:
            return jsonify({"message": "Trip not found."}), 404
        if not trip.stops:
            return jsonify({"message": "This trip has no stops yet — add some in the itinerary builder first."}), 400

        stops = sorted(trip.stops, key=lambda s: s.sequence_order)
        city_list = [f"{s.city.city_name}, {s.city.country}" for s in stops]
        start_date = trip.start_date.isoformat()
        end_date = trip.end_date.isoformat()
    else:
        cities = data.get("cities")
        if not cities or not isinstance(cities, list) or len(cities) < 2:
            return jsonify({"message": "Provide at least 2 cities, or a trip_id."}), 400
        city_list = [str(c).strip() for c in cities if str(c).strip()]
        if len(city_list) < 2:
            return jsonify({"message": "Provide at least 2 non-empty city names."}), 400

        try:
            start = parse_date(data.get("start_date"), "start_date")
            end = parse_date(data.get("end_date"), "end_date")
        except ValueError as e:
            return jsonify({"message": str(e)}), 400
        if end < start:
            return jsonify({"message": "end_date must be on or after start_date."}), 400
        start_date, end_date = start.isoformat(), end.isoformat()

    from datetime import date
    num_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1

    prompt = build_prompt(city_list, start_date, end_date, num_days, travelers, trip_style)
    result, error, status_code = call_gemini(prompt)
    if error:
        return jsonify({"message": error}), status_code

    result["route"] = city_list
    result["num_days"] = num_days
    result["travelers"] = travelers
    return jsonify({"estimate": result}), 200
