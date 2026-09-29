"""
app.py
------
Smart City Traffic Management and Route Optimization System.

A Streamlit web application that ties the project modules together:

    1. Road Network Modeling    -> road_network.py
    2. Route Planning           -> route_planner.py        (Dijkstra)
    3. Traffic Analysis         -> traffic_analysis.py     (Bellman-Ford)
    4. Network Connectivity     -> connectivity_module.py  (BFS and DFS)
    5. Infrastructure Planning  -> mst_planner.py          (Prim and Kruskal)
    6. Comparative Analysis     -> experiments.py

Run it with:  streamlit run app.py
"""

import matplotlib

matplotlib.use("Agg")   # draw figures in memory; Streamlit shows them as images

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from connectivity_module import bfs, connected_regions, dfs, tree_roads
from experiments import DEFAULT_SIZES, comparison_table, run_experiments, summary_table, timing_chart
from mst_planner import kruskal, prim, same_roads
from road_network import RoadNetwork
from route_planner import INFINITY, dijkstra
from traffic_analysis import apply_congestion, bellman_ford, compare_routes, congest_route
from visualizer import (distance_table, draw_network, edges_table, format_cost,
                        format_path, positions_for, steps_table)

PAGES = [
    "Road Network",
    "Route Planning",
    "Traffic Analysis",
    "Network Connectivity",
    "Infrastructure Planning",
    "Comparative Analysis",
]

st.set_page_config(
    page_title="Smart City Traffic Management System",
    page_icon="🚦",
    layout="wide",
)


# ----------------------------------------------------------------------
# Session helpers
# ----------------------------------------------------------------------
def get_network():
    """The city that every page works on. The sample city is loaded at the start."""
    if "network" not in st.session_state:
        st.session_state.network = RoadNetwork.sample_city()
        st.session_state.congestion = []
    return st.session_state.network


def set_network(network):
    """Replace the city and drop the congestion changes, which referred to the old roads."""
    st.session_state.network = network
    st.session_state.congestion = []


def map_positions():
    """
    Positions of the intersections on the map. They are cached until the set
    of intersections or roads changes, so the map does not jump around.
    """
    network = get_network()
    key = (tuple(network.intersections),
           frozenset(frozenset((a, b)) for a, b, _ in network.edges()))
    if st.session_state.get("positions_key") != key:
        st.session_state.positions = positions_for(network)
        st.session_state.positions_key = key
    return st.session_state.positions


def show_figure(figure):
    st.pyplot(figure)
    plt.close(figure)


def flash(message, kind="success"):
    """Remember a message so it survives the rerun after a button click."""
    st.session_state.flash = (kind, message)


def show_flash():
    kind, message = st.session_state.pop("flash", (None, None))
    if message:
        (st.warning if kind == "warning" else st.success)(message)


def too_small(network, minimum=2, need_roads=False):
    """Warn and return True when the city is too small for a module to work."""
    if network.number_of_intersections() < minimum or (need_roads and network.number_of_roads() == 0):
        needed = ("at least two intersections joined by a road" if need_roads
                  else f"at least {minimum} intersection(s)")
        st.warning(f"This module needs a city with {needed}. "
                   "Build or load one on the Road Network page first.")
        return True
    return False


def add_change(start, end, new_cost):
    """Record a congestion change, replacing any earlier change to the same road."""
    kept = [change for change in st.session_state.congestion
            if {change["from"], change["to"]} != {start, end}]
    kept.append({"from": start, "to": end, "new_cost": new_cost})
    st.session_state.congestion = kept


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
def sidebar():
    st.sidebar.title("Smart City Traffic")
    st.sidebar.caption("Traffic Management and Route Optimization System")

    # ?page=Route%20Planning in the address bar opens that module directly.
    requested = st.query_params.get("page", PAGES[0])
    index = PAGES.index(requested) if requested in PAGES else 0
    page = st.sidebar.radio("Module", PAGES, index=index)

    network = get_network()
    st.sidebar.divider()
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Intersections", network.number_of_intersections())
    col2.metric("Roads", network.number_of_roads())
    st.sidebar.divider()
    st.sidebar.caption("ENCA351 Design and Analysis of Algorithms Lab · BCA (AI&DS) · Semester V")
    st.sidebar.caption("Shreyansh Vaibhaw · 2401201094")
    return page


