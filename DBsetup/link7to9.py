from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import date
from itertools import groupby
# Assuming models are imported from your models file
# from models import db, User, Trip, Stop, ItineraryActivity, Expense

app = Flask(__name__)

@app.route('/profile/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    today = date.today()

    # Preplanned / Upcoming trips: start_date >= today
    preplanned_trips = Trip.query.filter(
        Trip.user_id == user.user_id,
        Trip.start_date >= today
    ).order_by(Trip.start_date.asc()).all()

    # Previous trips: start_date < today
    previous_trips = Trip.query.filter(
        Trip.user_id == user.user_id,
        Trip.start_date < today
    ).order_by(Trip.start_date.desc()).all()

    return render_template(
        'profile.html',
        user=user,
        preplanned_trips=preplanned_trips,
        previous_trips=previous_trips
    )


@app.route('/trip/<int:trip_id>/itinerary')
def trip_itinerary(trip_id):
    trip = Trip.query.get_or_404(trip_id)

    # Fetch all itinerary activities for this trip ordered by date and sequence
    activities = (
        db.session.query(ItineraryActivity, Stop)
        .join(Stop, ItineraryActivity.stop_id == Stop.stop_id)
        .filter(Stop.trip_id == trip_id)
        .order_by(ItineraryActivity.scheduled_date.asc(), ItineraryActivity.display_order.asc())
        .all()
    )

    # Group activities by day/date for the timeline view
    grouped_itinerary = {}
    for item, stop in activities:
        day_key = item.scheduled_date
        if day_key not in grouped_itinerary:
            grouped_itinerary[day_key] = []
        grouped_itinerary[day_key].append({
            'activity': item,
            'stop': stop,
            'title': item.custom_title or (item.activity.title if item.activity_id else "Activity"),
            'cost': item.cost or 0.0,
            'time': item.start_time
        })

    # Calculate total planned expense vs budget
    total_spent = sum(item.cost or 0.0 for item, _ in activities)

    return render_template(
        'itinerary.html',
        trip=trip,
        grouped_itinerary=grouped_itinerary,
        total_spent=total_spent
    )