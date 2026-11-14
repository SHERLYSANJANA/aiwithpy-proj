from dataclasses import dataclass, field
from typing import Optional

INF = float('inf')

# Every tile has the SAME structure: (display char, cost to enter)
TILES = {
    'path':   (' ', 1),
    'ground': ('_', 1),
    'plant':  ('|', INF),
    'wall':   ('■', INF),
    'ins':    ('=', INF),      # building interior; its letter lives in Grid.labels
}
TRACE = '□'
MARK = '×'
MIN_COST = 1                   # cheapest walkable tile; keeps the heuristic admissible
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


@dataclass
class Result:
    path: list = field(default_factory=list)
    cost: float = INF
    start: Optional[tuple] = None
    goal: Optional[tuple] = None
    expanded: int = 0
    found: bool = False


class Grid:
    """All positions are (row, col)."""

    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.cells = [['path' for _ in range(cols)] for _ in range(rows)]
        self.labels = {}                       # (row, col) -> building letter
        for r in range(rows):                  # outer boundary wall
            for c in range(cols):
                if r in (0, rows - 1) or c in (0, cols - 1):
                    self.cells[r][c] = 'wall'

    # ---------- queries ----------
    def in_bounds(self, p):
        return 0 <= p[0] < self.rows and 0 <= p[1] < self.cols

    def cost(self, p):
        return TILES[self.cells[p[0]][p[1]]][1]

    def walkable(self, p):
        return self.in_bounds(p) and self.cost(p) != INF

    def neighbors(self, p):
        for dr, dc in DIRS:
            n = (p[0] + dr, p[1] + dc)
            if self.walkable(n):
                yield n

    def path_cost(self, path):
        """Cost of entering every cell after the first."""
        return sum(self.cost(p) for p in path[1:])

    # ---------- building ----------
    def block(self, x1, y1, x2, y2, kind='wall', label=''):
        """Rectangle given as (x=col, y=row) corners, inclusive.
        kind='wall' draws a hollow building with an 'ins' interior;
        any other kind fills the rectangle with that tile."""
        for r in range(max(y1, 0), min(y2, self.rows - 1) + 1):
            for c in range(max(x1, 0), min(x2, self.cols - 1) + 1):
                if kind == 'wall':
                    if r in (y1, y2) or c in (x1, x2):
                        self.cells[r][c] = 'wall'
                    else:
                        self.cells[r][c] = 'ins'
                        self.labels[(r, c)] = label
                else:
                    self.cells[r][c] = kind

    # ---------- output ----------
    def render(self, path=(), start=None, goal=None):
        on_path = set(path)                    # O(1) lookups
        lines = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                p = (r, c)
                if p == start or p == goal:
                    row.append(MARK)
                elif p in on_path:
                    row.append(TRACE)
                elif self.cells[r][c] == 'ins':
                    row.append(self.labels.get(p, TILES['ins'][0]))
                else:
                    row.append(TILES[self.cells[r][c]][0])
            lines.append(''.join(row))
        return '\n'.join(lines)
