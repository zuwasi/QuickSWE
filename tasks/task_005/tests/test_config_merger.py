import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config_merger import deep_merge


# ---------------------------------------------------------------------------
# fail_to_pass: these tests expose the shallow-merge bug
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_nested_merge_preserves_base_keys():
    base = {"a": {"x": 1, "y": 2}, "b": 10}
    override = {"a": {"y": 3, "z": 4}}
    result = deep_merge(base, override)
    assert result == {"a": {"x": 1, "y": 3, "z": 4}, "b": 10}


@pytest.mark.fail_to_pass
def test_deeply_nested_merge():
    base = {"level1": {"level2": {"a": 1, "b": 2}}}
    override = {"level1": {"level2": {"b": 99, "c": 3}}}
    result = deep_merge(base, override)
    assert result == {"level1": {"level2": {"a": 1, "b": 99, "c": 3}}}


@pytest.mark.fail_to_pass
def test_mixed_nested_and_flat():
    base = {"db": {"host": "localhost", "port": 5432}, "debug": False}
    override = {"db": {"port": 3306}, "debug": True}
    result = deep_merge(base, override)
    assert result == {"db": {"host": "localhost", "port": 3306}, "debug": True}


# ---------------------------------------------------------------------------
# pass_to_pass: regression tests that already pass with the buggy code
# ---------------------------------------------------------------------------

def test_flat_merge():
    base = {"a": 1, "b": 2}
    override = {"b": 20, "c": 30}
    result = deep_merge(base, override)
    assert result == {"a": 1, "b": 20, "c": 30}


def test_empty_override():
    base = {"a": 1}
    result = deep_merge(base, {})
    assert result == {"a": 1}


def test_empty_base():
    override = {"x": 10}
    result = deep_merge({}, override)
    assert result == {"x": 10}


def test_does_not_mutate_inputs():
    base = {"a": 1}
    override = {"b": 2}
    deep_merge(base, override)
    assert base == {"a": 1}
    assert override == {"b": 2}


def test_override_replaces_non_dict_value():
    base = {"key": "old"}
    override = {"key": "new"}
    result = deep_merge(base, override)
    assert result == {"key": "new"}
