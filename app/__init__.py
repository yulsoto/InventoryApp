"""
Flask Application Factory
Creates and configures the Flask application instance.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions at module level (not yet tied to app)
db = SQLAlchemy()


def create_app(config_object=None):
    """
    Application factory function.
    
    Args:
        config_object: Configuration class or object to use.
                      If None, loads from environment.
    
    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    if config_object is None:
        from config import get_config
        config_object = get_config()

    app.config.from_object(config_object)

    # Initialize Flask extensions with the app
    db.init_app(app)

    # Register blueprints (route modules)
    with app.app_context():
        from app.routes import inventory_bp
        app.register_blueprint(inventory_bp)

        # Create all database tables if they don't exist
        db.create_all()

    # Register error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Registers custom error handlers for common HTTP errors."""

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('error.html', 
                               error_code=404, 
                               error_message="Page Not Found",
                               error_detail="The page you're looking for doesn't exist."), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        from app import db
        db.session.rollback()  # Roll back failed transaction
        return render_template('error.html',
                               error_code=500,
                               error_message="Internal Server Error",
                               error_detail="Something went wrong. Please try again."), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        from flask import render_template
        return render_template('error.html',
                               error_code=400,
                               error_message="Bad Request",
                               error_detail="The request could not be understood."), 400