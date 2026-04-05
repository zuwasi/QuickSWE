import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.trie import Trie


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestTrieBasics:
    """Tests for basic trie operations that already work correctly."""

    def test_insert_and_search(self):
        t = Trie()
        t.insert("hello")
        t.insert("help")
        assert t.search("hello") is True
        assert t.search("help") is True
        assert t.search("hell") is False

    def test_starts_with(self):
        t = Trie()
        t.insert("python")
        t.insert("pytorch")
        assert t.starts_with("py") is True
        assert t.starts_with("ja") is False

    def test_word_count(self):
        t = Trie()
        t.insert("a")
        t.insert("b")
        t.insert("c")
        assert t.word_count == 3


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestAutocompleteOrdering:
    """Tests for alphabetical ordering of autocomplete results."""

    @pytest.mark.fail_to_pass
    def test_autocomplete_alphabetical_order(self):
        """Results must be alphabetical regardless of insertion order."""
        t = Trie()
        # Insert in reverse alphabetical order
        for word in ["cherry", "banana", "avocado", "blueberry", "coconut"]:
            t.insert(word)
        results = t.autocomplete("")
        assert results == sorted(results), (
            f"Expected alphabetical order, got: {results}"
        )

    @pytest.mark.fail_to_pass
    def test_autocomplete_prefix_sorted(self):
        """Autocomplete with a prefix should still be sorted."""
        t = Trie()
        # Insert in non-alphabetical order
        for word in ["apply", "apple", "application", "appetite", "approve"]:
            t.insert(word)
        results = t.autocomplete("app")
        expected = ["appetite", "apple", "application", "apply", "approve"]
        assert results == expected, f"Expected {expected}, got {results}"

    @pytest.mark.fail_to_pass
    def test_autocomplete_max_results_sorted(self):
        """Even with max_results, the first N should be alphabetically first."""
        t = Trie()
        for word in ["zebra", "yak", "xenon", "wolf", "vulture"]:
            t.insert(word)
        results = t.autocomplete("", max_results=3)
        assert results == ["vulture", "wolf", "xenon"], (
            f"First 3 alphabetically should be ['vulture', 'wolf', 'xenon'], got {results}"
        )
