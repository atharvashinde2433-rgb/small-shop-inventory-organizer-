"""
Unit Tests — Small Shop Inventory Organizer

Tests core business logic for inventory and sales services.
Run with: python -m pytest tests/test_inventory.py -v
"""

import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_database, execute_query, execute_query_df, DB_PATH
from services.inventory import (
    add_product, get_all_products, get_product_by_id,
    update_product, delete_product, search_products,
    add_stock, remove_stock, get_all_categories,
    get_low_stock_products, get_total_products,
    get_total_stock_units, get_total_inventory_value
)
from services.sales import record_sale, get_today_sales, undo_sale
from data_structures.stack import Stack
from data_structures.linked_list import LinkedList


class TestStack(unittest.TestCase):
    """Test the Stack data structure."""

    def setUp(self):
        self.stack = Stack(max_size=5)

    def test_push_and_pop(self):
        self.stack.push({'action': 'sale', 'product_name': 'Milk', 'quantity': 2})
        self.stack.push({'action': 'stock_add', 'product_name': 'Rice', 'quantity': 10})
        result = self.stack.pop()
        self.assertEqual(result['product_name'], 'Rice')
        self.assertEqual(self.stack.size(), 1)

    def test_peek(self):
        self.stack.push({'action': 'sale', 'product_name': 'Bread', 'quantity': 1})
        result = self.stack.peek()
        self.assertEqual(result['product_name'], 'Bread')
        self.assertEqual(self.stack.size(), 1)  # peek should not remove

    def test_is_empty(self):
        self.assertTrue(self.stack.is_empty())
        self.stack.push({'action': 'test'})
        self.assertFalse(self.stack.is_empty())

    def test_pop_empty(self):
        result = self.stack.pop()
        self.assertIsNone(result)

    def test_max_size(self):
        for i in range(10):
            self.stack.push({'action': f'action_{i}'})
        self.assertEqual(self.stack.size(), 5)  # max size is 5

    def test_get_all(self):
        self.stack.push({'action': 'first'})
        self.stack.push({'action': 'second'})
        self.stack.push({'action': 'third'})
        all_items = self.stack.get_all()
        self.assertEqual(all_items[0]['action'], 'third')  # Most recent first
        self.assertEqual(all_items[2]['action'], 'first')


class TestLinkedList(unittest.TestCase):
    """Test the Linked List data structure."""

    def setUp(self):
        self.ll = LinkedList(max_size=5)

    def test_add_to_front(self):
        self.ll.add_to_front({'description': 'First action', 'action_type': 'test'})
        self.ll.add_to_front({'description': 'Second action', 'action_type': 'test'})
        self.assertEqual(self.ll.size(), 2)
        recent = self.ll.get_recent(1)
        self.assertEqual(recent[0]['description'], 'Second action')

    def test_get_recent(self):
        for i in range(5):
            self.ll.add_to_front({'description': f'Action {i}', 'action_type': 'test'})
        recent = self.ll.get_recent(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0]['description'], 'Action 4')  # Most recent

    def test_search(self):
        self.ll.add_to_front({'description': 'Sold 5 units of Milk', 'action_type': 'sale'})
        self.ll.add_to_front({'description': 'Added 10 units of Rice', 'action_type': 'stock_add'})
        results = self.ll.search('Milk')
        self.assertEqual(len(results), 1)
        self.assertIn('Milk', results[0]['description'])

    def test_max_size(self):
        for i in range(10):
            self.ll.add_to_front({'description': f'Action {i}', 'action_type': 'test'})
        self.assertEqual(self.ll.size(), 5)  # max size is 5

    def test_is_empty(self):
        self.assertTrue(self.ll.is_empty())
        self.ll.add_to_front({'description': 'test', 'action_type': 'test'})
        self.assertFalse(self.ll.is_empty())

    def test_clear(self):
        self.ll.add_to_front({'description': 'test', 'action_type': 'test'})
        self.ll.clear()
        self.assertTrue(self.ll.is_empty())


