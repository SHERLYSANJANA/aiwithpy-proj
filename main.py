import astar
import simanneal
import gbfs
import mapload
import time
import os
from PIL import Image, ImageDraw, ImageFont

CELL = mapload.CELL

# the grid is now built from IIITDM.png instead of by hand (rows/cols come from the image size)
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


def drawPaths(results, a, b, fileName):
    # results: list of (title, path, cost, exp, time, colour, width)
    img = Image.open("IIITDM.png").convert("RGB")
    d = ImageDraw.Draw(img)
    for title, path, c, exp, t, colour, w in results:       # drawn thickest first, so all stay visible
        if len(path) > 1:
            d.line([(x*CELL + CELL//2, y*CELL + CELL//2) for (y, x) in path], fill=colour, width=w, joint="curve")
    for k in (a, b):
        y, x = entries[k][0]
        d.ellipse((x*CELL-14, y*CELL-14, x*CELL+14, y*CELL+14), fill=(255,255,255), outline=(0,0,0), width=4)
    try:
        font = ImageFont.load_default(size=26)
    except TypeError:
        font = ImageFont.load_default()
    d.rectangle((10, 10, 700, 20 + 38*(len(results)+1)), fill=(255,255,255), outline=(0,0,0), width=3)
    d.text((22, 18), f"{inpKey[a]}  ->  {inpKey[b]}", fill=(0,0,0), font=font)
    for n, (title, path, c, exp, t, colour, w) in enumerate(results):
        costText = "not found" if c == float('inf') else f"cost {c}"
        d.line((22, 70 + 38*n, 62, 70 + 38*n), fill=colour, width=8)
        d.text((72, 56 + 38*n), f"{title}: {costText}, explored {exp}, {t*1000:.0f} ms", fill=(0,0,0), font=font)
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

    results = []
    for title, algoModule, colour, w in [("A*", astar, (0,90,255), 12), ("GBFS", gbfs, (255,140,0), 8), ("Sim. Annealing", simanneal, (230,0,0), 4)]:
        print("\n" + title)
        start_time = time.perf_counter()
        path, c, st, goal, exp = algoModule.search(entries[a],entries[b],map,mapDict,rows,cols)
        end_time = time.perf_counter()
        print("Total Cost : ",c)
        print(f"Explored States : {exp}")
        if(c == float('inf')):
            print("Didn't find goal")
        print(f"Elapsed Time : {end_time - start_time : .6f}")
        results.append((title, path, c, exp, end_time - start_time, colour, w))

    os.makedirs("routes", exist_ok=True)
    fileName = os.path.join("routes", f"route_{inpKey[a]}_to_{inpKey[b]}.png".replace(" ", "_"))
    drawPaths(results, a, b, fileName)
    print("\nSaved", os.path.abspath(fileName))

    fileName = f"route_{inpKey[a]}_to_{inpKey[b]}.png".replace(" ", "_")
    drawPaths(results, a, b, fileName)
    print("\nSaved", fileName)

    import matplotlib.pyplot as plt
    plt.figure(figsize=(8, 10))
    plt.imshow(Image.open(fileName))
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    #if SHOW_IMAGE:
    #    Image.open(fileName).show()
