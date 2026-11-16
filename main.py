import astar
import simanneal
import gbfs
import mapload
import crowd
import time
import os
import datetime
from PIL import Image, ImageDraw, ImageFont

CELL = mapload.CELL
SHOW_IMAGE = True          # open a window with the route map at the end

# the grid is built from IIITDM.png (rows/cols come from the image size)
map, rows, cols = mapload.loadMap("IIITDM.png")

# cost to walk onto a tile: road 1, dirt trail 2, grass 3, everything else is blocked
mapDict = {'path' : [' ',1], 'trail' : ['.',2], 'grass' : ['"',3], 'wall' : ['■',float('inf')], 'trace':['□',1]}

# in the format (y,x) = (row, col), already snapped onto a road cell
entries, moved = mapload.buildEntries(map, rows, cols)
inpKey = {k : v[0] for k, v in mapload.LANDMARKS.items()}          # '1' -> 'Main'
nameKey = {v[0].upper() : k for k, v in mapload.LANDMARKS.items()}  # 'MAIN' -> '1'


def checkEntries():
    # every landmark must be on a road and able to reach every other one
    seen = mapload.reachable(map, rows, cols, entries['1'][0])
    for k in entries:
        y, x = entries[k][0]
        if mapDict[map[y][x]][1] == float('inf') or entries[k][0] not in seen:
            print("Landmark", k, inpKey[k], "is not connected to the road network")
            return False
    return True


def ask(prompt, other=None):
    while(True):
        v = input(prompt).strip().upper()
        v = nameKey.get(v, v)                  # accept a number OR a name
        if v not in inpKey.keys():
            print("Not valid, enter a number or name from the key\n")
            continue
        if v == other:
            print("Destination must be different from the start\n")
            continue
        return v


def askTime():
    while(True):
        v = input("Time of travel (HH:MM, 24h or 1:30pm, Enter = now) : ").strip()
        if v == "":
            now = datetime.datetime.now()
            return now.hour * 60 + now.minute
        t = crowd.parseTime(v)
        if t is None:
            print("Use HH:MM, for example 13:15\n")
            continue
        return t


def drawPaths(results, a, b, fileName, levels=None, usual=None, timeText="", active=()):
    # results: list of (title, path, cost, exp, time, exposure, colour, width)
    img = Image.open("IIITDM.png").convert("RGBA")
    if levels is not None and levels.any():                  # crowd heat: yellow (light) -> red (packed)
        ov = Image.new("RGBA", img.size, (0,0,0,0))
        od = ImageDraw.Draw(ov)
        for y, x in zip(*levels.nonzero()):
            L = int(levels[y, x])
            od.rectangle((x*CELL, y*CELL, x*CELL+CELL-1, y*CELL+CELL-1), fill=(255, 225-55*L, 0, 110+30*L))
        img = Image.alpha_composite(img, ov)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    if usual and len(usual) > 1:                              # the route you would take with no crowd
        d.line([(x*CELL + CELL//2, y*CELL + CELL//2) for (y, x) in usual], fill=(40,40,40), width=5, joint="curve")
    for title, path, c, exp, t, ex, colour, w in results:     # thickest first, so all stay visible
        if len(path) > 1:
            d.line([(x*CELL + CELL//2, y*CELL + CELL//2) for (y, x) in path], fill=colour, width=w, joint="curve")
    for k in (a, b):
        y, x = entries[k][0]
        d.ellipse((x*CELL-14, y*CELL-14, x*CELL+14, y*CELL+14), fill=(255,255,255), outline=(0,0,0), width=4)
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    lines = len(results) + 3
    d.rectangle((10, 10, 800, 24 + 36*lines), fill=(255,255,255), outline=(0,0,0), width=3)
    d.text((22, 18), f"{inpKey[a]} -> {inpKey[b]}   at {timeText}", fill=(0,0,0), font=font)
    d.text((22, 54), "Crowd: " + (", ".join(active) if active else "none"), fill=(160,0,0), font=font)
    for n, (title, path, c, exp, t, ex, colour, w) in enumerate(results):
        costText = "not found" if c == float('inf') else f"cost {c:.1f}"
        y0 = 90 + 36*n
        d.line((22, y0 + 14, 62, y0 + 14), fill=colour, width=8)
        d.text((72, y0), f"{title}: {costText}, crowd {ex}, {t*1000:.0f} ms", fill=(0,0,0), font=font)
    y0 = 90 + 36*len(results)
    d.line((22, y0 + 14, 62, y0 + 14), fill=(40,40,40), width=5)
    d.text((72, y0), "Usual route (no crowd)", fill=(0,0,0), font=font)
    img.save(fileName)


if __name__ == "__main__":
    if not checkEntries():
        raise SystemExit

    print("Key :")
    for k, v in mapload.LANDMARKS.items():
        print(f"{k:>3} - {v[0]}")
    print()

    a = ask("Enter starting place : ")
    b = ask("Enter destination place : ", a)
    tMin = askTime()
    timeText = f"{tMin//60:02d}:{tMin%60:02d}"

    # crowd at this time -> a map where crowded cells cost more
    levels, active = crowd.crowdLevels(tMin, map, mapDict, entries, rows, cols)
    timeMap = crowd.timedMap(map, levels)
    timeDict = crowd.timedDict(mapDict)
    print(f"\nTime {timeText}: " + (", ".join(active) if active else "no crowds, usual routes apply"))

    # the route you would take with no crowd, and what it costs NOW
    usual = astar.search(entries[a], entries[b], map, mapDict, rows, cols)[0]
    usualNow = sum(timeDict[timeMap[y][x]][1] for (y, x) in usual[1:])

    results = []
    for title, algoModule, colour, w in [("A*", astar, (0,90,255), 12), ("GBFS", gbfs, (255,140,0), 8), ("Sim. Annealing", simanneal, (230,0,0), 4)]:
        print("\n" + title)
        start_time = time.perf_counter()
        path, c, st, goal, exp = algoModule.search(entries[a],entries[b],timeMap,timeDict,rows,cols)
        end_time = time.perf_counter()
        exposure = int(sum(levels[y, x] for (y, x) in path[1:]))      # total crowd level walked through
        print("Total Cost : ",c)
        print(f"Crowd Exposure : {exposure}")
        print(f"Explored States : {exp}")
        if(c == float('inf')):
            print("Didn't find goal")
        print(f"Elapsed Time : {end_time - start_time : .6f}")
        results.append((title, path, c, exp, end_time - start_time, exposure, colour, w))

    aPath, aCost = results[0][1], results[0][2]
    print(f"\nUsual route would cost {usualNow:.1f} right now; the crowd-aware A* route costs {aCost:.1f}.")
    if aPath == usual:
        print("Same route as usual: it avoids the crowd already (or the crowd isn't on your way).")
    else:
        print(f"Rerouted to avoid the crowd, saving {usualNow - aCost:.1f}.")

    os.makedirs("routes", exist_ok=True)
    fileName = os.path.join("routes", f"route_{inpKey[a]}_to_{inpKey[b]}_{timeText.replace(':','')}.png".replace(" ", "_"))
    drawPaths(results, a, b, fileName, levels, usual, timeText, active)
    print("\nSaved", os.path.abspath(fileName))

    if SHOW_IMAGE:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 10))
        plt.imshow(Image.open(fileName))
        plt.axis("off")
        plt.tight_layout()
        plt.show()
