"""
road_network.py
---------------
Road Network Modeling Module.

The city is stored as a weighted, undirected graph:
    * every intersection (junction) is a vertex
    * every road between two intersections is an edge
    * the weight of an edge is the travel cost (distance in km or time in minutes)

The graph is kept as a dictionary of dictionaries, for example:

    roads = {
        "Central Square": {"Old Market": 2, "Railway Station": 4},
        "Old Market":     {"Central Square": 2},
        ...
    }

This is the classic "adjacency list" representation. The adjacency matrix
can be produced from it whenever it is needed.
"""

import csv
import io
import math
import random

import networkx as nx
import pandas as pd


class RoadNetwork:
    """A small graph class that represents the roads of a city."""

    def __init__(self):
        # Insertion order is kept, so the list of intersections is stable.
        self.roads = {}

    # ------------------------------------------------------------------
    # Building the network
    # ------------------------------------------------------------------
    def add_intersection(self, name):
        """Add an intersection (vertex). Ignores duplicates."""
        name = name.strip()
        if name == "":
            raise ValueError("Intersection name cannot be empty.")
        if name not in self.roads:
            self.roads[name] = {}

    def add_road(self, start, end, cost):
        """Add a two-way road (edge) between two intersections with a travel cost."""
        start, end = start.strip(), end.strip()   # same cleaning as add_intersection
        if start == end:
            raise ValueError("A road must connect two different intersections.")
        cost = float(cost)
        if not math.isfinite(cost) or cost <= 0:
            raise ValueError("Travel cost must be a positive number.")
        # Make sure both intersections exist before joining them.
        self.add_intersection(start)
        self.add_intersection(end)
        self.roads[start][end] = cost
        self.roads[end][start] = cost

    def update_road(self, start, end, new_cost):
        """Change the travel cost of an existing road (used to simulate congestion)."""
        if not self.has_road(start, end):
            raise ValueError(f"There is no road between {start} and {end}.")
        self.add_road(start, end, new_cost)

    def remove_road(self, start, end):
        """Remove a road from the network (used to simulate a road closure)."""
        if self.has_road(start, end):
            del self.roads[start][end]
            del self.roads[end][start]

    def remove_intersection(self, name):
        """Remove an intersection and every road that touches it."""
        if name in self.roads:
            for neighbour in list(self.roads[name]):
                del self.roads[neighbour][name]
            del self.roads[name]

    def copy(self):
        """Return an independent copy, so experiments do not change the original."""
        clone = RoadNetwork()
        for start, neighbours in self.roads.items():
            clone.roads[start] = dict(neighbours)
        return clone

    # ------------------------------------------------------------------
    # Reading the network
    # ------------------------------------------------------------------
    @property
    def intersections(self):
        """List of all intersection names."""
        return list(self.roads.keys())

    def neighbours(self, name):
        """Dictionary of {neighbour: cost} for one intersection."""
        return self.roads.get(name, {})

    def has_road(self, start, end):
        return start in self.roads and end in self.roads[start]

    def get_cost(self, start, end):
        return self.roads[start][end]

    def edges(self):
        """Every road exactly once as (start, end, cost) tuples."""
        seen = set()
        result = []
        for start, neighbours in self.roads.items():
            for end, cost in neighbours.items():
                if (end, start) not in seen:
                    seen.add((start, end))
                    result.append((start, end, cost))
        return result

    def number_of_intersections(self):
        return len(self.roads)

    def number_of_roads(self):
        return len(self.edges())

    def total_cost(self):
        return sum(cost for _, _, cost in self.edges())

    # ------------------------------------------------------------------
    # Representations that the assignment asks us to display
    # ------------------------------------------------------------------
    def adjacency_list(self):
        """Adjacency list as {intersection: [(neighbour, cost), ...]}."""
        return {
            name: sorted(neighbours.items())
            for name, neighbours in self.roads.items()
        }

    def adjacency_list_text(self):
        """Adjacency list as printable lines, for example 'A -> B (4), C (2)'."""
        lines = []
        for name, neighbours in self.adjacency_list().items():
            if neighbours:
                joined = ", ".join(f"{n} ({cost:g})" for n, cost in neighbours)
            else:
                joined = "(no roads)"
            lines.append(f"{name} -> {joined}")
        return lines

    def adjacency_matrix(self):
        """Adjacency matrix as a pandas DataFrame. 0 means there is no direct road."""
        names = self.intersections
        matrix = []
        for row_name in names:
            row = []
            for col_name in names:
                row.append(self.roads[row_name].get(col_name, 0))
            matrix.append(row)
        return pd.DataFrame(matrix, index=names, columns=names)

    def road_table(self):
        """All roads as a DataFrame, handy for showing in the app."""
        rows = [{"From": s, "To": e, "Cost": c} for s, e, c in self.edges()]
        return pd.DataFrame(rows, columns=["From", "To", "Cost"])

    def to_networkx(self):
        """Convert to a networkx Graph (only used for drawing)."""
        graph = nx.Graph()
        graph.add_nodes_from(self.intersections)
        for start, end, cost in self.edges():
            graph.add_edge(start, end, weight=cost)
        return graph

    # ------------------------------------------------------------------
    # Saving and loading
    # ------------------------------------------------------------------
    def to_csv_text(self):
        """Roads as CSV text with the columns from,to,cost."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["from", "to", "cost"])
        for start, end, cost in self.edges():
            writer.writerow([start, end, cost])
        return output.getvalue()

    @classmethod
    def from_csv_text(cls, text):
        """Build a network from CSV text with the columns from, to and cost (any order or case)."""
        network = cls()
        reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))   # Excel adds a byte-order mark
        if not reader.fieldnames:
            raise ValueError("The file is empty.")
        columns = {name.strip().lower(): name for name in reader.fieldnames}
        if not {"from", "to", "cost"} <= set(columns):
            raise ValueError("The CSV needs the columns from, to and cost.")
        for line_number, row in enumerate(reader, start=2):
            start, end, cost = row[columns["from"]], row[columns["to"]], row[columns["cost"]]
            if not start or not end or cost in (None, ""):
                raise ValueError(f"Line {line_number} is incomplete.")
            network.add_road(start, end, cost)
        return network

    # ------------------------------------------------------------------
    # Ready-made networks
    # ------------------------------------------------------------------
    @classmethod
    def sample_city(cls):
        """A small fictional city with 10 intersections and 15 roads (cost = minutes)."""
        network = cls()
        sample_roads = [
            ("Central Square", "Railway Station", 4),
            ("Central Square", "Old Market", 2),
            ("Central Square", "City Hospital", 5),
            ("Railway Station", "Bus Terminal", 3),
            ("Railway Station", "University", 7),
            ("Old Market", "Bus Terminal", 6),
            ("Old Market", "Riverside", 3),
            ("City Hospital", "University", 4),
            ("City Hospital", "Stadium", 7),
            ("Bus Terminal", "Tech Park", 9),
            ("University", "Tech Park", 5),
            ("University", "Stadium", 3),
            ("Riverside", "Stadium", 7),
            ("Tech Park", "Airport Road", 6),
            ("Stadium", "Airport Road", 9),
        ]
        for start, end, cost in sample_roads:
            network.add_road(start, end, cost)
        return network

    @classmethod
    def random_city(cls, size, seed=42, roads_per_intersection=2):
        """
        A random but connected city with `size` intersections named J1, J2, ...

        First every new junction is joined to an earlier one (this guarantees
        that the city is connected), then extra random roads are added until
        there are about `roads_per_intersection * size` roads in total.
        """
        rng = random.Random(seed)
        network = cls()
        names = [f"J{i}" for i in range(1, size + 1)]
        for name in names:
            network.add_intersection(name)
        if size < 2:
            return network   # nothing to connect

        # Step 1: a random spanning tree keeps everything connected.
        for i in range(1, size):
            earlier = names[rng.randrange(0, i)]
            network.add_road(names[i], earlier, rng.randint(1, 20))

        # Step 2: extra roads give the commuters alternative routes.
        wanted = roads_per_intersection * size
        attempts = 0
        while network.number_of_roads() < wanted and attempts < wanted * 20:
            attempts += 1
            a, b = rng.sample(names, 2)
            if not network.has_road(a, b):
                network.add_road(a, b, rng.randint(1, 20))
        return network
