# José Herrera Ortiz
"""
test_weighted_graph.py

Basic sanity checks for weighted_graph.py.

The "vertices" and "edges" lists describe a graph (directed or not). The
script builds that graph with random edge weights, and then runs
Dijkstra, shortest-path search, Prim and Kruskal on it.
"""
import random
from typing import Union

import networkx as nx

import weighted_graph

MIN_EDGE_WEIGHT = 1
MAX_EDGE_WEIGHT = 12


############ Example weight functions ############

def constant_weight(G: Union[nx.Graph, nx.DiGraph], origin: object, destination: object):
    """Returns a constant weight for every edge."""
    return 1


def random_weight(G: Union[nx.Graph, nx.DiGraph], origin: object, destination: object):
    """Retrieves the random weight stored on the graph."""
    return G[origin][destination]["weight"]


# Lists of vertices and edges for the graph
directed = False
vertices = [1, 2, 3, "a", 5, 6]
edges = [(1, 2), (1, 3), (1, "a"), (1, 5), (2, "a"), (3, "a"), (3, 5), (5, 6)]

# Graph creation
G = nx.DiGraph() if directed else nx.Graph()
G.add_nodes_from(vertices)

for e in edges:
    # Store a random weight on each edge
    G.add_edge(e[0], e[1], weight=random.randrange(MIN_EDGE_WEIGHT, MAX_EDGE_WEIGHT))
    print(e[0], e[1], ":", G[e[0]][e[1]])


# Dijkstra and shortest path with constant weight
tree = weighted_graph.dijkstra(G, constant_weight, 1)
print(tree)

path = weighted_graph.shortest_path(G, constant_weight, 1, 5)
print(path)

# Dijkstra and shortest path with random weight
tree_rng = weighted_graph.dijkstra(G, random_weight, 1)
print(tree_rng)

path_rng = weighted_graph.shortest_path(G, random_weight, 1, 5)
print(path_rng)


if not directed:
    # Minimum spanning tree
    mst = weighted_graph.kruskal(G, constant_weight)
    print(mst)

    mst2 = weighted_graph.prim(G, constant_weight)
    print(mst2)

    mst_rng = weighted_graph.kruskal(G, random_weight)
    print(mst_rng)

    mst2_rng = weighted_graph.prim(G, random_weight)
    print(mst2_rng)
