"""
Matrix Spiral Order Traversal.

Traverses a 2D matrix in spiral order: right along the top row,
down the right column, left along the bottom row, up the left column,
then repeating for inner layers.
"""


def spiral_order(matrix):
    """Return elements of a 2D matrix in spiral order.

    Traverses the matrix layer by layer from the outside in,
    going right → down → left → up for each layer.

    Args:
        matrix: A list of lists representing a 2D matrix.
                All rows must have the same length.

    Returns:
        A flat list of elements in spiral traversal order.
    """
    if not matrix or not matrix[0]:
        return []

    result = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1

    while top <= bottom and left <= right:
        # Traverse right along the top row
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1

        # Traverse down the right column
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1

        # Traverse left along the bottom row
        if top <= bottom:
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
        bottom -= 1

        # Traverse up the left column
        if left <= right:
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
        left += 2

    return result


def create_spiral_matrix(n):
    """Create an n×n matrix filled in spiral order from 1 to n².

    Args:
        n: Size of the square matrix.

    Returns:
        An n×n matrix where spiral traversal yields 1, 2, 3, ..., n².
    """
    if n <= 0:
        return []

    matrix = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1
    num = 1

    while top <= bottom and left <= right:
        for col in range(left, right + 1):
            matrix[top][col] = num
            num += 1
        top += 1

        for row in range(top, bottom + 1):
            matrix[row][right] = num
            num += 1
        right -= 1

        if top <= bottom:
            for col in range(right, left - 1, -1):
                matrix[bottom][col] = num
                num += 1
        bottom -= 1

        if left <= right:
            for row in range(bottom, top - 1, -1):
                matrix[row][left] = num
                num += 1
        left += 1

    return matrix


def print_matrix(matrix):
    """Pretty-print a matrix for debugging.

    Args:
        matrix: A 2D list to print.
    """
    if not matrix:
        print("(empty matrix)")
        return

    col_widths = []
    for col in range(len(matrix[0])):
        width = max(len(str(matrix[row][col])) for row in range(len(matrix)))
        col_widths.append(width)

    for row in matrix:
        cells = [str(val).rjust(col_widths[i]) for i, val in enumerate(row)]
        print("  ".join(cells))
