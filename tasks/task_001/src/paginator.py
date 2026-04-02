import math


class Paginator:
    """Paginate a list into fixed-size pages (1-indexed)."""

    def __init__(self, items, page_size=10):
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        self.items = list(items)
        self.page_size = page_size

    @property
    def total_pages(self):
        """Return the total number of pages."""
        return math.ceil(len(self.items) / self.page_size)

    def get_page(self, page_number):
        """Return items for the given page number (1-indexed).

        Raises ValueError if page_number is out of range.
        """
        if page_number < 1 or page_number > self.total_pages:
            raise ValueError(
                f"page_number must be between 1 and {self.total_pages}"
            )
        # BUG: uses page_number directly as if 0-indexed, but API is 1-indexed
        start = page_number * self.page_size
        end = start + self.page_size
        return self.items[start:end]
