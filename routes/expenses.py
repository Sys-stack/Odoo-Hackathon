from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Trip, Expense
from utils.validation import parse_date

expenses_bp = Blueprint("expenses", __name__)

VALID_CATEGORIES = {"transport", "stay", "activity", "meals", "other"}


def _owned_trip_or_403(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != int(get_jwt_identity()):
        return None, (jsonify({"message": "You don't have access to this trip."}), 403)
    return trip, None


@expenses_bp.get("/trips/<int:trip_id>/expenses")
@jwt_required()
def list_expenses(trip_id):
    trip, error = _owned_trip_or_403(trip_id)
    if error:
        return error
    return jsonify({"expenses": [e.to_dict() for e in trip.expenses]})


@expenses_bp.post("/trips/<int:trip_id>/expenses")
@jwt_required()
def add_expense(trip_id):
    trip, error = _owned_trip_or_403(trip_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    category = data.get("category")
    if category not in VALID_CATEGORIES:
        return jsonify({"message": f"category must be one of {sorted(VALID_CATEGORIES)}."}), 400

    amount = data.get("amount")
    if amount is None or float(amount) < 0:
        return jsonify({"message": "amount must be a non-negative number."}), 400

    try:
        expense_date = parse_date(data.get("expense_date"), "Expense date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    expense = Expense(
        trip_id=trip.trip_id,
        stop_id=data.get("stop_id"),
        itinerary_activity_id=data.get("itinerary_activity_id"),
        category=category,
        amount=amount,
        expense_date=expense_date,
        notes=data.get("notes"),
    )
    db.session.add(expense)
    db.session.commit()

    return jsonify({"expense": expense.to_dict()}), 201


@expenses_bp.delete("/expenses/<int:expense_id>")
@jwt_required()
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.trip.user_id != int(get_jwt_identity()):
        return jsonify({"message": "You don't have access to this expense."}), 403
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted."})
