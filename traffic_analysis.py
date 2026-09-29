"""
traffic_analysis.py
-------------------
Traffic Analysis Module: Bellman-Ford algorithm and congestion simulation.

City administrators change the cost of some roads to simulate congestion
(a slow road) or a closure (a removed road), and then want to see how the
best route and its cost change.

Bellman-Ford finds shortest paths in a different way from Dijkstra: instead
of always expanding the closest intersection, it simply relaxes *every* road
in the city, and repeats that whole sweep up to (intersections - 1) times.
It is slower than Dijkstra, but it is very simple to rerun after road costs
are edited and its pass-by-pass table is easy to explain. It would also cope
with negative costs and detect negative cycles; in this project every cost
is positive, so that check is only a safety net that never fires.
"""

from route_planner import INFINITY, build_path


def bellman_ford(network, source, destination=None, record_steps=True):
    """
    Run the Bellman-Ford algorithm from `source` on a RoadNetwork.

    `record_steps=False` skips the "show your working" bookkeeping, which
    the experiments use so that only the algorithm itself is timed.

    Returns a dictionary with these keys:
        distance        {intersection: shortest cost from the source}
        previous        {intersection: the intersection we arrived from}
        path            list of intersections from source to destination
        cost            total travel cost of that path (infinity if unreachable)
        steps           every distance update, in order
        passes          snapshot of all distances after each full pass
        passes_needed   how many passes were run before the distances settled
        negative_cycle  True if a negative cycle exists (never for real roads)
    """
    if source not in network.roads:
        raise ValueError(f"Unknown intersection: {source}")
    if destination is not None and destination not in network.roads:
        raise ValueError(f"Unknown intersection: {destination}")

    distance = {name: INFINITY for name in network.intersections}
    previous = {name: None for name in network.intersections}
    distance[source] = 0

    # Roads are two-way, so every road is relaxed in both directions.
    directed_roads = []
    for start, end, cost in network.edges():
        directed_roads.append((start, end, cost))
        directed_roads.append((end, start, cost))

    steps = []
    passes = []
    passes_needed = 0

    # At most (number of intersections - 1) passes are ever needed, because
    # a shortest path can never use more roads than that.
    for pass_number in range(1, len(network.intersections)):
        passes_needed = pass_number
        something_changed = False

        for start, end, cost in directed_roads:
            if distance[start] == INFINITY:
                continue   # we have not reached `start` yet, nothing to relax
            new_distance = distance[start] + cost
            if new_distance < distance[end]:
                if record_steps:
                    steps.append({
                        "Step": len(steps) + 1,
                        "Pass": pass_number,
                        "Road": f"{start} -> {end}",
                        "Road cost": cost,
                        "Old distance": distance[end],
                        "New distance": new_distance,
                    })
                distance[end] = new_distance
                previous[end] = start
                something_changed = True

        if record_steps:
            passes.append({"Pass": pass_number, **distance})

        # If a whole pass changed nothing, the distances are final. Stop early.
        if not something_changed:
            break

    # One extra check: if any road can still be relaxed, a negative cycle
    # exists and "shortest path" has no meaning. Cannot happen with positive costs.
    negative_cycle = False
    for start, end, cost in directed_roads:
        if distance[start] != INFINITY and distance[start] + cost < distance[end]:
            negative_cycle = True
            break

    path = build_path(previous, source, destination) if destination else []
    cost = distance[destination] if destination else None

    return {
        "distance": distance,
        "previous": previous,
        "path": path,
        "cost": cost,
        "steps": steps,
        "passes": passes,
        "passes_needed": passes_needed,
        "negative_cycle": negative_cycle,
    }


# ----------------------------------------------------------------------
# Congestion simulation
# ----------------------------------------------------------------------
def apply_congestion(network, changes):
    """
    Return a *copy* of the network with the requested changes applied.

    `changes` is a list of dictionaries, one per road:
        {"from": "A", "to": "B", "new_cost": 12}     -> road becomes slower / faster
        {"from": "A", "to": "B", "new_cost": None}   -> road is closed (removed)

    The original network is never modified, so "before" and "after" can
    always be compared side by side.
    """
    congested = network.copy()
    for change in changes:
        start, end, new_cost = change["from"], change["to"], change["new_cost"]
        if not congested.has_road(start, end):
            continue   # the road may already have been removed
        if new_cost is None:
            congested.remove_road(start, end)
        else:
            congested.update_road(start, end, new_cost)
    return congested


def congest_route(network, path, factor=3):
    """
    Build a list of changes that multiply the cost of every road on `path`
    by `factor`. Handy for a one-click "peak hour on the current route" demo.
    """
    changes = []
    for i in range(len(path) - 1):
        start, end = path[i], path[i + 1]
        changes.append({
            "from": start,
            "to": end,
            "new_cost": network.get_cost(start, end) * factor,
        })
    return changes


def compare_routes(network, congested_network, source, destination):
    """
    Run Bellman-Ford on the original and the congested network and
    summarise what changed for the commuter.
    """
    before = bellman_ford(network, source, destination)
    after = bellman_ford(congested_network, source, destination)

    original_cost = before["cost"]
    updated_cost = after["cost"]

    if original_cost == INFINITY or updated_cost == INFINITY:
        extra_cost = INFINITY
        percent_increase = INFINITY
    else:
        extra_cost = updated_cost - original_cost
        percent_increase = (extra_cost / original_cost * 100) if original_cost else 0

    return {
        "before": before,
        "after": after,
        "original_path": before["path"],
        "updated_path": after["path"],
        "original_cost": original_cost,
        "updated_cost": updated_cost,
        "extra_cost": extra_cost,
        "percent_increase": percent_increase,
        "route_changed": before["path"] != after["path"],
    }
