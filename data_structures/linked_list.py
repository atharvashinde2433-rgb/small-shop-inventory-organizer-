"""
Linked List Data Structure — Small Shop Inventory Organizer

Implements a Singly Linked List for the Activity Log feature.
This is an educational data structure implementation that maintains
a recent-activity log in memory, separate from the SQLite database.

Each node stores an activity description and timestamp.
New activities are added at the head (most recent first).
"""

from datetime import datetime


class Node:
    """
    A single node in the linked list.

    Attributes:
        data: Dictionary containing activity information
        next: Reference to the next node (or None)
    """

    def __init__(self, data):
        self.data = data  # Activity info dictionary
        self.next = None  # Pointer to the next node

    def __str__(self):
        return f"[{self.data.get('timestamp', '')}] {self.data.get('description', '')}"


class LinkedList:
    """
    Singly Linked List for maintaining activity log.

    Each node's data dict contains:
        - description: str (e.g., "Sold 5 units of Milk")
        - action_type: str ('sale', 'stock_add', 'stock_remove', 'product_add', etc.)
        - timestamp: str (formatted datetime)
    """

    def __init__(self, max_size=100):
        """Initialize an empty linked list with a size limit."""
        self.head = None     # First node
        self._size = 0       # Current number of nodes
        self._max_size = max_size  # Maximum nodes to keep

    def add_to_front(self, data):
        """
        Add a new activity at the front (head) of the list.
        This makes the most recent activity first.
        """
        # Add timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
        self._size += 1

        # Trim if exceeds max size
        if self._size > self._max_size:
            self._trim()

    def _trim(self):
        """Remove nodes beyond the max size limit."""
        if self._size <= self._max_size:
            return

        current = self.head
        count = 1
        while current and count < self._max_size:
            current = current.next
            count += 1

        if current:
            current.next = None
        self._size = self._max_size

    def get_recent(self, count=10):
        """
        Get the most recent 'count' activities as a list of dicts.

        Args:
            count: Number of recent activities to return

        Returns:
            List of activity dictionaries
        """
        activities = []
        current = self.head
        while current and len(activities) < count:
            activities.append(current.data)
            current = current.next
        return activities

    def get_all(self):
        """Get all activities as a list of dicts."""
        activities = []
        current = self.head
        while current:
            activities.append(current.data)
            current = current.next
        return activities

    def search(self, keyword):
        """
        Search for activities containing a keyword.

        Args:
            keyword: String to search for in descriptions

        Returns:
            List of matching activity dictionaries
        """
        results = []
        current = self.head
        while current:
            description = current.data.get('description', '').lower()
            if keyword.lower() in description:
                results.append(current.data)
            current = current.next
        return results

    def is_empty(self):
        """Check if the list is empty."""
        return self.head is None

    def size(self):
        """Return the number of activities in the list."""
        return self._size

    def clear(self):
        """Remove all activities from the list."""
        self.head = None
        self._size = 0

    def __len__(self):
        return self._size

    def __str__(self):
        if self.is_empty():
            return "Activity Log is empty"
        activities = self.get_all()
        lines = [f"  {a.get('timestamp', '')} — {a.get('description', '')}" for a in activities]
        return f"Activity Log ({self._size} entries):\n" + "\n".join(lines)
