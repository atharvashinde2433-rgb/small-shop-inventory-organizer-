"""
Reports Service — Small Shop Inventory Organizer

Generates various reports: daily sales, category-wise inventory,
most/least sold products, and inventory value analysis.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import execute_query_df
from datetime import datetime, date, timedelta
import pandas as pd


def get_daily_sales_report(days=30):
    """
    Get daily sales totals for the past N days.
    Returns data suitable for a time-series chart.
    """
    start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = """
        SELECT DATE(sold_at) as sale_date,
               COUNT(*) as num_transactions,
               SUM(quantity) as total_units,
               SUM(total_amount) as total_revenue
        FROM sales
        WHERE DATE(sold_at) >= ?
        GROUP BY DATE(sold_at)
        ORDER BY sale_date
    """
    return execute_query_df(query, (start_date,))


def get_category_inventory_report():
    """Get inventory summary grouped by category."""
    query = """
        SELECT c.name as category,
               COUNT(p.id) as product_count,
               COALESCE(SUM(p.quantity), 0) as total_stock,
               COALESCE(SUM(p.price * p.quantity), 0) as total_value
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id, c.name
        ORDER BY total_value DESC
    """
    return execute_query_df(query)


def get_most_sold_products(limit=10):
    """Get the top-selling products by quantity."""
    query = """
        SELECT p.name, p.price,
               COALESCE(SUM(s.quantity), 0) as total_sold,
               COALESCE(SUM(s.total_amount), 0) as total_revenue
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id, p.name, p.price
        ORDER BY total_sold DESC
        LIMIT ?
    """
    return execute_query_df(query, (limit,))


def get_least_sold_products(limit=10):
    """Get the least-selling products by quantity."""
    query = """
        SELECT p.name, p.price, p.quantity as current_stock,
               COALESCE(SUM(s.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id, p.name, p.price, p.quantity
        ORDER BY total_sold ASC
        LIMIT ?
    """
    return execute_query_df(query, (limit,))


def get_inventory_value_report():
    """Get inventory value for each product."""
    query = """
        SELECT p.name, c.name as category, p.price, p.quantity,
               (p.price * p.quantity) as stock_value
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY stock_value DESC
    """
    return execute_query_df(query)


def get_all_transactions(limit=200):
    """Get all stock transactions (additions, removals, sales)."""
    query = """
        SELECT st.*, p.name as product_name
        FROM stock_transactions st
        JOIN products p ON st.product_id = p.id
        ORDER BY st.created_at DESC
        LIMIT ?
    """
    return execute_query_df(query, (limit,))


def get_transactions_by_type(trans_type):
    """Get transactions filtered by type."""
    query = """
        SELECT st.*, p.name as product_name
        FROM stock_transactions st
        JOIN products p ON st.product_id = p.id
        WHERE st.type = ?
        ORDER BY st.created_at DESC
    """
    return execute_query_df(query, (trans_type,))
