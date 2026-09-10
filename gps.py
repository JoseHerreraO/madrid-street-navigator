# José Herrera Ortiz
"""
gps.py

Command-line navigator that finds and displays a route between two
addresses in Madrid, using the street graph and the search algorithms
implemented in street_directory.py and weighted_graph.py.
"""

import math
import re
from typing import List

import contextily as ctx
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox

import street_directory as sd
import weighted_graph as wg
from street_directory import MAX_SPEEDS


def ask_addresses():
    print("\n----- NEW ROUTE -----")
    origin_text = input("Enter the origin address (leave empty to exit): ").strip()
    destination_text = input("Enter the destination address (leave empty to exit): ").strip()

    if origin_text == "" or destination_text == "":
        return None, None

    return origin_text, destination_text


def coordinates_to_nodes(G: nx.DiGraph, lat_o, long_o, lat_d, long_d):
    """Converts (latitude, longitude) coordinates into the nearest nodes
    of graph G."""
    origin_node = ox.distance.nearest_nodes(G, long_o, lat_o)
    destination_node = ox.distance.nearest_nodes(G, long_d, lat_d)

    print(f"Nearest origin node: {origin_node}")
    print(f"Nearest destination node: {destination_node}")

    return origin_node, destination_node


def select_route_mode() -> int:
    while True:
        print("\nChoose the route type:")
        print("  1) Shortest route (distance).")
        print("  2) Fastest route (time).")
        print("  3) Fastest route with traffic lights.")
        option = input("Option (1/2/3): ").strip()

        if option in {"1", "2", "3"}:
            return int(option)
        print("Invalid option, please try again.")


def distance_weight(G: nx.DiGraph, node1, node2) -> float:
    return float(G[node1][node2]["length"])


def _max_speed(G: nx.DiGraph, node1, node2) -> float:
    """Returns the maximum speed (km/h) of the street between two nodes,
    resolving the OSM value when it's missing or given as a list of
    values (common when a street has several lanes reported with
    different speeds)."""
    max_speed = G[node1][node2].get("maxspeed")

    if isinstance(max_speed, list):
        max_speed = max_speed[0]

    if max_speed is None:
        road_type = G[node1][node2].get("highway", "")
        if isinstance(road_type, list):
            road_type = road_type[0]
        max_speed = MAX_SPEEDS.get(road_type, "50")

    max_speed_num = re.sub(r"\D", "", str(max_speed))
    return float(max_speed_num) if max_speed_num else 50.0


def time_weight(G: nx.DiGraph, node1, node2) -> float:
    meters = distance_weight(G, node1, node2)
    max_speed_num = _max_speed(G, node1, node2)

    if max_speed_num <= 0:
        return 10**6

    speed_m_s = max_speed_num * 1000 / 3600  # km/h -> m/s
    return meters / speed_m_s


def traffic_light_time_weight(G: nx.DiGraph, node1, node2) -> float:
    base_time = time_weight(G, node1, node2)

    # Rough heuristic: treat node2 as an intersection if it has more than
    # two incident edges, and add the expected traffic-light delay
    num_connections = G.out_degree(node2) + G.in_degree(node2)

    if num_connections > 2:
        return base_time + (0.8 * 30)

    return base_time


def choose_weight_function(route_mode: int):
    if route_mode == 1:
        return distance_weight
    if route_mode == 2:
        return time_weight
    return traffic_light_time_weight


def load_data():
    """Loads the already-processed street directory and street graph.
    Returns: (street_directory, G)
    """
    street_directory = sd.load_street_directory()
    street_directory = sd.convert_coordinates(street_directory)

    multigraph = sd.load_graph()
    G = sd.process_graph(multigraph)

    return street_directory, G


