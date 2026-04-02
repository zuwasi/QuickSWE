"""Formatter — converts an AST back to a string representation.

Currently handles NumberNode and BinOpNode.
TODO: Handle new node types.
"""

from .ast_nodes import NumberNode, BinOpNode


class Formatter:
    """Formats an AST as a human-readable expression string."""

    def format(self, node):
        """Format an AST node as a string.

        Args:
            node: An ASTNode instance.

        Returns:
            String representation of the expression.
        """
        if isinstance(node, NumberNode):
            if isinstance(node.value, float) and node.value == int(node.value):
                return str(int(node.value))
            return str(node.value)

        if isinstance(node, BinOpNode):
            left = self.format(node.left)
            right = self.format(node.right)
            return f"({left} {node.op} {right})"

        raise TypeError(f"Unknown node type: {type(node).__name__}")
