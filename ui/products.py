"""
Products Page — Small Shop Inventory Organizer

Full product management: Add, Edit, Delete, Search, Filter by category.
"""

import streamlit as st
import pandas as pd

from services.inventory import (
    get_all_products, get_all_categories, add_product,
    update_product, delete_product, search_products,
    get_products_by_category
)


def render():
    """Render the Products management page."""
    st.title("📦 Product Management")
    st.divider()

    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📜 Product List", "➕ Add Product", "✏️ Edit / Delete"])

    # ── TAB 1: Product List ──
    with tab1:
        # Search and Filter controls
        col1, col2 = st.columns(2)

        with col1:
            search_term = st.text_input("🔍 Search products", placeholder="Type product name...")

        with col2:
            categories = get_all_categories()
            cat_options = {"All Categories": None}
            for cat in categories:
                cat_options[cat['name']] = cat['id']
            selected_cat = st.selectbox("Filter by Category", options=cat_options.keys())

        # Fetch products based on filters
        if search_term:
            products = search_products(search_term)
        elif cat_options[selected_cat] is not None:
            products = get_products_by_category(cat_options[selected_cat])
        else:
            products = get_all_products()

        if products:
            df = pd.DataFrame(products)
            display_cols = ['id', 'name', 'category_name', 'price', 'quantity',
                           'min_stock_level', 'updated_at']
            # Only show columns that exist
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = ['ID', 'Name', 'Category', 'Price (₹)', 'Quantity',
                                  'Min Stock', 'Last Updated'][:len(display_cols)]

            # Highlight low stock
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(products)} product(s)")
        else:
            st.info("No products found. Add some products to get started!")

    # ── TAB 2: Add Product ──
    with tab2:
        st.subheader("Add New Product")

        with st.form("add_product_form", clear_on_submit=True):
            name = st.text_input("Product Name *", placeholder="e.g., Amul Milk 500ml")

            col1, col2 = st.columns(2)
            with col1:
                categories = get_all_categories()
                cat_names = [c['name'] for c in categories]
                selected_category = st.selectbox("Category *", options=cat_names)
            with col2:
                price = st.number_input("Price (₹) *", min_value=0.0, step=0.5, format="%.2f")

            col3, col4 = st.columns(2)
            with col3:
                quantity = st.number_input("Initial Quantity", min_value=0, step=1, value=0)
            with col4:
                min_stock = st.number_input("Minimum Stock Level", min_value=0, step=1, value=5)

            submitted = st.form_submit_button("➕ Add Product", use_container_width=True)

            if submitted:
                if not name.strip():
                    st.error("❌ Product name is required.")
                elif price <= 0:
                    st.error("❌ Price must be greater than zero.")
                else:
                    try:
                        # Find category ID
                        cat_id = next(
                            c['id'] for c in categories if c['name'] == selected_category
                        )
                        product_id = add_product(name, cat_id, price, quantity, min_stock)

                        # Log to linked list if available
                        if 'activity_log' in st.session_state:
                            st.session_state.activity_log.add_to_front({
                                'description': f"Added new product: {name} (Qty: {quantity})",
                                'action_type': 'product_add'
                            })

                        st.success(f"✅ Product '{name}' added successfully! (ID: {product_id})")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")

    # ── TAB 3: Edit / Delete ──
    with tab3:
        st.subheader("Edit or Delete Product")

        products = get_all_products()
        if not products:
            st.info("No products to edit. Add products first.")
            return

        # Product selector
        product_options = {f"{p['name']} (ID: {p['id']})": p for p in products}
        selected_product_name = st.selectbox("Select Product", options=product_options.keys())
        product = product_options[selected_product_name]

        # Edit Form
        st.markdown("#### Edit Product Details")
        with st.form("edit_product_form"):
            edit_name = st.text_input("Product Name", value=product['name'])

            col1, col2 = st.columns(2)
            with col1:
                categories = get_all_categories()
                cat_names = [c['name'] for c in categories]
                current_cat_idx = 0
                if product.get('category_name') in cat_names:
                    current_cat_idx = cat_names.index(product['category_name'])
                edit_category = st.selectbox("Category", options=cat_names, index=current_cat_idx)
            with col2:
                edit_price = st.number_input("Price (₹)", min_value=0.0, step=0.5,
                                             value=float(product['price']), format="%.2f")

            edit_min_stock = st.number_input("Minimum Stock Level", min_value=0, step=1,
                                             value=int(product['min_stock_level']))

            col_save, col_delete = st.columns(2)
            with col_save:
                save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
            with col_delete:
                delete_btn = st.form_submit_button("🗑️ Delete Product", use_container_width=True)

            if save_btn:
                try:
                    cat_id = next(c['id'] for c in categories if c['name'] == edit_category)
                    update_product(product['id'], edit_name, cat_id, edit_price, edit_min_stock)
                    st.success(f"✅ Product '{edit_name}' updated successfully!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")

            if delete_btn:
                delete_product(product['id'])
                if 'activity_log' in st.session_state:
                    st.session_state.activity_log.add_to_front({
                        'description': f"Deleted product: {product['name']}",
                        'action_type': 'product_delete'
                    })
                st.success(f"✅ Product '{product['name']}' deleted.")
                st.rerun()