def draw_route(G, route):
    """Draws the full graph (in gray) and highlights the computed route
    on top of it. Used as a fallback when the OpenStreetMap basemap can't
    be downloaded (for example, without an internet connection)."""
    pos = {node: (G.nodes[node]["x"], G.nodes[node]["y"]) for node in G.nodes}

    plt.figure(figsize=(10, 10))
    nx.draw(G, pos, node_size=0, width=0.2, arrows=False)

    route_edges = list(zip(route[:-1], route[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=route_edges, width=3)
    nx.draw_networkx_nodes(G, pos, nodelist=[route[0]], node_size=40)  # origin
    nx.draw_networkx_nodes(G, pos, nodelist=[route[-1]], node_size=40)  # destination

    plt.title("Computed route")
    plt.axis("off")
    plt.show()


def draw_route_on_map(G, route):
    """Draws the route over a real OpenStreetMap basemap using contextily.
    If downloading the basemap fails (for example, due to no internet
    connection), automatically falls back to draw_route()."""
    xs = [G.nodes[n]["x"] for n in route]
    ys = [G.nodes[n]["y"] for n in route]

    try:
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_xlim(min(xs) - 0.01, max(xs) + 0.01)
        ax.set_ylim(min(ys) - 0.01, max(ys) + 0.01)
        ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.OpenStreetMap.Mapnik)

        ax.plot(xs, ys, color="red", linewidth=3)
        ax.scatter(xs[0], ys[0], c="green", s=50)
        ax.scatter(xs[-1], ys[-1], c="red", s=50)

        ax.set_axis_off()
        plt.show()
    except Exception:
        print("Could not download the basemap; showing the plain graph instead.")
        draw_route(G, route)


def edge_bearing(n1, n2, G: nx.DiGraph) -> float:
    """Computes the bearing, in degrees, from node n1 to node n2, in the
    range [0, 360)."""
    lat1 = math.radians(G.nodes[n1]["y"])
    lon1 = math.radians(G.nodes[n1]["x"])
    lat2 = math.radians(G.nodes[n2]["y"])
    lon2 = math.radians(G.nodes[n2]["x"])

    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    return (math.degrees(math.atan2(x, y)) + 360) % 360


def turn_direction(dir1: float, dir2: float) -> str:
    turn = dir2 - dir1

    # dir1 and dir2 are both in [0, 360), so the difference is in (-360, 360)
    if turn > 180:
        turn -= 360
    if turn < -180:
        turn += 360

    # Not every street is perfectly straight: below 25 degrees of turn,
    # it's considered as going straight
    if abs(turn) <= 25:
        return "straight"
    if turn > 0:
        return "right"
    return "left"


def build_instructions(node_list: List[int], G: nx.DiGraph):
    segments = list(zip(node_list[:-1], node_list[1:]))

    instructions = []
    previous_segment = None

    for segment in segments:
        meters = G[segment[0]][segment[1]].get("length")
        street_name = G[segment[0]][segment[1]].get("name")

        if isinstance(street_name, list):
            street_name = street_name[0]

        if previous_segment is not None:
            current_bearing = edge_bearing(segment[0], segment[1], G)
            previous_bearing = edge_bearing(previous_segment[0], previous_segment[1], G)
            turn = turn_direction(previous_bearing, current_bearing)
            instructions.append((turn, street_name, meters))
        else:
            instructions.append(("start", street_name, meters))

        previous_segment = segment

    return instructions


def print_instructions(instructions):
    for turn, street_name, meters in instructions:
        if turn == "start":
            print(f"Start on {street_name} for {meters:.0f} meters")
        elif turn == "straight":
            print(f"Continue straight on {street_name} for {meters:.0f} meters")
        elif turn == "left":
            print(f"Turn left onto {street_name} and continue for {meters:.0f} meters")
        elif turn == "right":
            print(f"Turn right onto {street_name} and continue for {meters:.0f} meters")

    print("You have arrived at your destination")


def merge_instructions(instructions):
    """Merges consecutive segments that have the same turn and the same
    street, to avoid redundant instructions."""
    if not instructions:
        return instructions

    merged = []
    prev_turn, prev_street, prev_dist = instructions[0]

    for turn, street_name, dist in instructions[1:]:
        if turn == "straight" and prev_turn == "straight" and street_name == prev_street:
            prev_dist += dist
        else:
            merged.append((prev_turn, prev_street, prev_dist))
            prev_turn, prev_street, prev_dist = turn, street_name, dist

    merged.append((prev_turn, prev_street, prev_dist))
    return merged


def main():
    print("Loading Madrid's street directory and graph (this may take a while on the first run)...")
    try:
        street_directory, G = load_data()
    except sd.ServiceNotAvailableError as exc:
        print(f"Cannot start the navigator: {exc}")
        return

    while True:
        origin_text, destination_text = ask_addresses()
        if origin_text is None or destination_text is None:
            print("Exiting the GPS")
            break

        try:
            lat_origin, long_origin = sd.find_address(origin_text, street_directory)
            lat_dest, long_dest = sd.find_address(destination_text, street_directory)
        except sd.AddressNotFoundError as exc:
            print(exc)
            continue

        origin_node, destination_node = coordinates_to_nodes(
            G, lat_origin, long_origin, lat_dest, long_dest
        )

        route_mode = select_route_mode()
        weight = choose_weight_function(route_mode)
        node_list = wg.shortest_path(G, weight, origin_node, destination_node)

        if not node_list:
            print("No route was found between the given addresses.")
            continue

        instructions = merge_instructions(build_instructions(node_list, G))
        print_instructions(instructions)

        draw_route_on_map(G, node_list)


if __name__ == "__main__":
    main()