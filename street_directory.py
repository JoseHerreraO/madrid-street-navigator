# José Herrera Ortiz
"""
street_directory.py

Loads Madrid's official street directory published by the Ayuntamiento de
Madrid and builds the street graph used for navigation, based on
OpenStreetMap data retrieved through OSMnx.
"""

import osmnx as ox
import networkx as nx
import pandas as pd
from typing import Tuple

STREET_FILE_NAME = "addresses.csv"
PLACE_NAME = "Madrid, Spain"
MAP_FILE_NAME = "madrid.graphml"

MAX_SPEEDS = {
    "living_street": "20",
    "residential": "30",
    "primary_link": "40",
    "unclassified": "40",
    "secondary_link": "40",
    "trunk_link": "40",
    "secondary": "50",
    "tertiary": "50",
    "primary": "50",
    "trunk": "50",
    "tertiary_link": "50",
    "busway": "50",
    "motorway_link": "70",
    "motorway": "100",
}


class ServiceNotAvailableError(Exception):
    """Raised when the street graph cannot be retrieved from OpenStreetMap."""


class AddressNotFoundError(Exception):
    """Raised when a requested address does not exist in the street
    directory."""


def remove_accents(text: str) -> str:
    """Normalizes accented characters, including some mis-encoded ones
    that commonly appear in the raw CSV export and in user input."""
    replacements = {
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "À": "A", "È": "E", "Ì": "I", "Ò": "O", "Ù": "U",
        "Ü": "U", "Ñ": "N",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
        "ü": "u", "ñ": "n",
        "�": "A",  # common artifact in poorly-decoded CSV files
    }
    for original, substitute in replacements.items():
        text = text.replace(original, substitute)
    return text


def load_street_directory() -> pd.DataFrame:
    """Loads Madrid's street directory from "addresses.csv" and normalizes
    it so that addresses can be matched consistently.

    Args: None
    Returns:
        pd.DataFrame: dataframe with the relevant columns (VIA_CLASE,
            VIA_PAR and VIA_NOMBRE upper-cased and stripped of extra
            whitespace).
    Raises:
        FileNotFoundError: if "addresses.csv" does not exist in the
            working directory.
    """
    # Column names below (VIA_CLASE, VIA_PAR, VIA_NOMBRE, NUMERO, LATITUD,
    # LONGITUD) come straight from the official dataset published by the
    # Ayuntamiento de Madrid and are kept as-is.
    columns = ["VIA_CLASE", "VIA_PAR", "VIA_NOMBRE", "NUMERO", "LATITUD", "LONGITUD"]
    df = pd.read_csv(STREET_FILE_NAME, encoding="ISO-8859-1", sep=";", usecols=columns)

    for column in ("VIA_CLASE", "VIA_PAR", "VIA_NOMBRE"):
        df[column] = df[column].astype(str).str.strip().str.upper()

    return df


def dms_to_decimal(coordinate: str) -> float:
    """Converts a coordinate in "degrees°minutes'seconds''orientation"
    format (e.g. "3°42'24.69''W") into a decimal-degrees float, following
    the convention that N and E are positive and S and W are negative.
    """
    coordinate = coordinate.replace("°", " ").replace("'", " ").strip()
    orientation = coordinate[-1].upper()
    coordinate = coordinate[:-1]

    degrees, minutes, seconds = map(float, coordinate.split())
    decimal = degrees + minutes / 60 + seconds / 3600

    if orientation in ("S", "W"):
        decimal = -decimal

    return decimal


def convert_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Converts the LATITUD and LONGITUD columns from text strings to
    decimal-degrees floats."""
    df["LATITUD"] = df["LATITUD"].apply(dms_to_decimal)
    df["LONGITUD"] = df["LONGITUD"].apply(dms_to_decimal)
    return df


def find_address(address: str, street_directory: pd.DataFrame) -> Tuple[float, float]:
    """Looks up an address, given in "Street, number" format, in Madrid's
    street directory and returns its geographic location.

    Args:
        address (str): full address, in "Street Name, N" format.
        street_directory (pd.DataFrame): dataframe returned by
            load_street_directory().
    Returns:
        Tuple[float, float]: (latitude, longitude) pair, in degrees, of
            the requested address.
    Raises:
        AddressNotFoundError: if the address doesn't match the expected
            format or doesn't exist in the street directory.
    Example:
        find_address("Calle de Alberto Aguilera, 23", data)
            -> (40.42998055555555, -3.7112583333333333)
    """
    text = remove_accents(address.strip().upper())

    if "," not in text:
        raise AddressNotFoundError(
            f"'{address}' does not match the expected format 'Street Name, N'."
        )

    street_part, number_text = text.split(",", 1)
    number_text = number_text.strip()

    tokens = street_part.split()
    if len(tokens) < 3:
        raise AddressNotFoundError(
            f"'{address}' does not match the expected format 'Street Name, N'."
        )

    try:
        number = int(number_text)
    except ValueError as exc:
        raise AddressNotFoundError(
            f"The house number '{number_text}' is not valid."
        ) from exc

    street_class = tokens[0]
    street_particle = tokens[1]
    street_name = " ".join(tokens[2:])

    conditions = (
        (street_directory["VIA_CLASE"] == street_class)
        & (street_directory["VIA_PAR"] == street_particle)
        & (street_directory["VIA_NOMBRE"] == street_name)
        & (street_directory["NUMERO"] == number)
    )

    filtered_df = street_directory.loc[conditions]

    if filtered_df.empty:
        raise AddressNotFoundError(f"The address '{address}' does not exist in the street directory.")

    row = filtered_df.iloc[0]
    return float(row["LATITUD"]), float(row["LONGITUD"])


def load_graph() -> nx.MultiDiGraph:
    """Retrieves Madrid's street graph. If a "madrid.graphml" file already
    exists in the working directory it is reused; otherwise it is
    downloaded from OpenStreetMap and saved for future use.

    Args: None
    Returns:
        nx.MultiDiGraph: multidigraph of Madrid's streets.
    Raises:
        ServiceNotAvailableError: if the graph cannot be retrieved from
            OpenStreetMap.
    """
    try:
        G = ox.load_graphml(MAP_FILE_NAME)
    except FileNotFoundError:
        try:
            G = ox.graph_from_place(PLACE_NAME, network_type="drive")
            ox.save_graphml(G, MAP_FILE_NAME)
        except Exception as exc:
            raise ServiceNotAvailableError(
                "Could not retrieve the street graph from OpenStreetMap."
            ) from exc

    return G


def process_graph(multidigraph: nx.MultiDiGraph) -> nx.DiGraph:
    """Converts the OSMnx multidigraph into a directed graph with no
    self-loops.

    Args:
        multidigraph: multidigraph of Madrid's streets obtained from
            OpenStreetMap.
    Returns:
        nx.DiGraph: directed, loop-free graph derived from the
            multidigraph.
    """
    G = ox.convert.to_digraph(multidigraph)

    self_loops = list(nx.selfloop_edges(G))
    G.remove_edges_from(self_loops)

    return G
