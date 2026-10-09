"""
Seed Data Service — Small Shop Inventory Organizer

Provides realistic sample data for demo, testing, and college evaluation.
Populates categories, realistic grocery items, stock transactions,
and a distribution of historical sales across past days.
"""

import sys
import os
import random
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import execute_query, execute_query_df, get_connection


def clear_all_data():
    """Clear products, sales, and transactions while keeping categories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales")
    cursor.execute("DELETE FROM stock_transactions")
    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()


def seed_sample_data():
    """
    Populates realistic retail products, initial stock transactions,
    and historical sales records spanning the past 21 days.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing tables
    cursor.execute("DELETE FROM sales")
    cursor.execute("DELETE FROM stock_transactions")
    cursor.execute("DELETE FROM products")

    # Fetch categories map
    cursor.execute("SELECT id, name FROM categories")
    cat_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Fallback if categories are missing
    if not cat_map:
        from database.database import init_database
        init_database()
        cursor.execute("SELECT id, name FROM categories")
        cat_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Sample inventory catalog: (name, category_name, price, current_qty, min_stock)
    sample_products = [
        ("Amul Taza Fresh Milk 500ml", "Dairy", 27.0, 18, 10),
        ("Nandini Full Cream Milk 1L", "Dairy", 54.0, 8, 12),     # Low stock
        ("Amul Butter 100g", "Dairy", 58.0, 25, 8),
        ("Britannia Cheese Slices 200g", "Dairy", 145.0, 3, 5),    # Low stock
        ("Basmati Rice Premium 1kg", "Grains & Cereals", 120.0, 45, 15),
        ("Aashirvaad Shudh Chakki Atta 5kg", "Grains & Cereals", 265.0, 22, 10),
        ("Tata Sampann Toor Dal 1kg", "Grains & Cereals", 160.0, 14, 8),
        ("Quaker Oats Pouch 1kg", "Grains & Cereals", 190.0, 0, 5), # Out of stock!
        ("Parle-G Gold Biscuits 1kg", "Snacks", 90.0, 60, 20),
        ("Lays Magic Masala 50g", "Snacks", 20.0, 80, 25),
        ("Haldiram Bhujia Sev 400g", "Snacks", 110.0, 19, 10),
        ("Cadbury Dairy Milk Silk 60g", "Snacks", 85.0, 4, 8),     # Low stock
        ("Tata Tea Gold 500g", "Beverages", 310.0, 28, 10),
        ("Nescafe Classic Coffee 50g", "Beverages", 185.0, 16, 6),
        ("Coca-Cola 750ml Bottle", "Beverages", 40.0, 35, 15),
        ("Dettol Original Bathing Soap 75g", "Personal Care", 38.0, 42, 15),
        ("Colgate MaxFresh Toothpaste 150g", "Personal Care", 115.0, 24, 10),
        ("Surf Excel Quick Wash 1kg", "Household", 155.0, 30, 12),
        ("Vim Dishwash Gel 500ml", "Household", 120.0, 18, 8),
        ("Good Knight Gold Flash Machine", "Household", 95.0, 12, 5),
    ]

    product_ids = []
    for name, cat_name, price, qty, min_stock in sample_products:
        cat_id = cat_map.get(cat_name, list(cat_map.values())[0] if cat_map else None)
        cursor.execute(
            """INSERT INTO products (name, category_id, price, quantity, min_stock_level, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now', '-25 days'), datetime('now', '-2 days'))""",
            (name, cat_id, price, qty, min_stock)
        )
        p_id = cursor.lastrowid
        product_ids.append((p_id, name, price, qty))

        # Initial stock transaction
        cursor.execute(
            """INSERT INTO stock_transactions (product_id, type, quantity, note, created_at)
               VALUES (?, 'addition', ?, 'Opening inventory stock', datetime('now', '-25 days'))""",
            (p_id, qty + 20)
        )

    # Generate historical sales for the past 21 days
    # High demand items: Milk, Parle-G, Lays, Tea
    # Medium demand: Rice, Atta, Dettol, Soap
    # Low demand: Coffee, Good Knight, Oats
    random.seed(42)  # Deterministic seed for reproducible evaluation
    now = datetime.now()

    for p_id, name, price, _ in product_ids:
        # Determine popularity multiplier
        if "Milk" in name or "Lays" in name or "Parle-G" in name:
            daily_prob = 0.85
            max_qty_per_sale = 5
        elif "Atta" in name or "Rice" in name or "Tea" in name or "Surf" in name:
            daily_prob = 0.60
            max_qty_per_sale = 3
        elif "Oats" in name or "Silk" in name:
            daily_prob = 0.40
            max_qty_per_sale = 2
        else:
            daily_prob = 0.50
            max_qty_per_sale = 2

        for day_offset in range(21, 0, -1):
            if random.random() < daily_prob:
                num_sales_today = random.randint(1, 3)
                for _ in range(num_sales_today):
                    sale_qty = random.randint(1, max_qty_per_sale)
                    sale_time = now - timedelta(days=day_offset, hours=random.randint(1, 10), minutes=random.randint(0, 59))
                    time_str = sale_time.strftime("%Y-%m-%d %H:%M:%S")
                    total_amount = round(sale_qty * price, 2)

                    cursor.execute(
                        """INSERT INTO sales (product_id, quantity, unit_price, total_amount, sold_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (p_id, sale_qty, price, total_amount, time_str)
                    )
                    sale_id = cursor.lastrowid

                    cursor.execute(
                        """INSERT INTO stock_transactions (product_id, type, quantity, note, created_at)
                           VALUES (?, 'sale', ?, ?, ?)""",
                        (p_id, sale_qty, f"Sale #{sale_id}", time_str)
                    )

    conn.commit()
    conn.close()
    return len(sample_products)
