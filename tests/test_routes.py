"""
Tests for all application routes.
Run with: pytest tests/ -v
"""

import pytest
from app import db
from app.models import InventoryItem


# ─────────────────────────────────────────────
# Dashboard / Index
# ─────────────────────────────────────────────

class TestIndex:
    def test_index_loads(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Inventory Dashboard' in response.data

    def test_index_shows_item(self, client, sample_item):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Test Widget' in response.data

    def test_index_search_match(self, client, sample_item):
        response = client.get('/?search=Widget')
        assert response.status_code == 200
        assert b'Test Widget' in response.data

    def test_index_search_no_match(self, client, sample_item):
        response = client.get('/?search=DoesNotExist')
        assert response.status_code == 200
        assert b'Test Widget' not in response.data

    def test_index_invalid_sort_falls_back(self, client):
        response = client.get('/?sort_by=invalid_field')
        assert response.status_code == 200


# ─────────────────────────────────────────────
# Add Item
# ─────────────────────────────────────────────

class TestAddItem:
    def test_add_page_loads(self, client):
        response = client.get('/add')
        assert response.status_code == 200
        assert b'Add New Item' in response.data

    def test_add_item_success(self, client, app):
        response = client.post('/add', data={
            'name': 'New Gadget',
            'quantity': '10',
            'price': '19.99',
            'category': 'Gadgets',
            'sku': 'GAD-001',
            'description': 'A shiny new gadget',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'New Gadget' in response.data

        with app.app_context():
            assert InventoryItem.query.filter_by(name='New Gadget').first() is not None

    def test_add_item_missing_name(self, client):
        response = client.post('/add', data={
            'name': '',
            'quantity': '5',
        })
        assert response.status_code == 400

    def test_add_item_negative_quantity(self, client):
        response = client.post('/add', data={
            'name': 'Bad Item',
            'quantity': '-1',
        })
        assert response.status_code == 400

    def test_add_item_duplicate_sku(self, client, sample_item):
        response = client.post('/add', data={
            'name': 'Another Item',
            'quantity': '1',
            'sku': 'TEST-001',  # already used by sample_item
        })
        assert response.status_code == 400

    def test_add_item_invalid_price(self, client):
        response = client.post('/add', data={
            'name': 'Price Error Item',
            'quantity': '5',
            'price': 'not-a-number',
        })
        assert response.status_code == 400


# ─────────────────────────────────────────────
# Item Detail
# ─────────────────────────────────────────────

class TestItemDetail:
    def test_detail_loads(self, client, sample_item):
        response = client.get(f'/item/{sample_item.id}')
        assert response.status_code == 200
        assert b'Test Widget' in response.data

    def test_detail_shows_fields(self, client, sample_item):
        response = client.get(f'/item/{sample_item.id}')
        assert b'TEST-001' in response.data
        assert b'Testing' in response.data

    def test_detail_404(self, client):
        response = client.get('/item/99999')
        assert response.status_code == 404


# ─────────────────────────────────────────────
# Edit Item
# ─────────────────────────────────────────────

class TestEditItem:
    def test_edit_page_loads(self, client, sample_item):
        response = client.get(f'/edit/{sample_item.id}')
        assert response.status_code == 200
        assert b'Test Widget' in response.data

    def test_edit_item_success(self, client, app, sample_item):
        response = client.post(f'/edit/{sample_item.id}', data={
            'name': 'Updated Widget',
            'quantity': '75',
            'price': '14.99',
            'category': 'Testing',
            'sku': 'TEST-001',
            'description': 'Updated description',
        }, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            updated = db.session.get(InventoryItem, sample_item.id)
            assert updated.name == 'Updated Widget'
            assert updated.quantity == 75

    def test_edit_item_missing_name(self, client, sample_item):
        response = client.post(f'/edit/{sample_item.id}', data={
            'name': '',
            'quantity': '5',
        })
        assert response.status_code == 400

    def test_edit_item_404(self, client):
        response = client.get('/edit/99999')
        assert response.status_code == 404


# ─────────────────────────────────────────────
# Delete Item
# ─────────────────────────────────────────────

class TestDeleteItem:
    def test_delete_item(self, client, app, sample_item):
        item_id = sample_item.id
        response = client.post(f'/delete/{item_id}', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            assert db.session.get(InventoryItem, item_id) is None

    def test_delete_404(self, client):
        response = client.post('/delete/99999')
        assert response.status_code == 404


# ─────────────────────────────────────────────
# Export CSV
# ─────────────────────────────────────────────

class TestExportCSV:
    def test_export_returns_csv(self, client, sample_item):
        response = client.get('/export/csv')
        assert response.status_code == 200
        assert 'text/csv' in response.content_type
        assert b'Test Widget' in response.data

    def test_export_has_header_row(self, client):
        response = client.get('/export/csv')
        assert b'Name' in response.data
        assert b'Quantity' in response.data
        assert b'Unit Price' in response.data

    def test_export_with_search_filter(self, client, sample_item):
        response = client.get('/export/csv?search=Widget')
        assert response.status_code == 200
        assert b'Test Widget' in response.data

    def test_export_empty_inventory(self, client):
        response = client.get('/export/csv')
        assert response.status_code == 200
        # Only the header row — no item rows
        lines = [l for l in response.data.decode().splitlines() if l.strip()]
        assert len(lines) == 1


# ─────────────────────────────────────────────
# API — /api/items
# ─────────────────────────────────────────────

class TestAPIListItems:
    def test_api_returns_json(self, client):
        response = client.get('/api/items')
        assert response.status_code == 200
        assert response.is_json

    def test_api_empty(self, client):
        data = client.get('/api/items').get_json()
        assert data['total'] == 0
        assert data['items'] == []

    def test_api_returns_item(self, client, sample_item):
        data = client.get('/api/items').get_json()
        assert data['total'] == 1
        assert data['items'][0]['name'] == 'Test Widget'

    def test_api_pagination_fields(self, client):
        data = client.get('/api/items').get_json()
        for field in ('items', 'page', 'per_page', 'total', 'pages', 'has_next', 'has_prev'):
            assert field in data

    def test_api_per_page_capped_at_100(self, client):
        data = client.get('/api/items?per_page=9999').get_json()
        assert data['per_page'] == 100

    def test_api_search(self, client, sample_item):
        match = client.get('/api/items?search=Widget').get_json()
        assert match['total'] == 1

        no_match = client.get('/api/items?search=DoesNotExist').get_json()
        assert no_match['total'] == 0


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_json(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.is_json

    def test_health_status_fields(self, client):
        data = client.get('/health').get_json()
        assert 'status' in data
        assert 'database' in data


# ─────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────

class TestErrorHandlers:
    def test_404_returns_error_page(self, client):
        response = client.get('/this-route-does-not-exist')
        assert response.status_code == 404
        assert b'404' in response.data


# ─────────────────────────────────────────────
# Model
# ─────────────────────────────────────────────

class TestInventoryItemModel:
    def test_stock_status_in_stock(self, app):
        with app.app_context():
            item = InventoryItem(name='X', quantity=20)
            assert item.stock_status == 'in_stock'

    def test_stock_status_low_stock(self, app):
        with app.app_context():
            item = InventoryItem(name='X', quantity=5)
            assert item.stock_status == 'low_stock'

    def test_stock_status_out_of_stock(self, app):
        with app.app_context():
            item = InventoryItem(name='X', quantity=0)
            assert item.stock_status == 'out_of_stock'

    def test_to_dict_keys(self, app):
        with app.app_context():
            item = InventoryItem(name='X', quantity=1, price=5.0)
            d = item.to_dict()
            for key in ('id', 'name', 'quantity', 'price', 'category', 'sku', 'description'):
                assert key in d
