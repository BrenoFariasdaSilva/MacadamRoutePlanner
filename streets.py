"""
================================================================================
Macadam Street Graph
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Build a walkable graph from observed and locally occluded street paths.

    Key features include:
        - Conservative collinear gap repair restricted to detected occluders.
        - Skeleton graph with metric calibration and bounded marker snapping.

Usage:
    Call build_graph after map registration.

Outputs:
    - Street graph, road mask, skeleton, and calibration evidence.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy, NetworkX.

Assumptions & Notes:
    - Approximate block calibration is reported explicitly.
"""

import math  # Calculate pixel-path lengths.
from typing import Any  # Describe graph diagnostics.
import cv2  # Segment and reconnect street evidence.
import networkx as nx  # Represent weighted street topology.
import numpy as np  # Perform vectorized skeleton thinning.
from settings import AnalysisError, Image, MapImage, Point, Settings  # Share analysis configuration.


