import itertools
import time
import csv
import astar
import gbfs
import simanneal
import main                                   # reuses map, mapDict, entries, rows, cols, inpKey (nothing runs on import)

algos = [("A*", astar), ("GBFS", gbfs), ("Sim. Annealing", simanneal)]
keys = list(main.entries.keys())
pairs = list(itertools.combinations(keys, 2))          # 17 landmarks -> 136 unordered pairs

rowsOut = []
for n, (a, b) in enumerate(pairs, 1):
    row = {"from": main.inpKey[a], "to": main.inpKey[b]}
    for title, algoModule in algos:
        start_time = time.perf_counter()
        path, c, st, goal, exp = algoModule.search(main.entries[a], main.entries[b], main.map, main.mapDict, main.rows, main.cols)
        end_time = time.perf_counter()
        row[title + " cost"] = c
        row[title + " explored"] = exp
        row[title + " time"] = end_time - start_time
    rowsOut.append(row)
    print(f"{n}/{len(pairs)} {row['from']} -> {row['to']}", flush=True)

# ---- per-pair results ----
with open("results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rowsOut[0].keys()))
    w.writeheader()
    w.writerows(rowsOut)

# ---- summary ----
inf = float('inf')
lines = []
lines.append("| Algorithm | Found | Avg cost | Avg cost vs A* | Optimal | Avg explored | Avg time (ms) |")
lines.append("|---|---|---|---|---|---|---|")
for title, _ in algos:
    ok = [r for r in rowsOut if r[title + " cost"] != inf]
    avgCost = sum(r[title + " cost"] for r in ok) / len(ok)
    ratio = sum(r[title + " cost"] / r["A* cost"] for r in ok) / len(ok)
    optimal = sum(1 for r in ok if r[title + " cost"] == r["A* cost"])
    avgExp = sum(r[title + " explored"] for r in rowsOut) / len(rowsOut)
    avgT = sum(r[title + " time"] for r in rowsOut) / len(rowsOut) * 1000
    lines.append(f"| {title} | {len(ok)}/{len(rowsOut)} | {avgCost:.1f} | {ratio:.2f}x | {optimal}/{len(rowsOut)} | {avgExp:.0f} | {avgT:.1f} |")

text = "\n".join(lines)
print("\n" + text)
open("summary.md", "w").write(text + "\n")

# ---- chart: average cost ratio, success and time ----
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = [t for t, _ in algos]
    ratios, found, times = [], [], []
    for title, _ in algos:
        ok = [r for r in rowsOut if r[title + " cost"] != inf]
        ratios.append(sum(r[title + " cost"] / r["A* cost"] for r in ok) / len(ok))
        found.append(100 * len(ok) / len(rowsOut))
        times.append(sum(r[title + " time"] for r in rowsOut) / len(rowsOut) * 1000)
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6))
    for axis, vals, label in zip(ax, [ratios, found, times], ["Avg cost vs A* (x)", "Goal found (%)", "Avg time (ms)"]):
        axis.bar(names, vals, color=["#005aff", "#ff8c00", "#e60000"])
        axis.set_title(label)
        axis.tick_params(axis="x", labelsize=8)
    plt.tight_layout()
    plt.savefig("comparison.png", dpi=150)
except ImportError:
    pass
