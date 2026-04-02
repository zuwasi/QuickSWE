"""Template parser — produces an AST from template strings."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextNode:
    """Plain text content."""
    text: str


@dataclass
class VariableNode:
    """Variable substitution: {{variable_name}}."""
    name: str


@dataclass
class IfNode:
    """Conditional block: {% if condition %}...{% else %}...{% endif %}."""
    condition: str
    body: list = field(default_factory=list)       # Nodes for true branch
    else_body: list = field(default_factory=list)   # Nodes for false branch


@dataclass
class ForNode:
    """Loop block: {% for item in items %}...{% endfor %}."""
    loop_var: str     # e.g., "item"
    iterable: str     # e.g., "items"
    body: list = field(default_factory=list)


class TemplateParser:
    """Parses a template string into an AST (list of Nodes).

    Supported syntax:
    - {{variable}} — variable substitution
    - {% if condition %}...{% else %}...{% endif %}
    - {% for item in iterable %}...{% endfor %}
    """

    def parse(self, template_str: str) -> list:
        """Parse a template string into a list of AST nodes.

        Args:
            template_str: The raw template string.

        Returns:
            List of Node objects (TextNode, VariableNode, IfNode, ForNode).
        """
        raise NotImplementedError("TemplateParser.parse not yet implemented")
