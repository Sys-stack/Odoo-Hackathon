from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db, bcrypt, jwt, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)

    # --- blueprints ---
    from routes.auth import auth_bp
    from routes.cities import cities_bp
    from routes.trips import trips_bp
    from routes.stops import stops_bp
    from routes.activities import activities_bp
    from routes.expenses import expenses_bp
    from routes.saved_destinations import saved_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(cities_bp, url_prefix="/api/cities")
    app.register_blueprint(trips_bp, url_prefix="/api/trips")
    app.register_blueprint(stops_bp, url_prefix="/api")
    app.register_blueprint(activities_bp, url_prefix="/api")
    app.register_blueprint(expenses_bp, url_prefix="/api")
    app.register_blueprint(saved_bp, url_prefix="/api/saved-destinations")

    # --- JWT error handlers -> consistent JSON instead of default HTML ---
    @jwt.unauthorized_loader
    def _missing_token(reason):
        return jsonify({"message": "Authentication required."}), 401

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return jsonify({"message": "Invalid or expired session. Please sign in again."}), 401

    @jwt.expired_token_loader
    def _expired_token(header, payload):
        return jsonify({"message": "Session expired. Please sign in again."}), 401

    @app.errorhandler(404)
    def _not_found(e):
        return jsonify({"message": "Not found."}), 404

    @app.errorhandler(500)
    def _server_error(e):
        return jsonify({"message": "Internal server error."}), 500

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=5000)
