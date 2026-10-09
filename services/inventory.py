"""
Inventory Service — Small Shop Inventory Organizer

Contains all business logic for managing products and stock.
This module sits between the UI and the database.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import execute_query, execute_query_df
from datetime import datetime


# ── Category Operations ──────────────────────────────────────────

def get_all_categories():
    """Fetch all product categories."""
    return execute_query_df("SELECT * FROM categories ORDER BY name")


def add_category(name, description=""):
    """Add a new category. Returns the new category ID."""
    name = name.strip()
    if not name:
        raise ValueError("Category name cannot be empty.")
    try:
        return execute_query(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description)
        )
    except Exception:
        raise ValueError(f"Category '{name}' already exists.")


def update_category(category_id, name, description=""):
    """Update an existing category's name and description."""
    name = name.strip()
    if not name:
        raise ValueError("Category name cannot be empty.")
    try:
        execute_query(
            "UPDATE categories SET name = ?, description = ? WHERE id = ?",
            (name, description, category_id)
        )
    except Exception:
        raise ValueError(f"Category name '{name}' already exists.")


def delete_category(category_id):
    """Delete a category. Products in this category will have category_id set to NULL."""
    execute_query("DELETE FROM categories WHERE id = ?", (category_id,))



# ── Product Operations ───────────────────────────────────────────

def get_all_products():
    """Fetch all products with their category names."""
    query = """
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.name
    """
    return execute_query_df(query)


def get_product_by_id(product_id):
    """Fetch a single product by ID."""
    query = """
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """
    results = execute_query_df(query, (product_id,))
    return results[0] if results else None


def search_products(search_term):
    """Search products by name (partial match)."""
    query = """
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.name LIKE ?
        ORDER BY p.name
    """
    return execute_query_df(query, (f"%{search_term}%",))


def get_products_by_category(category_id):
    """Filter products by category."""
    query = """
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.category_id = ?
        ORDER BY p.name
    """
    return execute_query_df(query, (category_id,))


def add_product(name, category_id, price, quantity, min_stock_level=5):
    """
    Add a new product to the inventory.

    Validates all inputs before insertion.
    Returns the new product ID.
    """
    # Validation
    name = name.strip()
    if not name:
        raise ValueError("Product name cannot be empty.")
    if price < 0:
        raise ValueError("Price cannot be negative.")
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    if min_stock_level < 0:
        raise ValueError("Minimum stock level cannot be negative.")

    # Check for duplicate name
    existing = execute_query_df(
        "SELECT id FROM products WHERE LOWER(name) = LOWER(?)", (name,)
    )
    if existing:
        raise ValueError(f"Product '{name}' already exists.")

    product_id = execute_query(
        """INSERT INTO products (name, category_id, price, quantity, min_stock_level)
           VALUES (?, ?, ?, ?, ?)""",
        (name, category_id, price, quantity, min_stock_level)
    )

    # Log initial stock as a transaction if quantity > 0
    if quantity > 0:
        execute_query(
            """INSERT INTO stock_transactions (product_id, type, quantity, note)
               VALUES (?, 'addition', ?, 'Initial stock')""",
            (product_id, quantity)
        )

    return product_id


def update_product(product_id, name, category_id, price, min_stock_level):
    """Update product details (not quantity — use stock operations for that)."""
    name = name.strip()
    if not name:
        raise ValueError("Product name cannot be empty.")
    if price < 0:
        raise ValueError("Price cannot be negative.")
    if min_stock_level < 0:
        raise ValueError("Minimum stock level cannot be negative.")

    # Check duplicate name (excluding current product)
    existing = execute_query_df(
        "SELECT id FROM products WHERE LOWER(name) = LOWER(?) AND id != ?",
        (name, product_id)
    )
    if existing:
        raise ValueError(f"Another product with name '{name}' already exists.")

    execute_query(
        """UPDATE products
           SET name = ?, category_id = ?, price = ?, min_stock_level = ?,
               updated_at = datetime('now', 'localtime')
           WHERE id = ?""",
        (name, category_id, price, min_stock_level, product_id)
    )


def delete_product(product_id):
    """Delete a product from the inventory."""
    execute_query("DELETE FROM products WHERE id = ?", (product_id,))


# ── Stock Operations ─────────────────────────────────────────────

def add_stock(product_id, quantity, note=""):
    """Add stock to a product."""
    if quantity <= 0:
        raise ValueError("Quantity to add must be positive.")

    # Update product quantity
    execute_query(
        """UPDATE products SET quantity = quantity + ?,
               updated_at = datetime('now', 'localtime')
           WHERE id = ?""",
        (quantity, product_id)
    )

    # Log the transaction
    execute_query(
        """INSERT INTO stock_transactions (product_id, type, quantity, note)
           VALUES (?, 'addition', ?, ?)""",
        (product_id, quantity, note or "Stock added")
    )


def remove_stock(product_id, quantity, note=""):
    """Remove stock from a product (e.g., damaged, expired)."""
    if quantity <= 0:
        raise ValueError("Quantity to remove must be positive.")

    # Check available stock
    product = get_product_by_id(product_id)
    if not product:
        raise ValueError("Product not found.")
    if product['quantity'] < quantity:
        raise ValueError(
            f"Cannot remove {quantity} units. Only {product['quantity']} in stock."
        )

    # Update product quantity
    execute_query(
        """UPDATE products SET quantity = quantity - ?,
               updated_at = datetime('now', 'localtime')
           WHERE id = ?""",
        (quantity, product_id)
    )

    # Log the transaction
    execute_query(
        """INSERT INTO stock_transactions (product_id, type, quantity, note)
           VALUES (?, 'removal', ?, ?)""",
        (product_id, quantity, note or "Stock removed")
    )


# ── Dashboard Queries ────────────────────────────────────────────

def get_total_products():
    """Get total number of products."""
    result = execute_query_df("SELECT COUNT(*) as count FROM products")
    return result[0]['count'] if result else 0


def get_total_stock_units():
    """Get total stock units across all products."""
    result = execute_query_df("SELECT COALESCE(SUM(quantity), 0) as total FROM products")
    return result[0]['total'] if result else 0


def get_low_stock_products():
    """Get products that are at or below minimum stock level."""
    query = """
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.quantity <= p.min_stock_level
        ORDER BY p.quantity ASC
    """
    return execute_query_df(query)


def get_total_inventory_value():
    """Get total value of all inventory."""
    result = execute_query_df(
        "SELECT COALESCE(SUM(price * quantity), 0) as total_value FROM products"
    )
    return result[0]['total_value'] if result else 0
