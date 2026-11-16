"""
Time-of-day crowd model.

Idea: at any time t, some places (the mess, the cafeteria) are busy. The crowd is
  1. a circle of congestion around the busy place, and
  2. congestion along the roads people WALK to reach it (the routes from the hostels / classes),
     which gets heavier the closer you get, because more of those routes overlap there.
Every walkable cell gets a crowd LEVEL 0..4, and a crowded cell costs more to enter:
    cost = base cost * (1 + STEP * level)
The search algorithms are untouched: they just see a different map at different times.
"""
import re
import numpy as np
from scipy import ndimage
import astar

# ---------------- EDIT THESE to match your campus ----------------
MESS = '9'                              # landmark number of the mess  (ASSUMPTION: Akshaya)
CAFETERIA = '17'
HOSTELS = ['10', '11', '12', '14', '15']   # Jasmine, Jasmine Annex, Banyan, Ashwatha, Ashoka (ASSUMPTION)
ACADEMIC = ['6', '3', '4', '8']            # Academics, Laboratory, Library, PEMS

EVENTS = [
    # name, where, start, end, peak (0-1), where the crowd walks FROM
    {"name": "Breakfast rush",    "at": MESS,      "start": "07:30", "end": "09:30", "peak": 1.0, "from": HOSTELS},
    {"name": "Lunch rush",        "at": MESS,      "start": "12:30", "end": "14:30", "peak": 1.0, "from": HOSTELS + ACADEMIC},
    {"name": "Snacks",            "at": MESS,      "start": "16:30", "end": "17:30", "peak": 0.5, "from": HOSTELS},
    {"name": "Dinner rush",       "at": MESS,      "start": "19:30", "end": "21:30", "peak": 1.0, "from": HOSTELS},
    {"name": "Cafeteria evening", "at": CAFETERIA, "start": "16:00", "end": "18:30", "peak": 0.7, "from": HOSTELS + ACADEMIC},
]
RAMP = 20            # minutes the crowd takes to build up before / die down after a window
RADIUS = 14          # cells (about 56 px) of congestion around the busy place
CORRIDOR_WIDTH = 2   # cells of extra width on the roads people walk along
LEVELS = 4           # crowd level 0..4
STEP = 0.75          # each level adds 75% of the base cost (level 4 = 4x)
# -----------------------------------------------------------------

_cache = {}


def parseTime(text):
    """'13:30', '1:30pm', '7:05 AM' -> minutes since midnight, or None."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*(am|pm)?\s*$", text, re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap:
        if not 1 <= h <= 12:
            return None
        h = h % 12 + (12 if ap.lower() == "pm" else 0)
    if h > 23 or mi > 59:
        return None
    return h * 60 + mi


def _minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def intensity(t, ev):
    """0..peak: ramps up before the window, flat during it, ramps down after."""
    s, e = _minutes(ev["start"]), _minutes(ev["end"])
    if s <= t <= e:
        return ev["peak"]
    if s - RAMP <= t < s:
        return ev["peak"] * (t - (s - RAMP)) / RAMP
    if e < t <= e + RAMP:
        return ev["peak"] * (1 - (t - e) / RAMP)
    return 0.0


def _fields(ev, _map, mapDict, entries, rows, cols):
    """Time-independent crowd shape for one event (cached)."""
    key = (ev["at"], tuple(ev["from"]))
    if key in _cache:
        return _cache[key]
    cy, cx = entries[ev["at"]][0]
    yy, xx = np.mgrid[0:rows, 0:cols]
    radial = np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / RADIUS ** 2))

    share = np.zeros((rows, cols))                       # how many walkers' routes pass through each cell
    for o in ev["from"]:
        if o == ev["at"]:
            continue
        path = astar.search(entries[o], entries[ev["at"]], _map, mapDict, rows, cols)[0]
        m = np.zeros((rows, cols), bool)
        for (y, x) in path:
            m[y, x] = True
        m = ndimage.binary_dilation(m, iterations=CORRIDOR_WIDTH)
        share += m
    share /= max(1, len(ev["from"]))                     # near the destination all routes overlap -> ~1
    _cache[key] = (radial, share)
    return _cache[key]


def crowdLevels(tMin, _map, mapDict, entries, rows, cols):
    """-> (levels: rows x cols int array 0..LEVELS, names of the events active at tMin)"""
    crowd = np.zeros((rows, cols))
    active = []
    for ev in EVENTS:
        I = intensity(tMin, ev)
        if I <= 0.02:
            continue
        active.append(ev["name"])
        radial, share = _fields(ev, _map, mapDict, entries, rows, cols)
        crowd += I * np.maximum(radial, share)
    levels = np.floor(np.clip(crowd, 0, 1) * (LEVELS + 0.99)).astype(int)
    for i in range(rows):                                 # walls never hold a crowd
        for j in range(cols):
            if _map[i][j] == 'wall':
                levels[i, j] = 0
    return levels, active


def timedMap(_map, levels):
    """Same grid, but crowded cells get a type like 'path@3'."""
    rows, cols = len(_map), len(_map[0])
    lv = levels.tolist()
    return [[_map[i][j] if lv[i][j] == 0 else f"{_map[i][j]}@{lv[i][j]}" for j in range(cols)] for i in range(rows)]


def timedDict(mapDict):
    """mapDict plus a crowded variant of every walkable tile."""
    d = dict(mapDict)
    for t in ('path', 'trail', 'grass'):
        ch, cost = mapDict[t]
        for L in range(1, LEVELS + 1):
            d[f"{t}@{L}"] = [ch, cost * (1 + STEP * L)]
    return d