class TestInventory(unittest.TestCase):
    """Test inventory operations (requires database)."""

    @classmethod
    def setUpClass(cls):
        """Initialize a fresh test database."""
        # Use a separate test database
        import database.database as db_module
        cls._original_db_path = db_module.DB_PATH
        db_module.DB_PATH = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "test_shop.db"
        )
        # Remove old test db if exists
        if os.path.exists(db_module.DB_PATH):
            os.remove(db_module.DB_PATH)
        init_database()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        import database.database as db_module
        if os.path.exists(db_module.DB_PATH):
            os.remove(db_module.DB_PATH)
        db_module.DB_PATH = cls._original_db_path

    def test_add_product(self):
        categories = get_all_categories()
        cat_id = categories[0]['id']
        product_id = add_product("Test Milk", cat_id, 50.0, 100, 10)
        self.assertIsNotNone(product_id)
        self.assertGreater(product_id, 0)

    def test_get_product(self):
        product = search_products("Test Milk")
        self.assertTrue(len(product) > 0)
        self.assertEqual(product[0]['name'], "Test Milk")

    def test_add_stock(self):
        product = search_products("Test Milk")[0]
        original_qty = product['quantity']
        add_stock(product['id'], 20, "Test stock addition")
        updated = get_product_by_id(product['id'])
        self.assertEqual(updated['quantity'], original_qty + 20)

    def test_remove_stock(self):
        product = search_products("Test Milk")[0]
        original_qty = product['quantity']
        remove_stock(product['id'], 10, "Test removal")
        updated = get_product_by_id(product['id'])
        self.assertEqual(updated['quantity'], original_qty - 10)

    def test_prevent_negative_stock(self):
        product = search_products("Test Milk")[0]
        with self.assertRaises(ValueError):
            remove_stock(product['id'], 99999, "Should fail")

    def test_duplicate_product_name(self):
        categories = get_all_categories()
        cat_id = categories[0]['id']
        with self.assertRaises(ValueError):
            add_product("Test Milk", cat_id, 30.0, 50)

    def test_invalid_price(self):
        categories = get_all_categories()
        cat_id = categories[0]['id']
        with self.assertRaises(ValueError):
            add_product("Bad Product", cat_id, -10.0, 50)

    def test_record_sale(self):
        product = search_products("Test Milk")[0]
        original_qty = product['quantity']
        sale_info = record_sale(product['id'], 5)
        self.assertEqual(sale_info['quantity'], 5)
        self.assertEqual(sale_info['total_amount'], product['price'] * 5)
        updated = get_product_by_id(product['id'])
        self.assertEqual(updated['quantity'], original_qty - 5)

    def test_sale_insufficient_stock(self):
        product = search_products("Test Milk")[0]
        with self.assertRaises(ValueError):
            record_sale(product['id'], 99999)

    def test_dashboard_queries(self):
        total = get_total_products()
        self.assertGreater(total, 0)
        stock = get_total_stock_units()
        self.assertGreaterEqual(stock, 0)
        value = get_total_inventory_value()
        self.assertGreaterEqual(value, 0)

    def test_category_management(self):
        from services.inventory import add_category, update_category, delete_category
        cat_id = add_category("TestCategory", "Test description")
        self.assertIsNotNone(cat_id)
        update_category(cat_id, "TestCategoryUpdated", "New description")
        cats = [c for c in get_all_categories() if c['id'] == cat_id]
        self.assertEqual(len(cats), 1)
        self.assertEqual(cats[0]['name'], "TestCategoryUpdated")
        delete_category(cat_id)
        cats_after = [c for c in get_all_categories() if c['id'] == cat_id]
        self.assertEqual(len(cats_after), 0)

    def test_demand_forecasting_ml(self):
        from ml.demand_analysis import predict_future_demand
        product = search_products("Test Milk")[0]
        forecast = predict_future_demand(product['id'], forecast_days=7)
        self.assertIsNotNone(forecast)
        self.assertEqual(len(forecast['forecast_dates']), 7)
        self.assertEqual(len(forecast['forecast_sales']), 7)
        self.assertIn("trend", forecast)
        self.assertGreaterEqual(forecast['recommended_reorder'], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

