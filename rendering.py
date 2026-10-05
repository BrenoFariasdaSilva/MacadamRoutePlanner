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


COLORS = {"user": (235, 105, 25), "girlfriend": (165, 60, 235), "shared": (65, 165, 35)}  # Define blue, pink, and green in OpenCV BGR order.
ROUTE_COLOR = (195, 65, 95)  # Keep route lines distinct from collectible categories.
LABEL_FONT_SCALE = 0.72  # Balance readable digits with compact intersection badges.
LABEL_MIN_FONT_SCALE = 0.6  # Preserve legibility on smaller output images.
LABEL_PADDING = 4  # Separate digits from the badge border.
LABEL_MAX_OFFSET = 18  # Limit unavoidable local collision shifts to roughly one compact badge radius.
NAVIGATION_TOLERANCE = 8  # Ignore small skeleton deviations in normalized pixels.
NAVIGATION_ANGLE = 35  # Retain meaningful heading changes rather than pixel stair steps.
NAVIGATION_SPUR = 20  # Treat tiny out-and-back collectible spurs as one navigation stop.
LABEL_DARK = (30, 30, 30)  # Contrast badges against both map styles.
LABEL_LIGHT = (255, 255, 255)  # Contrast digits and borders against dark details.


