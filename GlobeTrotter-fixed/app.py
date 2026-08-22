import os

from dotenv import load_dotenv
from flask import Flask, render_template

from setup import db

# Load variables from a .env file in the project root, if present.
# Must happen before create_app() reads any os.environ values below.
load_dotenv()


def create_app():
    app = Flask(__name__)

    # --- Config -------------------------------------------------------
    # In production, load these from environment variables / a secrets manager,
    # never hardcode them.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///waypoint.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_EXP_HOURS"] = 24

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from auth_routes import auth_bp
    from trip_routes import trips_bp
    from catalog_routes import catalog_bp
    from budget_routes import budget_bp
    from public_routes import public_bp
    from admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    register_page_routes(app)

    return app


# ---------------------------------------------------------------------
# Page routes (serve the HTML shell; the pages fetch their own data via
# the JSON API above, using the JWT stored in localStorage)
# ---------------------------------------------------------------------
def register_page_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    @app.route("/trips")
    def my_trips_page():
        return render_template("my-trips.html")

    @app.route("/trips/new")
    def create_trip_page():
        return render_template("create-trip.html")

    @app.route("/trips/<int:trip_id>/plan")
    def itinerary_builder_page(trip_id):
        return render_template("itinerary-builder.html", trip_id=trip_id)

    @app.route("/trips/<int:trip_id>")
    def itinerary_view_page(trip_id):
        return render_template("itinerary-view.html", trip_id=trip_id)

    @app.route("/trips/<int:trip_id>/budget")
    def trip_budget_page(trip_id):
        return render_template("trip-budget.html", trip_id=trip_id)

    @app.route("/trips/<int:trip_id>/calendar")
    def trip_calendar_page(trip_id):
        return render_template("trip-calendar.html", trip_id=trip_id)

    @app.route("/cities")
    def city_search_page():
        return render_template("city-search.html")

    @app.route("/activities")
    def activity_search_page():
        return render_template("activity-search.html")

    @app.route("/shared/<string:token>")
    def shared_trip_page(token):
        return render_template("shared-trip.html", token=token)

    @app.route("/profile")
    def profile_page():
        return render_template("profile.html")

    @app.route("/admin")
    def admin_page():
        return render_template("admin.html")


app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
