"""Template engine — parses and renders templates."""

from .context import Context
from .parser import TemplateParser


class Template:
    """A compiled template that can be rendered with a context.

    Usage:
        tpl = Template("Hello, {{name}}!")
        result = tpl.render(Context({"name": "World"}))
        # result == "Hello, World!"
    """

    def __init__(self, template_str: str):
        """Compile a template string.

        Args:
            template_str: The raw template string.
        """
        self._raw = template_str
        self._parser = TemplateParser()
        self._ast = None  # Should be populated by parsing

    def render(self, context: Context) -> str:
        """Render the template with the given context.

        Args:
            context: A Context object containing template variables.

        Returns:
            The rendered string.
        """
        raise NotImplementedError("Template.render not yet implemented")
