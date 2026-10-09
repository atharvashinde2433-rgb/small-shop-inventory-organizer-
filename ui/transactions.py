"""
Transactions Page — Small Shop Inventory Organizer

Dedicated view for transaction auditing and educational data structure demonstration:
- Complete database audit trail of all inventory events (additions, sales, removals)
- Linked List based in-memory activity log
- CSV export for reporting
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

from services.reports import get_all_transactions, get_transactions_by_type
from services.inventory import get_all_products


def render():
    """Render the Transactions page."""
    st.title("📝 Transactions & Audit Log")
    st.markdown("Track every inventory movement with timestamps, quantities, and reference notes.")
    st.divider()

    tab1, tab2 = st.tabs(["🏛️ Database Transactions", "🔗 Educational Linked List Log"])

    # ── TAB 1: Database Transactions ──
    with tab1:
        st.subheader("Inventory Movement Audit Trail")

        # Filters row
        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            trans_type = st.selectbox(
                "Filter by Transaction Type",
                ["All Types", "Stock Additions (Stock In)", "Sales (Customer Purchases)", "Stock Removals (Damaged/Expired)"],
                key="trans_filter_type"
            )

        with col2:
            search_query = st.text_input("🔍 Filter by Product Name", placeholder="e.g. Milk, Rice", key="trans_search")

        with col3:
            limit_count = st.selectbox("Show Recent Rows", [50, 100, 200, 500, 1000], index=1)

        type_map = {
            "Stock Additions (Stock In)": "addition",
            "Sales (Customer Purchases)": "sale",
            "Stock Removals (Damaged/Expired)": "removal"
        }

        # Fetch records
        if trans_type == "All Types":
            records = get_all_transactions(limit=limit_count)
        else:
            records = get_transactions_by_type(type_map[trans_type])
            records = records[:limit_count]

        # Apply search filter if entered
        if search_query.strip() and records:
            q = search_query.strip().lower()
            records = [r for r in records if q in r['product_name'].lower() or q in (r.get('note') or '').lower()]

        if records:
            df = pd.DataFrame(records)

            # Summary metrics
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            additions_count = sum(1 for r in records if r['type'] == 'addition')
            sales_count = sum(1 for r in records if r['type'] == 'sale')
            removals_count = sum(1 for r in records if r['type'] == 'removal')
            total_units_moved = sum(r['quantity'] for r in records)

            with mcol1:
                st.metric("Total Events", len(records))
            with mcol2:
                st.metric("📥 Additions", additions_count)
            with mcol3:
                st.metric("💵 Sales", sales_count)
            with mcol4:
                st.metric("📦 Units Moved", f"{total_units_moved:,}")

            st.write("")

            # Prepare table display
            display_cols = ['id', 'product_name', 'type', 'quantity', 'note', 'created_at']
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()

            # Format type column with icons
            type_labels = {
                'addition': '📥 Stock In (+)',
                'sale': '💵 Sale (-)',
                'removal': '⚠️ Removed (-)'
            }
            df_display['type'] = df_display['type'].map(lambda t: type_labels.get(t, t))
            df_display.columns = ['ID', 'Product Name', 'Movement Type', 'Quantity', 'Note / Reference', 'Timestamp'][:len(display_cols)]

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Export button
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Transactions as CSV",
                data=csv,
                file_name=f"shop_transactions_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No transaction records found matching your filters.")

    # ── TAB 2: Educational Linked List Log ──
    with tab2:
        st.subheader("🔗 In-Memory Linked List Activity Log")
        st.markdown("""
        > **Academic Concept:** This activity stream is backed by a custom **Singly Linked List** (`data_structures/linked_list.py`).
        > Unlike the persistent SQLite database, this operates in-memory with \(O(1)\) insertion at the **Head Node**.
        """)

        if 'activity_log' not in st.session_state:
            from data_structures.linked_list import LinkedList
            st.session_state.activity_log = LinkedList(max_size=100)

        log = st.session_state.activity_log

        # Node visualization explanation
        with st.expander("🔍 How the Linked List Data Structure Works Here"):
            st.code("""
HEAD -> [Node: Recent Action | Timestamp] -> [Node: Older Action] -> ... -> None
- Time Complexity to add new event: O(1) (prepend to front)
- Time Complexity to search: O(n) (traverse from head)
- Memory: Nodes dynamically allocated in heap
            """, language="text")

        col_search, col_actions = st.columns([3, 1])
        with col_search:
            search_ll = st.text_input("🔍 Search within Linked List", placeholder="Search activity description...", key="ll_search")
        with col_actions:
            st.metric("Nodes in List", log.size())

        if search_ll.strip():
            activities = log.search(search_ll.strip())
        else:
            activities = log.get_recent(50)

        if activities:
            for i, act in enumerate(activities):
                a_type = act.get('action_type', 'unknown')
                icons = {
                    'sale': '💵',
                    'stock_add': '📥',
                    'stock_remove': '➖',
                    'product_add': '📦',
                    'product_delete': '🗑️',
                    'undo': '↩️',
                    'demo': '✨'
                }
                icon = icons.get(a_type, '🔹')
                st.markdown(f"**{icon} Node #{i+1}** `[{act.get('timestamp')}]` — {act.get('description')}")
        else:
            st.info("The linked list log is currently empty. Record a sale or add stock to see live nodes created!")

        st.divider()
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✨ Add Demo Activity Node to Linked List", use_container_width=True):
                log.add_to_front({
                    'description': f"Manual inspection event recorded by store manager",
                    'action_type': 'demo'
                })
                st.success("Added new node to head of Linked List!")
                st.rerun()

        with col_btn2:
            if st.button("🗑️ Clear Linked List", use_container_width=True):
                log.clear()
                st.info("Linked list cleared.")
                st.rerun()
