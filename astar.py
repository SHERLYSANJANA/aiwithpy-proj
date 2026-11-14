import heapq as h


def algo(s, goal, _map, _mapDict, rows, cols):
    nexts = [(-1,0),(1,0),(0,-1),(0,1)]       # FIX: random.shuffle removed (results are repeatable)
    exploredStates = 0
    found = False

    def heur(_s, _g):
        # FIX: Manhattan is tighter than Euclidean on a 4-direction grid and still admissible
        return abs(_g[0] - _s[0]) + abs(_g[1] - _s[1])

    OPEN = []
    parent = {}
    path = []

    g = {s: 0}
    f = {s: heur(s,goal)}
    h.heappush(OPEN, (f[s], s))                # FIX: was (0, s)

    while OPEN:
        fc, curr = h.heappop(OPEN)
        if fc > f[curr]:                       # FIX: skip stale entries (a better f was pushed later)
            continue
        exploredStates += 1                    # FIX: count expansions, not every neighbour

        if(curr == goal):
            while curr in parent:
                path.append(curr)
                curr = parent[curr]
            path.append(s)
            found = True
            break

        for r, c in (nexts):
            next = (curr[0] + r, curr[1] + c)

            if 0 <= next[0] < rows and 0 <= next[1] < cols:

                if _mapDict[_map[next[0]][next[1]]][1] == float('inf'):
                    continue

                tent_g = g[curr] + _mapDict[_map[next[0]][next[1]]][1]

                if tent_g < g.get(next, float('inf')):
                    parent[next] = curr
                    g[next] = tent_g
                    f[next] = tent_g + heur(next, goal)
                    h.heappush(OPEN, (f[next],next))   # FIX: ALWAYS push (OPENED set removed)

    # FIX: g.get(...) so an unreachable goal gives inf instead of KeyError
    return path, g.get(goal, float('inf')), s, goal, exploredStates, found


def search(s_list, goal_list, _map, _mapDict, rows, cols):
    minPath = []
    minC = float('inf')
    st = tuple()
    go = tuple()
    exp = 0

    for s in s_list:
        for g in goal_list:
            p,c,_s,_g, _exp, f = algo(s,g, _map, _mapDict, rows, cols)

            exp += _exp                        # FIX: total work over ALL pairs (matches the timer)

            if f and c < minC:
                minC = c
                minPath = p
                st = _s
                go = _g

    return minPath, minC, st, go, exp
