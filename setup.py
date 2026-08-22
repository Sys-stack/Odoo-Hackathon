from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    profile_picture_url = db.Column(db.String(255))
    language_preference = db.Column(db.String(10), default='en')
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trips = db.relationship('Trip', backref='owner', lazy=True)

    def set_password(self, raw_password):
        """Hash and store the given plaintext password. Never store raw passwords."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    def to_public_dict(self):
        """Safe representation of the user for API responses (never includes password_hash)."""
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
    __tablename__ = 'cities'
    city_id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100))
    cost_index = db.Column(db.Float)
    popularity_score = db.Column(db.Integer)
    image_url = db.Column(db.String(255))

    activities = db.relationship('Activity', backref='city', lazy=True)
    stops = db.relationship('Stop', backref='city', lazy=True)

    def to_dict(self):
        return {
            "city_id": self.city_id,
            "city_name": self.city_name,
            "country": self.country,
            "region": self.region,
            "cost_index": self.cost_index,
            "popularity_score": self.popularity_score,
            "image_url": self.image_url,
        }

class Trip(db.Model):
    __tablename__ = 'trips'
    trip_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    trip_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    cover_photo_url = db.Column(db.String(255))
    total_budget = db.Column(db.Float)
    is_public = db.Column(db.Boolean, default=False)
    shareable_token = db.Column(db.String(64), unique=True)

    stops = db.relationship(
        'Stop', backref='trip', cascade="all, delete-orphan", lazy=True,
        order_by='Stop.sequence_order'
    )
    expenses = db.relationship('Expense', backref='trip', cascade="all, delete-orphan", lazy=True)

    def estimated_cost(self):
        total = 0.0
        for stop in self.stops:
            for ia in stop.itinerary_activities:
                total += ia.cost or 0.0
        return round(total, 2)

    def to_summary_dict(self):
        return {
            "trip_id": self.trip_id,
            "trip_name": self.trip_name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "cover_photo_url": self.cover_photo_url,
            "is_public": self.is_public,
            "stop_count": len(self.stops),
            "estimated_cost": self.estimated_cost(),
        }

    def to_full_dict(self):
        data = self.to_summary_dict()
        data["stops"] = [s.to_dict() for s in self.stops]
        return data

class Stop(db.Model):
    __tablename__ = 'stops'
    stop_id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.trip_id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.city_id'), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    arrival_date = db.Column(db.Date, nullable=False)
    departure_date = db.Column(db.Date, nullable=False)

    itinerary_activities = db.relationship(
        'ItineraryActivity', backref='stop', cascade="all, delete-orphan", lazy=True,
        order_by='ItineraryActivity.scheduled_date, ItineraryActivity.display_order'
    )

    def to_dict(self):
        return {
            "stop_id": self.stop_id,
            "trip_id": self.trip_id,
            "city": self.city.to_dict() if self.city else None,
            "sequence_order": self.sequence_order,
            "arrival_date": self.arrival_date.isoformat() if self.arrival_date else None,
            "departure_date": self.departure_date.isoformat() if self.departure_date else None,
            "activities": [a.to_dict() for a in self.itinerary_activities],
        }

class Activity(db.Model):
    __tablename__ = 'activities'
    activity_id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.city_id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50))
    estimated_cost = db.Column(db.Float)
    estimated_duration_mins = db.Column(db.Integer)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))

    def to_dict(self):
        return {
            "activity_id": self.activity_id,
            "city_id": self.city_id,
            "title": self.title,
            "category": self.category,
            "estimated_cost": self.estimated_cost,
            "estimated_duration_mins": self.estimated_duration_mins,
            "description": self.description,
            "image_url": self.image_url,
        }

class ItineraryActivity(db.Model):
    __tablename__ = 'itinerary_activities'
    itinerary_activity_id = db.Column(db.Integer, primary_key=True)
    stop_id = db.Column(db.Integer, db.ForeignKey('stops.stop_id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.activity_id'), nullable=True)
    custom_title = db.Column(db.String(150))
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    cost = db.Column(db.Float, default=0.0)
    display_order = db.Column(db.Integer)

    activity = db.relationship('Activity', lazy=True)

    def to_dict(self):
        return {
            "itinerary_activity_id": self.itinerary_activity_id,
            "stop_id": self.stop_id,
            "activity_id": self.activity_id,
            "title": self.custom_title or (self.activity.title if self.activity else None),
            "category": self.activity.category if self.activity else "custom",
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else None,
            "cost": self.cost,
            "display_order": self.display_order,
        }

class Expense(db.Model):
    __tablename__ = 'expenses'
    expense_id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.trip_id'), nullable=False)
    stop_id = db.Column(db.Integer, db.ForeignKey('stops.stop_id'), nullable=True)
    itinerary_activity_id = db.Column(db.Integer, db.ForeignKey('itinerary_activities.itinerary_activity_id'), nullable=True)
    category = db.Column(db.String(50), nullable=False) # e.g., 'transport', 'stay', 'activity', 'meals'
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)