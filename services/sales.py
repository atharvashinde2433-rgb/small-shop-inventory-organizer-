"""
Sales Service — Small Shop Inventory Organizer

Handles all sales-related business logic: recording sales,
reducing inventory, and calculating totals.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import execute_query, execute_query_df
from services.inventory import get_product_by_id
from datetime import datetime, date


def record_sale(product_id, quantity):
    """
    Record a sale: reduce stock and create sale record.

    Args:
        product_id: ID of the product being sold
        quantity: Number of units sold

    Returns:
        Dictionary with sale details (for undo stack)
    """
    if quantity <= 0:
        raise ValueError("Sale quantity must be positive.")

    # Get product details
    product = get_product_by_id(product_id)
    if not product:
        raise ValueError("Product not found.")
    if product['quantity'] < quantity:
        raise ValueError(
            f"Insufficient stock. Only {product['quantity']} units available."
        )

    unit_price = product['price']
    total_amount = unit_price * quantity

    # Record the sale
    sale_id = execute_query(
        """INSERT INTO sales (product_id, quantity, unit_price, total_amount)
           VALUES (?, ?, ?, ?)""",
        (product_id, quantity, unit_price, total_amount)
    )

    # Reduce product stock
    execute_query(
        """UPDATE products SET quantity = quantity - ?,
               updated_at = datetime('now', 'localtime')
           WHERE id = ?""",
        (quantity, product_id)
    )

    # Log the stock transaction
    execute_query(
        """INSERT INTO stock_transactions (product_id, type, quantity, note)
           VALUES (?, 'sale', ?, ?)""",
        (product_id, quantity, f"Sale #{sale_id}")
    )

    return {
        'sale_id': sale_id,
        'product_id': product_id,
        'product_name': product['name'],
        'quantity': quantity,
        'unit_price': unit_price,
        'total_amount': total_amount
    }


def get_today_sales():
    """Get all sales made today."""
    today = date.today().strftime("%Y-%m-%d")
    query = """
        SELECT s.*, p.name as product_name
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE DATE(s.sold_at) = ?
        ORDER BY s.sold_at DESC
    """
    return execute_query_df(query, (today,))


def get_today_sales_total():
    """Get total sales amount for today."""
    today = date.today().strftime("%Y-%m-%d")
    result = execute_query_df(
        """SELECT COALESCE(SUM(total_amount), 0) as total
           FROM sales WHERE DATE(sold_at) = ?""",
        (today,)
    )
    return result[0]['total'] if result else 0


def get_all_sales(limit=100):
    """Get recent sales records."""
    query = """
        SELECT s.*, p.name as product_name
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sold_at DESC
        LIMIT ?
    """
    return execute_query_df(query, (limit,))


def get_sales_by_date_range(start_date, end_date):
    """Get sales within a date range."""
    query = """
        SELECT s.*, p.name as product_name
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE DATE(s.sold_at) BETWEEN ? AND ?
        ORDER BY s.sold_at DESC
    """
    return execute_query_df(query, (start_date, end_date))


def undo_sale(sale_id, product_id, quantity):
    """
    Undo a sale: delete the sale record and restore stock.
    Used by the Undo (Stack) feature.
    """
    # Restore product stock
    execute_query(
        """UPDATE products SET quantity = quantity + ?,
               updated_at = datetime('now', 'localtime')
           WHERE id = ?""",
        (quantity, product_id)
    )

    # Delete the sale record
    execute_query("DELETE FROM sales WHERE id = ?", (sale_id,))

    # Delete the stock transaction for this sale
    execute_query(
        "DELETE FROM stock_transactions WHERE product_id = ? AND type = 'sale' AND note = ?",
        (product_id, f"Sale #{sale_id}")
    )
