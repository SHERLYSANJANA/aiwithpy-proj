# Campus Pathfinding: A*, Greedy Best-First Search and Simulated Annealing

Finds routes between 17 landmarks on the IIITDM campus and compares three search algorithms on the same map.

The map is not hand-built. The grid is generated automatically from the campus illustration (`IIITDM.png`), and each algorithm's route is drawn back onto the original image.

![Banyan to Arjuna](docs/route_Banyan_to_Arjuna.png)

*Blue is A\*, orange is Greedy Best-First Search and red is Simulated Annealing.*

---

## Table of contents

1. [Overview](#overview)
2. [How it works](#how-it-works)
3. [The algorithms](#the-algorithms)
4. [Results](#results)
5. [Setup and usage](#setup-and-usage)
6. [Project structure](#project-structure)
7. [Limitations](#limitations)
8. [Possible improvements](#possible-improvements)

---

## Overview

The project has two parts:

1. **Turn a drawing into a weighted graph.** Image processing classifies every part of the map as road, trail, grass or blocked.
2. **Search that graph three different ways.** A\*, Greedy Best-First Search (GBFS) and Simulated Annealing (SA) all solve the same routing problem, so their cost, speed and reliability can be compared fairly.

The algorithms know nothing about images. They only see a 2D list of tile types and a table of what each tile costs.

```
IIITDM.png → classify pixels → grid of cells → snap landmarks → 3 search algorithms → draw routes
             (mapload.py)                       (mapload.py)     (astar / gbfs / simanneal)   (main.py)
```

---

## How it works

### 1. Image to grid (`mapload.py`)

The image is 1080×1350 pixels. Every 4×4 block of pixels becomes one grid cell, giving a **337 × 270** grid (about 91,000 cells, of which roughly 21,000 are walkable).

**Roads.** Roads in the drawing are mid-grey, so their red, green and blue values are almost equal. That is tested per pixel:

```python
road = (abs(r - g) < 12) & (abs(g - b) < 18) & (r > 100) & (r < 165)
```

This also catches some grey roofs and courts, so two clean-up steps follow:

- **Dilation.** The grey fill is only about 10 pixels wide, with black outlines on both sides. Growing the mask by 5 pixels covers the outlines, so each road becomes one solid strip.
- **Largest connected component.** The mask is split into separate blobs and only the biggest one, the road network, is kept. Roofs and speckles are separate blobs and disappear.

A cell is a road when more than half of its pixels are road.

**Terrain.** Every other pixel is classified by colour:

| Colour | Meaning |
|---|---|
| Yellow-green | Grass (also tree canopies) |
| Orange | Dirt trail |
| Near-black | Outline (ignored in the vote) |
| Anything else | Wall colour: roofs, courts, water, grey |

Each cell takes the majority. It is walkable if grass and trail pixels outnumber wall-coloured ones, and roads always win over terrain.

Two filters then remove mistakes:

- **Inside the loop only.** A flood fill starts in the middle of the sports field and spreads through non-road cells. The campus loop road stops it, so grass and forest outside the loop stay blocked.
- **Connected to a road.** Walkable cells that cannot reach the road network are removed, so there are no unreachable islands.

**Tile costs**

| Tile | Cost to enter |
|---|---|
| Road | 1 |
| Dirt trail | 2 |
| Grass | 3 |
| Wall (buildings, courts, lake) | blocked |

### 2. Landmarks

Each of the 17 numbered places on the map has a pixel position. The code converts it to a cell, then runs a breadth-first search outward until it reaches a road cell. A landmark drawn on a building therefore lands on the road beside it. At start-up, `checkEntries()` confirms that all 17 landmarks can reach each other.

### 3. The search problem

Every walkable cell is a node, connected to its up, down, left and right neighbours. Stepping onto a cell costs 1, 2 or 3, and walls cannot be entered. A route is a path through this graph, and its cost is the sum of the costs of the cells it steps onto.

All three algorithms share one idea: keep a set of cells to explore, pick one, look at its neighbours, and repeat. They differ in how they pick.

---

## The algorithms

### A\* (`astar.py`)

Each cell gets two numbers:

- `g`: the cheapest known cost from the start to this cell.
- `h`: a guess of the remaining cost to the goal.

A\* always expands the cell with the lowest `f = g + h`, using a heap ordered by `f`.

```python
tent_g = g[curr] + cost of next
if tent_g < g.get(next, inf):          # found a cheaper way to reach next
    parent[next] = curr
    g[next] = tent_g
    heappush(OPEN, (f[next], next))
```

- **Heuristic.** `h` is Manhattan distance, `|Δrow| + |Δcol|`. It never overestimates, because every step costs at least 1, so no route can be shorter than the number of steps Manhattan distance counts. This is what guarantees A\* finds the cheapest route.
- **Stale entries.** When a cheaper route to a cell is found, the cell is pushed again. The old entry is skipped when it is popped (`if fc > f[curr]: continue`).
- **Path.** The `parent` dictionary records how each cell was reached, and the path is rebuilt backwards from the goal.

### Greedy Best-First Search (`gbfs.py`)

GBFS uses only `h`. It always expands the cell that looks closest to the goal and ignores what it cost to get there. It is very fast because it dives straight toward the goal, but it cannot tell that grass costs three times as much as road. Its route cost is added up afterwards from the final path, and the route is not guaranteed to be cheapest.

### Simulated Annealing (`simanneal.py`)

This is a different kind of algorithm. There is no frontier, only a single random walk with distance to the goal as its "energy":

1. Pick a random walkable neighbour.
2. If it is closer to the goal, always move there.
3. If it is farther (by 1, since Manhattan distance changes by ±1), move there anyway with probability `exp(-1/T)`.
4. Multiply the temperature `T` by 0.9999. It starts at 10.

| Temperature | Chance of accepting a worse step |
|---|---|
| T = 10 | about 90% |
| T = 1 | about 37% |
| T = 0.2 | under 1% |

About 92,000 iterations bring `T` down to the stopping value of 0.001. The final walk is **loop-erased**, so the drawn route is a clean path and the reported cost matches it.

The weakness is that "distance to the goal" ignores walls. A walk can slide into a dead end where every move is farther from the goal, and once `T` is low it cannot escape. The code uses 5 random restarts per route and a fixed seed (42) to make results repeatable, but it still fails on about a quarter of the pairs.

---

## Results

All 136 landmark pairs, with grass cost 3 and trail cost 2:

| Algorithm | Goal found | Avg cost | Avg cost vs A* | Matched A* | Avg explored | Avg time |
|---|---|---|---|---|---|---|
| A* | 136/136 | 199.4 | 1.00x | 136/136 | 2,649 | 6.3 ms |
| GBFS | 136/136 | 302.8 | 1.42x | 14/136 | 397 | 0.7 ms |
| Simulated annealing | 105/136 | 436.5 | 2.30x | 1/136 | 205,187 | 270.6 ms |

![Comparison](comparison.png)

- **A\*** always finds the cheapest route, and no other algorithm ever beat it. It explores more states than GBFS but still takes only a few milliseconds.
- **GBFS** is about 9 times faster than A\* but its routes cost 42% more on average, because it ignores terrain cost and takes grass shortcuts.
- **Simulated annealing** failed on 31 of 136 pairs, and its successful routes cost 2.3 times A\*'s. Random walking guided by straight-line distance gets stuck behind buildings, so it is a poor fit for shortest-path problems on a map like this.
- **Terrain matters.** A\* leaves the road for grass or trails on 19 of the 136 pairs. With grass at cost 2 and trails at 1.5, that rises to about 40 pairs.

Full per-pair results are in `results.csv`.

---

## Setup and usage

```bash
pip install -r requirements.txt
```

Run all commands from the repository root, because the code opens `IIITDM.png` by relative path.

**Find a route.** Enter a start and a destination as a number or a name (for example `15` or `Ashoka`):

```bash
python3 main.py
```

It prints cost, explored states and time for each algorithm, saves `route_<from>_to_<to>.png`, and shows the map with all three routes.

**Compare all 136 pairs:**

```bash
python3 compare.py
```

This writes `results.csv`, `summary.md` and `comparison.png`. It takes about 30 to 45 seconds, mostly simulated annealing.

### Landmarks

| # | Place | # | Place |
|---|---|---|---|
| 1 | Main | 10 | Jasmine |
| 2 | Admin | 11 | Jasmine Annex |
| 3 | Laboratory | 12 | Banyan |
| 4 | Library | 13 | Ultimate Store |
| 5 | Skybridge | 14 | Ashwatha |
| 6 | Academics | 15 | Ashoka |
| 7 | OAT | 16 | Arjuna |
| 8 | PEMS | 17 | Cafeteria |
| 9 | Akshaya | | |

---

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Interactive route finder and image output |
| `mapload.py` | Image to grid, landmark table and snapping |
| `astar.py` | A* search |
| `gbfs.py` | Greedy best-first search |
| `simanneal.py` | Simulated annealing |
| `compare.py` | All-pairs comparison |
| `IIITDM.png` | Campus map used as input |
| `results.csv`, `summary.md`, `comparison.png` | Output of `compare.py` |
| `docs/` | Example route images |

---

## Limitations

- The grid is built using colour thresholds tuned by eye for this one image. A different map needs retuning in `mapload.py`.
- Some light-coloured patches of grass are read as blocked.
- Landmarks are snapped to the nearest road, so routes start beside a building, not at its door.
- Costs are counts of 4-pixel cells weighted by terrain, not real distances. The grass and trail costs (3 and 2) are chosen values, not measurements.
- "Explored" means expanded nodes for A\* and GBFS, but iterations for simulated annealing, so those counts are not directly comparable.
- Each pair was run in one direction. A\* costs are symmetric, but GBFS and simulated annealing can differ by direction.

---

## Possible improvements

- Add **Dijkstra** as a baseline (A\* with the heuristic set to zero) to show how much the heuristic saves.
- Make simulated annealing fail less, for example with reheating or a slower cooling schedule.
- Test how the results change with different grass and trail costs.
- Add diagonal moves at cost √2.
