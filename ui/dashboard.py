"""
Dashboard Page — Small Shop Inventory Organizer

Displays key performance indicators (KPIs) and summary charts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from services.inventory import (
    get_total_products, get_total_stock_units,
    get_low_stock_products, get_total_inventory_value
)
from services.sales import get_today_sales_total, get_today_sales
from services.reports import get_category_inventory_report, get_daily_sales_report
from ml.demand_analysis import get_stock_warnings


def render():
    """Render the Dashboard page."""
    st.title("🏠 Dashboard")
    st.markdown("Welcome to your **Small Shop Inventory Organizer**!")
    st.divider()

    # ── KPI Cards ──
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="📦 Total Products", value=get_total_products())
    with col2:
        st.metric(label="📊 Total Stock Units", value=f"{get_total_stock_units():,}")
    with col3:
        low_stock = get_low_stock_products()
        st.metric(label="⚠️ Low Stock Items", value=len(low_stock))
    with col4:
        st.metric(label="💰 Today's Sales", value=f"₹{get_today_sales_total():,.2f}")
    with col5:
        st.metric(label="🏦 Inventory Value", value=f"₹{get_total_inventory_value():,.2f}")

    st.divider()

    # ── Charts Row ──
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📈 Sales Trend (Last 30 Days)")
        sales_data = get_daily_sales_report(30)
        if sales_data:
            df = pd.DataFrame(sales_data)
            fig = px.line(
                df, x='sale_date', y='total_revenue',
                labels={'sale_date': 'Date', 'total_revenue': 'Revenue (₹)'},
                markers=True
            )
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data yet. Start recording sales!")

    with chart_col2:
        st.subheader("📊 Category-wise Inventory")
        cat_data = get_category_inventory_report()
        if cat_data:
            df = pd.DataFrame(cat_data)
            df_with_stock = df[df['total_stock'] > 0]
            if not df_with_stock.empty:
                fig = px.pie(
                    df_with_stock, values='total_stock', names='category',
                    hole=0.4
                )
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No products in inventory yet.")
        else:
            st.info("No categories found.")

    st.divider()

    # ── Stock Warnings ──
    st.subheader("⚠️ Stock Alerts")
    warnings = get_stock_warnings()
    if warnings:
        df = pd.DataFrame(warnings)[['name', 'current_stock', 'min_stock_level',
                                      'avg_daily_sales', 'days_of_stock_remaining',
                                      'stock_status']]
        df.columns = ['Product', 'Current Stock', 'Min Level', 'Avg Daily Sales',
                      'Days Remaining', 'Status']
        # Replace inf with 'N/A'
        df['Days Remaining'] = df['Days Remaining'].apply(
            lambda x: 'N/A' if x == float('inf') else f"{x:.0f} days"
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ All products are well-stocked!")

    # ── Today's Sales Table ──
    st.subheader("📝 Today's Sales")
    today_sales = get_today_sales()
    if today_sales:
        df = pd.DataFrame(today_sales)[['product_name', 'quantity', 'unit_price', 'total_amount', 'sold_at']]
        df.columns = ['Product', 'Qty', 'Unit Price (₹)', 'Total (₹)', 'Time']
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No sales recorded today.")
