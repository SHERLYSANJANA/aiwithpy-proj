import heapq as h


def algo(s, goal, _map, _mapDict, rows, cols):
    nexts = [(-1,0),(1,0),(0,-1),(0,1)]       
    exploredStates = 0
    found = False

    def heur(_s, _g):

        return abs(_g[0] - _s[0]) + abs(_g[1] - _s[1])

    OPEN = []
    parent = {}
    path = []

    g = {s: 0}
    f = {s: heur(s,goal)}
    h.heappush(OPEN, (f[s], s))              

    while OPEN:
        fc, curr = h.heappop(OPEN)
        if fc > f[curr]:                       
            continue
        exploredStates += 1                    

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
                    h.heappush(OPEN, (f[next],next))   


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

            exp += _exp                       

            if f and c < minC:
                minC = c
                minPath = p
                st = _s
                go = _g

    return minPath, minC, st, go, exp
