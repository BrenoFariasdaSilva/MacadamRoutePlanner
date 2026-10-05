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


def match_locations(first: MapImage, second: MapImage, matrix: NDArray[np.float64], graph: nx.Graph, settings: Settings, coverage: Image | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:  # Classify physical collectible opportunities.
    """
    Match nearby account detections without using their visual variant.

    :param first: User account detections.
    :param second: Girlfriend account detections.
    :param matrix: Girlfriend-to-user map homography.
    :param graph: HOME-connected street graph.
    :param settings: Matching and snapping tolerances.
    :param coverage: Optional shared visible map mask in user coordinates.
    :return: Physical location records and rejected candidates.
    """

    transformed = transform_points([item.point for item in second.detections], matrix)  # Align girlfriend locations.
    eligible_a, eligible_b, outside = set(), set(), []  # Filter visibility before matching or snapping near an overlap boundary.
    for kind, points, eligible in (("user", [item.point for item in first.detections], eligible_a), ("girlfriend", transformed, eligible_b)):  # Treat both accounts symmetrically in aligned coordinates.
        for index, point in enumerate(points):  # Preserve original detection indices for ownership records.
            x, y = (int(round(value)) for value in point)  # Sample the same coverage pixels used by the graph.
            if coverage is None or (0 <= x < coverage.shape[1] and 0 <= y < coverage.shape[0] and coverage[y, x]):  # Require actual common coverage rather than merely proximity to its border.
                eligible.add(index)  # Retain a visible account opportunity.
            else:  # Keep outside detections auditable without assigning misleading ownership.
                outside.append({"point": tuple(point), "kind": kind, "reason": "outside common visible map area"})  # Explain why the detected collectible is not routed.
    pairs = sorted((math.dist(first.detections[a].point, transformed[b]), a, b) for a in sorted(eligible_a) for b in sorted(eligible_b) if math.dist(first.detections[a].point, transformed[b]) <= settings.match_tolerance)  # Consider only spatially plausible pairs inside common coverage.
    used_a, used_b = set(), set()  # Enforce one-to-one account correspondence.
    records = []  # Collect classified physical sites.
    for distance, a, b in pairs:  # Prefer the closest geometric correspondence.
        if a in used_a or b in used_b:  # Prevent merging multiple nearby sites.
            continue  # Preserve already assigned physical locations.
        alternatives = [other[0] for other in pairs if (other[1] == a or other[2] == b) and other[1:] != (a, b)]  # Detect ambiguous nearest neighbors.
        if alternatives and min(alternatives) - distance < 4:  # Require a small geometric separation margin.
            raise AnalysisError(f"Ambiguous cross-account collectible match near {first.detections[a].point}")  # Refuse an unreliable shared classification.
        used_a.add(a)  # Reserve the user detection.
        used_b.add(b)  # Reserve the girlfriend detection.
        records.append({"point": first.detections[a].point, "kind": "shared", "variants": [first.detections[a].variant, second.detections[b].variant], "match_error": distance})  # Preserve shared benefit without doubling distance.
    records.extend({"point": item.point, "kind": "user", "variants": [item.variant]} for index, item in enumerate(first.detections) if index in eligible_a and index not in used_a)  # Retain user-only opportunities inside common coverage.
    records.extend({"point": tuple(point), "kind": "girlfriend", "variants": [second.detections[index].variant]} for index, point in enumerate(transformed) if index in eligible_b and index not in used_b)  # Retain girlfriend-only opportunities inside common coverage.
    accepted, rejected = snap_locations(records, graph, settings)  # Preserve existing geometric snapping and ownership colors.
    return accepted, outside + rejected  # Report visibility exclusions separately from failed street associations.


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


def route_length(graph: nx.Graph, path: list[tuple[int, int]]) -> float:  # Measure only real graph transitions.
    """
    Sum the weighted length of an explicit street walk.

    :param graph: Metric street graph.
    :param path: Ordered graph-node walk.
    :return: Route distance in meters.
    """

    return sum(graph[a][b]["weight"] for a, b in zip(path, path[1:]))  # Include repeated walking without duplicated rewards.


def extend_distance(graph: nx.Graph, walk: list[tuple[int, int]], home: tuple[int, int], lower: float, upper: float, target: float) -> list[tuple[int, int]]:  # Prefer useful street cycles over repeated distance padding.
    """
    Add a supported cycle or bounded HOME excursion when below target.

    :param graph: HOME-connected metric graph.
    :param walk: Current closed street walk.
    :param home: Fixed HOME node.
    :param lower: Preferred minimum distance.
    :param upper: Hard maximum distance.
    :param target: Requested metric target.
    :return: A valid closed walk with improved target proximity.
    """

    distance = route_length(graph, walk)  # Measure available distance slack.
    if distance >= lower:  # Avoid unnecessary repeated traversal.
        return walk  # Preserve an already suitable route.
    visited = set(walk)  # Identify cycle attachment points.
    options = []  # Collect legal extensions.
    for cycle in nx.cycle_basis(graph):  # Consider simple detected street loops.
        anchors = visited.intersection(cycle)  # Require a connection to the current route.
        if not anchors:  # Avoid inventing an attachment path.
            continue  # Inspect another cycle.
        anchor = min(anchors)  # Choose a deterministic attachment.
        index = cycle.index(anchor)  # Rotate the cycle to the attachment node.
        loop = cycle[index:] + cycle[:index] + [anchor]  # Form a closed street loop.
        total = distance + route_length(graph, loop)  # Include actual cycle distance.
        if total <= upper:  # Enforce the hard cap.
            options.append((abs(total - target), loop, anchor))  # Rank by target proximity.
    if options:  # Prefer a cycle if it improves the short route.
        _, loop, anchor = min(options)  # Choose the nearest-target street loop.
        index = walk.index(anchor)  # Locate the route attachment.
        walk = walk[:index] + loop + walk[index + 1:]  # Splice the cycle into the closed walk.
        distance = route_length(graph, walk)  # Recompute remaining slack.
    if distance < lower:  # Search a bounded fallback excursion.
        lengths, paths = nx.single_source_dijkstra(graph, home, weight="weight")  # Measure legal HOME excursions.
        candidates = [node for node, length in lengths.items() if 0 < 2 * length <= upper - distance]  # Reserve both outbound and return legs.
        if candidates:  # Choose the closest achievable target distance.
            node = min(candidates, key=lambda item: (abs(distance + 2 * lengths[item] - target), item))  # Prefer target proximity deterministically.
            path = paths[node]  # Recover a supported street excursion.
            walk = walk + path[1:] + list(reversed(path))[1:]  # Return HOME along actual graph edges.
    return walk  # Preserve closed-loop geometry.


