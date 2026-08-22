from datetime import datetime

from flask import Blueprint, request, jsonify

from setup import db, Trip, Stop, ItineraryActivity, Expense
from auth_utils import token_required
from trip_routes import get_owned_trip, get_owned_stop, parse_date

budget_bp = Blueprint("budget", __name__, url_prefix="/api")

VALID_CATEGORIES = {"transport", "stay", "activity", "meals", "misc"}


def get_owned_expense(expense_id, user):
    expense = Expense.query.get(expense_id)
    if expense is None:
        return None, (jsonify({"message": "Expense not found."}), 404)
    if expense.trip.user_id != user.user_id:
        return None, (jsonify({"message": "You don't have access to this expense."}), 403)
    return expense, None


# ---------------------------------------------------------------------
# Budget summary
# ---------------------------------------------------------------------
@budget_bp.route("/trips/<int:trip_id>/budget", methods=["GET"])
@token_required
def get_trip_budget(trip_id):
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err

    # Itinerary activity costs count as the "activity" bucket automatically.
    activities_total = trip.estimated_cost()

    breakdown = {"transport": 0.0, "stay": 0.0, "activity": activities_total, "meals": 0.0, "misc": 0.0}
    for expense in trip.expenses:
        category = expense.category if expense.category in VALID_CATEGORIES else "misc"
        breakdown[category] = round(breakdown.get(category, 0.0) + expense.amount, 2)

    total_spent = round(sum(breakdown.values()), 2)
    num_days = max((trip.end_date - trip.start_date).days + 1, 1)
    average_per_day = round(total_spent / num_days, 2)

    total_budget = trip.total_budget
    is_overbudget = total_budget is not None and total_spent > total_budget
    remaining = round(total_budget - total_spent, 2) if total_budget is not None else None

    return jsonify({
        "trip_id": trip.trip_id,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "remaining": remaining,
        "is_overbudget": is_overbudget,
        "breakdown_by_category": breakdown,
        "num_days": num_days,
        "average_cost_per_day": average_per_day,
        "expenses": [e.to_dict() for e in trip.expenses],
    }), 200


# ---------------------------------------------------------------------
# Expense CRUD
# ---------------------------------------------------------------------
@budget_bp.route("/trips/<int:trip_id>/expenses", methods=["POST"])
@token_required
def add_expense(trip_id):
    trip, err = get_owned_trip(trip_id, request.current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip().lower()
    amount = data.get("amount")
    notes = (data.get("notes") or "").strip() or None
    stop_id = data.get("stop_id")
    itinerary_activity_id = data.get("itinerary_activity_id")

    if category not in VALID_CATEGORIES:
        return jsonify({
            "message": f"category must be one of: {', '.join(sorted(VALID_CATEGORIES))}."
        }), 400

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"message": "amount must be a number."}), 400
    if amount < 0:
        return jsonify({"message": "amount must be zero or positive."}), 400

    try:
        expense_date = parse_date(data.get("expense_date"), "expense_date")
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    if stop_id is not None:
        stop = Stop.query.get(stop_id)
        if stop is None or stop.trip_id != trip.trip_id:
            return jsonify({"message": "stop_id does not belong to this trip."}), 400

    if itinerary_activity_id is not None:
        ia = ItineraryActivity.query.get(itinerary_activity_id)
        if ia is None or ia.stop.trip_id != trip.trip_id:
            return jsonify({"message": "itinerary_activity_id does not belong to this trip."}), 400

    expense = Expense(
        trip_id=trip.trip_id,
        stop_id=stop_id,
        itinerary_activity_id=itinerary_activity_id,
        category=category,
        amount=amount,
        expense_date=expense_date,
        notes=notes,
    )
    db.session.add(expense)
    db.session.commit()

    return jsonify({"expense": expense.to_dict()}), 201


@budget_bp.route("/expenses/<int:expense_id>", methods=["PUT"])
@token_required
def update_expense(expense_id):
    expense, err = get_owned_expense(expense_id, request.current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}

    if "category" in data:
        category = (data.get("category") or "").strip().lower()
        if category not in VALID_CATEGORIES:
            return jsonify({
                "message": f"category must be one of: {', '.join(sorted(VALID_CATEGORIES))}."
            }), 400
        expense.category = category

    if "amount" in data:
        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return jsonify({"message": "amount must be a number."}), 400
        if amount < 0:
            return jsonify({"message": "amount must be zero or positive."}), 400
        expense.amount = amount

    if "expense_date" in data:
        try:
            expense.expense_date = parse_date(data.get("expense_date"), "expense_date")
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    if "notes" in data:
        expense.notes = (data.get("notes") or "").strip() or None

    db.session.commit()
    return jsonify({"expense": expense.to_dict()}), 200


@budget_bp.route("/expenses/<int:expense_id>", methods=["DELETE"])
@token_required
def delete_expense(expense_id):
    expense, err = get_owned_expense(expense_id, request.current_user)
    if err:
        return err

    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted."}), 200
