"""
mst_planner.py
--------------
Infrastructure Planning Module: Prim's and Kruskal's algorithms.

The city wants to connect every major intersection using the cheapest possible
set of roads. That is exactly a Minimum Spanning Tree (MST): a set of roads
that reaches every intersection, contains no cycle, and has the smallest
possible total cost. For N intersections the MST always has N - 1 roads.

    * Prim grows ONE tree from a starting intersection. At every step it adds
      the cheapest road that connects the tree to a new intersection. If the
      city is not connected it starts another tree for each separate region.
    * Kruskal sorts ALL roads by cost and keeps adding the cheapest road that
      does not create a cycle. A union-find structure answers the question
      "are these two intersections already connected?" very quickly.

Both algorithms give the same total cost (the MST cost is unique), although
they may pick different roads when several roads share the same cost.
"""

import heapq


def prim(network, start=None, record_steps=True):
    """
    Prim's algorithm.

    `record_steps=False` skips the step table (used when timing the algorithm).

    Returns a dictionary with these keys:
        mst_edges    list of (start, end, cost) roads chosen for the tree
        total_cost   sum of the chosen road costs
        steps        every road that was considered and what was decided
        connected    False if the city is in several pieces; the result is then a
                     spanning forest with one tree per region, the same as Kruskal
    """
    intersections = network.intersections
    if not intersections:
        return {"mst_edges": [], "total_cost": 0, "steps": [], "connected": True}
    if start is None:
        start = intersections[0]
    if start not in network.roads:
        raise ValueError(f"Unknown intersection: {start}")

    in_tree = {start}
    mst_edges = []
    steps = []

    # Candidate roads leaving the tree, kept in a min-heap as (cost, from, to)
    # so the cheapest road is always at the front.
    candidates = []
    for neighbour, cost in network.neighbours(start).items():
        heapq.heappush(candidates, (cost, start, neighbour))

    trees = 1
    while len(in_tree) < len(intersections):
        if not candidates:
            # The tree cannot grow any further, so the city is not connected.
            # Start another tree from the next intersection that is still outside.
            next_start = next(name for name in intersections if name not in in_tree)
            in_tree.add(next_start)
            trees += 1
            if record_steps:
                steps.append({
                    "Step": len(steps) + 1,
                    "Road": f"(new tree from {next_start})",
                    "Cost": 0,
                    "Decision": "No road reaches the rest of the city, started another tree",
                })
            for neighbour, next_cost in network.neighbours(next_start).items():
                if neighbour not in in_tree:
                    heapq.heappush(candidates, (next_cost, next_start, neighbour))
            continue

        cost, tree_side, new_side = heapq.heappop(candidates)

        if new_side in in_tree:
            # Both ends are already in the tree, this road would form a cycle.
            if record_steps:
                steps.append({
                    "Step": len(steps) + 1,
                    "Road": f"{tree_side} - {new_side}",
                    "Cost": cost,
                    "Decision": "Skipped (both ends already connected)",
                })
            continue

        in_tree.add(new_side)
        mst_edges.append((tree_side, new_side, cost))
        if record_steps:
            steps.append({
                "Step": len(steps) + 1,
                "Road": f"{tree_side} - {new_side}",
                "Cost": cost,
                "Decision": "Added to the tree",
            })

        # The new intersection brings new candidate roads with it.
        for neighbour, next_cost in network.neighbours(new_side).items():
            if neighbour not in in_tree:
                heapq.heappush(candidates, (next_cost, new_side, neighbour))

    return {
        "mst_edges": mst_edges,
        "total_cost": sum(cost for _, _, cost in mst_edges),
        "steps": steps,
        "connected": trees == 1,
    }


def kruskal(network, record_steps=True):
    """
    Kruskal's algorithm.

    `record_steps=False` skips the step table (used when timing the algorithm).

    Returns a dictionary with these keys:
        mst_edges    list of (start, end, cost) roads chosen for the tree
        total_cost   sum of the chosen road costs
        steps        every road in sorted order and whether it was kept
        connected    False if the city is in several disconnected pieces
    """
    intersections = network.intersections

    # Union-find: every intersection starts as its own little group.
    parent = {name: name for name in intersections}

    def find(name):
        """Follow the parent links up to the representative of the group."""
        while parent[name] != name:
            parent[name] = parent[parent[name]]   # path halving keeps it fast
            name = parent[name]
        return name

    def union(a, b):
        """Merge the two groups that contain a and b."""
        parent[find(a)] = find(b)

    mst_edges = []
    steps = []

    # Cheapest roads first.
    sorted_roads = sorted(network.edges(), key=lambda road: road[2])

    for start, end, cost in sorted_roads:
        if find(start) != find(end):
            union(start, end)
            mst_edges.append((start, end, cost))
            decision = "Added to the tree"
        else:
            decision = "Rejected (would create a cycle)"

        if record_steps:
            steps.append({
                "Step": len(steps) + 1,
                "Road": f"{start} - {end}",
                "Cost": cost,
                "Decision": decision,
            })

        # A spanning tree of N intersections has exactly N - 1 roads.
        if len(mst_edges) == len(intersections) - 1:
            break

    return {
        "mst_edges": mst_edges,
        "total_cost": sum(cost for _, _, cost in mst_edges),
        "steps": steps,
        "connected": len(mst_edges) == max(len(intersections) - 1, 0),
    }


def road_set(edges):
    """The roads as a set of unordered pairs: frozenset makes (A, B) and (B, A) the same road."""
    return {frozenset((start, end)) for start, end, _cost in edges}


def same_roads(edges_a, edges_b):
    """True when two lists of roads contain the same roads (ignoring direction)."""
    return road_set(edges_a) == road_set(edges_b)
