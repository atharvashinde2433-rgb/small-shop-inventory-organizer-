"""
Settings Page — Small Shop Inventory Organizer

Allows managing categories, loading demo data, performing database backups,
and viewing academic system diagnostics.
"""

import streamlit as st
import pandas as pd
import os
import sys

from services.inventory import (
    get_all_categories, add_category, update_category, delete_category,
    get_all_products
)
from services.sales import get_all_sales
from services.seed_data import seed_sample_data, clear_all_data
from database.database import DB_PATH, execute_query_df


def render():
    """Render the Settings page."""
    st.title("⚙️ Shop Settings & Data Controls")
    st.markdown("Configure categories, manage database state, generate demo data, and export backups.")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏷️ Category Management",
        "🚀 Demo Data & Reset",
        "💾 Data Export & Backup",
        "ℹ️ System Information"
    ])

    # ── TAB 1: Category Management ──
    with tab1:
        st.subheader("Manage Product Categories")
        categories = get_all_categories()

        c_col1, c_col2 = st.columns([1, 1])

        with c_col1:
            st.markdown("##### ➕ Add New Category")
            with st.form("add_cat_form", clear_on_submit=True):
                new_cat_name = st.text_input("Category Name *", placeholder="e.g. Frozen Foods, Bakery")
                new_cat_desc = st.text_input("Description (optional)", placeholder="e.g. Ice cream, frozen snacks")
                submitted_cat = st.form_submit_button("Create Category", use_container_width=True)

                if submitted_cat:
                    if not new_cat_name.strip():
                        st.error("Category name is required.")
                    else:
                        try:
                            add_category(new_cat_name, new_cat_desc)
                            st.success(f"Category '{new_cat_name}' created successfully!")
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

        with c_col2:
            st.markdown("##### ✏️ Edit or Delete Category")
            if categories:
                cat_dict = {c['name']: c for c in categories}
                selected_cat_name = st.selectbox("Select Category", list(cat_dict.keys()), key="cat_edit_select")
                selected_cat = cat_dict[selected_cat_name]

                with st.form("edit_cat_form"):
                    edit_name = st.text_input("Update Name", value=selected_cat['name'])
                    edit_desc = st.text_input("Update Description", value=selected_cat.get('description') or '')

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        update_sub = st.form_submit_button("💾 Save Changes", use_container_width=True)
                    with btn_c2:
                        delete_sub = st.form_submit_button("🗑️ Delete", use_container_width=True)

                    if update_sub:
                        try:
                            update_category(selected_cat['id'], edit_name, edit_desc)
                            st.success(f"Updated category to '{edit_name}'")
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))

                    if delete_sub:
                        delete_category(selected_cat['id'])
                        st.success(f"Deleted category '{selected_cat_name}'")
                        st.rerun()
            else:
                st.info("No categories exist.")

        st.divider()
        st.markdown("##### 📋 Existing Categories")
        if categories:
            cat_df = pd.DataFrame(categories)[['id', 'name', 'description', 'created_at']]
            cat_df.columns = ['ID', 'Category Name', 'Description', 'Created At']
            st.dataframe(cat_df, use_container_width=True, hide_index=True)

    # ── TAB 2: Demo Data & Reset ──
    with tab2:
        st.subheader("Demo Data Setup & Reset Controls")
        st.markdown("""
        Prepare realistic mock data for college presentations, viva, and project demonstrations.
        This generates **20 realistic products** and **500+ sales over the past 21 days**.
        """)

        col_seed, col_clear = st.columns(2)

        with col_seed:
            st.info("💡 **Demo Seeder:** Perfect for demonstrating graphs, ML predictions, and KPI cards with realistic numbers.")
            if st.button("🚀 Load Realistic Demo Data", use_container_width=True, type="primary"):
                with st.spinner("Seeding realistic shop data..."):
                    count = seed_sample_data()
                    # Add to linked list
                    if 'activity_log' in st.session_state:
                        st.session_state.activity_log.add_to_front({
                            'description': f"Seeded demo dataset with {count} products & 21 days of sales",
                            'action_type': 'demo'
                        })
                    st.success(f"Successfully loaded {count} products with full sales history!")
                    st.rerun()

        with col_clear:
            st.warning("⚠️ **Danger Zone:** Wipe all products, sales, and transaction records from the database.")
            confirm_clear = st.checkbox("I confirm I want to erase all inventory & sales data", key="confirm_clear")
            if st.button("🗑️ Reset Database Records", disabled=not confirm_clear, use_container_width=True):
                clear_all_data()
                if 'undo_stack' in st.session_state:
                    st.session_state.undo_stack.clear()
                if 'activity_log' in st.session_state:
                    st.session_state.activity_log.clear()
                st.success("All products and transactions have been cleared.")
                st.rerun()

    # ── TAB 3: Data Export & Backup ──
    with tab3:
        st.subheader("Export Tables & Download Database")
        st.markdown("Export inventory records to CSV or download the raw SQLite file.")

        exp_c1, exp_c2, exp_c3 = st.columns(3)

        with exp_c1:
            products = get_all_products()
            if products:
                prod_csv = pd.DataFrame(products).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Products (CSV)",
                    data=prod_csv,
                    file_name="products_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.button("No Products to Export", disabled=True, use_container_width=True)

        with exp_c2:
            sales = get_all_sales(limit=5000)
            if sales:
                sales_csv = pd.DataFrame(sales).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Sales (CSV)",
                    data=sales_csv,
                    file_name="sales_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.button("No Sales to Export", disabled=True, use_container_width=True)

        with exp_c3:
            if os.path.exists(DB_PATH):
                with open(DB_PATH, "rb") as fp:
                    db_bytes = fp.read()
                st.download_button(
                    label="💾 Download SQLite DB (`shop.db`)",
                    data=db_bytes,
                    file_name="shop.db",
                    mime="application/x-sqlite3",
                    use_container_width=True
                )

    # ── TAB 4: System Information ──
    with tab4:
        st.subheader("ℹ️ System Diagnostics & Academic Information")

        # Database stats
        prod_count = execute_query_df("SELECT count(*) as c FROM products")[0]['c']
        sales_count = execute_query_df("SELECT count(*) as c FROM sales")[0]['c']
        cat_count = execute_query_df("SELECT count(*) as c FROM categories")[0]['c']
        tx_count = execute_query_df("SELECT count(*) as c FROM stock_transactions")[0]['c']

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("##### 🗄️ Database Metrics")
            st.write(f"- **Database Path:** `{DB_PATH}`")
            st.write(f"- **Categories:** {cat_count}")
            st.write(f"- **Products:** {prod_count}")
            st.write(f"- **Sales Records:** {sales_count}")
            st.write(f"- **Stock Transaction Events:** {tx_count}")

        with col_s2:
            st.markdown("##### 🧠 In-Memory Data Structures")
            stack_len = st.session_state.undo_stack.size() if 'undo_stack' in st.session_state else 0
            ll_len = st.session_state.activity_log.size() if 'activity_log' in st.session_state else 0
            st.write(f"- **Stack (`Stack` Class):** {stack_len} / 50 actions stored (LIFO)")
            st.write(f"- **Linked List (`LinkedList` Class):** {ll_len} / 100 nodes stored (Singly Linked)")
            st.write(f"- **Python Version:** `{sys.version.split()[0]}`")
            st.write(f"- **Framework:** `Streamlit {st.__version__}`")
