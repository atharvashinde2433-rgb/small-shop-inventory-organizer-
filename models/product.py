"""
Product Model — Small Shop Inventory Organizer

Defines the Product data class for clean data passing between modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    """Represents a product in the shop inventory."""
    id: Optional[int] = None
    name: str = ""
    category_id: Optional[int] = None
    category_name: str = ""  # For display purposes
    price: float = 0.0
    quantity: int = 0
    min_stock_level: int = 5
    created_at: str = ""
    updated_at: str = ""

    @property
    def stock_value(self) -> float:
        """Calculate the total value of this product's stock."""
        return self.price * self.quantity

    @property
    def is_low_stock(self) -> bool:
        """Check if the product is below minimum stock level."""
        return self.quantity <= self.min_stock_level

    @property
    def is_out_of_stock(self) -> bool:
        """Check if the product is completely out of stock."""
        return self.quantity == 0

    def __str__(self):
        return f"{self.name} (Qty: {self.quantity}, Price: ₹{self.price:.2f})"
