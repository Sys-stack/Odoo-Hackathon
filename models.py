import secrets
from datetime import datetime

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100))
    profile_picture_url = db.Column(db.String(255))
    language_preference = db.Column(db.String(10), default="en")
    role = db.Column(db.String(20), default="user")  # 'user' | 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trips = db.relationship("Trip", backref="owner", lazy=True, cascade="all, delete-orphan")
    saved_destinations = db.relationship(
        "SavedDestination", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "profile_picture_url": self.profile_picture_url,
            "language_preference": self.language_preference,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class City(db.Model):
    __tablename__ = "cities"

    city_id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100))
    cost_index = db.Column(db.Numeric(3, 2))
    popularity_score = db.Column(db.Integer)
    image_url = db.Column(db.String(255))

    activities = db.relationship("Activity", backref="city", lazy=True)
    stops = db.relationship("Stop", backref="city", lazy=True)

    def to_dict(self):
        return {
            "city_id": self.city_id,
            "city_name": self.city_name,
            "country": self.country,
            "region": self.region,
            "cost_index": float(self.cost_index) if self.cost_index is not None else None,
            "popularity_score": self.popularity_score,
            "image_url": self.image_url,
        }


class Trip(db.Model):
    __tablename__ = "trips"

    trip_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    trip_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    cover_photo_url = db.Column(db.String(255))
    total_budget = db.Column(db.Numeric(10, 2))
    is_public = db.Column(db.Boolean, default=False)
    shareable_token = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stops = db.relationship(
        "Stop", backref="trip", cascade="all, delete-orphan", lazy=True,
        order_by="Stop.sequence_order",
    )
    expenses = db.relationship("Expense", backref="trip", cascade="all, delete-orphan", lazy=True)

    def generate_shareable_token(self):
        self.shareable_token = secrets.token_urlsafe(12)
        return self.shareable_token

    def to_dict(self, include_stops=False):
        data = {
            "trip_id": self.trip_id,
            "user_id": self.user_id,
            "trip_name": self.trip_name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "cover_photo_url": self.cover_photo_url,
            "total_budget": float(self.total_budget) if self.total_budget is not None else None,
            "is_public": self.is_public,
            "shareable_token": self.shareable_token,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_stops:
            data["stops"] = [s.to_dict() for s in self.stops]
        return data


class Stop(db.Model):
    __tablename__ = "stops"

    stop_id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.trip_id"), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.city_id"), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    arrival_date = db.Column(db.Date, nullable=False)
    departure_date = db.Column(db.Date, nullable=False)

    itinerary_activities = db.relationship(
        "ItineraryActivity", backref="stop", cascade="all, delete-orphan", lazy=True,
        order_by="ItineraryActivity.display_order",
    )

    def to_dict(self, include_activities=False):
        data = {
            "stop_id": self.stop_id,
            "trip_id": self.trip_id,
            "city_id": self.city_id,
            "city": self.city.to_dict() if self.city else None,
            "sequence_order": self.sequence_order,
            "arrival_date": self.arrival_date.isoformat() if self.arrival_date else None,
            "departure_date": self.departure_date.isoformat() if self.departure_date else None,
        }
        if include_activities:
            data["itinerary_activities"] = [a.to_dict() for a in self.itinerary_activities]
        return data


class Activity(db.Model):
    __tablename__ = "activities"

    activity_id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.city_id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(20))  # sightseeing | food | adventure | culture | other
    estimated_cost = db.Column(db.Numeric(8, 2))
    estimated_duration_mins = db.Column(db.Integer)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))

    def to_dict(self):
        return {
            "activity_id": self.activity_id,
            "city_id": self.city_id,
            "title": self.title,
            "category": self.category,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost is not None else None,
            "estimated_duration_mins": self.estimated_duration_mins,
            "description": self.description,
            "image_url": self.image_url,
        }


class ItineraryActivity(db.Model):
    __tablename__ = "itinerary_activities"

    itinerary_activity_id = db.Column(db.Integer, primary_key=True)
    stop_id = db.Column(db.Integer, db.ForeignKey("stops.stop_id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.activity_id"), nullable=True)
    custom_title = db.Column(db.String(150))
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    cost = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    display_order = db.Column(db.Integer)

    activity = db.relationship("Activity", lazy=True)
    expenses = db.relationship("Expense", backref="itinerary_activity", lazy=True)

    def to_dict(self):
        return {
            "itinerary_activity_id": self.itinerary_activity_id,
            "stop_id": self.stop_id,
            "activity_id": self.activity_id,
            "activity": self.activity.to_dict() if self.activity else None,
            "custom_title": self.custom_title,
            "title": self.custom_title or (self.activity.title if self.activity else None),
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "cost": float(self.cost) if self.cost is not None else 0,
            "display_order": self.display_order,
        }


class Expense(db.Model):
    __tablename__ = "expenses"

    expense_id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.trip_id"), nullable=False)
    stop_id = db.Column(db.Integer, db.ForeignKey("stops.stop_id"), nullable=True)
    itinerary_activity_id = db.Column(
        db.Integer, db.ForeignKey("itinerary_activities.itinerary_activity_id"), nullable=True
    )
    category = db.Column(db.String(20), nullable=False)  # transport|stay|activity|meals|other
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "expense_id": self.expense_id,
            "trip_id": self.trip_id,
            "stop_id": self.stop_id,
            "itinerary_activity_id": self.itinerary_activity_id,
            "category": self.category,
            "amount": float(self.amount) if self.amount is not None else None,
            "expense_date": self.expense_date.isoformat() if self.expense_date else None,
            "notes": self.notes,
        }


class SavedDestination(db.Model):
    __tablename__ = "saved_destinations"

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.city_id"), primary_key=True)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    city = db.relationship("City", lazy=True)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "city_id": self.city_id,
            "city": self.city.to_dict() if self.city else None,
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }
