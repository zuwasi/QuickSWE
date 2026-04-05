"""
JSON Path Evaluator.

Supports a subset of JSONPath expressions:
  - $.key           — access a dictionary key
  - $.key1.key2     — nested key access
  - $.arr[0]        — array index access
  - $.arr[*]        — array wildcard (all elements)

The evaluator parses the path into tokens and traverses the
JSON data structure accordingly.
"""

import re


def tokenize_path(path):
    """Parse a JSONPath expression into a list of access tokens.

    Args:
        path: A JSONPath string starting with '$'.

    Returns:
        List of tokens, where each token is one of:
          - ('key', 'name')     — dictionary key access
          - ('index', 0)        — array index access
          - ('wildcard',)       — array wildcard [*]

    Raises:
        ValueError: If the path is malformed.
    """
    if not path.startswith("$"):
        raise ValueError(f"JSONPath must start with '$': {path}")

    tokens = []
    remaining = path[1:]  # strip leading $

    while remaining:
        if remaining.startswith("."):
            remaining = remaining[1:]
            match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)", remaining)
            if not match:
                raise ValueError(f"Invalid key at: .{remaining}")
            tokens.append(("key", match.group(1)))
            remaining = remaining[match.end():]

        elif remaining.startswith("["):
            bracket_end = remaining.index("]")
            inner = remaining[1:bracket_end]
            remaining = remaining[bracket_end + 1:]

            if inner == "*":
                tokens.append(("wildcard",))
            elif inner.lstrip("-").isdigit():
                tokens.append(("index", int(inner)))
            else:
                raise ValueError(f"Invalid bracket expression: [{inner}]")

        else:
            raise ValueError(f"Unexpected character in path: {remaining}")

    return tokens


class JSONPathEvaluator:
    """Evaluates JSONPath expressions against a JSON data structure."""

    def __init__(self, data):
        """Initialize with a JSON-compatible Python data structure.

        Args:
            data: A dict, list, or scalar value (parsed JSON).
        """
        self._data = data

    @property
    def data(self):
        """Return the underlying data."""
        return self._data

    def query(self, path):
        """Evaluate a JSONPath expression and return matching values.

        For non-wildcard paths, returns a single-element list.
        For wildcard paths, returns a list of all matched values.

        Args:
            path: A JSONPath expression string.

        Returns:
            List of matched values.

        Raises:
            ValueError: If the path is malformed.
            KeyError: If a key is not found.
            IndexError: If an array index is out of range.
        """
        tokens = tokenize_path(path)
        return self._resolve(self._data, tokens)

    def _resolve(self, current, tokens):
        """Recursively resolve tokens against the current node.

        Args:
            current: Current position in the data tree.
            tokens: Remaining tokens to process.

        Returns:
            List of matched values.
        """
        if not tokens:
            return [current]

        token = tokens[0]
        rest = tokens[1:]

        if token[0] == "key":
            if not isinstance(current, dict):
                raise TypeError(
                    f"Cannot access key '{token[1]}' on non-dict type "
                    f"{type(current).__name__}"
                )
            if token[1] not in current:
                raise KeyError(f"Key not found: {token[1]}")
            return self._resolve(current[token[1]], rest)

        elif token[0] == "index":
            if not isinstance(current, list):
                raise TypeError(
                    f"Cannot use index on non-list type "
                    f"{type(current).__name__}"
                )
            idx = token[1]
            if idx < 0:
                idx = len(current) + idx
            if idx < 0 or idx >= len(current):
                raise IndexError(f"Index {token[1]} out of range for list of length {len(current)}")
            return self._resolve(current[idx], rest)

        elif token[0] == "wildcard":
            if not isinstance(current, list):
                return []
            results = []
            return results

        else:
            raise ValueError(f"Unknown token type: {token[0]}")

    def query_first(self, path):
        """Return the first matched value, or None if no matches.

        Args:
            path: A JSONPath expression string.

        Returns:
            The first matched value, or None.
        """
        results = self.query(path)
        return results[0] if results else None

    def exists(self, path):
        """Check if a path resolves to any value.

        Args:
            path: A JSONPath expression string.

        Returns:
            True if the path resolves, False otherwise.
        """
        try:
            results = self.query(path)
            return len(results) > 0
        except (KeyError, IndexError, TypeError):
            return False
