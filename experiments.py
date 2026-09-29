"""
experiments.py
--------------
Comparative Analysis helpers (Task 8).

Builds random cities of different sizes, runs every algorithm on each of
them, and records the execution time, number of roads, route length and
peak memory. The notebook and the "Comparative Analysis" page of the app
both use these functions, so the numbers they show come from the same code.

Timing is done with `record_steps=False`, so the step-by-step tables that
the app shows are not included in the measured time. Only the algorithm
itself is measured.
"""

import statistics
import time
import tracemalloc

import pandas as pd

from connectivity_module import bfs, dfs
from mst_planner import kruskal, prim
from road_network import RoadNetwork
from route_planner import dijkstra
from traffic_analysis import bellman_ford

DEFAULT_SIZES = (10, 25, 50, 100)


def measure(function, *args, repeats=5, **kwargs):
    """
    Run `function(*args, **kwargs)` several times and return
    (median time in milliseconds, peak memory in KB).

    The median of several runs is used because a single run of a function
    that takes a fraction of a millisecond is very noisy. Memory is measured
    once with tracemalloc, which tracks the memory that Python allocates.
    """
    timings = []
    for _ in range(repeats):
        started = time.perf_counter()
        function(*args, **kwargs)
        timings.append((time.perf_counter() - started) * 1000)

    tracemalloc.start()
    function(*args, **kwargs)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return statistics.median(timings), peak_bytes / 1024


def run_experiments(sizes=DEFAULT_SIZES, repeats=5, seed=42):
    """
    Run every algorithm on a random city of each size.
    Returns a DataFrame with one row per (city size, algorithm).
    """
    rows = []
    for size in sizes:
        city = RoadNetwork.random_city(size, seed=seed)
        source = city.intersections[0]
        destination = city.intersections[-1]
        roads = city.number_of_roads()

        def record(category, algorithm, ms, kb, **extra):
            rows.append({
                "Intersections": size,
                "Roads": roads,
                "Category": category,
                "Algorithm": algorithm,
                "Execution time (ms)": round(ms, 4),
                "Peak memory (KB)": round(kb, 1),
                **extra,
            })

        # Shortest path: Dijkstra vs Bellman-Ford
        for name, function in (("Dijkstra", dijkstra), ("Bellman-Ford", bellman_ford)):
            ms, kb = measure(function, city, source, destination, repeats=repeats, record_steps=False)
            details = function(city, source, destination)   # once more, with the working recorded
            extra = {
                "Route length (roads)": max(len(details["path"]) - 1, 0),
                "Route cost": details["cost"],
                "Distance updates": len(details["steps"]),
            }
            if name == "Bellman-Ford":
                extra["Passes"] = details["passes_needed"]
            record("Shortest path", name, ms, kb, **extra)

        # Traversal: BFS vs DFS
        for name, function in (("BFS", bfs), ("DFS", dfs)):
            ms, kb = measure(function, city, source, repeats=repeats, record_steps=False)
            details = function(city, source)
            record("Traversal", name, ms, kb,
                   **{"Reachable intersections": len(details["order"])})

        # Minimum spanning tree: Prim vs Kruskal
        for name, function in (("Prim", prim), ("Kruskal", kruskal)):
            ms, kb = measure(function, city, repeats=repeats, record_steps=False)
            details = function(city)
            record("Minimum spanning tree", name, ms, kb,
                   **{"MST roads": len(details["mst_edges"]),
                      "MST cost": details["total_cost"]})

    return pd.DataFrame(rows)


def describe_result(row):
    """One readable phrase for the result of a measurement row."""
    if row["Category"] == "Shortest path":
        return f"route cost {row['Route cost']:g} using {int(row['Route length (roads)'])} roads"
    if row["Category"] == "Traversal":
        return f"{int(row['Reachable intersections'])} intersections reached"
    return f"{int(row['MST roads'])} roads, total cost {row['MST cost']:g}"


def summary_table(results):
    """The measurements in a compact form for display: one result column instead of many."""
    columns = ["Intersections", "Roads", "Category", "Algorithm", "Execution time (ms)", "Peak memory (KB)"]
    table = results[columns].copy()
    table["Result"] = [describe_result(row) for _, row in results.iterrows()]
    return table


def comparison_table(results, first, second):
    """
    Side-by-side comparison of two algorithms from the experiment results:
    one row per city size, with the time and memory of each algorithm and
    which one was faster.
    """
    columns = ["Intersections", "Roads"]
    table = results[results["Algorithm"] == first][columns].copy()
    table = table.drop_duplicates().set_index("Intersections")

    for name in (first, second):
        subset = results[results["Algorithm"] == name].set_index("Intersections")
        table[f"{name} time (ms)"] = subset["Execution time (ms)"]
        table[f"{name} memory (KB)"] = subset["Peak memory (KB)"]

    faster = []
    for size in table.index:
        a = table.loc[size, f"{first} time (ms)"]
        b = table.loc[size, f"{second} time (ms)"]
        faster.append(first if a <= b else second)
    table["Faster"] = faster
    return table.reset_index()


def timing_chart(results, ax=None):
    """Line chart of execution time against city size, one line per algorithm."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5))
    for algorithm, group in results.groupby("Algorithm"):
        group = group.sort_values("Intersections")
        ax.plot(group["Intersections"], group["Execution time (ms)"],
                marker="o", label=algorithm)
    ax.set_xlabel("Number of intersections")
    ax.set_ylabel("Median execution time (ms)")
    ax.set_title("Execution time as the city grows")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return ax
