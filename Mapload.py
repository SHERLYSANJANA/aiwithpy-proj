import numpy as np
from PIL import Image
from scipy import ndimage
from collections import deque

CELL = 4                                   # pixels per grid cell

# landmark number -> (name, pixel x, pixel y) on IIITDM.png
LANDMARKS = {
    '1':  ('Main',           1033, 403),
    '2':  ('Admin',           925, 617),
    '3':  ('Laboratory',      914, 745),
    '4':  ('Library',         817, 791),
    '5':  ('Skybridge',       790, 720),
    '6':  ('Academics',       765, 585),
    '7':  ('OAT',             705, 430),
    '8':  ('PEMS',            656, 593),
    '9':  ('Akshaya',         518, 453),
    '10': ('Jasmine',         415, 490),
    '11': ('Jasmine Annex',   387, 413),
    '12': ('Banyan',          343, 748),
    '13': ('Ultimate Store',  270, 731),
    '14': ('Ashwatha',        170, 738),
    '15': ('Ashoka',          135, 832),
    '16': ('Arjuna',          468, 1002),
    '17': ('Cafeteria',       790, 1020),
}

LAKE = (860, 1110, 1080, 1350)             # x1, y1, x2, y2 in pixels: blocked (water touches the road)


def loadMap(imgPath="IIITDM.png"):
    img = Image.open(imgPath).convert("RGB")
    a = np.array(img).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    # 1. road fill colour at full resolution (mid grey, low saturation)
    road = (abs(r - g) < 12) & (abs(g - b) < 18) & (r > 100) & (r < 165)
    x1, y1, x2, y2 = LAKE
    road[y1:y2, x1:x2] = False

    # 2. the grey fill is only ~10px wide, so grow it to cover the black road outlines,
    #    then keep only the biggest connected piece (drops roofs, courts, speckle)
    road = ndimage.binary_dilation(road, structure=ndimage.generate_binary_structure(2, 1), iterations=5)
    lab, n = ndimage.label(road)
    sizes = ndimage.sum(road, lab, range(1, n + 1))
    road = lab == (1 + int(np.argmax(sizes)))

    # 3. downscale: a cell is road when most of its pixels are road
    H, W = road.shape
    rows, cols = H // CELL, W // CELL
    blocks = road[:rows * CELL, :cols * CELL].reshape(rows, CELL, cols, CELL).mean(axis=(1, 3))
    cell = blocks > 0.5

    _map = [['path' if cell[i, j] else 'wall' for j in range(cols)] for i in range(rows)]
    return _map, rows, cols


def snap(_map, rows, cols, start):
    """Nearest 'path' cell to start (BFS through any cell). start is (row, col)."""
    q = deque([start]); seen = {start}
    while q:
        cur = q.popleft()
        if _map[cur[0]][cur[1]] == 'path':
            return cur
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            n = (cur[0] + dr, cur[1] + dc)
            if 0 <= n[0] < rows and 0 <= n[1] < cols and n not in seen:
                seen.add(n); q.append(n)


def buildEntries(_map, rows, cols):
    """number -> [(row, col)] on a road cell, plus how many cells each had to move."""
    entries, moved = {}, {}
    for k, (name, x, y) in LANDMARKS.items():
        c0 = (min(y // CELL, rows - 1), min(x // CELL, cols - 1))
        c1 = snap(_map, rows, cols, c0)
        entries[k] = [c1]
        moved[k] = abs(c1[0] - c0[0]) + abs(c1[1] - c0[1])
    return entries, moved


def reachable(_map, rows, cols, start):
    q = deque([start]); seen = {start}
    while q:
        cur = q.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            n = (cur[0] + dr, cur[1] + dc)
            if 0 <= n[0] < rows and 0 <= n[1] < cols and n not in seen and _map[n[0]][n[1]] == 'path':
                seen.add(n); q.append(n)
    return seen
