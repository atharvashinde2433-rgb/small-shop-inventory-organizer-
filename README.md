# 🏪 Small Shop Inventory Organizer

A complete, professional inventory management system built for a small retail shop. Developed as an academic project to demonstrate practical applications of Data Structures, Database Management, and Data Science concepts.

---

## 📋 Project Overview

**Small Shop Inventory Organizer** is a web-based inventory management application that helps small shop owners track products, manage stock, record sales, and analyze business performance. The application uses custom implementations of data structures (Stack and Linked List) alongside modern web technologies.

## 🎯 Problem Statement

Small retail shops often struggle with:
- Tracking product inventory manually
- Knowing when to restock products
- Analyzing sales trends
- Maintaining transaction records

This application solves these problems by providing a digital, easy-to-use inventory system with built-in analytics and predictions.

---

## ✨ Features

### Core Features
| Feature | Description |
|---------|-------------|
| **Dashboard** | KPI cards showing total products, stock units, low-stock alerts, today's sales, and inventory value |
| **Product Management** | Add, edit, delete, search, and filter products by category |
| **Inventory Management** | Add/remove stock, set minimum stock levels, low-stock alerts |
| **Sales Recording** | Select products, enter quantity, auto-reduce inventory, calculate totals |
| **Transaction History** | Complete log of all stock additions, removals, and sales with timestamps |
| **Reports & Charts** | Daily sales trends, category-wise inventory, most/least sold products |

### Data Structure Features
| Feature | Data Structure | Description |
|---------|---------------|-------------|
| **Undo Last Action** | Stack (LIFO) | Reverse the most recent inventory action (sale, stock add, stock remove) |
| **Activity Log** | Singly Linked List | In-memory activity log with most recent activities at the head |

### Data Science Features
| Feature | Description |
|---------|-------------|
| **Average Daily Sales** | Calculates average daily sales per product over the past 30 days |
| **Days of Stock Remaining** | Estimates how many days until a product runs out of stock |
| **Stock Status Warnings** | Flags products as Healthy, Low Stock, Running Out Soon, or Out of Stock |
| **Demand Summary** | Identifies highest and lowest demand products |
| **ML Demand Forecasting** | Ordinary Least Squares (OLS) Linear Regression + Moving Average trend prediction for 7–21 days ahead |
| **Smart Reorder Recommendation** | Recommends replenishment units based on forecasted demand, lead safety stock, and current inventory |

---

## 🛠️ Technology Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Core programming language |
| **Streamlit** | Web application framework |
| **SQLite** | Relational database storage |
| **Pandas & NumPy** | Data processing, statistical analysis, OLS regression |
| **Plotly** | Interactive charts and visualizations |

---

## 📊 Data Structures Used

### 1. Stack (Array-based, LIFO)
- **File:** `data_structures/stack.py`
- **Purpose:** Implements the "Undo Last Action" feature
- **How it works:** Every inventory action (sale, stock add, stock remove) is pushed onto the stack. The "Undo" button pops the most recent action and reverses it.
- **Operations:** `push()`, `pop()`, `peek()`, `is_empty()`, `size()`, `get_all()`

### 2. Singly Linked List
- **File:** `data_structures/linked_list.py`
- **Purpose:** Maintains an in-memory activity log (separate from SQLite database)
- **How it works:** Each new activity creates a Node that is added at the head of the list. Traversal gives activities in most-recent-first order.
- **Operations:** `add_to_front()`, `get_recent()`, `search()`, `get_all()`, `size()`

### 3. Arrays
- Used throughout via Python lists for storing query results, product collections, and as the underlying storage for the Stack implementation.

---

## 🗄️ Database Design

### Entity-Relationship Diagram

```
categories (1) ──── (N) products (1) ──── (N) sales
                              │
                              └── (N) stock_transactions
```

### Tables

| Table | Fields | Purpose |
|-------|--------|---------|
| **categories** | id, name, description, created_at | Product categories |
| **products** | id, name, category_id (FK), price, quantity, min_stock_level, created_at, updated_at | Product catalog |
| **sales** | id, product_id (FK), quantity, unit_price, total_amount, sold_at | Sales records |
| **stock_transactions** | id, product_id (FK), type, quantity, note, created_at | Stock movement log |

