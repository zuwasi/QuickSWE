"""AST node classes for the expression evaluator.

Existing nodes: NumberNode, BinOpNode.
TODO: Add UnaryOpNode, ComparisonNode, BooleanNode as needed.
"""


class ASTNode:
    """Base class for all AST nodes."""
    pass


class NumberNode(ASTNode):
    """Represents a numeric literal.

    Attributes:
        value: The numeric value (int or float).
    """

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"NumberNode({self.value!r})"

    def __eq__(self, other):
        return isinstance(other, NumberNode) and self.value == other.value


class BinOpNode(ASTNode):
    """Represents a binary operation.

    Attributes:
        op: The operator string ('+', '-', '*', '/', '^').
        left: The left operand (ASTNode).
        right: The right operand (ASTNode).
    """

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinOpNode({self.op!r}, {self.left!r}, {self.right!r})"

    def __eq__(self, other):
        return (isinstance(other, BinOpNode) and self.op == other.op
                and self.left == other.left and self.right == other.right)
