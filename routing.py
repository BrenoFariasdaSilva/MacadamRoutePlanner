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


