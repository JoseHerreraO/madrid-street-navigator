# Madrid Street Navigator

A command-line GPS-style navigator for the city of Madrid. It builds a graph
of the city's street network from OpenStreetMap data and computes routes
between two addresses using graph algorithms implemented from scratch —
Dijkstra, Prim and Kruskal are not taken from NetworkX, only the graph data
structure is.

Given an origin and a destination address, the navigator finds the
shortest, fastest, or traffic-light-aware fastest route, and outputs
turn-by-turn instructions along with a plot of the route over a real map of
Madrid.

## Features

- **Custom graph algorithms**: Dijkstra (shortest path tree), Prim and
  Kruskal (minimum spanning tree), implemented with a binary heap /
  union-find from first principles.
- **Real street data**: the road network is downloaded from OpenStreetMap
  via [OSMnx](https://osmnx.readthedocs.io/) and cached locally after the
  first run.
- **Address lookup**: addresses are matched against Madrid's official
  street directory (published by the Ayuntamiento de Madrid).
- **Three routing modes**:
  - Shortest route by distance.
  - Fastest route, assuming each street is driven at its maximum legal
    speed.
  - Fastest route accounting for traffic lights, modeled as a probability
    of stopping for 30 seconds at each intersection.
- **Turn-by-turn instructions**, with consecutive segments on the same
  street merged into a single instruction.
- **Route visualization** over an OpenStreetMap basemap, with an automatic
  fallback to a plain NetworkX plot if the basemap can't be downloaded.

## Project structure

```
.
├── weighted_graph.py     # Graph algorithms: dijkstra, shortest_path, prim, kruskal
├── street_directory.py   # Loads the street directory and builds the street graph
├── gps.py                # CLI navigator: routing, instructions and visualization
├── test_weighted_graph.py# Sanity checks for weighted_graph.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Getting started

### Prerequisites

- Python 3.10+
- The address dataset for Madrid (see below)

### Installation

```bash
git clone https://github.com/JoseHerreraO/madrid-street-navigator.git
cd madrid-street-navigator
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Getting the address dataset

The street directory is not included in this repository, since it's a
large, publicly available dataset. To get it:

1. Go to the [Madrid open data portal](https://datos.madrid.es) and search
   for "Callejero Vigente. Direcciones", or open it directly through the
   [Ayuntamiento de Madrid data catalog](https://datos.madrid.es/portal/site/egob/menuitem.c05c1f754a33a9fbe4b2e4b284f1a5a0/?vgnextoid=e3f0f0e5e2fb4410VgnVCM2000000c205a0aRCRD).
2. Download the CSV version of "Relación de direcciones vigentes, con
   coordenadas".
3. Rename it to `addresses.csv` and place it in the project's root
   directory.

The street graph itself doesn't need to be downloaded manually: the first
time `gps.py` runs, it fetches Madrid's road network from OpenStreetMap and
caches it locally as `madrid.graphml`, so subsequent runs start instantly.

### Usage

```bash
python gps.py
```

The program will:

1. Load the address directory and the street graph (this can take a
   while on the very first run, while the OSM data is downloaded).
2. Ask for an origin and a destination address, in the format:
   ```
   Calle de Alberto Aguilera, 23
   ```
   (street names come from the underlying Madrid dataset, so they're in
   Spanish, matching how they appear officially.)
3. Ask which type of route to compute (shortest, fastest, or fastest with
   traffic lights).
4. Print turn-by-turn instructions and plot the resulting route.
5. Repeat until an empty address is entered.

### Running the tests

`test_weighted_graph.py` builds a small graph with random edge weights and
exercises every function in `weighted_graph.py`:

```bash
python test_weighted_graph.py
```

## Tech stack

- [NetworkX](https://networkx.org/) — graph data structures
- [OSMnx](https://osmnx.readthedocs.io/) — OpenStreetMap street network
  retrieval
- [pandas](https://pandas.pydata.org/) — address dataset processing
- [Matplotlib](https://matplotlib.org/) / [contextily](https://contextily.readthedocs.io/) —
  route visualization

## Background

This project was originally developed as coursework for the Discrete
Mathematics course at Universidad Pontificia Comillas (ICAI), which
required implementing Dijkstra, Prim and Kruskal from the pseudocode
covered in class rather than relying on NetworkX's built-in
implementations. It has since been cleaned up and hardened for general
use.

## Possible improvements

- Fuzzy/approximate address matching, to tolerate typos or partial street
  names.
- A small web UI instead of a CLI.
- Caching resolved addresses to speed up repeated lookups.

## Authors

Developed by [José Herrera Ortiz](https://github.com/JoseHerreraO) and
Gonzalo Crespo Comín.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE)
for details.
