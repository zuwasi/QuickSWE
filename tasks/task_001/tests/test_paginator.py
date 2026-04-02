import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.paginator import Paginator


# ---------------------------------------------------------------------------
# fail_to_pass: these tests expose the off-by-one bug
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_get_page_1_returns_first_items():
    p = Paginator([1, 2, 3, 4, 5], page_size=2)
    assert p.get_page(1) == [1, 2]


@pytest.mark.fail_to_pass
def test_get_last_page_returns_remaining_items():
    p = Paginator([1, 2, 3, 4, 5], page_size=2)
    assert p.get_page(3) == [5]


@pytest.mark.fail_to_pass
def test_single_page():
    p = Paginator([10, 20, 30], page_size=5)
    assert p.get_page(1) == [10, 20, 30]


# ---------------------------------------------------------------------------
# pass_to_pass: regression tests that already pass with the buggy code
# ---------------------------------------------------------------------------

def test_total_pages_exact_division():
    p = Paginator([1, 2, 3, 4], page_size=2)
    assert p.total_pages == 2


def test_total_pages_with_remainder():
    p = Paginator([1, 2, 3, 4, 5], page_size=2)
    assert p.total_pages == 3


def test_invalid_page_number_zero():
    p = Paginator([1, 2, 3], page_size=2)
    with pytest.raises(ValueError):
        p.get_page(0)


def test_invalid_page_number_too_high():
    p = Paginator([1, 2, 3], page_size=2)
    with pytest.raises(ValueError):
        p.get_page(5)


def test_page_size_must_be_positive():
    with pytest.raises(ValueError):
        Paginator([1, 2], page_size=0)
