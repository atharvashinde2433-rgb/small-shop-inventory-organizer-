"""
Inventory Page — Small Shop Inventory Organizer

Manage stock levels: Add stock, Remove stock, View low-stock alerts.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from services.inventory import (
    get_all_products, add_stock, remove_stock,
    get_low_stock_products, get_product_by_id
)


def render():
    """Render the Inventory management page."""
    st.title("📥 Inventory Management")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["➕ Add Stock", "➖ Remove Stock", "⚠️ Low Stock Alerts"])

    products = get_all_products()

    if not products:
        st.info("No products found. Please add products first.")
        return

    # ── TAB 1: Add Stock ──
    with tab1:
        st.subheader("Add Stock to Product")

        with st.form("add_stock_form", clear_on_submit=True):
            product_options = {f"{p['name']} (Stock: {p['quantity']})": p for p in products}
            selected = st.selectbox("Select Product", options=product_options.keys(),
                                    key="add_stock_product")
            product = product_options[selected]

            col1, col2 = st.columns(2)
            with col1:
                qty = st.number_input("Quantity to Add", min_value=1, step=1, value=1)
            with col2:
                note = st.text_input("Note (optional)", placeholder="e.g., New shipment")

            submitted = st.form_submit_button("➕ Add Stock", use_container_width=True)

            if submitted:
                try:
                    add_stock(product['id'], qty, note)

                    # Push to undo stack
                    if 'undo_stack' in st.session_state:
                        st.session_state.undo_stack.push({
                            'action': 'stock_add',
                            'product_id': product['id'],
                            'product_name': product['name'],
                            'quantity': qty,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                    # Log to linked list
                    if 'activity_log' in st.session_state:
                        st.session_state.activity_log.add_to_front({
                            'description': f"Added {qty} units of {product['name']}",
                            'action_type': 'stock_add'
                        })

                    st.success(f"✅ Added {qty} units to '{product['name']}'")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")

    # ── TAB 2: Remove Stock ──
    with tab2:
        st.subheader("Remove Stock from Product")
        st.caption("Use this for damaged, expired, or returned items.")

        with st.form("remove_stock_form", clear_on_submit=True):
            product_options2 = {f"{p['name']} (Stock: {p['quantity']})": p for p in products}
            selected2 = st.selectbox("Select Product", options=product_options2.keys(),
                                     key="remove_stock_product")
            product2 = product_options2[selected2]

            col1, col2 = st.columns(2)
            with col1:
                qty2 = st.number_input("Quantity to Remove", min_value=1, step=1, value=1,
                                       key="remove_qty")
            with col2:
                note2 = st.text_input("Reason (optional)", placeholder="e.g., Expired",
                                      key="remove_note")

            submitted2 = st.form_submit_button("➖ Remove Stock", use_container_width=True)

            if submitted2:
                try:
                    remove_stock(product2['id'], qty2, note2)

                    # Push to undo stack
                    if 'undo_stack' in st.session_state:
                        st.session_state.undo_stack.push({
                            'action': 'stock_remove',
                            'product_id': product2['id'],
                            'product_name': product2['name'],
                            'quantity': qty2,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                    # Log to linked list
                    if 'activity_log' in st.session_state:
                        st.session_state.activity_log.add_to_front({
                            'description': f"Removed {qty2} units of {product2['name']}",
                            'action_type': 'stock_remove'
                        })

                    st.success(f"✅ Removed {qty2} units from '{product2['name']}'")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")

    # ── TAB 3: Low Stock Alerts ──
    with tab3:
        st.subheader("Products Below Minimum Stock Level")

        low_stock = get_low_stock_products()
        if low_stock:
            df = pd.DataFrame(low_stock)
            display_cols = ['name', 'category_name', 'quantity', 'min_stock_level', 'price']
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = ['Product', 'Category', 'Current Stock', 'Min Level', 'Price (₹)'][:len(display_cols)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            st.warning(f"⚠️ {len(low_stock)} product(s) need restocking!")
        else:
            st.success("✅ All products are above minimum stock levels!")

        # Current inventory overview
        st.subheader("📦 Full Inventory Overview")
        all_products = get_all_products()
        if all_products:
            df = pd.DataFrame(all_products)
            display_cols = ['name', 'category_name', 'price', 'quantity', 'min_stock_level']
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = ['Product', 'Category', 'Price (₹)', 'Stock', 'Min Level'][:len(display_cols)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
