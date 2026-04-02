# Feature Request: Template Engine with Conditionals and Loops

## Summary

Implement a template engine that supports `{{variable}}` substitution, `{% if %}...{% else %}...{% endif %}` conditionals, `{% for item in list %}...{% endfor %}` loops, and nested variable access `{{user.name}}`.

## Current State

- `src/template.py`: Stub `Template` class with `render(context)` raising `NotImplementedError`.
- `src/parser.py`: Stub `TemplateParser` with `parse(template_str)` raising `NotImplementedError`.
- `src/context.py`: `Context` class for variable storage — working, supports nested access via dot notation.

## Requirements

### Template Syntax
1. **Variable substitution**: `{{variable_name}}` replaced with the variable's value from context. Missing variables default to empty string.
2. **Dot notation**: `{{user.name}}` accesses nested dict keys or object attributes.
3. **Conditionals**: `{% if condition %}...{% endif %}` and `{% if condition %}...{% else %}...{% endif %}`. Condition is a variable name — truthy if exists and is truthy value.
4. **For loops**: `{% for item in items %}...{% endfor %}`. Inside the loop, `{{item}}` refers to the current element. Nested access works: `{{item.name}}`.
5. **Nesting**: Conditionals and loops can be nested inside each other.

### Parser (`src/parser.py`)
- `parse(template_str) -> list[Node]` — produces an AST (list of nodes).
- Node types: `TextNode`, `VariableNode`, `IfNode`, `ForNode`.
- Nodes are defined in the parser module.

### Template (`src/template.py`)
- `Template(template_str)` — parses on construction.
- `render(context: Context) -> str` — renders the template.

### Context (`src/context.py`)
- Already implemented. Supports `get(key)` with dot notation, `set(key, value)`.

## Edge Cases
- Missing variables render as empty string (no error).
- Empty for loop list produces no output.
- Falsy values (`0`, `""`, `None`, `False`, `[]`) in if conditions take the else branch.
- Whitespace in tags is flexible: `{{ var }}`, `{{var}}`, `{%if x%}` all work.
