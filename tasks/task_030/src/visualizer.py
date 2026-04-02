"""ASCII graph visualizer.

RED HERRING: This module has complex string formatting and grid-based
rendering logic that looks suspicious, but it works correctly.
The shortest path bugs are NOT here.
"""


class GraphVisualizer:
    """Renders a graph as ASCII art.

    The rendering logic is complex but correct. Each node is placed
    on a grid and edges are drawn as lines between them.
    """

    def __init__(self, graph, cell_width=12, cell_height=3):
        self._graph = graph
        self._cell_width = cell_width
        self._cell_height = cell_height
        self._positions = {}
        self._grid = []

    def auto_layout(self):
        """Automatically position nodes in a grid layout.

        Uses a simple row-based layout. This has some tricky modular
        arithmetic but produces correct results.
        """
        nodes = sorted(self._graph.nodes(), key=str)
        cols = max(1, int(len(nodes) ** 0.5))

        for i, node in enumerate(nodes):
            row = i // cols
            col = i % cols
            self._positions[node] = (row, col)

    def set_position(self, node, row, col):
        """Manually set a node's position."""
        self._positions[node] = (row, col)

    def render(self):
        """Render the graph as an ASCII string.

        This looks complex with the grid calculations and edge drawing,
        but each step is straightforward and correct.
        """
        if not self._positions:
            self.auto_layout()

        max_row = max(r for r, c in self._positions.values()) + 1
        max_col = max(c for r, c in self._positions.values()) + 1

        grid_height = max_row * self._cell_height
        grid_width = max_col * self._cell_width
        grid = [[' ' for _ in range(grid_width)] for _ in range(grid_height)]

        # Draw nodes
        for node, (row, col) in self._positions.items():
            y = row * self._cell_height + self._cell_height // 2
            x = col * self._cell_width + self._cell_width // 2

            label = str(node)
            # Truncate label if too long — this looks like it could cause
            # off-by-one errors but it correctly centers the label
            max_label = self._cell_width - 2
            if len(label) > max_label:
                label = label[:max_label - 1] + '…'

            start_x = x - len(label) // 2
            for i, ch in enumerate(label):
                if 0 <= start_x + i < grid_width and 0 <= y < grid_height:
                    grid[y][start_x + i] = ch

            # Draw brackets around node
            if start_x - 1 >= 0:
                grid[y][start_x - 1] = '['
            if start_x + len(label) < grid_width:
                grid[y][start_x + len(label)] = ']'

        # Draw edges (horizontal connections only for simplicity)
        for edge in self._graph.all_edges():
            if edge.source in self._positions and edge.target in self._positions:
                sr, sc = self._positions[edge.source]
                tr, tc = self._positions[edge.target]

                sy = sr * self._cell_height + self._cell_height // 2
                sx = sc * self._cell_width + self._cell_width // 2
                ty = tr * self._cell_height + self._cell_height // 2
                tx = tc * self._cell_width + self._cell_width // 2

                # Draw horizontal line for same-row edges
                if sr == tr and sc != tc:
                    start_x = min(sx, tx) + len(str(edge.source)) // 2 + 2
                    end_x = max(sx, tx) - len(str(edge.target)) // 2 - 2

                    for x in range(start_x, end_x + 1):
                        if 0 <= x < grid_width:
                            grid[sy][x] = '-'

                    # Add weight label
                    mid_x = (start_x + end_x) // 2
                    weight_str = str(int(edge.weight) if edge.weight == int(edge.weight) else edge.weight)
                    label_start = mid_x - len(weight_str) // 2
                    for i, ch in enumerate(weight_str):
                        pos = label_start + i
                        if 0 <= pos < grid_width:
                            grid[sy][pos] = ch

                # Draw vertical line for same-column edges
                elif sc == tc and sr != tr:
                    start_y = min(sy, ty) + 1
                    end_y = max(sy, ty) - 1
                    x = sx

                    for y in range(start_y, end_y + 1):
                        if 0 <= y < grid_height and 0 <= x < grid_width:
                            grid[y][x] = '|'

        return '\n'.join(''.join(row).rstrip() for row in grid)

    def render_with_path(self, path, dist=None):
        """Render the graph with a path highlighted.

        Adds asterisks around nodes on the path and shows the total
        distance.
        """
        base = self.render()
        lines = base.split('\n')

        # Simple approach: just append path info below
        lines.append('')
        if path:
            path_str = ' -> '.join(str(n) for n in path)
            lines.append(f"Path: {path_str}")
            if dist is not None:
                lines.append(f"Distance: {dist}")
        else:
            lines.append("No path found")

        return '\n'.join(lines)

    def __repr__(self):
        return (
            f"GraphVisualizer(nodes={len(self._positions)}, "
            f"cell={self._cell_width}x{self._cell_height})"
        )
