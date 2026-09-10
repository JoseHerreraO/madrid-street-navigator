# José Herrera Ortiz
"""
weighted_graph.py

Library for the analysis of weighted graphs: shortest paths (Dijkstra) and
minimum spanning trees (Prim and Kruskal), implemented from scratch on top
of NetworkX graph objects (built-in NetworkX path/tree algorithms are
intentionally not used).

Weight functions
-----------------
Every function below receives a "weight function" as a parameter. A weight
function takes a graph (or digraph) and two vertices, and returns the
weight (a float) of the edge that connects them. For example, if the edges
of the graph store their weight in a field called "value", a valid weight
function would be:

    def my_weight(G: nx.Graph, u: object, v: object) -> float:
        return G[u][v]["value"]

and to run Dijkstra with it:

    path = shortest_path(G, my_weight, origin, destination)
"""

from typing import List, Tuple, Dict, Callable, Union
import networkx as nx
import sys
import heapq     # Priority queue used by Dijkstra and Prim
import itertools  # Tie-breaking counter for the priority queue

INFINITY = sys.float_info.max  # "Infinite" distance between two vertices


def dijkstra(
    G: Union[nx.Graph, nx.DiGraph],
    weight: Union[
        Callable[[nx.Graph, object, object], float],
        Callable[[nx.DiGraph, object, object], float],
    ],
    origin: object,
) -> Dict[object, object]:
    """Computes a shortest-path tree for the weighted graph starting from
    "origin", using Dijkstra's algorithm. Only the tree for the connected
    component containing "origin" is computed.

    Args:
        G: NetworkX graph or digraph.
        weight: function that takes a graph and two vertices and returns
            the weight of the edge connecting them.
        origin (object): source vertex.
    Returns:
        Dict[object, object]: for every vertex reachable from "origin",
            the vertex that is its parent in the shortest-path tree.
    Raises:
        TypeError: if origin is not in the graph or is not hashable.
    Example:
        If dijkstra(G, weight, 1) == {2: 1, 3: 2, 4: 1}, then 1 is the
        parent of 2 and 4, and 2 is the parent of 3. In particular, a
        shortest path from 1 to 3 would be 1 -> 2 -> 3.
    """
    if origin not in G:
        raise TypeError("The origin is not in the graph or is not hashable.")

    parent = {}
    visited = {}
    d = {}

    for v in G.nodes():
        parent[v] = None
        visited[v] = False
        d[v] = INFINITY

    d[origin] = 0

    # The counter is used purely as a tie-breaker: if two entries have the
    # same distance, heapq would otherwise try to compare the vertices
    # themselves, which fails whenever they aren't mutually orderable
    # (e.g. mixing integers and strings).
    counter = itertools.count()

    Q = []
    heapq.heappush(Q, (0, next(counter), origin))

    while Q:
        dist_v, _, v = heapq.heappop(Q)

        if visited[v]:
            continue

        visited[v] = True

        for x in G.neighbors(v):
            w_vx = weight(G, v, x)
            if d[x] > d[v] + w_vx:
                d[x] = d[v] + w_vx
                parent[x] = v
                heapq.heappush(Q, (d[x], next(counter), x))

    return parent


def shortest_path(
    G: Union[nx.Graph, nx.DiGraph],
    weight: Union[
        Callable[[nx.Graph, object, object], float],
        Callable[[nx.DiGraph, object, object], float],
    ],
    origin: object,
    destination: object,
) -> List[object]:
    """Computes the shortest path from "origin" to "destination" using
    Dijkstra's algorithm.

    Args:
        G: graph or digraph.
        weight: function that takes a graph and two vertices and returns
            the weight of the edge connecting them.
        origin (object): source vertex.
        destination (object): target vertex.
    Returns:
        List[object]: vertices the shortest path goes through, in order
            (the first element is origin and the last is destination).
            Returns an empty list if no path exists.
    Raises:
        TypeError: if origin or destination are not valid.
    Example:
        If shortest_path(G, weight, 1, 4) == [1, 5, 2, 4], the shortest
        path in G between 1 and 4 is 1 -> 5 -> 2 -> 4.
    """
    if origin not in G or destination not in G:
        raise TypeError("Invalid origin or destination.")

    parent = dijkstra(G, weight, origin)

    path = []
    current = destination

    if current != origin and parent[current] is None:
        return []  # No path exists

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    return path


def prim(
    G: nx.Graph, weight: Callable[[nx.Graph, object, object], float]
) -> Dict[object, object]:
    """Computes a minimum spanning tree for the weighted graph using
    Prim's algorithm.

    Args:
        G: graph.
        weight: function that takes a graph and two vertices and returns
            the weight of the edge connecting them.
    Returns:
        Dict[object, object]: for every vertex in the graph, the vertex
            that is its parent in the minimum spanning tree.
    Example:
        If prim(G, weight) == {1: None, 2: 1, 3: 2, 4: 1}, then 1 is a
        root (has no parent), 1 is the parent of 2 and 4, and 2 is the
        parent of 3.
    """
    parent = {}
    min_cost = {}
    Q = []

    for v in G.nodes():
        parent[v] = None
        min_cost[v] = INFINITY

    counter = itertools.count()

    start = next(iter(G.nodes()))
    min_cost[start] = 0
    heapq.heappush(Q, (0, next(counter), start))

    visited = {v: False for v in G.nodes()}

    while Q:
        cost_v, _, v = heapq.heappop(Q)

        if visited[v]:
            continue

        visited[v] = True

        for x in G.neighbors(v):
            if not visited[x]:
                w_vx = weight(G, v, x)
                if w_vx < min_cost[x]:
                    min_cost[x] = w_vx
                    parent[x] = v
                    heapq.heappush(Q, (w_vx, next(counter), x))

    return parent


def kruskal(
    G: nx.Graph, weight: Callable[[nx.Graph, object, object], float]
) -> List[Tuple[object, object]]:
    """Computes a minimum spanning tree for the graph using Kruskal's
    algorithm, backed by a union-find structure to detect cycles
    efficiently.

    Args:
        G: graph.
        weight: function that takes a graph and two vertices and returns
            the weight of the edge connecting them.
    Returns:
        List[Tuple[object, object]]: list [(s1, t1), (s2, t2), ...] with
            the pairs of vertices that form the edges of the minimum
            spanning tree.
    Example:
        In the example above where prim(G, weight) == {1: None, 2: 1,
        3: 2, 4: 1}, we could have kruskal(G, weight) == [(1, 2), (1, 4),
        (3, 2)].
    """
    uf_parent = {v: v for v in G.nodes()}
    uf_rank = {v: 0 for v in G.nodes()}

    def find(v: object) -> object:
        root = v
        while uf_parent[root] != root:
            root = uf_parent[root]
        # Path compression
        while uf_parent[v] != root:
            uf_parent[v], v = root, uf_parent[v]
        return root

    def union(u: object, v: object) -> bool:
        root_u, root_v = find(u), find(v)
        if root_u == root_v:
            return False  # u and v are already connected -> would form a cycle

        if uf_rank[root_u] < uf_rank[root_v]:
            root_u, root_v = root_v, root_u
        uf_parent[root_v] = root_u
        if uf_rank[root_u] == uf_rank[root_v]:
            uf_rank[root_u] += 1
        return True

    sorted_edges = sorted(G.edges(), key=lambda edge: weight(G, edge[0], edge[1]))

    tree = []
    for u, v in sorted_edges:
        if union(u, v):
            tree.append((u, v))

    return tree
