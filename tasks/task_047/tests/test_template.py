import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.context import Context
from src.template import Template
from src.parser import TemplateParser, TextNode, VariableNode, IfNode, ForNode


# ── pass-to-pass: Context operations ──────────────────────────


class TestContextBasic:
    def test_get_simple(self):
        ctx = Context({"name": "Alice"})
        assert ctx.get("name") == "Alice"

    def test_get_missing_default(self):
        ctx = Context({})
        assert ctx.get("missing") is None
        assert ctx.get("missing", "fallback") == "fallback"

    def test_get_nested(self):
        ctx = Context({"user": {"name": "Bob", "age": 30}})
        assert ctx.get("user.name") == "Bob"
        assert ctx.get("user.age") == 30

    def test_set_and_get(self):
        ctx = Context()
        ctx.set("x", 42)
        assert ctx.get("x") == 42

    def test_has(self):
        ctx = Context({"a": 1})
        assert ctx.has("a") is True
        assert ctx.has("b") is False

    def test_child_context(self):
        parent = Context({"x": 1, "y": 2})
        child = parent.child(y=99, z=3)
        assert child.get("x") == 1
        assert child.get("y") == 99
        assert child.get("z") == 3

    def test_deeply_nested(self):
        ctx = Context({"a": {"b": {"c": "deep"}}})
        assert ctx.get("a.b.c") == "deep"


# ── fail-to-pass: Parser ──────────────────────────


class TestParser:
    @pytest.mark.fail_to_pass
    def test_parse_plain_text(self):
        """Plain text produces a single TextNode."""
        parser = TemplateParser()
        nodes = parser.parse("Hello, World!")
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert nodes[0].text == "Hello, World!"

    @pytest.mark.fail_to_pass
    def test_parse_variable(self):
        """{{variable}} produces TextNode + VariableNode + TextNode."""
        parser = TemplateParser()
        nodes = parser.parse("Hello, {{name}}!")
        var_nodes = [n for n in nodes if isinstance(n, VariableNode)]
        assert len(var_nodes) == 1
        assert var_nodes[0].name == "name"

    @pytest.mark.fail_to_pass
    def test_parse_if_block(self):
        """{% if x %}...{% endif %} produces an IfNode."""
        parser = TemplateParser()
        nodes = parser.parse("{% if show %}visible{% endif %}")
        if_nodes = [n for n in nodes if isinstance(n, IfNode)]
        assert len(if_nodes) == 1
        assert if_nodes[0].condition == "show"

    @pytest.mark.fail_to_pass
    def test_parse_for_block(self):
        """{% for item in items %}...{% endfor %} produces a ForNode."""
        parser = TemplateParser()
        nodes = parser.parse("{% for x in things %}{{x}}{% endfor %}")
        for_nodes = [n for n in nodes if isinstance(n, ForNode)]
        assert len(for_nodes) == 1
        assert for_nodes[0].loop_var == "x"
        assert for_nodes[0].iterable == "things"


# ── fail-to-pass: Template rendering ──────────────────────────


class TestTemplateVariables:
    @pytest.mark.fail_to_pass
    def test_simple_substitution(self):
        """{{variable}} replaced with context value."""
        tpl = Template("Hello, {{name}}!")
        result = tpl.render(Context({"name": "World"}))
        assert result == "Hello, World!"

    @pytest.mark.fail_to_pass
    def test_multiple_variables(self):
        """Multiple variables in one template."""
        tpl = Template("{{greeting}}, {{name}}!")
        result = tpl.render(Context({"greeting": "Hi", "name": "Alice"}))
        assert result == "Hi, Alice!"

    @pytest.mark.fail_to_pass
    def test_missing_variable_empty_string(self):
        """Missing variables render as empty string."""
        tpl = Template("Hello, {{name}}!")
        result = tpl.render(Context({}))
        assert result == "Hello, !"

    @pytest.mark.fail_to_pass
    def test_nested_variable_access(self):
        """{{user.name}} accesses nested dict."""
        tpl = Template("Name: {{user.name}}")
        result = tpl.render(Context({"user": {"name": "Bob"}}))
        assert result == "Name: Bob"

    @pytest.mark.fail_to_pass
    def test_variable_with_spaces(self):
        """{{ variable }} with spaces should work."""
        tpl = Template("Hello, {{ name }}!")
        result = tpl.render(Context({"name": "World"}))
        assert result == "Hello, World!"


class TestTemplateConditionals:
    @pytest.mark.fail_to_pass
    def test_if_true(self):
        """{% if x %} renders body when x is truthy."""
        tpl = Template("{% if show %}visible{% endif %}")
        result = tpl.render(Context({"show": True}))
        assert result == "visible"

    @pytest.mark.fail_to_pass
    def test_if_false(self):
        """{% if x %} skips body when x is falsy."""
        tpl = Template("{% if show %}visible{% endif %}")
        result = tpl.render(Context({"show": False}))
        assert result == ""

    @pytest.mark.fail_to_pass
    def test_if_else(self):
        """{% if x %}...{% else %}...{% endif %} uses else branch when falsy."""
        tpl = Template("{% if logged_in %}Welcome{% else %}Please log in{% endif %}")
        result = tpl.render(Context({"logged_in": False}))
        assert result == "Please log in"

    @pytest.mark.fail_to_pass
    def test_if_missing_variable_is_falsy(self):
        """Missing variable in condition is falsy."""
        tpl = Template("{% if nonexistent %}yes{% else %}no{% endif %}")
        result = tpl.render(Context({}))
        assert result == "no"


class TestTemplateLoops:
    @pytest.mark.fail_to_pass
    def test_for_loop(self):
        """{% for item in items %} iterates over list."""
        tpl = Template("{% for x in items %}[{{x}}]{% endfor %}")
        result = tpl.render(Context({"items": ["a", "b", "c"]}))
        assert result == "[a][b][c]"

    @pytest.mark.fail_to_pass
    def test_for_loop_with_nested_access(self):
        """Loop variable supports dot notation."""
        tpl = Template("{% for u in users %}{{u.name}},{% endfor %}")
        result = tpl.render(Context({
            "users": [{"name": "Alice"}, {"name": "Bob"}]
        }))
        assert result == "Alice,Bob,"

    @pytest.mark.fail_to_pass
    def test_for_loop_empty_list(self):
        """Empty list produces no output."""
        tpl = Template("{% for x in items %}{{x}}{% endfor %}")
        result = tpl.render(Context({"items": []}))
        assert result == ""


class TestTemplateNested:
    @pytest.mark.fail_to_pass
    def test_if_inside_for(self):
        """Conditional inside a loop."""
        tpl = Template(
            "{% for n in nums %}"
            "{% if n %}{{n}}{% else %}zero{% endif %}, "
            "{% endfor %}"
        )
        result = tpl.render(Context({"nums": [1, 0, 3]}))
        assert "1" in result
        assert "zero" in result
        assert "3" in result

    @pytest.mark.fail_to_pass
    def test_for_inside_if(self):
        """Loop inside a conditional."""
        tpl = Template(
            "{% if show_list %}"
            "{% for item in items %}{{item}} {% endfor %}"
            "{% endif %}"
        )
        result = tpl.render(Context({"show_list": True, "items": ["x", "y"]}))
        assert "x" in result
        assert "y" in result
