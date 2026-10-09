"""
Sales Page — Small Shop Inventory Organizer

Record new sales and view sales history.
Includes Undo feature using the Stack data structure.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from services.inventory import get_all_products, add_stock, remove_stock
from services.sales import record_sale, get_today_sales, get_all_sales, undo_sale


def render():
    """Render the Sales page."""
    st.title("💰 Sales")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🛒 New Sale", "📜 Sales History", "↩️ Undo Last Action"])

    # ── TAB 1: New Sale ──
    with tab1:
        st.subheader("Record a Sale")

        products = get_all_products()
        if not products:
            st.info("No products available. Add products first.")
            return

        # Only show products with stock
        in_stock = [p for p in products if p['quantity'] > 0]
        if not in_stock:
            st.warning("All products are out of stock!")
            return

        with st.form("sale_form", clear_on_submit=True):
            product_options = {
                f"{p['name']} — ₹{p['price']:.2f} (Stock: {p['quantity']})": p
                for p in in_stock
            }
            selected = st.selectbox("Select Product", options=product_options.keys())
            product = product_options[selected]

            col1, col2 = st.columns(2)
            with col1:
                qty = st.number_input(
                    "Quantity", min_value=1,
                    max_value=int(product['quantity']),
                    step=1, value=1
                )
            with col2:
                # Show calculated total
                total = product['price'] * qty
                st.metric("Total Amount", f"₹{total:,.2f}")

            submitted = st.form_submit_button("💵 Record Sale", use_container_width=True)

            if submitted:
                try:
                    sale_info = record_sale(product['id'], qty)

                    # Push to undo stack
                    if 'undo_stack' in st.session_state:
                        st.session_state.undo_stack.push({
                            'action': 'sale',
                            'sale_id': sale_info['sale_id'],
                            'product_id': product['id'],
                            'product_name': product['name'],
                            'quantity': qty,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                    # Log to linked list
                    if 'activity_log' in st.session_state:
                        st.session_state.activity_log.add_to_front({
                            'description': f"Sold {qty} units of {product['name']} for ₹{sale_info['total_amount']:.2f}",
                            'action_type': 'sale'
                        })

                    st.success(
                        f"✅ Sale recorded! Sold {qty} x {product['name']} "
                        f"= ₹{sale_info['total_amount']:,.2f}"
                    )
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")

    # ── TAB 2: Sales History ──
    with tab2:
        st.subheader("📝 Today's Sales")
        today_sales = get_today_sales()
        if today_sales:
            df = pd.DataFrame(today_sales)
            display_cols = ['product_name', 'quantity', 'unit_price', 'total_amount', 'sold_at']
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = ['Product', 'Qty', 'Unit Price (₹)', 'Total (₹)', 'Time'][:len(display_cols)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            total_today = sum(s['total_amount'] for s in today_sales)
            st.metric("Today's Total Revenue", f"₹{total_today:,.2f}")
        else:
            st.info("No sales today yet.")

        st.divider()
        st.subheader("📅 All Recent Sales")
        all_sales = get_all_sales(50)
        if all_sales:
            df = pd.DataFrame(all_sales)
            display_cols = ['product_name', 'quantity', 'unit_price', 'total_amount', 'sold_at']
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = ['Product', 'Qty', 'Unit Price (₹)', 'Total (₹)', 'Date/Time'][:len(display_cols)]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No sales recorded yet.")

    # ── TAB 3: Undo Last Action ──
    with tab3:
        st.subheader("↩️ Undo Last Action (Stack Feature)")
        st.markdown("""
        > **How it works:** Every sale, stock addition, or stock removal is pushed
        > onto a **Stack** (Last-In-First-Out). Clicking **Undo** pops the most
        > recent action and reverses it.
        """)

        if 'undo_stack' not in st.session_state:
            st.warning("Undo stack not initialized.")
            return

        stack = st.session_state.undo_stack

        if stack.is_empty():
            st.info("📭 No actions to undo. The stack is empty.")
        else:
            # Show what will be undone
            top_action = stack.peek()
            st.warning(
                f"**Next undo:** {top_action['action'].replace('_', ' ').title()} — "
                f"{top_action['product_name']} (Qty: {top_action['quantity']}) "
                f"at {top_action['timestamp']}"
            )

            if st.button("↩️ Undo Last Action", use_container_width=True, type="primary"):
                action = stack.pop()
                try:
                    if action['action'] == 'sale':
                        undo_sale(action['sale_id'], action['product_id'], action['quantity'])
                        msg = f"Undone: Sale of {action['quantity']} x {action['product_name']}"

                    elif action['action'] == 'stock_add':
                        remove_stock(action['product_id'], action['quantity'],
                                     "Undo: stock addition reversed")
                        msg = f"Undone: Addition of {action['quantity']} x {action['product_name']}"

                    elif action['action'] == 'stock_remove':
                        add_stock(action['product_id'], action['quantity'],
                                  "Undo: stock removal reversed")
                        msg = f"Undone: Removal of {action['quantity']} x {action['product_name']}"
                    else:
                        msg = "Unknown action"

                    # Log undo to linked list
                    if 'activity_log' in st.session_state:
                        st.session_state.activity_log.add_to_front({
                            'description': msg,
                            'action_type': 'undo'
                        })

                    st.success(f"✅ {msg}")
                    st.rerun()
                except Exception as e:
                    # Push back if undo failed
                    stack.push(action)
                    st.error(f"❌ Undo failed: {str(e)}")

            # Show undo history
            st.divider()
            st.markdown("**Undo Stack Contents (most recent first):**")
            all_actions = stack.get_all()
            for i, action in enumerate(all_actions):
                icon = "💵" if action['action'] == 'sale' else "➕" if action['action'] == 'stock_add' else "➖"
                st.text(
                    f"{i+1}. {icon} {action['action'].replace('_', ' ').title()} — "
                    f"{action['product_name']} (Qty: {action['quantity']}) | "
                    f"{action['timestamp']}"
                )
