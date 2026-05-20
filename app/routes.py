"""
Application Routes
Defines URL routes and view functions for the inventory application.
"""

import csv
import io
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
    Response,
)
from sqlalchemy import asc, desc
from app import db
from app.models import InventoryItem

# Create a Blueprint to organize related routes
inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/', methods=['GET'])
def index():
    """
    Main inventory list view.
    Displays all inventory items with optional search and sort functionality.
    
    Query Parameters:
        search (str): Filter items by name or category
        sort_by (str): Field to sort by (name, quantity, price, created_at)
        order (str): Sort order - 'asc' or 'desc'
        page (int): Page number for pagination
    """
    # Capture query parameters with safe defaults
    search_term = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)

    # Validate sort field to prevent injection
    allowed_sort_fields = ['name', 'quantity', 'price', 'category', 'created_at']
    if sort_by not in allowed_sort_fields:
        sort_by = 'created_at'

    # Build base query
    query = InventoryItem.query

    # Apply search filter if provided
    if search_term:
        search_filter = f"%{search_term}%"
        query = query.filter(
            db.or_(
                InventoryItem.name.ilike(search_filter),
                InventoryItem.category.ilike(search_filter),
                InventoryItem.description.ilike(search_filter),
                InventoryItem.sku.ilike(search_filter),
            )
        )

    # Apply sorting
    sort_column = getattr(InventoryItem, sort_by)
    if order == 'asc':
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Paginate results (20 items per page)
    items_paginated = query.paginate(page=page, per_page=20, error_out=False)

    # Calculate summary statistics
    total_items = InventoryItem.query.count()
    total_value = db.session.query(
        db.func.sum(InventoryItem.price * InventoryItem.quantity)
    ).scalar() or 0

    low_stock_count = InventoryItem.query.filter(
        InventoryItem.quantity > 0,
        InventoryItem.quantity < 10
    ).count()

    out_of_stock_count = InventoryItem.query.filter(
        InventoryItem.quantity == 0
    ).count()

    return render_template(
        'index.html',
        items=items_paginated.items,
        pagination=items_paginated,
        search_term=search_term,
        sort_by=sort_by,
        order=order,
        total_items=total_items,
        total_value=total_value,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
    )


@inventory_bp.route('/add', methods=['GET', 'POST'])
def add_item():
    """
    Add new inventory item view.
    
    GET:  Display the add item form
    POST: Process form submission and create new item
    """
    if request.method == 'POST':
        # Extract and sanitize form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        quantity_str = request.form.get('quantity', '0').strip()
        price_str = request.form.get('price', '').strip()
        category = request.form.get('category', '').strip()
        sku = request.form.get('sku', '').strip()

        # --- Input Validation ---
        errors = []

        # Name is required
        if not name:
            errors.append("Item name is required.")
        elif len(name) > 200:
            errors.append("Item name cannot exceed 200 characters.")

        # Quantity must be a non-negative integer
        try:
            quantity = int(quantity_str)
            if quantity < 0:
                errors.append("Quantity cannot be negative.")
        except ValueError:
            errors.append("Quantity must be a whole number.")
            quantity = 0

        # Price must be a positive number (optional field)
        price = None
        if price_str:
            try:
                price = float(price_str)
                if price < 0:
                    errors.append("Price cannot be negative.")
            except ValueError:
                errors.append("Price must be a valid number (e.g., 9.99).")

        # SKU must be unique if provided
        if sku:
            existing_sku = InventoryItem.query.filter_by(sku=sku).first()
            if existing_sku:
                errors.append(f"SKU '{sku}' is already in use by another item.")

        # If validation failed, re-render form with errors and user input
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'add_item.html',
                form_data=request.form  # Preserve user input
            ), 400

        # --- Create and Save Item ---
        try:
            new_item = InventoryItem(
                name=name,
                description=description if description else None,
                quantity=quantity,
                price=price,
                category=category if category else None,
                sku=sku if sku else None,
            )
            db.session.add(new_item)
            db.session.commit()

            flash(f"✓ '{name}' has been added to inventory successfully!", 'success')
            return redirect(url_for('inventory.index'))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while saving the item. Please try again.", 'danger')
            return render_template(
                'add_item.html',
                form_data=request.form
            ), 500

    # GET request - display empty form
    return render_template('add_item.html', form_data={})


