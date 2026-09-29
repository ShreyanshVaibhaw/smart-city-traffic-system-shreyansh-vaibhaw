"""
route_planner.py
----------------
Route Planning Module: Dijkstra's algorithm.

A commuter wants to travel from a source to a destination with the smallest
total travel cost. Dijkstra's algorithm is the right tool when every road
cost is positive, which is always true for distances and travel times.

The idea in one paragraph: keep a table with the best known distance to every
intersection (infinity everywhere except the source, which is 0). Repeatedly
pick the unvisited intersection with the smallest known distance, mark it
visited, and check whether going through it gives a shorter route to each of
its neighbours (this check is called "relaxing" the road). When every
intersection has been visited, the table holds the final shortest distances.
"""

import heapq
import math

INFINITY = math.inf


def dijkstra(network, source, destination=None, record_steps=True):
    """
    Run Dijkstra's algorithm from `source` on a RoadNetwork.

    `record_steps=False` skips the "show your working" bookkeeping, which
    the experiments use so that only the algorithm itself is timed.

    Returns a dictionary with these keys:
        distance     {intersection: shortest cost from the source}
        previous     {intersection: the intersection we arrived from}
        path         list of intersections from source to destination
        cost         total travel cost of that path (infinity if unreachable)
        steps        every distance update, in order (for the "show working" table)
        table        snapshot of all distances after each intersection is visited
        visit_order  the order in which intersections were finalised
    """
    if source not in network.roads:
        raise ValueError(f"Unknown intersection: {source}")
    if destination is not None and destination not in network.roads:
        raise ValueError(f"Unknown intersection: {destination}")

    distance = {name: INFINITY for name in network.intersections}
    previous = {name: None for name in network.intersections}
    distance[source] = 0

    visited = set()
    visit_order = []
    steps = []   # one row for every time a distance gets smaller
    table = []   # the whole distance table after each visit

    # The priority queue holds (distance, intersection) pairs.
    # heapq always hands us the pair with the smallest distance first.
    queue = [(0, source)]

    while queue:
        current_distance, current = heapq.heappop(queue)

        # The same intersection can be pushed more than once with different
        # distances. Only the first (smallest) one matters, skip the rest.
        if current in visited:
            continue
        visited.add(current)
        visit_order.append(current)

        # Relax every road that leaves the current intersection.
        for neighbour, road_cost in network.neighbours(current).items():
            if neighbour in visited:
                continue
            new_distance = current_distance + road_cost
            if new_distance < distance[neighbour]:
                if record_steps:
                    steps.append({
                        "Step": len(steps) + 1,
                        "Visiting": current,
                        "Road to": neighbour,
                        "Road cost": road_cost,
                        "Old distance": distance[neighbour],
                        "New distance": new_distance,
                    })
                distance[neighbour] = new_distance
                previous[neighbour] = current
                heapq.heappush(queue, (new_distance, neighbour))

        if record_steps:
            table.append({"Visited": current, **distance})

    path = build_path(previous, source, destination) if destination else []
    cost = distance[destination] if destination else None

    return {
        "distance": distance,
        "previous": previous,
        "path": path,
        "cost": cost,
        "steps": steps,
        "table": table,
        "visit_order": visit_order,
    }


def build_path(previous, source, destination):
    """
    Walk backwards from the destination using the `previous` links and
    return the route as a list. An empty list means "unreachable".
    """
    if destination != source and previous[destination] is None:
        return []
    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path


def path_cost(network, path):
    """Add up the road costs along a path (useful to double-check a route)."""
    total = 0
    for i in range(len(path) - 1):
        total += network.get_cost(path[i], path[i + 1])
    return total
