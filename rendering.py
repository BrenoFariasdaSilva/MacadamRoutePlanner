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


def save_image(path: Path, image: Image) -> None:  # Write Unicode output paths safely.
    """
    Encode a PNG and verify that it can be decoded.

    :param path: Destination PNG path.
    :param image: Rendered image pixels.
    :return: None.
    """

    success, encoded = cv2.imencode(".png", image)  # Encode without platform path limitations.
    if not success:  # Reject a failed encoder result.
        raise AnalysisError(f"Cannot encode output: {path}")  # Identify the failed artifact.
    encoded.tofile(path)  # Write only the generated artifact.
    decoded = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)  # Reopen the actual written file.
    if decoded is None or decoded.shape != image.shape:  # Verify the artifact is readable.
        raise AnalysisError(f"Output verification failed: {path}")  # Report an unusable generated image.


def navigation_points(graph: nx.Graph, walk: list[tuple[int, int]]) -> list[dict[str, Any]]:  # Derive annotations without modifying the optimized walk.
    """
    Select significant corners and reversals in traversal order.

    :param graph: Actual routed street graph.
    :param walk: Complete ordered graph-node walk.
    :return: Navigation events with exact route indices and coordinates.
    """

    points = np.asarray(walk, dtype=np.int32)  # Keep original graph coordinates for every annotation.
    reversals = {index for index in range(1, len(walk) - 1) if walk[index - 1] == walk[index + 1]}  # Preserve actual turnaround stops.
    boundaries = sorted({0, len(walk) - 1, *reversals, *(index for index, point in enumerate(walk) if point == walk[0])})  # Split at reversals and HOME visits before simplifying annotations.
    splits = [start + int(np.argmax(np.linalg.norm(points[start:end + 1] - points[start], axis=1))) for start, end in zip(boundaries, boundaries[1:]) if walk[start] == walk[end]]  # Open closed loops at a routed point so simplification cannot rotate traversal order.
    boundaries = sorted(set(boundaries + splits))  # Preserve every original route boundary.
    vertices = [0]  # Retain ordered route indices instead of only simplified coordinates.
    corners = set(reversals)  # Keep turnarounds even when the outbound and return streets coincide.
    for start, end in zip(boundaries, boundaries[1:]):  # Analyze each uninterrupted traversal separately.
        simplified = cv2.approxPolyDP(points[start:end + 1], NAVIGATION_TOLERANCE, False).reshape(-1, 2)  # Suppress skeleton jitter without changing the rendered path.
        cursor = start  # Resolve repeated coordinates in their actual traversal order.
        for point in simplified[1:]:  # Resolve simplified vertices without inventing route coordinates.
            index = cursor + int(np.flatnonzero(np.all(points[cursor:end + 1] == point, axis=1))[0])  # Recover the exact occurrence in the original route.
            cursor = index + 1  # Keep subsequent corner lookup ordered.
            vertices.append(index)  # Include split boundaries so their heading changes are evaluated too.
    for previous, index, following in zip(vertices, vertices[1:], vertices[2:]):  # Inspect geometric corners across the complete traversal.
        incoming, outgoing = points[index] - points[previous], points[following] - points[index]  # Measure headings across complete straight sections.
        angle = np.degrees(np.arctan2(abs(float(incoming[0] * outgoing[1] - incoming[1] * outgoing[0])), float(np.dot(incoming, outgoing))))  # Distinguish substantial turns from shallow centerline bends.
        if angle >= NAVIGATION_ANGLE:  # Number only meaningful direction changes.
            corners.add(index)  # Retain the route event independently of image layout.
    events = []  # Build one shared annotation sequence for both outputs.
    for index in sorted(corners):  # Preserve the full navigation order including repeated visits.
        if walk[index] == walk[0]:  # Let the existing HOME annotation identify start and return.
            continue  # Avoid redundant numbered HOME badges.
        if index not in reversals and any(abs(index - reverse) <= NAVIGATION_SPUR for reverse in reversals):  # Combine a tiny spur's entrance and exit with its turnaround stop.
            continue  # Avoid three overlapping instructions for one short collectible excursion.
        nearby = range(max(1, index - NAVIGATION_TOLERANCE), min(len(walk) - 1, index + NAVIGATION_TOLERANCE + 1))  # Limit junction refinement to this local route passage.
        junctions = [position for position in nearby if graph.degree[walk[position]] >= 3]  # Prefer an actual street junction over a nearby rounded corner pixel.
        if index not in reversals and junctions:  # Keep collectible turnaround coordinates exact.
            index = min(junctions, key=lambda position: (abs(position - index), walk[position]))  # Use the closest traversed junction node.
        for event in events:  # Unify repeated visits to the same small junction footprint.
            if index not in reversals and np.linalg.norm(points[index] - event["point"]) <= NAVIGATION_TOLERANCE:  # Identify the same geographic corner without moving a turnaround stop.
                matches = [position for position in nearby if walk[position] == event["point"]]  # Require the shared anchor to belong to this route passage too.
                if not matches and event["kind"] == "turn":  # Adjacent junction pixels can differ between street approaches.
                    earlier = range(max(1, event["route_index"] - NAVIGATION_TOLERANCE), min(len(walk) - 1, event["route_index"] + NAVIGATION_TOLERANCE + 1))  # Restrict grouping to the original local passage.
                    shared = set(walk[position] for position in earlier).intersection(walk[position] for position in nearby)  # Require an exact node traversed on both visits.
                    if shared:  # Never merge neighboring streets without shared route geometry.
                        anchor = min(shared, key=lambda point: (graph.degree[point] < 3, np.linalg.norm(np.subtract(point, event["point"])) + np.linalg.norm(points[index] - point), point))  # Prefer the common junction nearest both events.
                        event.update(point=anchor, route_index=min((position for position in earlier if walk[position] == anchor), key=lambda position: abs(position - event["route_index"])))  # Keep the earlier event on its actual route passage.
                        matches = [position for position in nearby if walk[position] == anchor]  # Attach the repeated visit to that same graph coordinate.
                if matches:  # Preserve exact graph association on every visit.
                    index = min(matches, key=lambda position: abs(position - index))  # Reuse the actual common intersection pixel.
                    break  # Stop after finding this junction's existing coordinate.
        events.append({"number": len(events) + 1, "route_index": index, "point": walk[index], "kind": "turnaround" if index in reversals else "turn"})  # Retain auditable navigation semantics.
    return events  # Share identical event numbers and anchors across both maps.


