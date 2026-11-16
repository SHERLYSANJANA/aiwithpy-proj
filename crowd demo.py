# Shows ONE trip at four different times, so you can see the route change with the crowd.
# Usage:  python3 crowd_demo.py            (PEMS -> Jasmine)
#         python3 crowd_demo.py 4 10       (any two landmark numbers)
import sys
import os
os.environ.setdefault("MPLBACKEND", "Agg")
import astar
import crowd
import main
from PIL import Image, ImageDraw, ImageFont

a = sys.argv[1] if len(sys.argv) > 2 else '8'
b = sys.argv[2] if len(sys.argv) > 2 else '10'
times = ["11:00", "08:30", "13:00", "17:00"]

usual = astar.search(main.entries[a], main.entries[b], main.map, main.mapDict, main.rows, main.cols)[0]
os.makedirs("routes", exist_ok=True)
panels = []
for t in times:
    tMin = crowd.parseTime(t)
    levels, active = crowd.crowdLevels(tMin, main.map, main.mapDict, main.entries, main.rows, main.cols)
    tmap, tdict = crowd.timedMap(main.map, levels), crowd.timedDict(main.mapDict)
    path, c, st, go, exp = astar.search(main.entries[a], main.entries[b], tmap, tdict, main.rows, main.cols)
    exposure = int(sum(levels[y, x] for (y, x) in path[1:]))
    fn = os.path.join("routes", f"_demo_{t.replace(':','')}.png")
    main.drawPaths([("A*", path, c, exp, 0, exposure, (0, 90, 255), 12)], a, b, fn, levels, usual, t, active)
    panels.append(Image.open(fn).resize((540, 675)))
    os.remove(fn)

sheet = Image.new("RGB", (1080, 1350), "white")
for i, p in enumerate(panels):
    sheet.paste(p, ((i % 2) * 540, (i // 2) * 675))
sheet.save("crowd_demo.png")
print(f"{main.inpKey[a]} -> {main.inpKey[b]} at {', '.join(times)}  ->  saved crowd_demo.png")
