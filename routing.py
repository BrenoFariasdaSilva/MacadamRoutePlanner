"""
================================================================================
Macadam Two-Account Route Optimization
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Match physical collectible locations and search for bounded HOME loops.

    Key features include:
        - Artwork-independent spatial matching with graph-context validation.
        - Deterministic beam search using actual weighted shortest paths.

Usage:
    Call match_locations and optimize_route from the main pipeline.

Outputs:
    - Classified collectible locations and a validated closed street walk.

Dependencies:
    - Python >= 3.13, NumPy, NetworkX.

Assumptions & Notes:
    - Bounded search is heuristic and never claims global optimality.
"""

import heapq  # Search distance-ordered collectible states.
import math  # Convert step budgets and compare distances.
from typing import Any  # Describe JSON-compatible route records.
import networkx as nx  # Compute actual street shortest paths.
import numpy as np  # Transform account marker positions.
from numpy.typing import NDArray  # Annotate homographies.
from registration import transform_points  # Share projective geometry.
from settings import AnalysisError, Image, MapImage, Settings  # Reuse account records.
from streets import snap_point  # Associate collectibles with streets.


def snap_locations(records: list[dict[str, Any]], graph: nx.Graph, settings: Settings) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:  # Share graph safety across both account modes.
    """Snap detected physical sites to HOME-connected streets and retain rejection evidence."""

    accepted, rejected = [], []  # Separate routable sites from unsupported ones.
    for record in records:  # Require physical street context.
        try:  # Snap only to the HOME-connected topology.
            node, distance = snap_point(graph, record["point"], settings.snap_tolerance)  # Enforce geometric tolerance.
        except AnalysisError as error:  # Preserve explicit off-graph rejection evidence.
            rejected.append({**record, "reason": str(error)})  # Report unsupported physical locations.
            continue  # Exclude unreachable sites from the optimizer.
        record.update(node=node, snap_pixels=distance, reward=2 if record["kind"] == "shared" else 1)  # Count opportunities per account.
        accepted.append(record)  # Retain a routable collectible site.
    return sorted(accepted, key=lambda item: (item["node"], item["kind"])), rejected  # Ensure deterministic candidate ordering.


