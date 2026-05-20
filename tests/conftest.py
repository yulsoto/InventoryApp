"""
Pytest configuration and shared fixtures.
Uses an in-memory SQLite database so no PostgreSQL server is required.
"""

import pytest
from config import TestingConfig
from app import create_app, db as _db
from app.models import InventoryItem


@pytest.fixture(scope='session')
def app():
    """Create the Flask application configured for testing."""
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client — resets the database between tests."""
    with app.app_context():
        # Wipe all rows before each test for isolation
        _db.session.query(InventoryItem).delete()
        _db.session.commit()
    return app.test_client()


@pytest.fixture
def sample_item(app):
    """Insert and return a single InventoryItem for use in tests."""
    with app.app_context():
        item = InventoryItem(
            name='Test Widget',
            description='A widget used in tests',
            quantity=50,
            price=9.99,
            category='Testing',
            sku='TEST-001',
        )
        _db.session.add(item)
        _db.session.commit()
        # Detach from session so the object can be used outside the context
        _db.session.refresh(item)
        return item
