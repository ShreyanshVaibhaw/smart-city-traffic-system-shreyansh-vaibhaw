"""
visualizer.py
-------------
Drawing and formatting helpers shared by the Streamlit app, the notebook
and the report. Everything here is about presentation only; the algorithm
modules never import it.
"""

import math

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

# One colour scheme for the whole project.
NODE_COLOUR = "#9ecae1"        # light blue for ordinary intersections
NODE_HIGHLIGHT = "#fd8d3c"     # orange for intersections on a route
NODE_START = "#31a354"         # green for the start / source
NODE_END = "#de2d26"           # red for the destination
EDGE_COLOUR = "#bdbdbd"        # grey for ordinary roads
EDGE_HIGHLIGHT = "#e6550d"     # orange for a route or the MST
EDGE_CHANGED = "#d62728"       # red dashed for congested / changed roads


def positions_for(network, seed=7):
    """
    Fixed positions for drawing. Using the same seed every time means the
    map does not jump around when a route is highlighted.
    """
    graph = network.to_networkx()
    if network.number_of_intersections() == 0:
        return {}
    spread = 1.6 / math.sqrt(max(network.number_of_intersections(), 1))
    # weight=None: the layout ignores road costs, so editing a cost for a
    # congestion experiment does not move the intersections around.
    return nx.spring_layout(graph, seed=seed, k=spread, weight=None)


def draw_network(network, positions=None, highlight_path=None, highlight_edges=None,
                 highlight_nodes=None, changed_roads=None, closed_roads=None,
                 start=None, end=None, title="", show_costs=None):
    """
    Draw the city map and return a matplotlib Figure.

        highlight_path   list of intersections, drawn as a bold orange route
        highlight_edges  list of (a, b, cost) roads, drawn bold (used for the MST)
        highlight_nodes  intersections to colour orange without drawing a route
        changed_roads    list of (a, b) roads, drawn red and dashed (congestion)
        closed_roads     list of (a, b) roads that were removed, drawn red and dotted
        start / end      intersections to colour green / red
        show_costs       draw the road costs; defaults to "only for small cities"
    """
    graph = network.to_networkx()
    if positions is None:
        positions = positions_for(network)

    size = network.number_of_intersections()
    if show_costs is None:
        show_costs = size <= 20

    # Sizes shrink as the city grows so that big maps stay readable.
    if size <= 15:
        node_size, font_size = 1100, 8
    elif size <= 40:
        node_size, font_size = 450, 7
    else:
        node_size, font_size = 160, 5

    fig, ax = plt.subplots(figsize=(9, 6.5))

    # 1) all roads in grey
    nx.draw_networkx_edges(graph, positions, ax=ax, edge_color=EDGE_COLOUR, width=1.3)

    # 2) special roads drawn on top
    if highlight_edges:
        edge_list = [(a, b) for a, b, _ in highlight_edges]
        nx.draw_networkx_edges(graph, positions, ax=ax, edgelist=edge_list,
                               edge_color=EDGE_HIGHLIGHT, width=3.2)
    if highlight_path and len(highlight_path) > 1:
        route_edges = list(zip(highlight_path, highlight_path[1:]))
        nx.draw_networkx_edges(graph, positions, ax=ax, edgelist=route_edges,
                               edge_color=EDGE_HIGHLIGHT, width=3.5)
    if changed_roads:
        changed = [(a, b) for a, b in changed_roads if graph.has_edge(a, b)]
        nx.draw_networkx_edges(graph, positions, ax=ax, edgelist=changed,
                               edge_color=EDGE_CHANGED, width=3, style="dashed")
    if closed_roads:
        # A closed road is no longer in the graph, so it is drawn by hand as a dotted line.
        for a, b in closed_roads:
            if a in positions and b in positions:
                (x1, y1), (x2, y2) = positions[a], positions[b]
                ax.plot([x1, x2], [y1, y2], color=EDGE_CHANGED, linestyle=":", linewidth=2.2)

    # 3) intersections, coloured by their role
    on_route = set(highlight_path or []) | set(highlight_nodes or [])
    colours = []
    for name in graph.nodes:
        if name == start:
            colours.append(NODE_START)
        elif name == end:
            colours.append(NODE_END)
        elif name in on_route:
            colours.append(NODE_HIGHLIGHT)
        else:
            colours.append(NODE_COLOUR)
    nx.draw_networkx_nodes(graph, positions, ax=ax, node_color=colours,
                           node_size=node_size, edgecolors="#555555", linewidths=0.8)

    # 4) labels (above 60 intersections the names overlap, so only the map is drawn)
    if size <= 60:
        nx.draw_networkx_labels(graph, positions, ax=ax, font_size=font_size)
    if show_costs:
        labels = {(a, b): f"{c:g}" for a, b, c in network.edges()}
        nx.draw_networkx_edge_labels(graph, positions, ax=ax, edge_labels=labels,
                                     font_size=7, label_pos=0.5,
                                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))

    ax.set_title(title, fontsize=12)
    ax.axis("off")
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------
# Small formatting helpers
# ----------------------------------------------------------------------
def format_cost(value, unit=""):
    """Turn 12.0 into '12', 12.5 into '12.5' and infinity into the symbol."""
    if value is None:
        return "-"
    if value == math.inf:
        return "∞ (unreachable)"
    text = f"{value:g}"
    return f"{text} {unit}".strip()


def format_path(path, arrow=" → "):
    """Join a list of intersections into a readable route."""
    if not path:
        return "No route found"
    return arrow.join(path)


def _pretty(value):
    """Show infinity as ∞ and whole-number costs without a trailing .0"""
    if isinstance(value, float):
        if value == math.inf:
            return "∞"
        if value.is_integer():
            return int(value)
    return value


def _text_columns(frame):
    """
    A column that mixes numbers with the ∞ symbol is turned into text, so that
    Streamlit can show the table without warnings. Purely numeric columns stay numeric.
    """
    for column in frame.columns:
        if frame[column].map(lambda value: isinstance(value, str)).any():
            frame[column] = frame[column].astype(str)
    return frame


def steps_table(steps):
    """Convert a list of step dictionaries into a DataFrame, with ∞ for infinity."""
    if not steps:
        return pd.DataFrame()
    return _text_columns(pd.DataFrame(steps).map(_pretty))


def distance_table(rows, first_column):
    """
    Turn the per-iteration distance snapshots (from Dijkstra or Bellman-Ford)
    into a DataFrame with one row per iteration and one column per intersection.
    """
    if not rows:
        return pd.DataFrame()
    return _text_columns(pd.DataFrame(rows).set_index(first_column).map(_pretty))


def edges_table(edges):
    """List of (a, b, cost) roads as a DataFrame."""
    return pd.DataFrame([{"From": a, "To": b, "Cost": c} for a, b, c in edges],
                        columns=["From", "To", "Cost"])
