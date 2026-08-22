from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100))
    profile_picture_url = db.Column(db.String(255))
    language_preference = db.Column(db.String(10), default='en')
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trips = db.relationship('Trip', backref='owner', lazy=True)

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

    stops = db.relationship('Stop', backref='trip', cascade="all, delete-orphan", lazy=True)
    expenses = db.relationship('Expense', backref='trip', cascade="all, delete-orphan", lazy=True)

class Stop(db.Model):
    __tablename__ = 'stops'
    stop_id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.trip_id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.city_id'), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    arrival_date = db.Column(db.Date, nullable=False)
    departure_date = db.Column(db.Date, nullable=False)

    itinerary_activities = db.relationship('ItineraryActivity', backref='stop', cascade="all, delete-orphan", lazy=True)

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