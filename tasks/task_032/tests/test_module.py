import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.template_engine import TemplateEngine


class TestTemplateEnginePassToPass:
    """Tests that should pass both before and after the fix."""

    def test_simple_variable(self):
        engine = TemplateEngine()
        result = engine.render("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"

    def test_simple_for_loop(self):
        engine = TemplateEngine()
        tpl = "{% for x in items %}{{ x }}{% endfor %}"
        result = engine.render(tpl, {"items": [1, 2, 3]})
        assert result == "123"

    def test_if_condition(self):
        engine = TemplateEngine()
        tpl = "{% if show %}visible{% endif %}"
        assert engine.render(tpl, {"show": True}) == "visible"
        assert engine.render(tpl, {"show": False}) == ""


@pytest.mark.fail_to_pass
class TestTemplateEngineFailToPass:
    """Tests that fail before the fix and pass after.

    The bug: _render_for writes directly to context[var_name] without
    saving/restoring. When inner and outer loops use the same var name,
    the outer value is lost after the inner loop.
    """

    def test_same_var_inner_loop_restores_outer(self):
        engine = TemplateEngine()
        tpl = ("{% for x in outer %}"
               "{% for x in x.inner %}{{ x }}{% endfor %}"
               ":{{ x.name }},"
               "{% endfor %}")
        context = {
            "outer": [
                {"name": "A", "inner": ["p", "q"]},
                {"name": "B", "inner": ["r", "s"]},
            ]
        }
        result = engine.render(tpl, context)
        assert "pq:A" in result
        assert "rs:B" in result

    def test_same_var_double_nested_values(self):
        engine = TemplateEngine()
        tpl = ("{% for item in items %}"
               "({% for item in item.subs %}{{ item }}{% endfor %})"
               "={{ item.id }}"
               "{% endfor %}")
        context = {
            "items": [
                {"id": "1", "subs": ["a", "b"]},
                {"id": "2", "subs": ["c", "d"]},
            ]
        }
        result = engine.render(tpl, context)
        assert "(ab)=1" in result
        assert "(cd)=2" in result

    def test_context_not_polluted_after_loop(self):
        engine = TemplateEngine()
        context = {"items": [1, 2, 3], "x": "original"}
        tpl = "{% for x in items %}{{ x }}{% endfor %}={{ x }}"
        result = engine.render(tpl, context)
        assert result == "123=original"

    def test_nested_same_name_three_levels(self):
        engine = TemplateEngine()
        tpl = ("{% for v in a %}"
               "{% for v in v.b %}"
               "{% for v in v.c %}{{ v }}{% endfor %}"
               "{% endfor %}"
               ":{{ v.name }},"
               "{% endfor %}")
        context = {
            "a": [
                {
                    "name": "X",
                    "b": [{"c": ["1", "2"]}, {"c": ["3", "4"]}],
                },
            ]
        }
        result = engine.render(tpl, context)
        assert "1234:X" in result
