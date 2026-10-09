"""
Small Shop Inventory Organizer — Main Application

Run with: streamlit run app.py

This is the entry point of the application.
It sets up the Streamlit page, sidebar navigation,
initializes the database, and routes to the appropriate page.
"""

import streamlit as st
import sys
import os

# Add project root to path so imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import init_database
from data_structures.stack import Stack
from data_structures.linked_list import LinkedList

# Import UI pages
from ui import dashboard, products, inventory, sales, transactions, reports, settings


# ── Page Configuration ──
st.set_page_config(
    page_title="Small Shop Inventory Organizer",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables (runs once per session)."""
    if 'undo_stack' not in st.session_state:
        st.session_state.undo_stack = Stack(max_size=50)

    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = LinkedList(max_size=100)


def main():
    """Main application function."""

    # Initialize database tables
    init_database()

    # Initialize session state (stack & linked list)
    init_session_state()

    # ── Sidebar Navigation ──
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/shop.png", width=80)
        st.title("🏪 Small Shop")
        st.caption("Inventory Organizer")
        st.divider()

        # Navigation menu
        page = st.radio(
            "Navigate to",
            options=[
                "🏠 Dashboard",
                "📦 Products",
                "📥 Inventory",
                "💰 Sales",
                "📝 Transactions",
                "📊 Reports",
                "⚙️ Settings",
            ],
            label_visibility="collapsed"
        )

        st.divider()

        # Sidebar info
        stack_size = st.session_state.undo_stack.size()
        log_size = st.session_state.activity_log.size()
        st.caption(f"🔄 Undo stack: {stack_size} action(s)")
        st.caption(f"🔗 Activity log: {log_size} entries")

        st.divider()
        st.markdown(
            """
            <div style='text-align: center; color: gray; font-size: 0.8em;'>
                <b>Small Shop Inventory Organizer</b><br>
                College Project — 2026<br>
                Built with ❤️ using Streamlit
            </div>
            """,
            unsafe_allow_html=True
        )

    # ── Page Routing ──
    if page == "🏠 Dashboard":
        dashboard.render()
    elif page == "📦 Products":
        products.render()
    elif page == "📥 Inventory":
        inventory.render()
    elif page == "💰 Sales":
        sales.render()
    elif page == "📝 Transactions":
        transactions.render()
    elif page == "📊 Reports":
        reports.render()
    elif page == "⚙️ Settings":
        settings.render()



if __name__ == "__main__":
    main()
