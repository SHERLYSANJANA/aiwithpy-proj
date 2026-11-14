import math
import random


def loopErase(path):
    # NEW helper: removes loops from the random walk so it becomes a clean route
    out = []
    idx = {}
    for p in path:
        if p in idx:
            i = idx[p]
            for q in out[i+1:]:
                del idx[q]
            out = out[:i+1]
        else:
            idx[p] = len(out)
            out.append(p)
    return out


def search(s_list, goal_list, _map, _mapDict, rows, cols):
    random.seed(42)                            # FIX: reproducible results
    minPath = []
    minC = float('inf')
    st = tuple()
    go = tuple()
    exp = 0
    fbPath, fbH, fbS, fbG = [], float('inf'), tuple(), tuple()   # best FAILED attempt, only for display

    for s in s_list:
        for g in goal_list:
            for _ in range(5):                 # FIX: random restarts to escape local minima
                p,c,_exp, _f, _bh = algo(s,g, _map, _mapDict, rows, cols)

                exp += _exp

                if _f:                         # FIX: only successful runs compete
                    if c < minC:
                        minC = c
                        minPath = p
                        st = s
                        go = g
                elif _bh < fbH:
                    fbPath, fbH, fbS, fbG = p, _bh, s, g

    if minC == float('inf'):                   # nothing succeeded: show the closest attempt
        minPath, st, go = fbPath, fbS, fbG

    return minPath, minC, st, go, exp


def algo(s, goal, map, mapDict, rows, cols):
    nexts = [(-1,0),(1,0),(0,-1),(0,1)]
    exploredStates = 0
    found = False

    def heur(_s, _g):
        return abs(_g[0] - _s[0]) + abs(_g[1] - _s[1])

    curr = s
    h = heur(s,goal)
    T = 10.0
    path = [curr]                              # FIX: ordered list (was a set)
    cost = 0
    bestH = h                                  # FIX: best-so-far tracking
    bestLen = 1

    while(h>0 and T>0.001):
        # FIX: build the list of walkable neighbours; the old "while True" hung when boxed in
        options = []
        for n in nexts:
            nxt = (curr[0] + n[0], curr[1] + n[1])
            if 0 <= nxt[0] < rows and 0 <= nxt[1] < cols:
                if mapDict[map[nxt[0]][nxt[1]]][1] != float('inf'):
                    options.append(nxt)
        if not options:
            break
        nxt = random.choice(options)

        exploredStates += 1
        _h = heur(nxt,goal)
        dl = h - _h

        # FIX: standard acceptance exp(dl/T) (was a sigmoid). dl <= 0 here, so exp() cannot overflow,
        # which also removes the old "-(dl/T) > 709: continue" branch that skipped cooling and could hang.
        if(dl > 0 or random.random() <= math.exp(dl/T)):
            curr = nxt
            h = _h
            path.append(nxt)
            if h < bestH:
                bestH = h
                bestLen = len(path)

        T *= 0.9999                            # FIX: cools on EVERY iteration now

    found = (h == 0)                           # FIX: success means the goal was reached
    if found:
        path = loopErase(path)
    else:
        path = loopErase(path[:bestLen])
    # FIX: cost recomputed from the clean path, so the drawn route and the printed cost agree
    cost = sum(mapDict[map[p[0]][p[1]]][1] for p in path[1:])

    return path, cost, exploredStates, found, bestH
