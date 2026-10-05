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


def thin_mask(mask: Image) -> Image:  # Avoid an extra image-processing dependency.
    """
    Thin a binary road mask using topology-preserving Zhang-Suen iterations.

    :param mask: Binary street corridor mask.
    :return: One-pixel street skeleton.
    """

    pixels = np.pad(mask > 0, 1).astype(np.uint8)  # Protect image boundaries during neighborhood operations.
    changed = True  # Iterate until skeleton topology stabilizes.
    while changed:  # Remove boundary pixels without breaking connectivity.
        changed = False  # Track deletions in both thinning phases.
        for phase in (0, 1):  # Apply alternating directional constraints.
            center = pixels[1:-1, 1:-1]  # Reference current foreground pixels.
            neighbors = [pixels[:-2, 1:-1], pixels[:-2, 2:], pixels[1:-1, 2:], pixels[2:, 2:], pixels[2:, 1:-1], pixels[2:, :-2], pixels[1:-1, :-2], pixels[:-2, :-2]]  # Read clockwise neighbors.
            count = sum(neighbors)  # Count occupied neighbors.
            transitions = sum((neighbors[index] == 0) & (neighbors[(index + 1) % 8] == 1) for index in range(8))  # Count contour transitions.
            north, east, south, west = neighbors[0], neighbors[2], neighbors[4], neighbors[6]  # Name orthogonal neighbors.
            guard = ((north * east * south == 0) & (east * south * west == 0)) if phase == 0 else ((north * east * west == 0) & (north * south * west == 0))  # Preserve directional connectivity.
            remove = (center == 1) & (count >= 2) & (count <= 6) & (transitions == 1) & guard  # Identify safely removable boundary pixels.
            if np.any(remove):  # Continue only when pixels were removed.
                center[remove] = 0  # Thin the current boundary.
                changed = True  # Request another stabilization pass.
    return pixels[1:-1, 1:-1] * 255  # Return unpadded binary skeleton.


def corridor_lengths(graph: nx.Graph) -> list[float]:  # Measure topology-defined street sections.
    """
    Measure nonbranching corridors between graph junctions.

    :param graph: Pixel street graph.
    :return: Junction-to-junction pixel lengths.
    """

    lengths = []  # Collect unique corridor measurements.
    visited = set()  # Avoid measuring undirected corridors twice.
    for start in graph:  # Begin only at structural endpoints and intersections.
        if graph.degree[start] == 2:  # Ignore intermediate pixels.
            continue  # Move to a structural node.
        for neighbor in graph[start]:  # Trace each incident street corridor.
            edge = frozenset((start, neighbor))  # Use orientation-independent edge identity.
            if edge in visited:  # Avoid duplicated measurements.
                continue  # Continue with another corridor.
            previous, current = start, neighbor  # Initialize corridor traversal.
            length = graph[start][neighbor]["pixels"]  # Include the initial street step.
            visited.add(edge)  # Record the measured edge.
            while graph.degree[current] == 2:  # Follow nonbranching street geometry.
                following = next(node for node in graph[current] if node != previous)  # Advance without reversing.
                visited.add(frozenset((current, following)))  # Mark the next corridor edge.
                length += graph[current][following]["pixels"]  # Accumulate actual centerline length.
                previous, current = current, following  # Advance the traversal state.
            if graph.degree[start] >= 3 and graph.degree[current] >= 3:  # Calibrate only intersection-to-intersection sections.
                lengths.append(length)  # Retain a genuine block candidate.
    return lengths  # Return measured block geometry.


