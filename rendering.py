"""
================================================================================
Macadam Route Rendering
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Render original-resolution overlays and a standalone walking map.

    Key features include:
        - Consistent account colors, numbered traversal, and direction arrows.
        - Separate JSON statistics and optional diagnostic artifacts.

Usage:
    Call render_outputs after final route validation.

Outputs:
    - overlay.png, clean_map.png, and route.json in a dedicated run directory.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy, NetworkX.

Assumptions & Notes:
    - Route coordinates use normalized pixels until final overlay scaling.
"""

import json  # Save machine-readable route evidence.
from pathlib import Path  # Manage output paths.
from typing import Any  # Annotate output records.
import cv2  # Draw route geometry and labels.
import networkx as nx  # Render observed street edges.
import numpy as np  # Prepare rendering canvases.
from settings import AnalysisError, Image, MapImage  # Share image contracts.


