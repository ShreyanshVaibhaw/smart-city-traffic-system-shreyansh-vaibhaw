# Smart City Traffic Management and Route Optimization System

Capstone assignment for **ENCA351 Design and Analysis of Algorithms Lab**, BCA (AI&DS) Semester V,
School of Engineering & Technology, session 2026-27.

The city's road network is modelled as a weighted graph and classic graph algorithms help commuters and
city administrators make routing decisions:

* **Dijkstra** finds the fastest route between two intersections.
* **Bellman-Ford** recomputes routes after congestion or road closures and measures the extra cost.
* **Breadth First Search and Depth First Search** show which intersections are reachable and in what order.
* **Prim and Kruskal** find the cheapest set of roads that keeps the whole city connected.

Everything is wrapped in an interactive Streamlit application, and a Jupyter notebook runs the
comparative analysis. All algorithms are written by hand in plain Python; NetworkX is used only to draw maps.

## Modules

| Module | File | What it does |
|---|---|---|
| Road Network Modeling | `road_network.py` | `RoadNetwork` graph class: add intersections and roads, adjacency list, adjacency matrix, CSV load and save, sample and random cities |
| Route Planning | `route_planner.py` | Dijkstra's algorithm with every intermediate distance update recorded |
| Traffic Analysis | `traffic_analysis.py` | Bellman-Ford algorithm, congestion and closure simulation, before/after route comparison |
| Network Connectivity | `connectivity_module.py` | BFS, DFS, traversal order, reachable intersections, connected regions |
| Infrastructure Planning | `mst_planner.py` | Prim's and Kruskal's algorithms for the minimum spanning tree |
| Comparative Analysis | `experiments.py` | Timing and memory experiments on cities of 10, 25, 50 and 100 intersections |
| Visualisation | `visualizer.py` | Map drawing and table formatting shared by the app, notebook and report |
| Web application | `app.py` | Streamlit interface with one page per module |

## Project structure

```
smart-city-traffic-system-shreyansh-vaibhaw/
├── app.py                      Streamlit web application
├── road_network.py             Graph model (adjacency list and matrix)
├── route_planner.py            Dijkstra
├── traffic_analysis.py         Bellman-Ford and congestion simulation
├── connectivity_module.py      BFS and DFS
├── mst_planner.py              Prim and Kruskal
├── experiments.py              Comparative analysis helpers
├── visualizer.py               Drawing and formatting helpers
├── project_notebook.ipynb      Walk-through of every module and the experiments
├── results/                    experiment_results.csv and the figures saved by the notebook
├── screenshots/                Screenshots of the running application
├── report/                     Final project report
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

```bash
git clone https://github.com/ShreyanshVaibhaw/smart-city-traffic-system-shreyansh-vaibhaw.git
cd smart-city-traffic-system-shreyansh-vaibhaw
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

## Run the application

```bash
streamlit run app.py
```

The app opens at <http://localhost:8501> with the sample city already loaded. Pick a module in the
sidebar. Adding `?page=Route%20Planning` (or any other module name) to the address opens that module directly.

## Run the notebook

```bash
jupyter notebook project_notebook.ipynb
```

The notebook is saved with its outputs, so it can also be read without running it. Running it again
refreshes `results/experiment_results.csv` and the figures in `results/figures/`.

## Using the application

1. **Road Network.** Load the sample city, generate a random city, upload a CSV (columns `from,to,cost`)
   or start from an empty city. Add intersections and roads, edit or remove roads, and view the map,
   the adjacency list, the adjacency matrix and the road table.
2. **Route Planning.** Choose a source and a destination. The shortest route, its total cost, the
   distance to every intersection and every intermediate distance update of Dijkstra's algorithm are shown.
3. **Traffic Analysis.** Raise the cost of a road, close it, or press the peak-hour button to slow down the
   whole current route. Bellman-Ford recomputes the route on the changed city and the page compares the
   original and updated routes, costs and passes side by side.
4. **Network Connectivity.** Choose a starting intersection to see the BFS and DFS traversal orders,
   the queue or recursion route at every step, the reachable and unreachable intersections and the
   regions of the city.
5. **Infrastructure Planning.** Prim and Kruskal build the minimum spanning tree; the page lists the
   selected roads, the total construction cost, the cost saved and each algorithm's decisions.
6. **Comparative Analysis.** Run every algorithm on random cities of the chosen sizes and compare
   execution time and memory in tables and a chart.

