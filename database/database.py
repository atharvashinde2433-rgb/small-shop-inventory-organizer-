"""
Database Module — Small Shop Inventory Organizer

Handles SQLite database connection, table creation, and provides
helper functions for executing queries safely.
"""

import sqlite3
import os
from datetime import datetime

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shop.db")


def get_connection():
    """Create and return a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    return conn


def init_database():
    """
    Initialize the database by creating all required tables.
    This is safe to call multiple times (uses IF NOT EXISTS).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            price REAL NOT NULL CHECK(price >= 0),
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            min_stock_level INTEGER NOT NULL DEFAULT 5,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
                ON DELETE SET NULL
        )
    """)

    # Sales table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            sold_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        )
    """)

    # Stock Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('addition', 'removal', 'sale')),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE CASCADE
        )
    """)

    # Insert default categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("Dairy", "Milk, cheese, butter, yogurt"),
            ("Grains & Cereals", "Rice, wheat, oats, flour"),
            ("Snacks", "Biscuits, chips, cookies"),
            ("Beverages", "Tea, coffee, juices, soft drinks"),
            ("Personal Care", "Soap, shampoo, toothpaste"),
            ("Household", "Detergent, cleaning supplies"),
            ("Fruits & Vegetables", "Fresh produce"),
            ("Other", "Miscellaneous items"),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            default_categories
        )

    conn.commit()
    conn.close()


def execute_query(query, params=(), fetch=False):
    """
    Execute a SQL query safely.

    Args:
        query: SQL query string
        params: Tuple of parameters for the query
        fetch: If True, returns all results; if False, returns lastrowid

    Returns:
        List of rows if fetch=True, otherwise the last inserted row ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            results = cursor.fetchall()
            conn.close()
            return results
        else:
            conn.commit()
            last_id = cursor.lastrowid
            conn.close()
            return last_id
    except sqlite3.Error as e:
        conn.close()
        raise e


def execute_query_df(query, params=()):
    """
    Execute a query and return results as a list of dictionaries.
    Useful for converting to Pandas DataFrames.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    except sqlite3.Error as e:
        conn.close()
        raise e