@inventory_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    """
    Edit an existing inventory item.

    GET:  Display the edit form pre-populated with current values.
    POST: Validate and save updated values.
    """
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        abort(404)

    if request.method == 'POST':
        name          = request.form.get('name', '').strip()
        description   = request.form.get('description', '').strip()
        quantity_str  = request.form.get('quantity', '0').strip()
        price_str     = request.form.get('price', '').strip()
        category      = request.form.get('category', '').strip()
        sku           = request.form.get('sku', '').strip()

        errors = []

        if not name:
            errors.append("Item name is required.")
        elif len(name) > 200:
            errors.append("Item name cannot exceed 200 characters.")

        try:
            quantity = int(quantity_str)
            if quantity < 0:
                errors.append("Quantity cannot be negative.")
        except ValueError:
            errors.append("Quantity must be a whole number.")
            quantity = 0

        price = None
        if price_str:
            try:
                price = float(price_str)
                if price < 0:
                    errors.append("Price cannot be negative.")
            except ValueError:
                errors.append("Price must be a valid number (e.g., 9.99).")

        if sku:
            existing_sku = InventoryItem.query.filter(
                InventoryItem.sku == sku,
                InventoryItem.id != item_id
            ).first()
            if existing_sku:
                errors.append(f"SKU '{sku}' is already in use by another item.")

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('edit_item.html', item=item, form_data=request.form), 400

        try:
            item.name        = name
            item.description = description if description else None
            item.quantity    = quantity
            item.price       = price
            item.category    = category if category else None
            item.sku         = sku if sku else None
            db.session.commit()

            flash(f"✓ '{name}' has been updated successfully!", 'success')
            return redirect(url_for('inventory.index'))

        except Exception:
            db.session.rollback()
            flash("An error occurred while updating the item. Please try again.", 'danger')
            return render_template('edit_item.html', item=item, form_data=request.form), 500

    # GET — display form with current item values
    return render_template('edit_item.html', item=item, form_data={})


@inventory_bp.route('/export/csv', methods=['GET'])
def export_csv():
    """
    Export the full inventory as a CSV file download.
    Respects the same search filter as the dashboard (optional ?search= param).
    """
    search_term = request.args.get('search', '').strip()

    query = InventoryItem.query.order_by(InventoryItem.name.asc())
    if search_term:
        search_filter = f"%{search_term}%"
        query = query.filter(
            db.or_(
                InventoryItem.name.ilike(search_filter),
                InventoryItem.category.ilike(search_filter),
                InventoryItem.description.ilike(search_filter),
                InventoryItem.sku.ilike(search_filter),
            )
        )

    items = query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(['ID', 'Name', 'Category', 'SKU', 'Quantity', 'Unit Price',
                     'Total Value', 'Stock Status', 'Description', 'Date Added', 'Last Updated'])

    for item in items:
        total_value = round(float(item.price) * item.quantity, 2) if item.price is not None else ''
        writer.writerow([
            item.id,
            item.name,
            item.category or '',
            item.sku or '',
            item.quantity,
            float(item.price) if item.price is not None else '',
            total_value,
            item.stock_status,
            item.description or '',
            item.created_at.strftime('%Y-%m-%d') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d') if item.updated_at else '',
        ])

    output.seek(0)
    filename = 'inventory_export.csv'

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@inventory_bp.route('/item/<int:item_id>', methods=['GET'])
def item_detail(item_id):
    """Display full details for a single inventory item."""
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        abort(404)
    return render_template('item_detail.html', item=item)


@inventory_bp.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    """Delete an inventory item by ID."""
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        abort(404)
    name = item.name
    try:
        db.session.delete(item)
        db.session.commit()
        flash(f"'{name}' has been removed from inventory.", 'success')
    except Exception:
        db.session.rollback()
        flash("An error occurred while deleting the item. Please try again.", 'danger')
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for load balancers and monitoring tools.
    Returns JSON with application and database status.
    """
    health_status = {
        'status': 'healthy',
        'application': 'running',
        'database': 'unknown',
    }
    http_status = 200

    try:
        # Test database connectivity
        db.session.execute(db.text('SELECT 1'))
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['database'] = 'disconnected'
        health_status['error'] = str(e)
        http_status = 503

    return jsonify(health_status), http_status


@inventory_bp.route('/api/items', methods=['GET'])
def api_list_items():
    """
    JSON API endpoint to list inventory items with pagination and search.

    Query Parameters:
        page (int):     Page number, default 1.
        per_page (int): Items per page, default 20, max 100.
        search (str):   Filter by name, category, description, or SKU.
    """
    page     = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search_term = request.args.get('search', '').strip()

    query = InventoryItem.query.order_by(InventoryItem.name.asc())

    if search_term:
        search_filter = f"%{search_term}%"
        query = query.filter(
            db.or_(
                InventoryItem.name.ilike(search_filter),
                InventoryItem.category.ilike(search_filter),
                InventoryItem.description.ilike(search_filter),
                InventoryItem.sku.ilike(search_filter),
            )
        )

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items':    [item.to_dict() for item in paginated.items],
        'page':     paginated.page,
        'per_page': paginated.per_page,
        'total':    paginated.total,
        'pages':    paginated.pages,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev,
    })