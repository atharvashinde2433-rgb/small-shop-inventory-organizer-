"""
Demand Analysis Module — Small Shop Inventory Organizer

Data Science Features:
1. Calculate average daily sales for each product
2. Estimate days of stock remaining
3. Identify products running low on stock
4. Simple demand trend analysis

This module demonstrates practical data science in inventory management.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import execute_query_df
from datetime import datetime, date, timedelta
import pandas as pd


def get_average_daily_sales():
    """
    Calculate the average daily sales for each product.

    Method:
    - Look at sales over the past 30 days
    - Calculate: total_sold / number_of_days_with_sales
    - This gives a realistic daily average
    """
    query = """
        SELECT p.id, p.name, p.quantity as current_stock,
               p.min_stock_level, p.price,
               COALESCE(SUM(s.quantity), 0) as total_sold_30d,
               COUNT(DISTINCT DATE(s.sold_at)) as days_with_sales
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id
            AND DATE(s.sold_at) >= DATE('now', '-30 days')
        GROUP BY p.id, p.name, p.quantity, p.min_stock_level, p.price
    """
    results = execute_query_df(query)

    for product in results:
        if product['days_with_sales'] > 0:
            product['avg_daily_sales'] = round(
                product['total_sold_30d'] / 30, 2  # Over the full 30-day window
            )
        else:
            product['avg_daily_sales'] = 0.0

        # Estimate days of stock remaining
        if product['avg_daily_sales'] > 0:
            product['days_of_stock_remaining'] = round(
                product['current_stock'] / product['avg_daily_sales'], 1
            )
        else:
            product['days_of_stock_remaining'] = float('inf')  # No sales = infinite days

        # Stock status
        if product['current_stock'] == 0:
            product['stock_status'] = '🔴 Out of Stock'
        elif product['current_stock'] <= product['min_stock_level']:
            product['stock_status'] = '🟡 Low Stock'
        elif product.get('days_of_stock_remaining', float('inf')) <= 7:
            product['stock_status'] = '🟠 Running Out Soon'
        else:
            product['stock_status'] = '🟢 Healthy'

    return results


def get_stock_warnings():
    """
    Get products that need attention based on:
    - Current stock below minimum level
    - Estimated days of stock remaining < 7
    - Out of stock
    """
    all_products = get_average_daily_sales()
    warnings = []

    for p in all_products:
        if p['stock_status'] != '🟢 Healthy':
            warnings.append(p)

    # Sort: out of stock first, then by days remaining
    warnings.sort(key=lambda x: (
        0 if x['stock_status'] == '🔴 Out of Stock' else
        1 if x['stock_status'] == '🟠 Running Out Soon' else 2,
        x.get('days_of_stock_remaining', float('inf'))
    ))

    return warnings


def get_sales_trend(product_id, days=30):
    """
    Get daily sales data for a specific product over the past N days.
    Useful for plotting sales trends.
    """
    start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = """
        SELECT DATE(sold_at) as sale_date,
               SUM(quantity) as daily_quantity,
               SUM(total_amount) as daily_revenue
        FROM sales
        WHERE product_id = ? AND DATE(sold_at) >= ?
        GROUP BY DATE(sold_at)
        ORDER BY sale_date
    """
    return execute_query_df(query, (product_id, start_date))


def get_demand_summary():
    """
    Generate a comprehensive demand analysis summary.
    Returns a dictionary with key insights.
    """
    products = get_average_daily_sales()

    if not products:
        return {
            'total_products': 0,
            'out_of_stock': 0,
            'low_stock': 0,
            'running_out_soon': 0,
            'healthy': 0,
            'highest_demand': None,
            'lowest_demand': None
        }

    # Count by status
    out_of_stock = sum(1 for p in products if p['stock_status'] == '🔴 Out of Stock')
    low_stock = sum(1 for p in products if p['stock_status'] == '🟡 Low Stock')
    running_out = sum(1 for p in products if p['stock_status'] == '🟠 Running Out Soon')
    healthy = sum(1 for p in products if p['stock_status'] == '🟢 Healthy')

    # Find highest and lowest demand products (with sales)
    with_sales = [p for p in products if p['avg_daily_sales'] > 0]
    highest = max(with_sales, key=lambda x: x['avg_daily_sales']) if with_sales else None
    lowest = min(with_sales, key=lambda x: x['avg_daily_sales']) if with_sales else None

    return {
        'total_products': len(products),
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'running_out_soon': running_out,
        'healthy': healthy,
        'highest_demand': highest,
        'lowest_demand': lowest,
        'all_products': products
    }


def predict_future_demand(product_id, forecast_days=7):
    """
    Predict future demand using Ordinary Least Squares (OLS) Linear Regression
    on historical daily sales.

    Parameters:
        product_id: ID of the product to forecast
        forecast_days: Number of future days to forecast (e.g. 7 or 14)

    Returns:
        Dictionary containing historical data, projected future daily sales,
        total predicted demand, recommended reorder quantity, and trend analysis.
    """
    import numpy as np

    # Fetch product details
    query_prod = "SELECT * FROM products WHERE id = ?"
    prod_rows = execute_query_df(query_prod, (product_id,))
    if not prod_rows:
        return None
    product = prod_rows[0]

    # Fetch sales across the past 30 days
    start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    query_sales = """
        SELECT DATE(sold_at) as sale_date,
               COALESCE(SUM(quantity), 0) as units_sold
        FROM sales
        WHERE product_id = ? AND DATE(sold_at) >= ?
        GROUP BY DATE(sold_at)
        ORDER BY sale_date ASC
    """
    sales_rows = execute_query_df(query_sales, (product_id, start_date))
    sales_map = {row['sale_date']: row['units_sold'] for row in sales_rows}

    # Build continuous daily timeline for past 30 days
    all_past_dates = [
        (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in reversed(range(30))
    ]
    historical_sales = [sales_map.get(d, 0) for d in all_past_dates]

    # X represents day index 0 to 29, Y represents sales
    x = np.arange(len(historical_sales), dtype=float)
    y = np.array(historical_sales, dtype=float)

    # Calculate linear regression slope and intercept using least squares
    if np.sum(y) > 0:
        # np.polyfit(x, y, 1) returns [slope, intercept]
        slope, intercept = np.polyfit(x, y, 1)
        r_matrix = np.corrcoef(x, y)
        r_squared = float(r_matrix[0, 1] ** 2) if not np.isnan(r_matrix[0, 1]) else 0.0
    else:
        slope, intercept = 0.0, 0.0
        r_squared = 0.0

    # Project future days
    forecast_dates = [
        (date.today() + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        for i in range(forecast_days)
    ]
    forecast_x = np.arange(len(historical_sales), len(historical_sales) + forecast_days, dtype=float)
    predicted_values = slope * forecast_x + intercept

    # Constrain predictions: demand cannot be negative
    # Also blend with 7-day recent moving average for robust forecasting
    recent_7d_avg = float(np.mean(historical_sales[-7:])) if len(historical_sales) >= 7 else float(np.mean(historical_sales))
    forecast_sales = []
    for val in predicted_values:
        # Blend model with recent moving average to smooth extreme slopes
        blended = max(0.0, float(0.6 * val + 0.4 * recent_7d_avg))
        forecast_sales.append(round(blended, 1))

    total_forecast_demand = sum(forecast_sales)
    current_stock = product['quantity']
    min_stock = product['min_stock_level']

    # Recommended replenishment = Expected Demand + Safety Stock (min_stock) - Current Stock
    recommended_reorder = max(0, int(round(total_forecast_demand + min_stock - current_stock)))

    # Trend categorization
    if slope > 0.05:
        trend = "📈 Upward (Increasing Demand)"
    elif slope < -0.05:
        trend = "📉 Downward (Decreasing Demand)"
    else:
        trend = "➡️ Stable Demand"

    return {
        'product_id': product['id'],
        'product_name': product['name'],
        'current_stock': current_stock,
        'min_stock_level': min_stock,
        'historical_dates': all_past_dates,
        'historical_sales': historical_sales,
        'forecast_dates': forecast_dates,
        'forecast_sales': forecast_sales,
        'total_forecast_demand': round(total_forecast_demand, 1),
        'recommended_reorder': recommended_reorder,
        'trend': trend,
        'slope': round(float(slope), 4),
        'r_squared': round(float(r_squared), 3),
        'avg_daily_sales': round(float(np.mean(historical_sales)), 2)
    }

