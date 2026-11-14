# Campus Pathfinding: A*, Greedy Best-First Search and Simulated Annealing

Finds routes between 17 landmarks on the IIITDM campus map and compares three search algorithms on the same grid.

The grid is built automatically from the campus illustration (`IIITDM.png`). Each algorithm's route is then drawn on top of the original map.

![Banyan to Arjuna](docs/route_Banyan_to_Arjuna.png)

## How it works

1. **Map to grid.** `mapload.py` reads `IIITDM.png` and classifies every 4x4-pixel cell by colour:
   - **Road:** cost 1
   - **Dirt trail:** cost 2
   - **Grass (inside the campus loop only):** cost 3
   - **Blocked:** buildings, courts and the lake
2. **Landmarks.** The 17 numbered places on the map are snapped to the nearest road cell. All of them can reach each other.
3. **Search.** The same grid is given to three algorithms:
   - **A\*** with a Manhattan-distance heuristic. It is optimal here, because the cheapest tile costs 1.
   - **Greedy Best-First Search (GBFS)**. It follows the heuristic only and ignores cost.
   - **Simulated Annealing (SA)**. It uses a standard `exp(delta/T)` acceptance rule, 5 random restarts per route and a fixed seed (42), and loop-erases the final walk.
4. **Output.** `main.py` prints cost, explored states and time for each algorithm, and saves an image with all three routes drawn on the map.

## Landmarks

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

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run all commands from the repository root, because the code opens `IIITDM.png` by relative path.

**Find a route.** Enter a start and a destination as a number or a name (for example `15` or `Ashoka`):

```bash
python3 main.py
```

This saves `route_<from>_to_<to>.png`. Blue is A\*, orange is GBFS and red is simulated annealing.

**Compare all 136 landmark pairs:**

```bash
python3 compare.py
```

This writes `results.csv`, `summary.md` and `comparison.png`. It takes about 30 to 45 seconds, mostly simulated annealing.

## Results

All 136 landmark pairs, grass cost 3 and trail cost 2:

| Algorithm | Goal found | Avg cost | Avg cost vs A* | Matched A* | Avg explored | Avg time |
|---|---|---|---|---|---|---|
| A* | 136/136 | 199.4 | 1.00x | 136/136 | 2,649 | 6.3 ms |
| GBFS | 136/136 | 302.8 | 1.42x | 14/136 | 397 | 0.7 ms |
| Simulated annealing | 105/136 | 436.5 | 2.30x | 1/136 | 205,187 | 270.6 ms |

- **A\*** always finds the cheapest route, and no other algorithm ever beat it.
- **GBFS** is about 9 times faster than A\* but its routes cost 42% more on average, because it ignores terrain cost and takes grass shortcuts.
- **Simulated annealing** failed on 31 of 136 pairs. Random walking guided by distance gets stuck behind buildings, so it is a poor fit for shortest-path problems on a map like this.

Full per-pair results are in `results.csv`.

![Comparison](comparison.png)

## Limitations

- The grid is built by colour thresholds tuned by eye for this one image. A different map needs retuning in `mapload.py`.
- Some light-coloured patches of grass are read as blocked.
- Landmarks are snapped to the nearest road, so routes start beside a building, not at its door.
- Costs are counts of 4-pixel cells weighted by terrain, not real distances. The grass and trail costs (3 and 2) are chosen values, not measurements.
- "Explored" means expanded nodes for A\* and GBFS, but iterations for simulated annealing, so those counts are not directly comparable.

## Files

| File | Purpose |
|---|---|
| `main.py` | Interactive route finder and image output |
| `mapload.py` | Image to grid, landmark table and snapping |
| `astar.py`, `gbfs.py`, `simanneal.py` | The three algorithms |
| `compare.py` | All-pairs comparison |
| `IIITDM.png` | Campus map used as input |

<img width="1800" height="540" alt="image" src="https://github.com/user-attachments/assets/f5cbf6e1-8fb5-446a-b863-69c2b48f9619" />
