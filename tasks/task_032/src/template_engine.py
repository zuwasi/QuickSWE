"""
Simple template engine supporting variable interpolation, for loops,
if/else conditionals, and filters.

Syntax:
  {{ variable }}           - Variable interpolation
  {% for item in list %}   - For loop
  {% endfor %}
  {% if condition %}       - Conditional
  {% else %}
  {% endif %}
  {{ value|filter }}       - Filters
"""

import re
from typing import Any, Dict, List, Optional, Callable


class TemplateError(Exception):
    """Raised on template parsing or rendering errors."""
    pass


class TemplateNode:
    """Base class for template AST nodes."""
    pass


class TextNode(TemplateNode):
    def __init__(self, text: str):
        self.text = text


class VarNode(TemplateNode):
    def __init__(self, name: str, filters: List[str] = None):
        self.name = name
        self.filters = filters or []


class ForNode(TemplateNode):
    def __init__(self, var_name: str, iterable_name: str,
                 body: List[TemplateNode]):
        self.var_name = var_name
        self.iterable_name = iterable_name
        self.body = body


class IfNode(TemplateNode):
    def __init__(self, condition: str, true_body: List[TemplateNode],
                 false_body: List[TemplateNode] = None):
        self.condition = condition
        self.true_body = true_body
        self.false_body = false_body or []


class TemplateParser:
    """Parses a template string into an AST."""

    TAG_RE = re.compile(r'(\{\{.*?\}\}|\{%.*?%\})')

    def parse(self, template: str) -> List[TemplateNode]:
        tokens = self.TAG_RE.split(template)
        return self._parse_tokens(iter(tokens), None)

    def _parse_tokens(self, tokens, end_tag: Optional[str]) -> List[TemplateNode]:
        nodes = []
        for token in tokens:
            token_stripped = token.strip()
            if not token_stripped:
                continue

            if token_stripped.startswith('{{') and token_stripped.endswith('}}'):
                expr = token_stripped[2:-2].strip()
                parts = expr.split('|')
                name = parts[0].strip()
                filters = [f.strip() for f in parts[1:]]
                nodes.append(VarNode(name, filters))

            elif token_stripped.startswith('{%') and token_stripped.endswith('%}'):
                tag_content = token_stripped[2:-2].strip()

                if tag_content.startswith('for '):
                    parts = tag_content[4:].strip().split(' in ')
                    var_name = parts[0].strip()
                    iter_name = parts[1].strip()
                    body = self._parse_tokens(tokens, 'endfor')
                    nodes.append(ForNode(var_name, iter_name, body))

                elif tag_content.startswith('if '):
                    condition = tag_content[3:].strip()
                    true_body = self._parse_tokens(tokens, 'else_or_endif')
                    false_body = []
                    if self._last_end == 'else':
                        false_body = self._parse_tokens(tokens, 'endif')
                    nodes.append(IfNode(condition, true_body, false_body))

                elif tag_content == 'endfor':
                    self._last_end = 'endfor'
                    return nodes

                elif tag_content == 'else':
                    self._last_end = 'else'
                    return nodes

                elif tag_content == 'endif':
                    self._last_end = 'endif'
                    return nodes

            else:
                if token:
                    nodes.append(TextNode(token))

        return nodes


class TemplateEngine:
    """Renders templates with variable substitution, loops, and conditionals."""

    def __init__(self):
        self._filters: Dict[str, Callable] = {
            'upper': lambda x: str(x).upper(),
            'lower': lambda x: str(x).lower(),
            'title': lambda x: str(x).title(),
            'strip': lambda x: str(x).strip(),
            'length': lambda x: str(len(x)),
            'default': lambda x, d='': x if x else d,
        }
        self._parser = TemplateParser()

    def register_filter(self, name: str, func: Callable):
        self._filters[name] = func

    def render(self, template: str, context: Dict[str, Any]) -> str:
        nodes = self._parser.parse(template)
        return self._render_nodes(nodes, context)

    def _render_nodes(self, nodes: List[TemplateNode],
                      context: Dict[str, Any]) -> str:
        parts = []
        for node in nodes:
            if isinstance(node, TextNode):
                parts.append(node.text)
            elif isinstance(node, VarNode):
                parts.append(self._render_var(node, context))
            elif isinstance(node, ForNode):
                parts.append(self._render_for(node, context))
            elif isinstance(node, IfNode):
                parts.append(self._render_if(node, context))
        return ''.join(parts)

    def _render_var(self, node: VarNode, context: Dict[str, Any]) -> str:
        value = self._resolve(node.name, context)
        for f_name in node.filters:
            if f_name in self._filters:
                value = self._filters[f_name](value)
        return str(value) if value is not None else ''

    def _resolve(self, name: str, context: Dict[str, Any]) -> Any:
        parts = name.split('.')
        obj = context
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            elif hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return None
            if obj is None:
                return None
        return obj

    def _render_for(self, node: ForNode, context: Dict[str, Any]) -> str:
        iterable = self._resolve(node.iterable_name, context)
        if iterable is None:
            return ''

        parts = []
        for item in iterable:
            context[node.var_name] = item
            parts.append(self._render_nodes(node.body, context))
        return ''.join(parts)

    def _render_if(self, node: IfNode, context: Dict[str, Any]) -> str:
        value = self._resolve(node.condition, context)
        if value:
            return self._render_nodes(node.true_body, context)
        else:
            return self._render_nodes(node.false_body, context)

    def render_string(self, template: str, **kwargs) -> str:
        return self.render(template, kwargs)