## Sample city results

The sample city has 10 intersections and 15 roads with costs in minutes.

| Question | Answer |
|---|---|
| Fastest route, Central Square to Airport Road | Central Square → City Hospital → University → Tech Park → Airport Road, 20 minutes |
| Same route after peak-hour traffic triples the costs on it | Central Square → Old Market → Riverside → Stadium → Airport Road, 21 minutes |
| Route after the University–Tech Park road is closed | Central Square → City Hospital → Stadium → Airport Road, 21 minutes |
| BFS order from Central Square | Central Square, Railway Station, Old Market, City Hospital, Bus Terminal, University, Riverside, Stadium, Tech Park, Airport Road |
| DFS order from Central Square | Central Square, Railway Station, Bus Terminal, Old Market, Riverside, Stadium, City Hospital, University, Tech Park, Airport Road |
| Minimum spanning tree | 9 roads, total cost 35 (building all 15 roads would cost 80) |

## Comparative analysis

Random connected cities with about two roads per intersection. Execution time is the median of 30 runs
with the step recording switched off; memory is the peak measured by `tracemalloc`. Full data is in
`results/experiment_results.csv`.

| Intersections | Roads | Dijkstra (ms) | Bellman-Ford (ms) | BFS (ms) | DFS (ms) | Prim (ms) | Kruskal (ms) |
|---|---|---|---|---|---|---|---|
| 10 | 20 | 0.012 | 0.027 | 0.007 | 0.008 | 0.015 | 0.024 |
| 25 | 50 | 0.032 | 0.094 | 0.017 | 0.019 | 0.040 | 0.063 |
| 50 | 100 | 0.072 | 0.192 | 0.034 | 0.037 | 0.081 | 0.126 |
| 100 | 200 | 0.160 | 0.446 | 0.070 | 0.074 | 0.165 | 0.265 |

Findings: Dijkstra was two to three times faster than Bellman-Ford at every size, and both always agreed
on the route and cost. BFS and DFS were indistinguishable. Prim was faster than Kruskal at every size,
and both always produced the same minimum cost. The discussion is in the notebook and in the report.

## Algorithms at a glance

| Algorithm | Used for | Time complexity |
|---|---|---|
| Dijkstra | Route planning | O((V + E) log V) with a binary heap |
| Bellman-Ford | Traffic analysis, rerouting after congestion | O(V × E), stops early when a pass changes nothing |
| BFS | Reachability, levels from a start point | O(V + E) |
| DFS | Reachability, region exploration | O(V + E) |
| Prim | Minimum spanning tree | O(E log V) with a binary heap |
| Kruskal | Minimum spanning tree | O(E log E) for sorting plus union-find |

## Screenshots

Screenshots of the running application are in the `screenshots/` folder:

* `01_road_network_map.png`, `02_adjacency_list.png`, `03_adjacency_matrix.png`: road network module
* `04_route_planning_dijkstra.png`: shortest route with the intermediate distance updates
* `05_traffic_analysis_bellman_ford.png`: original route against the route after peak-hour congestion
* `06_network_connectivity_bfs_dfs.png`: BFS and DFS traversal orders and trees
* `07_infrastructure_planning_mst.png`: Prim and Kruskal minimum spanning trees
* `08_comparative_analysis.png`, `09_dijkstra_vs_bellman_ford.png`: experiment results

## Report

The final project report is in `report/Final_Project_Report.docx` (also exported as
`report/Final_Project_Report.pdf`). It covers smart city concepts, the system design, the experimental
results, the comparison of the algorithms and the conclusions.

## CSV format for loading a city

```
from,to,cost
Central Square,Railway Station,4
Central Square,Old Market,2
```

Roads are two-way. Costs must be positive numbers (kilometres or minutes).

## Author

Shreyansh Vaibhaw, roll number 2401201094, BCA (AI&DS) Semester V. Course instructor: Dr. Aarti.

## References

* T. H. Cormen, C. E. Leiserson, R. L. Rivest and C. Stein, *Introduction to Algorithms*, MIT Press.
* J. Kleinberg and É. Tardos, *Algorithm Design*, Pearson.
* Python documentation: <https://docs.python.org/3/>
* Streamlit documentation: <https://docs.streamlit.io/>
* NetworkX documentation: <https://networkx.org/documentation/stable/>
