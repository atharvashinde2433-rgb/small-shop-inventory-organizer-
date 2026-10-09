"""
Stack Data Structure — Small Shop Inventory Organizer

Implements a Stack (Last-In-First-Out) for the Undo feature.
When the user performs an inventory action (sale, stock add, stock remove),
it is pushed onto this stack. "Undo" pops and reverses the last action.

This is an educational implementation using Python lists as the
underlying array-based storage.
"""


class Stack:
    """
    Array-based Stack implementation (LIFO).

    Each item stored is a dictionary with:
        - action: str ('sale', 'stock_add', 'stock_remove')
        - product_id: int
        - product_name: str
        - quantity: int
        - timestamp: str
    """

    def __init__(self, max_size=50):
        """Initialize the stack with a maximum size."""
        self._items = []        # Internal array (Python list)
        self._max_size = max_size  # Prevent unlimited memory usage

    def push(self, item):
        """
        Push an action onto the stack.
        If stack exceeds max_size, remove the oldest item.
        """
        if len(self._items) >= self._max_size:
            self._items.pop(0)  # Remove oldest to maintain size limit
        self._items.append(item)

    def pop(self):
        """
        Pop and return the most recent action from the stack.
        Returns None if stack is empty.
        """
        if self.is_empty():
            return None
        return self._items.pop()

    def peek(self):
        """
        View the most recent action without removing it.
        Returns None if stack is empty.
        """
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self):
        """Check if the stack is empty."""
        return len(self._items) == 0

    def size(self):
        """Return the number of items in the stack."""
        return len(self._items)

    def clear(self):
        """Remove all items from the stack."""
        self._items.clear()

    def get_all(self):
        """
        Return all items in the stack (top to bottom).
        Useful for displaying the undo history.
        """
        return list(reversed(self._items))

    def __len__(self):
        return self.size()

    def __str__(self):
        if self.is_empty():
            return "Stack is empty"
        items_str = "\n".join(
            f"  {i+1}. {item.get('action', '?')} — {item.get('product_name', '?')} "
            f"(qty: {item.get('quantity', '?')})"
            for i, item in enumerate(self.get_all())
        )
        return f"Undo Stack ({self.size()} actions):\n{items_str}"
