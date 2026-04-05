"""
Trie (Prefix Tree) with autocomplete support.

Supports inserting words, searching for exact matches, prefix checking,
and autocompletion that returns all words sharing a given prefix.
"""


class TrieNode:
    """A single node in the trie."""

    def __init__(self):
        self.children = {}
        self.is_end = False
        self.count = 0  # number of words passing through this node


class Trie:
    """Prefix tree supporting insert, search, and autocomplete."""

    def __init__(self):
        self._root = TrieNode()
        self._word_count = 0

    @property
    def word_count(self):
        """Return the total number of words in the trie."""
        return self._word_count

    def insert(self, word):
        """Insert a word into the trie.

        Args:
            word: The word to insert (must be a non-empty string).

        Raises:
            ValueError: If word is empty or not a string.
        """
        if not isinstance(word, str) or not word:
            raise ValueError("Word must be a non-empty string")

        node = self._root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.count += 1

        if not node.is_end:
            self._word_count += 1
        node.is_end = True

    def search(self, word):
        """Check if an exact word exists in the trie.

        Args:
            word: The word to search for.

        Returns:
            True if the word exists, False otherwise.
        """
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix):
        """Check if any word in the trie starts with the given prefix.

        Args:
            prefix: The prefix to check.

        Returns:
            True if any word has this prefix, False otherwise.
        """
        return self._find_node(prefix) is not None

    def autocomplete(self, prefix, max_results=None):
        """Return all words starting with the given prefix.

        Words should be returned in alphabetical order.

        Args:
            prefix: The prefix to search for.
            max_results: Optional limit on number of results.

        Returns:
            List of words matching the prefix, in alphabetical order.
        """
        node = self._find_node(prefix)
        if node is None:
            return []

        results = []
        self._collect_words(node, prefix, results, max_results)
        return results

    def delete(self, word):
        """Remove a word from the trie.

        Args:
            word: The word to delete.

        Returns:
            True if the word was found and deleted, False otherwise.
        """
        node = self._find_node(word)
        if node is None or not node.is_end:
            return False
        node.is_end = False
        self._word_count -= 1
        return True

    def _find_node(self, prefix):
        """Navigate to the node corresponding to the given prefix.

        Args:
            prefix: The prefix string.

        Returns:
            The TrieNode at the end of the prefix path, or None.
        """
        node = self._root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def _collect_words(self, node, prefix, results, max_results):
        """Recursively collect all words under a node using DFS.

        Args:
            node: Current trie node.
            prefix: Current prefix built so far.
            results: List to append found words to.
            max_results: Optional limit.
        """
        if max_results is not None and len(results) >= max_results:
            return

        if node.is_end:
            results.append(prefix)

        for char in node.children:
            self._collect_words(
                node.children[char], prefix + char, results, max_results
            )

    def __len__(self):
        return self._word_count

    def __contains__(self, word):
        return self.search(word)
