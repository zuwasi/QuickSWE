"""Evaluator — walks the AST and computes the result.

Currently handles NumberNode and BinOpNode (+, -, *, /).
TODO: Handle new node types (UnaryOpNode, ComparisonNode, BooleanNode)
      and new operators (^, comparisons, boolean).
"""

from .ast_nodes import NumberNode, BinOpNode


class Evaluator:
    """Evaluates an AST to produce a result."""

    def evaluate(self, node):
        """Evaluate an AST node and return its value.

        Args:
            node: An ASTNode instance.

        Returns:
            The computed value (number, bool, etc.).

        Raises:
            ZeroDivisionError: If dividing by zero.
            TypeError: If an unknown node type is encountered.
        """
        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, BinOpNode):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            if node.op == '+':
                return left + right
            elif node.op == '-':
                return left - right
            elif node.op == '*':
                return left * right
            elif node.op == '/':
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return left / right
            else:
                raise TypeError(f"Unknown operator: {node.op!r}")

        raise TypeError(f"Unknown node type: {type(node).__name__}")