# ----------------------------------------------------------------------
# Page 1: Road Network Modeling
# ----------------------------------------------------------------------
def page_road_network():
    st.header("Road Network Modeling")
    st.write("The city is modelled as a weighted graph. **Intersections** are the vertices, "
             "**roads** are the edges and the **travel cost** (distance or time) is the edge weight.")
    show_flash()
    network = get_network()

    # ---- 1. create or load ----
    st.subheader("1. Create or load a city")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("Ten named intersections and fifteen roads, costs in minutes.")
        if st.button("Load the sample city", width="stretch"):
            set_network(RoadNetwork.sample_city())
            flash("Sample city loaded.")
            st.rerun()
    with col2:
        size = st.number_input("Number of intersections", min_value=3, max_value=200, value=25)
        if st.button("Generate a random city", width="stretch"):
            set_network(RoadNetwork.random_city(int(size)))
            flash(f"Random city with {int(size)} intersections generated.")
            st.rerun()
    with col3:
        st.write("Start from scratch and add every intersection and road yourself.")
        if st.button("Start an empty city", width="stretch"):
            set_network(RoadNetwork())
            flash("Empty city ready. Add intersections and roads below.")
            st.rerun()

    col_up, col_down = st.columns(2)
    with col_up:
        uploaded = st.file_uploader("Load roads from a CSV file (columns: from, to, cost)", type="csv")
        if uploaded is not None and st.button("Use the uploaded file"):
            try:
                # utf-8-sig also accepts files saved by Excel, which start with a byte-order mark.
                loaded = RoadNetwork.from_csv_text(uploaded.getvalue().decode("utf-8-sig"))
                if loaded.number_of_roads() == 0:
                    st.error("The file contains no roads, so the current city was kept.")
                else:
                    set_network(loaded)
                    flash(f"Loaded {uploaded.name}: {loaded.number_of_intersections()} intersections "
                          f"and {loaded.number_of_roads()} roads.")
                    st.rerun()
            except Exception as error:
                st.error(f"Could not read the file: {error}")
    with col_down:
        st.write("Save the current city so it can be loaded again later.")
        st.download_button("Download the current city as CSV", network.to_csv_text(),
                           file_name="city_roads.csv", mime="text/csv")

    # ---- 2. add intersections and roads ----
    st.subheader("2. Add intersections and roads")
    left, right = st.columns(2)
    with left:
        with st.form("add_intersection_form", clear_on_submit=True):
            name = st.text_input("Intersection name", placeholder="for example: Metro Station")
            if st.form_submit_button("Add intersection"):
                if name.strip() in network.roads:
                    st.warning(f"'{name.strip()}' already exists.")
                else:
                    try:
                        network.add_intersection(name)
                        flash(f"Added intersection '{name.strip()}'.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
    with right:
        names = network.intersections
        if len(names) < 2:
            st.info("Add at least two intersections before adding a road.")
        else:
            with st.form("add_road_form"):
                start = st.selectbox("From", names)
                end = st.selectbox("To", names, index=1)
                cost = st.number_input("Travel cost (distance or time)", min_value=0.1, value=5.0, step=0.5)
                if st.form_submit_button("Add road"):
                    try:
                        network.add_road(start, end, cost)
                        flash(f"Added road {start} – {end} with cost {cost:g}.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

    # ---- 3. edit or remove ----
    roads = network.edges()
    if roads or network.intersections:
        st.subheader("3. Edit or remove")
    if roads:
        labels = [f"{a} – {b}  (cost {c:g})" for a, b, c in roads]
        c1, c2, c3 = st.columns([3, 2, 2])
        # The key keeps the same road selected after its cost (and so its label) changes.
        chosen = c1.selectbox("Road", range(len(roads)), format_func=lambda i: labels[i], key="edit_road")
        start, end, current = roads[chosen]
        new_cost = c2.number_input("New travel cost", min_value=min(0.1, float(current)),
                                   value=float(current), step=0.5)
        with c3:
            st.write("")
            if st.button("Update cost", width="stretch"):
                network.update_road(start, end, new_cost)
                flash(f"Road {start} – {end} now costs {new_cost:g}.")
                st.rerun()
            if st.button("Remove road", width="stretch"):
                network.remove_road(start, end)
                flash(f"Removed road {start} – {end}.")
                st.rerun()
    if network.intersections:
        with st.expander("Remove an intersection"):
            victim = st.selectbox("Intersection", network.intersections)
            if st.button("Remove this intersection and all its roads"):
                network.remove_intersection(victim)
                flash(f"Removed {victim}.")
                st.rerun()

    # ---- 4. representations ----
    st.subheader("4. Graph representation")
    if network.number_of_intersections() == 0:
        st.info("The city is empty. Add some intersections and roads first.")
        return
    tab_map, tab_list, tab_matrix, tab_table = st.tabs(
        ["City map", "Adjacency list", "Adjacency matrix", "Road table"])
    with tab_map:
        show_figure(draw_network(network, map_positions(), title="City road network"))
    with tab_list:
        st.caption("Each intersection is followed by its neighbours and the cost of the road to each of them.")
        st.code("\n".join(network.adjacency_list_text()), language="text")
    with tab_matrix:
        st.caption("Row i, column j holds the cost of the direct road between i and j. "
                   "A 0 means there is no direct road.")
        st.dataframe(network.adjacency_matrix(), width="stretch")
    with tab_table:
        st.dataframe(network.road_table(), width="stretch", hide_index=True)


# ----------------------------------------------------------------------
# Page 2: Route Planning (Dijkstra)
# ----------------------------------------------------------------------
def page_route_planning():
    st.header("Route Planning")
    st.caption("Dijkstra's algorithm · used by navigation systems, ride-sharing services "
               "and emergency response routing")
    network = get_network()
    if too_small(network, need_roads=True):
        return

    names = network.intersections
    col1, col2 = st.columns(2)
    source = col1.selectbox("Source", names, index=0, key="route_source")
    destination = col2.selectbox("Destination", names, index=len(names) - 1, key="route_destination")
    if source == destination:
        st.info("Choose two different intersections.")
        return

    result = dijkstra(network, source, destination)

    if not result["path"]:
        st.error(f"There is no route from {source} to {destination}. "
                 "They lie in different parts of the network.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total travel cost", format_cost(result["cost"]))
        m2.metric("Roads on the route", len(result["path"]) - 1)
        m3.metric("Distance updates made", len(result["steps"]))
        st.success(f"Shortest route: {format_path(result['path'])}")

    left, right = st.columns([3, 2])
    with left:
        show_figure(draw_network(network, map_positions(), highlight_path=result["path"],
                                 start=source, end=destination,
                                 title=f"Shortest route from {source} to {destination}"))
    with right:
        st.markdown("**Shortest cost from the source to every intersection**")
        rows = [{"Intersection": name,
                 "Shortest cost": format_cost(result["distance"][name]),
                 "Reached via": result["previous"][name] or "-"} for name in names]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.subheader("Intermediate distance updates")
    st.caption("One row is added every time the algorithm finds a shorter way to reach an intersection.")
    st.dataframe(steps_table(result["steps"]), width="stretch", hide_index=True)

    with st.expander("Distance table after each visited intersection"):
        st.dataframe(distance_table(result["table"], "Visited"), width="stretch")

    with st.expander("How Dijkstra's algorithm works"):
        st.markdown(
            "1. Every intersection starts with distance ∞, except the source which gets 0.\n"
            "2. Take the unvisited intersection with the smallest distance and mark it visited.\n"
            "3. For each of its neighbours, check whether *distance + road cost* is smaller than the "
            "neighbour's current distance. If so, update it (this is one row in the table above).\n"
            "4. Repeat until every reachable intersection is visited. The route is read backwards "
            "through the 'reached via' links.\n\n"
            "Time complexity with a binary heap: **O((V + E) log V)**. It needs all road costs to be positive.")


# ----------------------------------------------------------------------
# Page 3: Traffic Analysis (Bellman-Ford)
# ----------------------------------------------------------------------
def page_traffic_analysis():
    st.header("Traffic Analysis")
    st.caption("Bellman-Ford algorithm · used for dynamic traffic management, accident rerouting "
               "and road closure planning")
    show_flash()
    network = get_network()
    if too_small(network, need_roads=True):
        return

    names = network.intersections
    col1, col2 = st.columns(2)
    source = col1.selectbox("Source", names, index=0, key="traffic_source")
    destination = col2.selectbox("Destination", names, index=len(names) - 1, key="traffic_destination")
    if source == destination:
        st.info("Choose two different intersections.")
        return

    changes = st.session_state.congestion

    # ---- 1. congestion editor ----
    st.subheader("1. Simulate congestion")
    st.write("Increase the cost of a road to model slow traffic, or close the road completely. "
             "The original city is kept unchanged so that both routes can be compared.")
    roads = network.edges()
    labels = [f"{a} – {b}  (current cost {c:g})" for a, b, c in roads]
    c1, c2, c3 = st.columns([3, 2, 2])
    chosen = c1.selectbox("Road", range(len(roads)), format_func=lambda i: labels[i], key="traffic_road")
    start, end, current = roads[chosen]
    new_cost = c2.number_input("New travel cost", min_value=min(0.1, float(current)),
                               value=float(current) * 2, step=1.0)
    with c3:
        st.write("")
        if st.button("Apply congestion", width="stretch"):
            add_change(start, end, new_cost)
            flash(f"Road {start} – {end} now costs {new_cost:g} instead of {current:g}.")
            st.rerun()
        if st.button("Close this road", width="stretch"):
            add_change(start, end, None)
            flash(f"Road {start} – {end} is closed.")
            st.rerun()

    quick1, quick2 = st.columns(2)
    if quick1.button("Peak hour: triple the cost of every road on the current shortest route",
                     width="stretch"):
        # "Current" means the route through the city as it is now, with earlier changes applied.
        current_city = apply_congestion(network, changes)
        current_route = bellman_ford(current_city, source, destination)["path"]
        if current_route:
            for change in congest_route(current_city, current_route, factor=3):
                add_change(change["from"], change["to"], change["new_cost"])
            flash("Peak-hour congestion applied to the current shortest route.")
        else:
            flash("There is no route between the chosen intersections, so nothing was changed.", "warning")
        st.rerun()
    if quick2.button("Clear all congestion", width="stretch", disabled=not changes):
        st.session_state.congestion = []
        st.rerun()

    if changes:
        rows = []
        for change in changes:
            a, b = change["from"], change["to"]
            rows.append({
                "From": a,
                "To": b,
                "Original cost": format_cost(network.get_cost(a, b)) if network.has_road(a, b) else "-",
                "New cost": "Closed" if change["new_cost"] is None else format_cost(change["new_cost"]),
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("No congestion applied yet, so the updated route is the same as the original one.")

    # ---- 2. comparison ----
    st.subheader("2. Original route vs. route after congestion")
    congested = apply_congestion(network, changes)
    comparison = compare_routes(network, congested, source, destination)

    extra = comparison["extra_cost"]
    if extra == INFINITY:
        delta_text = "unreachable"
    elif extra == 0:
        delta_text = None
    else:
        delta_text = f"{extra:+g} ({comparison['percent_increase']:+.0f}%)"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Original travel cost", format_cost(comparison["original_cost"]))
    m2.metric("Updated travel cost", format_cost(comparison["updated_cost"]),
              delta=delta_text, delta_color="inverse")
    m3.metric("Extra travel cost", format_cost(extra))
    m4.metric("Route changed?", "Yes" if comparison["route_changed"] else "No")

    changed_roads = [(c["from"], c["to"]) for c in changes if c["new_cost"] is not None]
    closed_roads = [(c["from"], c["to"]) for c in changes if c["new_cost"] is None]
    positions = map_positions()
    left, right = st.columns(2)
    with left:
        st.markdown("**Original route**")
        if comparison["original_path"]:
            st.success(format_path(comparison["original_path"]))
        else:
            st.error("No route exists.")
        show_figure(draw_network(network, positions, highlight_path=comparison["original_path"],
                                 start=source, end=destination, title="Before congestion"))
    with right:
        st.markdown("**Route after congestion**")
        if comparison["updated_path"]:
            st.success(format_path(comparison["updated_path"]))
        else:
            st.error("No route exists after the changes.")
        show_figure(draw_network(congested, positions, highlight_path=comparison["updated_path"],
                                 changed_roads=changed_roads, closed_roads=closed_roads,
                                 start=source, end=destination,
                                 title="After congestion (red dashed = slower road, red dotted = closed road)"))

    # ---- 3. working ----
    st.subheader("3. Bellman-Ford working")
    tab_before, tab_after = st.tabs(["Original network", "Congested network"])
    for tab, run, label in ((tab_before, comparison["before"], "original"),
                            (tab_after, comparison["after"], "congested")):
        with tab:
            st.write(f"Passes run on the {label} network: **{run['passes_needed']}** of at most "
                     f"{len(names) - 1} (the last pass only confirms that nothing changes any more). "
                     f"Distance updates: **{len(run['steps'])}**.")
            if run["negative_cycle"]:
                st.error("A negative cycle was detected, so shortest paths are not defined.")
            st.markdown("**Distance table after each pass**")
            st.dataframe(distance_table(run["passes"], "Pass"), width="stretch")
            with st.expander("Every distance update"):
                st.dataframe(steps_table(run["steps"]), width="stretch", hide_index=True)

    with st.expander("How the Bellman-Ford algorithm works"):
        st.markdown(
            "1. Every intersection starts with distance ∞, except the source which gets 0.\n"
            "2. Go through **every** road once and relax it: if *distance[start] + cost* is smaller "
            "than *distance[end]*, update it. That is one pass.\n"
            "3. Repeat the pass until nothing changes (at most V - 1 passes are ever needed).\n"
            "4. One more pass that still finds an improvement would mean a negative cycle.\n\n"
            "Time complexity: **O(V × E)**. Slower than Dijkstra, but simple to rerun after road costs "
            "are edited, and it shows its working pass by pass. It would also handle negative costs, "
            "which never occur here because every road cost is positive.")


# ----------------------------------------------------------------------
# Page 4: Network Connectivity (BFS and DFS)
# ----------------------------------------------------------------------
def page_connectivity():
    st.header("Network Connectivity")
    st.caption("Breadth First Search and Depth First Search · used for traffic monitoring, "
               "network exploration and route accessibility analysis")
    network = get_network()
    if too_small(network, minimum=1):
        return

    names = network.intersections
    start = st.selectbox("Starting intersection", names, key="connectivity_start")

    bfs_result = bfs(network, start)
    dfs_result = dfs(network, start)
    regions = connected_regions(network)

    m1, m2, m3 = st.columns(3)
    m1.metric("Reachable intersections (including the start)", len(bfs_result["reachable"]))
    m2.metric("Unreachable intersections", len(bfs_result["unreachable"]))
    m3.metric("Separate regions in the city", len(regions))
    if bfs_result["unreachable"]:
        st.warning("Cannot be reached from " + start + ": " + ", ".join(bfs_result["unreachable"]))

    positions = map_positions()
    left, right = st.columns(2)
    columns = (
        (left, bfs_result, "Breadth First Search", "BFS",
         "Uses a **queue**: the intersections nearest to the start are visited first, level by level."),
        (right, dfs_result, "Depth First Search", "DFS",
         "Uses a **stack** (recursion): follows one road as deep as possible, then backtracks."),
    )
    for column, result, title, short_name, explanation in columns:
        with column:
            st.subheader(title)
            st.write(explanation)
            st.success("Traversal order: " + format_path(result["order"]))
            show_figure(draw_network(network, positions, highlight_edges=tree_roads(result),
                                     highlight_nodes=result["order"], start=start,
                                     title=f"{short_name} tree (orange roads show how each "
                                           "intersection was first reached)"))
            st.dataframe(steps_table(result["steps"]), width="stretch", hide_index=True)

    with st.expander("BFS levels: how many roads away is each intersection?"):
        rows = [{"Intersection": name, "Roads from start": bfs_result["levels"][name]}
                for name in bfs_result["order"]]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    with st.expander("Regions of the city"):
        st.write("Vehicles can travel between any two intersections of the same region, "
                 "but never from one region to another.")
        for number, region in enumerate(regions, start=1):
            st.write(f"Region {number} ({len(region)} intersections): " + ", ".join(region))

    with st.expander("BFS and DFS in a nutshell"):
        st.markdown(
            "Both algorithms visit every intersection reachable from the start exactly once, "
            "so both run in **O(V + E)** time. BFS additionally tells us the smallest number of roads "
            "to each intersection, which is useful to see how far a traffic jam spreads. DFS is the "
            "natural choice for exploring a network region by region or for detecting cycles.")


# ----------------------------------------------------------------------
# Page 5: Infrastructure Planning (Prim and Kruskal)
# ----------------------------------------------------------------------
def page_infrastructure():
    st.header("Infrastructure Planning")
    st.caption("Prim's and Kruskal's algorithms · used for road network expansion, utility "
               "distribution planning and smart city infrastructure development")
    network = get_network()
    if too_small(network, need_roads=True):
        return

    names = network.intersections
    start = st.selectbox("Starting intersection for Prim's algorithm", names, key="mst_start")

    prim_result = prim(network, start)
    kruskal_result = kruskal(network)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prim: total infrastructure cost", format_cost(prim_result["total_cost"]))
    m2.metric("Kruskal: total infrastructure cost", format_cost(kruskal_result["total_cost"]))
    m3.metric("Roads kept", f"{len(kruskal_result['mst_edges'])} of {network.number_of_roads()}")
    m4.metric("Cost saved versus building every road",
              format_cost(network.total_cost() - kruskal_result["total_cost"]))

    if not kruskal_result["connected"]:
        st.warning("The city is not fully connected, so both algorithms return a minimum spanning "
                   "*forest*: one tree for each region.")
    if same_roads(prim_result["mst_edges"], kruskal_result["mst_edges"]):
        st.info("Both algorithms selected exactly the same roads.")
    elif abs(prim_result["total_cost"] - kruskal_result["total_cost"]) < 1e-9:
        st.info("The two algorithms selected different roads but reached the same total cost. "
                "This happens when several roads share the same cost.")
    else:
        st.error("The two totals differ, which should never happen for a minimum spanning tree.")

    positions = map_positions()
    left, right = st.columns(2)
    columns = (
        (left, prim_result, "Prim's algorithm",
         "Grows one tree from the starting intersection, always adding the cheapest road "
         "that reaches a new intersection."),
        (right, kruskal_result, "Kruskal's algorithm",
         "Sorts all roads by cost and keeps the cheapest road that does not create a cycle."),
    )
    for column, result, title, explanation in columns:
        with column:
            st.subheader(title)
            st.write(explanation)
            st.success(f"Total infrastructure cost: {format_cost(result['total_cost'])}")
            show_figure(draw_network(network, positions, highlight_edges=result["mst_edges"],
                                     start=start if title.startswith("Prim") else None,
                                     title=f"{title}: selected roads in orange"))
            st.markdown("**Selected roads**")
            st.dataframe(edges_table(result["mst_edges"]), width="stretch", hide_index=True)
            with st.expander("Step by step"):
                st.dataframe(steps_table(result["steps"]), width="stretch", hide_index=True)


# ----------------------------------------------------------------------
# Page 6: Comparative Analysis
# ----------------------------------------------------------------------
SUITABILITY_NOTES = {
    ("BFS", "DFS"):
        "Both traversals visit every reachable intersection once, so their running time grows "
        "the same way (O(V + E)) and the measured times are almost identical. When one of them looks "
        "faster it is timing noise. **BFS** is the better fit for traffic monitoring because it also "
        "gives the number of roads to every intersection, which shows how far a disruption spreads. "
        "**DFS** suits region-by-region exploration and cycle detection, but its recursion depth grows "
        "with the longest route.",
    ("Dijkstra", "Bellman-Ford"):
        "Both find the same route and cost. **Dijkstra** (O((V + E) log V)) only relaxes the roads of "
        "the closest unsettled intersection, so it is consistently the faster one and the right choice "
        "for live navigation. **Bellman-Ford** (O(V × E)) relaxes every road in every pass. It stops "
        "early once a pass changes nothing, which keeps it usable, but it stays clearly slower. It "
        "suits the Traffic Analysis module because it is simple to rerun after road costs are edited "
        "and its pass-by-pass table is easy to explain. It would also handle negative costs, which "
        "never occur in this project.",
    ("Prim", "Kruskal"):
        "Both algorithms always find the same minimum total cost. **Prim** (O(E log V) with a heap) "
        "only pushes the roads leaving the growing tree onto the heap and was the faster one in these "
        "experiments. **Kruskal** (O(E log E)) sorts every road first and then checks each one with "
        "union-find, which costs a little more time, but its sorted accept-or-reject list is easy to "
        "explain to city planners and it works directly on a plain list of roads.",
}


def page_comparative_analysis():
    st.header("Comparative Analysis")
    st.write("Random but connected cities of different sizes are generated, and every algorithm is "
             "run on each of them. The same functions are used in `project_notebook.ipynb`.")

    col1, col2 = st.columns([3, 1])
    sizes = col1.multiselect("Network sizes (number of intersections)",
                             [10, 25, 50, 100, 150, 200], default=list(DEFAULT_SIZES))
    repeats = col2.number_input("Repeats per timing", min_value=1, max_value=20, value=5)

    if st.button("Run experiments", type="primary", disabled=not sizes):
        with st.spinner("Running every algorithm on every city size..."):
            st.session_state.results = run_experiments(sorted(sizes), repeats=int(repeats))

    results = st.session_state.get("results")
    if results is None:
        st.info("Choose the sizes and click **Run experiments**.")
        return

    st.subheader("All measurements")
    st.caption("Execution time is the median of the repeated runs with the step recording switched off. "
               "The CSV download contains every recorded column.")
    st.dataframe(summary_table(results), width="stretch", hide_index=True)
    st.download_button("Download results as CSV", results.to_csv(index=False),
                       file_name="experiment_results.csv", mime="text/csv")

    st.subheader("Execution time as the city grows")
    figure, axis = plt.subplots(figsize=(9, 5))
    timing_chart(results, axis)
    show_figure(figure)

    st.subheader("Head-to-head comparisons")
    pairs = [("BFS", "DFS"), ("Dijkstra", "Bellman-Ford"), ("Prim", "Kruskal")]
    tabs = st.tabs([f"{a} vs {b}" for a, b in pairs])
    for tab, pair in zip(tabs, pairs):
        with tab:
            st.dataframe(comparison_table(results, *pair), width="stretch", hide_index=True)
            st.markdown(SUITABILITY_NOTES[pair])


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    page = sidebar()
    if page == "Road Network":
        page_road_network()
    elif page == "Route Planning":
        page_route_planning()
    elif page == "Traffic Analysis":
        page_traffic_analysis()
    elif page == "Network Connectivity":
        page_connectivity()
    elif page == "Infrastructure Planning":
        page_infrastructure()
    elif page == "Comparative Analysis":
        page_comparative_analysis()


main()