### Constraints
- Primary keys with auto-increment
- Foreign keys with CASCADE/SET NULL
- CHECK constraints for non-negative prices and quantities
- UNIQUE constraint on category names
- Automatic timestamps

---

## 🧠 Data Science Component

The `ml/demand_analysis.py` module provides:

1. **Average Daily Sales Calculation:**
   - Analyzes sales data over the past 30 days
   - Formula: `avg_daily_sales = total_sold_30d / 30`

2. **Stock Duration Estimation:**
   - Formula: `days_remaining = current_stock / avg_daily_sales`
   - Products with no sales show "N/A"

3. **Intelligent Stock Warnings:**
   - 🔴 **Out of Stock** — Quantity is 0
   - 🟡 **Low Stock** — Below minimum stock level
   - 🟠 **Running Out Soon** — Less than 7 days of stock remaining
   - 🟢 **Healthy** — Adequate stock levels

4. **Predictive Demand Forecasting & Reorder Assistant:**
   - Fits Ordinary Least Squares (OLS) regression line across historical sales timeline
   - Computes slope, direction, and $R^2$ correlation
   - Blends trend with recent 7-day moving average
   - Generates recommended replenishment formula:
     $$\text{Reorder Quantity} = \max(0, \text{Forecast Demand} + \text{Safety Stock} - \text{Current Stock})$$

---

## 📁 Project Structure

```
small-shop-inventory/
│
├── app.py                          # Main Streamlit entry point & navigation
├── requirements.txt                # Python dependencies
├── README.md                       # Complete documentation
├── .gitignore                      # Git ignore rules
│
├── database/
│   ├── __init__.py
│   └── database.py                 # SQLite setup, queries, helpers
│
├── models/
│   ├── __init__.py
│   └── product.py                  # Product data class
│
├── data_structures/
│   ├── __init__.py
│   ├── stack.py                    # Stack (LIFO) for Undo feature
│   └── linked_list.py             # Linked List for Activity Log
│
├── services/
│   ├── __init__.py
│   ├── inventory.py               # Product & stock business logic
│   ├── sales.py                   # Sales recording & retrieval
│   ├── reports.py                 # Report generation queries
│   └── seed_data.py               # Demo data generator (20 products, 500+ sales)
│
├── ml/
│   ├── __init__.py
│   └── demand_analysis.py         # Data science & ML demand forecasting
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py               # Dashboard page with KPI cards
│   ├── products.py                # Product CRUD interface
│   ├── inventory.py               # Stock management interface
│   ├── sales.py                   # Sales recording & undo interface
│   ├── transactions.py            # Transaction history & linked list log
│   ├── reports.py                 # Reports, charts & ML forecasting
│   └── settings.py                # Category CRUD, demo seeder & backups
│
└── tests/
    ├── __init__.py
    └── test_inventory.py          # Unit tests (24 passing tests)
```


---

## ⚙️ Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/small-shop-inventory.git
   cd small-shop-inventory
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

5. **Run tests:**
   ```bash
   python -m unittest tests.test_inventory -v
   ```

---

## 🚀 How to Run

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

### Quick Start Guide
1. **Dashboard** — View overall shop performance
2. **Products** — Add your shop's products with prices and categories
3. **Inventory** — Add or remove stock as shipments arrive or items expire
4. **Sales** — Record sales transactions (stock is auto-reduced)
5. **Reports** — Analyze sales trends, view demand analysis, check the activity log

---

## 📸 Screenshots

> *Screenshots will be added after the application is running.*

| Page | Description |
|------|-------------|
| Dashboard | KPI cards and summary charts |
| Products | Product list with search and filter |
| Inventory | Stock management with alerts |
| Sales | Sale recording and undo feature |
| Reports | Charts, demand analysis, transaction history |

---

## 🔮 Future Scope

- [ ] Multi-user authentication system
- [ ] Barcode scanner integration
- [ ] Export reports to PDF/Excel
- [ ] SMS/Email alerts for low stock
- [ ] Supplier management module
- [ ] Advanced ML-based demand forecasting (ARIMA/Prophet)
- [ ] Mobile-responsive PWA version
- [ ] Cloud database (PostgreSQL) for multi-device access

---

## 👨‍💻 Author

**Vinay** — 2nd Year Data Science Student

---

## 📝 License

This project is developed for academic purposes as a college project.
