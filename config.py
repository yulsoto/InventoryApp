"""
Application Configuration Module
Loads environment variables and provides configuration classes
for different deployment environments.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration with common settings."""

    # Flask Core Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-dev-key-change-in-production'
    
    # Database Configuration
    # DATABASE_URL takes priority (standard for Heroku/Render/Railway).
    # Falls back to building a PostgreSQL URL from individual variables.
    DB_HOST     = os.environ.get('DB_HOST', 'localhost')
    DB_PORT     = os.environ.get('DB_PORT', '5432')
    DB_NAME     = os.environ.get('DB_NAME', 'inventory_db')
    DB_USER     = os.environ.get('DB_USER', 'inventory_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # SQLAlchemy Performance Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_timeout': 30,
        'pool_recycle': 1800,      # Recycle connections every 30 minutes
        'pool_pre_ping': True,     # Verify connections before using them
    }

    # Pagination
    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production-specific configuration with enhanced security."""
    DEBUG = False
    FLASK_ENV = 'production'

    # Enforce secure secret key in production
    @classmethod
    def validate(cls):
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        if not os.environ.get('DB_PASSWORD'):
            raise ValueError("DB_PASSWORD environment variable must be set in production")


class TestingConfig(Config):
    """Configuration for automated tests using an in-memory SQLite database."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # SQLite does not support connection pool options
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False


# Configuration mapping for easy selection
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig,
}


def get_config():
    """Returns the appropriate configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'production')
    return config_map.get(env, ProductionConfig)