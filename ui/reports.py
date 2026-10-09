"""
Reports Page — Small Shop Inventory Organizer

Displays analytical reports with charts:
- Daily sales trends
- Category-wise inventory
- Most/least sold products
- Inventory value analysis
- Data Science: stock predictions & demand analysis
- Transaction history
- Activity log (linked list)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from services.reports import (
    get_daily_sales_report, get_category_inventory_report,
    get_most_sold_products, get_least_sold_products,
    get_inventory_value_report, get_all_transactions,
    get_transactions_by_type
)
from ml.demand_analysis import get_average_daily_sales, get_demand_summary


def render():
    """Render the Reports page."""
    st.title("📊 Reports & Analytics")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Sales Reports", "📦 Inventory Reports",
        "🧠 Demand Analysis", "📝 Transactions",
        "🔗 Activity Log"
    ])

    # ── TAB 1: Sales Reports ──
    with tab1:
        st.subheader("📈 Daily Sales Trend")
        days = st.slider("Show past days", 7, 90, 30)
        sales_data = get_daily_sales_report(days)

        if sales_data:
            df = pd.DataFrame(sales_data)

            # Revenue trend
            fig = px.bar(
                df, x='sale_date', y='total_revenue',
                labels={'sale_date': 'Date', 'total_revenue': 'Revenue (₹)'},
                title='Daily Revenue',
                color_discrete_sequence=['#4CAF50']
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

            # Units sold trend
            fig2 = px.line(
                df, x='sale_date', y='total_units',
                labels={'sale_date': 'Date', 'total_units': 'Units Sold'},
                title='Daily Units Sold',
                markers=True
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No sales data available yet.")

        st.divider()

        # Most and Least Sold
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏆 Most Sold Products")
            most_sold = get_most_sold_products(10)
            if most_sold:
                df = pd.DataFrame(most_sold)
                sold_df = df[df['total_sold'] > 0]
                if not sold_df.empty:
                    fig = px.bar(
                        sold_df, x='name', y='total_sold',
                        labels={'name': 'Product', 'total_sold': 'Units Sold'},
                        color_discrete_sequence=['#2196F3']
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No sales recorded yet.")

        with col2:
            st.subheader("📉 Least Sold Products")
            least_sold = get_least_sold_products(10)
            if least_sold:
                df = pd.DataFrame(least_sold)
                df_display = df[['name', 'total_sold', 'current_stock']].copy()
                df_display.columns = ['Product', 'Total Sold', 'Current Stock']
                st.dataframe(df_display, use_container_width=True, hide_index=True)

    # ── TAB 2: Inventory Reports ──
    with tab2:
        st.subheader("📦 Category-wise Inventory")
        cat_data = get_category_inventory_report()
        if cat_data:
            df = pd.DataFrame(cat_data)

            col1, col2 = st.columns(2)
            with col1:
                df_with_stock = df[df['total_stock'] > 0]
                if not df_with_stock.empty:
                    fig = px.pie(
                        df_with_stock, values='total_stock', names='category',
                        title='Stock Distribution by Category',
                        hole=0.3
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                df_with_value = df[df['total_value'] > 0]
                if not df_with_value.empty:
                    fig = px.bar(
                        df_with_value, x='category', y='total_value',
                        title='Inventory Value by Category',
                        labels={'category': 'Category', 'total_value': 'Value (₹)'},
                        color_discrete_sequence=['#FF9800']
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)

            # Summary table
            df_display = df[['category', 'product_count', 'total_stock', 'total_value']].copy()
            df_display.columns = ['Category', 'Products', 'Total Stock', 'Value (₹)']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No inventory data.")

        st.divider()

        st.subheader("💰 Inventory Value by Product")
        value_data = get_inventory_value_report()
        if value_data:
            df = pd.DataFrame(value_data)
            df_display = df[['name', 'category', 'price', 'quantity', 'stock_value']].copy()
            df_display.columns = ['Product', 'Category', 'Price (₹)', 'Quantity', 'Stock Value (₹)']
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            total_val = df['stock_value'].sum()
            st.metric("Total Inventory Value", f"₹{total_val:,.2f}")

    # ── TAB 3: Demand Analysis (Data Science Feature) ──
    with tab3:
        st.subheader("🧠 Demand Analysis & Stock Predictions")
        st.markdown("""
        > **Data Science Feature:** This module calculates average daily sales,
        > estimates how many days of stock remain, and flags products that are
        > running low or out of stock.
        """)

        demand = get_demand_summary()

        if demand['total_products'] == 0:
            st.info("No products to analyze. Add products first.")
            return

        # Status summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🟢 Healthy", demand['healthy'])
        with col2:
            st.metric("🟡 Low Stock", demand['low_stock'])
        with col3:
            st.metric("🟠 Running Out", demand['running_out_soon'])
        with col4:
            st.metric("🔴 Out of Stock", demand['out_of_stock'])

        # Detailed table
        st.divider()
        if demand.get('all_products'):
            df = pd.DataFrame(demand['all_products'])
            display_cols = ['name', 'current_stock', 'avg_daily_sales',
                           'days_of_stock_remaining', 'stock_status']
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = ['Product', 'Current Stock', 'Avg Daily Sales',
                                  'Days Remaining', 'Status'][:len(display_cols)]
            df_display['Days Remaining'] = df_display['Days Remaining'].apply(
                lambda x: 'N/A (no sales)' if x == float('inf') else f"{x:.0f} days"
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Highlight key insights
        if demand['highest_demand']:
            st.info(
                f"📈 **Highest Demand:** {demand['highest_demand']['name']} "
                f"({demand['highest_demand']['avg_daily_sales']:.1f} units/day)"
            )
        if demand['lowest_demand']:
            st.info(
                f"📉 **Lowest Demand:** {demand['lowest_demand']['name']} "
                f"({demand['lowest_demand']['avg_daily_sales']:.1f} units/day)"
            )

        st.divider()
        st.subheader("🤖 Machine Learning Demand Forecasting & Smart Reorder")
        st.markdown("""
        > **Advanced Feature:** Uses **Ordinary Least Squares (OLS) Linear Regression** blended with **Moving Average Trend Analysis**
        > to forecast future consumer demand and suggest optimal replenishment levels to prevent stockouts.
        """)

        all_prods = demand.get('all_products', [])
        if all_prods:
            prod_names = {p['name']: p['id'] for p in all_prods}
            selected_pred_pname = st.selectbox("Select Product to Forecast Demand", list(prod_names.keys()), key="forecast_prod_select")
            forecast_horizon = st.slider("Forecast Horizon (Days into Future)", min_value=3, max_value=21, value=7, step=1)

            selected_pid = prod_names[selected_pred_pname]
            from ml.demand_analysis import predict_future_demand
            forecast_res = predict_future_demand(selected_pid, forecast_days=forecast_horizon)

            if forecast_res:
                fc1, fc2, fc3, fc4 = st.columns(4)
                with fc1:
                    st.metric("📦 Current Stock", f"{forecast_res['current_stock']} units")
                with fc2:
                    st.metric(f"🔮 Predicted Demand ({forecast_horizon}d)", f"{forecast_res['total_forecast_demand']} units")
                with fc3:
                    reorder_val = forecast_res['recommended_reorder']
                    st.metric("🛒 Recommended Reorder", f"{reorder_val} units", delta=f"{reorder_val} needed" if reorder_val > 0 else "Sufficient", delta_color="inverse" if reorder_val > 0 else "normal")
                with fc4:
                    st.metric("📊 Trend Direction", forecast_res['trend'])

                # Forecast visualization chart
                hist_df = pd.DataFrame({
                    'Date': forecast_res['historical_dates'],
                    'Units': forecast_res['historical_sales'],
                    'Type': 'Historical Sales'
                })
                future_df = pd.DataFrame({
                    'Date': forecast_res['forecast_dates'],
                    'Units': forecast_res['forecast_sales'],
                    'Type': 'Forecasted Demand (Predicted)'
                })
                combined_df = pd.concat([hist_df, future_df], ignore_index=True)

                fig_forecast = px.line(
                    combined_df, x='Date', y='Units', color='Type',
                    markers=True,
                    title=f"Demand Forecast for '{selected_pred_pname}' ({forecast_horizon} Days Ahead)",
                    color_discrete_map={
                        'Historical Sales': '#1976D2',
                        'Forecasted Demand (Predicted)': '#E91E63'
                    }
                )
                fig_forecast.add_hline(
                    y=forecast_res['min_stock_level'],
                    line_dash="dash", line_color="orange",
                    annotation_text=f"Min Stock ({forecast_res['min_stock_level']})"
                )
                fig_forecast.update_layout(height=380)
                st.plotly_chart(fig_forecast, use_container_width=True)


    # ── TAB 4: Transaction History ──
    with tab4:
        st.subheader("📝 Transaction History")

        trans_type = st.selectbox(
            "Filter by type",
            ["All", "Stock Additions", "Stock Removals", "Sales"]
        )

        type_map = {
            "Stock Additions": "addition",
            "Stock Removals": "removal",
            "Sales": "sale"
        }

        if trans_type == "All":
            transactions = get_all_transactions(200)
        else:
            transactions = get_transactions_by_type(type_map[trans_type])

        if transactions:
            df = pd.DataFrame(transactions)
            display_cols = ['product_name', 'type', 'quantity', 'note', 'created_at']
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = ['Product', 'Type', 'Quantity', 'Note', 'Date/Time'][:len(display_cols)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(transactions)} transaction(s)")
        else:
            st.info("No transactions recorded yet.")

    # ── TAB 5: Activity Log (Linked List Feature) ──
    with tab5:
        st.subheader("🔗 Activity Log (Linked List Feature)")
        st.markdown("""
        > **How it works:** This log uses a **Singly Linked List** data structure.
        > Each new activity is added at the **head** of the list, making the most
        > recent activity appear first. This is an educational in-memory data
        > structure, separate from the SQLite database.
        """)

        if 'activity_log' not in st.session_state:
            st.warning("Activity log not initialized.")
            return

        log = st.session_state.activity_log

        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search activities", key="log_search",
                                        placeholder="Type to search...")
        with col2:
            st.metric("Total Activities", log.size())

        if search_term:
            activities = log.search(search_term)
        else:
            activities = log.get_recent(50)

        if activities:
            for i, activity in enumerate(activities):
                action_type = activity.get('action_type', 'unknown')
                icons = {
                    'sale': '💵', 'stock_add': '➕', 'stock_remove': '➖',
                    'product_add': '📦', 'product_delete': '🗑️',
                    'undo': '↩️', 'unknown': '•'
                }
                icon = icons.get(action_type, '•')
                timestamp = activity.get('timestamp', '')
                description = activity.get('description', '')
                st.text(f"{icon} [{timestamp}] {description}")
        else:
            st.info("📭 No activities logged yet. Perform some actions to see them here!")

        if not log.is_empty():
            if st.button("🗑️ Clear Activity Log"):
                log.clear()
                st.success("Activity log cleared.")
                st.rerun()
