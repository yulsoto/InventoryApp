"""
Database Models
Defines SQLAlchemy ORM models for the inventory application.
"""

from datetime import datetime, timezone
from app import db


class InventoryItem(db.Model):
    """
    Represents a single item in the inventory.
    
    Attributes:
        id: Auto-incrementing primary key
        name: Item name (required, indexed for fast lookups)
        description: Optional detailed description
        quantity: Current stock quantity (defaults to 0)
        price: Unit price in dollars
        category: Optional category for grouping items
        sku: Optional Stock Keeping Unit identifier
        created_at: Timestamp when item was added
        updated_at: Timestamp when item was last modified
    """
    
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    name = db.Column(
        db.String(200), 
        nullable=False, 
        index=True,
        comment="Item name - required field"
    )
    
    description = db.Column(
        db.Text, 
        nullable=True,
        comment="Detailed description of the item"
    )
    
    quantity = db.Column(
        db.Integer, 
        nullable=False, 
        default=0,
        comment="Current stock quantity"
    )
    
    price = db.Column(
        db.Numeric(10, 2),  # Up to 99,999,999.99
        nullable=True,
        comment="Unit price in dollars"
    )
    
    category = db.Column(
        db.String(100), 
        nullable=True, 
        index=True,
        comment="Category for grouping items"
    )
    
    sku = db.Column(
        db.String(100), 
        nullable=True, 
        unique=True,
        comment="Stock Keeping Unit identifier"
    )
    
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="When the item was created"
    )
    
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="When the item was last updated"
    )

    def __repr__(self):
        return f"<InventoryItem id={self.id} name='{self.name}' qty={self.quantity}>"

    def to_dict(self):
        """Serialize the model to a dictionary (useful for API responses)."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'price': float(self.price) if self.price is not None else None,
            'category': self.category,
            'sku': self.sku,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def stock_status(self):
        """Returns a human-readable stock status based on quantity."""
        if self.quantity == 0:
            return 'out_of_stock'
        elif self.quantity < 10:
            return 'low_stock'
        else:
            return 'in_stock'

    @property
    def stock_status_label(self):
        """Returns a Bootstrap badge class for stock status display."""
        status_classes = {
            'out_of_stock': 'danger',
            'low_stock': 'warning',
            'in_stock': 'success',
        }
        return status_classes.get(self.stock_status, 'secondary')