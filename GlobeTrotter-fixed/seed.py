"""Populate the database with sample cities and activities so the app is
demo-able immediately. Safe to re-run: it clears and re-inserts catalog
data (cities/activities) without touching users or trips.

Usage:
    python seed.py
"""

import os

from app import create_app
from setup import db, City, Activity, User

CITIES = [
    # city_name, country, region, cost_index, popularity_score, image_url
    ("Lisbon", "Portugal", "Europe", 55, 92, "https://images.unsplash.com/photo-1585208798174-6cedd86e019a"),
    ("Porto", "Portugal", "Europe", 50, 78, "https://images.unsplash.com/photo-1555881551-8b8fb8f70b3d"),
    ("Barcelona", "Spain", "Europe", 65, 95, "https://images.unsplash.com/photo-1583422409516-2895a77efded"),
    ("Marrakech", "Morocco", "Africa", 40, 85, "https://images.unsplash.com/photo-1597212720158-2f6c3f5e0e0c"),
    ("Fes", "Morocco", "Africa", 35, 70, "https://images.unsplash.com/photo-1548013146-72479768bada"),
    ("Tokyo", "Japan", "Asia", 75, 98, "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf"),
    ("Kyoto", "Japan", "Asia", 68, 90, "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e"),
    ("Bangkok", "Thailand", "Asia", 42, 88, "https://images.unsplash.com/photo-1508009603885-50cf7c579365"),
    ("Chiang Mai", "Thailand", "Asia", 35, 74, "https://images.unsplash.com/photo-1598935898639-81586f7d2129"),
    ("Mexico City", "Mexico", "North America", 48, 86, "https://images.unsplash.com/photo-1518659526054-190340b32735"),
    ("Oaxaca", "Mexico", "North America", 40, 68, "https://images.unsplash.com/photo-1583531352515-8884af319dc1"),
    ("New York", "USA", "North America", 90, 96, "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9"),
    ("Rome", "Italy", "Europe", 62, 94, "https://images.unsplash.com/photo-1552832230-c0197dd311b5"),
    ("Florence", "Italy", "Europe", 58, 80, "https://images.unsplash.com/photo-1543429257-3e6a336b8b5b"),
    ("Cape Town", "South Africa", "Africa", 45, 82, "https://images.unsplash.com/photo-1580060839134-75a50a1fa0af"),
    ("Reykjavik", "Iceland", "Europe", 85, 76, "https://images.unsplash.com/photo-1504829857797-ddff29c27927"),
]

ACTIVITY_TEMPLATES = [
    # title_template, category, cost, duration_mins, description
    ("Old Town walking tour", "sightseeing", 0, 120, "A self-guided or led walk through the historic core."),
    ("Local food market crawl", "food", 25, 90, "Sample street food and produce at the main city market."),
    ("Museum of Art & History", "sightseeing", 15, 100, "Highlights of the city's art and cultural history."),
    ("Sunset viewpoint hike", "outdoor", 0, 90, "Easy hike or walk up to the best sunset viewpoint in town."),
    ("Cooking class", "food", 55, 150, "Hands-on class making a traditional regional dish."),
    ("Bike tour of the city", "outdoor", 30, 180, "Guided bike tour covering the main sights and neighborhoods."),
    ("Rooftop dinner", "food", 45, 90, "Dinner at a highly rated rooftop restaurant with a view."),
    ("Day trip to nearby ruins/landmark", "sightseeing", 60, 360, "Full-day excursion to a notable nearby landmark."),
]


def run():
    app = create_app()
    with app.app_context():
        Activity.query.delete()
        City.query.delete()
        db.session.commit()

        city_objs = []
        for name, country, region, cost_index, popularity, image_url in CITIES:
            city = City(
                city_name=name,
                country=country,
                region=region,
                cost_index=cost_index,
                popularity_score=popularity,
                image_url=image_url,
            )
            db.session.add(city)
            city_objs.append(city)
        db.session.flush()  # assign city_ids

        for city in city_objs:
            for title, category, cost, duration, description in ACTIVITY_TEMPLATES:
                db.session.add(
                    Activity(
                        city_id=city.city_id,
                        title=f"{title} — {city.city_name}",
                        category=category,
                        estimated_cost=cost,
                        estimated_duration_mins=duration,
                        description=description,
                        image_url=city.image_url,
                    )
                )

        db.session.commit()
        print(f"Seeded {len(city_objs)} cities and {len(city_objs) * len(ACTIVITY_TEMPLATES)} activities.")

        seed_admin()


def seed_admin():
    """Ensure at least one admin account exists, so /api/admin/* is reachable.
    Idempotent — does nothing if an admin already exists. Does NOT touch
    other users, unlike the catalog reset above.
    """
    if User.query.filter_by(role="admin").first() is not None:
        print("Admin user already exists — skipping.")
        return

    email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    password = os.environ.get("ADMIN_PASSWORD", "changeme123")

    existing = User.query.filter_by(email=email).first()
    if existing is not None:
        existing.role = "admin"
        db.session.commit()
        print(f"Promoted existing user {email} to admin.")
        return

    admin = User(email=email, full_name="Admin", role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Created admin user: {email} / {password} — change this password after first login.")


if __name__ == "__main__":
    run()
