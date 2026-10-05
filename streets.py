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


def repair_roads(scene: MapImage) -> Image:  # Bridge only short supported occlusions.
    """
    Reconnect collinear road fragments across known map artwork.

    :param scene: Prepared screenshot with marker detections.
    :return: Cleaned street mask with conservative gap repairs.
    """

    roads = cv2.morphologyEx(scene.roads, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # Remove antialiasing pinholes.
    roads = cv2.morphologyEx(roads, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))  # Remove thin glyph halos and decorative outlines.
    dark = (cv2.cvtColor(scene.image, cv2.COLOR_BGR2GRAY) < 170).astype(np.uint8) * 255  # Locate label and symbol occluders.
    occlusion = cv2.dilate(dark, np.ones((7, 7), np.uint8))  # Include glyph margins.
    for x, y, w, h in [scene.home_box] + [item.box for item in scene.detections]:  # Include entire known marker footprints.
        cv2.rectangle(occlusion, (x - 4, y - 4), (x + w + 4, y + h + 4), 255, -1)  # Permit narrowly supported reconstruction under artwork.
        cv2.rectangle(roads, (x - 4, y - 4), (x + w + 4, y + h + 4), 0, -1)  # Prevent marker borders from becoming walkable streets.
    lines = cv2.HoughLinesP(roads, 1, np.pi / 720, threshold=65, minLineLength=100, maxLineGap=150)  # Propose straight street continuations.
    support = cv2.dilate(roads, np.ones((5, 5), np.uint8))  # Allow two pixels of line-fitting error at road boundaries.
    if lines is not None:  # Inspect supported line candidates.
        for x1, y1, x2, y2 in lines[:, 0]:  # Validate every proposed continuation.
            length = int(np.hypot(x2 - x1, y2 - y1)) + 1  # Sample at roughly pixel spacing.
            xs = np.linspace(x1, x2, length).astype(int)  # Sample horizontal coordinates.
            ys = np.linspace(y1, y2, length).astype(int)  # Sample vertical coordinates.
            observed = roads[ys, xs] > 0  # Identify directly visible street support.
            supported = support[ys, xs] > 0  # Measure evidence within the narrow fitting tolerance.
            allowed = supported | (occlusion[ys, xs] > 0)  # Reject reconstruction through colored blocks.
            if np.mean(observed) >= 0.5 and np.mean(supported) >= 0.65 and np.all(allowed) and np.all(scene.usable[ys, xs] > 0):  # Require substantial street evidence and no interface crossing.
                cv2.line(roads, (int(x1), int(y1)), (int(x2), int(y2)), 255, 3)  # Restore the supported centerline corridor.
    return cv2.bitwise_and(roads, scene.usable)  # Preserve strict interface exclusion.


