"""
connectivity_module.py
----------------------
Network Connectivity Module: Breadth First Search and Depth First Search.

Both traversals start at one intersection and visit every intersection that
can be reached from it by road. They differ only in which intersection they
look at next:

    * BFS uses a queue  -> explores the nearest intersections first, level by level.
    * DFS uses a stack  -> follows one road as far as it goes, then backtracks.

The traversal order tells a traffic monitor which junctions a vehicle can
reach from a starting point, and in what order a "wave" of traffic spreads.
"""

import sys
from collections import deque


def bfs(network, start, record_steps=True):
    """
    Breadth First Search from `start`.

    `record_steps=False` skips the step table (used when timing the algorithm).

    Returns a dictionary with these keys:
        order        intersections in the order they were visited
        levels       {intersection: number of roads away from the start}
        parent       {intersection: the intersection it was discovered from}
        steps        one row per visited intersection, showing the queue
        reachable    list of intersections that can be reached from the start
        unreachable  list of intersections that cannot be reached
    """
    if start not in network.roads:
        raise ValueError(f"Unknown intersection: {start}")

    visited = {start}
    order = []
    levels = {start: 0}
    parent = {start: None}
    queue = deque([start])
    steps = []

    while queue:
        current = queue.popleft()      # take from the FRONT of the queue
        order.append(current)

        newly_discovered = []
        for neighbour in network.neighbours(current):
            if neighbour not in visited:
                visited.add(neighbour)
                levels[neighbour] = levels[current] + 1
                parent[neighbour] = current
                queue.append(neighbour)  # add to the BACK of the queue
                newly_discovered.append(neighbour)

        if record_steps:
            steps.append({
                "Step": len(steps) + 1,
                "Visiting": current,
                "Level": levels[current],
                "Newly discovered": ", ".join(newly_discovered) or "-",
                "Queue after this step": ", ".join(queue) or "(empty)",
            })

    unreachable = [name for name in network.intersections if name not in visited]
    return {
        "order": order,
        "levels": levels,
        "parent": parent,
        "steps": steps,
        "reachable": order,
        "unreachable": unreachable,
    }


def dfs(network, start, record_steps=True):
    """
    Depth First Search from `start` (recursive version).

    `record_steps=False` skips the step table (used when timing the algorithm).

    Returns a dictionary with these keys:
        order        intersections in the order they were visited
        depth        {intersection: how deep in the DFS tree it was found}
        parent       {intersection: the intersection it was discovered from}
        steps        one row per visited intersection, showing the current route
        reachable    list of intersections that can be reached from the start
        unreachable  list of intersections that cannot be reached
    """
    if start not in network.roads:
        raise ValueError(f"Unknown intersection: {start}")

    # Recursion goes one level deeper for every intersection on the current
    # route, so make sure Python allows enough depth for a very large city.
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(network.roads) + 500))

    visited = set()
    order = []
    depth = {}
    parent = {start: None}
    steps = []
    route = []   # the intersections on the current path from the start

    def visit(current):
        visited.add(current)
        order.append(current)
        depth[current] = len(route)
        route.append(current)
        if record_steps:
            steps.append({
                "Step": len(steps) + 1,
                "Visiting": current,
                "Depth": depth[current],
                "Route from start": " -> ".join(route),
            })
        for neighbour in network.neighbours(current):
            if neighbour not in visited:
                parent[neighbour] = current
                visit(neighbour)          # go deeper first
        route.pop()                       # backtrack

    visit(start)

    unreachable = [name for name in network.intersections if name not in visited]
    return {
        "order": order,
        "depth": depth,
        "parent": parent,
        "steps": steps,
        "reachable": order,
        "unreachable": unreachable,
    }


def tree_roads(result):
    """
    The roads along which BFS or DFS first reached each intersection, as
    (parent, intersection, 0) tuples ready for drawing. The 0 is a placeholder
    in the cost slot: the drawing code expects three values but never shows it.
    """
    return [(result["parent"][name], name, 0)
            for name in result["order"] if result["parent"][name] is not None]


def connected_regions(network):
    """
    Split the city into regions (connected components). Vehicles can travel
    between any two intersections in the same region, but never between regions.
    Returns a list of lists of intersection names.
    """
    remaining = set(network.intersections)
    regions = []
    for name in network.intersections:
        if name in remaining:
            region = bfs(network, name)["order"]
            regions.append(region)
            remaining -= set(region)
    return regions
