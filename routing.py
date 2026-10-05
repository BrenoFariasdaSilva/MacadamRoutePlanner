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


def optimize_route(graph: nx.Graph, home: tuple[int, int], locations: list[dict[str, Any]], steps: int, minimum: int, settings: Settings) -> dict[str, Any]:  # Search for a bounded closed street walk.
    """
    Optimize collectible reward while preserving return-HOME feasibility.

    :param graph: HOME-connected metric graph.
    :param home: Snapped start and finish node.
    :param locations: Classified physical collectible sites.
    :param steps: Requested step target.
    :param minimum: Required combined account opportunities.
    :param settings: Deterministic beam width.
    :return: Explicit route, statistics, and unmet requirements.
    """

    target = math.ceil(steps / 1.3)  # Apply the requested integer-ceiling conversion.
    lower, upper = target * 0.95, target * 1.05  # Preserve the requested tolerance interval.
    terminals = list(dict.fromkeys([home] + [item["node"] for item in locations]))  # Deduplicate graph destinations.
    distances, paths = {}, {}  # Cache weighted metric closure.
    for node in terminals:  # Solve each source once.
        distances[node], paths[node] = nx.single_source_dijkstra(graph, node, weight="weight")  # Use real street distances.
    masks = {}  # Cache incidental pickups along shortest-path legs.
    for source in terminals:  # Inspect every terminal-to-terminal leg.
        for destination in terminals:  # Include pickups passed en route.
            visited = set(paths[source][destination])  # Index street nodes on this leg.
            masks[source, destination] = sum(1 << index for index, item in enumerate(locations) if item["node"] in visited)  # Count each physical site once.
    rewards = {}  # Cache combined account opportunity counts.
    beam = [(0.0, (home,), masks[home, home])]  # Initialize the fixed starting point.
    completed = []  # Retain best valid closed alternatives.
    for _ in range(len(terminals)):  # Bound expansions by newly visited collectible terminals.
        next_states = {}  # Deduplicate equivalent partial states.
        for cost, stops, mask in beam:  # Extend only HOME-returnable partial routes.
            last = stops[-1]  # Read the current street terminal.
            closed_mask = mask | masks[last, home]  # Include return-leg opportunities.
            total = cost + distances[last][home]  # Reserve the mandatory return length.
            if total <= upper and total > 0:  # Retain valid nonempty closed walks.
                reward = rewards.setdefault(closed_mask, sum(item["reward"] for index, item in enumerate(locations) if closed_mask & (1 << index)))  # Count account opportunities independently.
                completed.append((reward, total >= lower, -abs(total - target), stops + (home,), closed_mask))  # Prefer coverage and target proximity.
            for node in terminals[1:]:  # Consider unvisited reward destinations.
                if node in stops:  # Avoid redundant terminal ordering.
                    continue  # Keep repetitions only where shortest paths require them.
                new_mask = mask | masks[last, node]  # Include incidental collectible visits.
                if new_mask == mask:  # Do not add rewardless terminal visits during search.
                    continue  # Leave target-distance extension to the final phase.
                new_cost = cost + distances[last][node]  # Measure the additional walking leg.
                if new_cost + distances[node][home] > upper:  # Reserve an admissible return to HOME.
                    continue  # Reject over-budget partial routes immediately.
                key = (node, new_mask)  # Identify equivalent reward and position states.
                if key not in next_states or new_cost < next_states[key][0]:  # Retain the shorter equivalent partial route.
                    next_states[key] = (new_cost, stops + (node,), new_mask)  # Store the improved partial state.
        if not next_states:  # Stop when no additional reward fits.
            break  # Finish the bounded search.
        beam = sorted(next_states.values(), key=lambda state: (-sum(item["reward"] for index, item in enumerate(locations) if state[2] & (1 << index)), state[0], state[1]))[:settings.beam_width]  # Bound deterministic reward-first search.
        completed = sorted(completed, reverse=True)[:settings.beam_width]  # Bound retained closed alternatives.
    if completed:  # Select the strongest discovered closed route.
        _, _, _, stops, _ = max(completed)  # Prioritize reward, interval membership, and target closeness.
        walk = [home]  # Expand the metric closure into actual graph steps.
        for a, b in zip(stops, stops[1:]):  # Expand each selected terminal leg.
            walk.extend(paths[a][b][1:])  # Preserve the full street-following geometry.
    else:  # Permit a distance-only walk when no collectible terminal fits.
        walk = [home]  # Start a valid alternative search from HOME.
    walk = extend_distance(graph, walk, home, lower, upper, target)  # Prefer a near-target alternative without exceeding the cap.
    distance = route_length(graph, walk)  # Independently recompute final walking distance.
    if len(walk) < 2 or walk[0] != home or walk[-1] != home or distance > upper + 1e-7:  # Enforce final invariants.
        raise AnalysisError(f"No nonempty HOME-returning route found within {upper:.2f} m")  # Report a failed bounded search.
    visited = set(walk)  # Deduplicate physical visits.
    selected = [index for index, item in enumerate(locations) if item["node"] in visited]  # Include incidental final-route pickups.
    counts = {kind: sum(locations[index]["kind"] == kind for index in selected) for kind in ("user", "girlfriend", "shared")}  # Count category-specific physical sites.
    opportunities = counts["user"] + counts["girlfriend"] + 2 * counts["shared"]  # Count shared benefit for both people.
    unmet = []  # Explicitly identify every unmet request.
    if distance < lower:  # Distinguish a valid shorter alternative from full satisfaction.
        unmet.append(f"Distance below preferred lower bound {lower:.2f} m")  # Report the distance shortfall.
    if opportunities < minimum:  # Preserve the requested collectible minimum.
        unmet.append(f"Only {opportunities} account opportunities; requested {minimum}")  # Report the reward shortfall.
    unique_edges = {frozenset((a, b)) for a, b in zip(walk, walk[1:])}  # Measure unavoidable and avoidable repeated walking.
    unique_length = sum(graph[a][b]["weight"] for edge in unique_edges for a, b in [tuple(edge)])  # Count each street edge once.
    return {"walk": walk, "selected": selected, "distance_m": distance, "estimated_steps": math.ceil(distance * 1.3), "target_m": target, "lower_m": lower, "upper_m": upper, "user_only": counts["user"], "girlfriend_only": counts["girlfriend"], "shared": counts["shared"], "user_opportunities": counts["user"] + counts["shared"], "girlfriend_opportunities": counts["girlfriend"] + counts["shared"], "distinct_locations": len(selected), "route_nodes": len(visited), "intersections": sum(graph.degree[node] >= 3 for node in visited), "repeated_distance_m": distance - unique_length, "unmet": unmet, "optimizer": "bounded deterministic beam search; global optimality not guaranteed"}  # Return complete auditable statistics.


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


def optimize_single_route(graph: nx.Graph, home: tuple[int, int], locations: list[dict[str, Any]], coins: int | None, steps: int | None, settings: Settings) -> dict[str, Any]:  # Separate single-account objective priorities explicitly.
    """
    Find minimum-distance pickup loops or maximum pickups under a hard cap.

    Exact distance-state search proves pickup feasibility on the extracted graph.
    Target-distance refinement reuses bounded street cycles and HOME excursions.
    Its secondary proximity/repetition preference does not claim global optimality.
    """

    target = math.ceil(steps / 1.3) if steps is not None else None  # Never invent a coins-only budget.
    lower, upper = (target * 0.95, target * 1.05) if target is not None else (None, None)  # Preserve existing step conversion.
    terminals = list(dict.fromkeys([home] + [item["node"] for item in locations]))  # Share the existing metric-closure representation.
    distances, paths = {}, {}  # Cache real weighted graph paths.
    for node in terminals:  # Solve each distinct collectible source once.
        distances[node], paths[node] = nx.single_source_dijkstra(graph, node, weight="weight")  # Use actual street distances.
    masks = {}  # Include incidental pickups on every leg.
    for source in terminals:  # Inspect all source and destination pairs.
        for destination in terminals:  # Include HOME-return pickups too.
            visited = set(paths[source][destination])  # Resolve each exact street leg.
            masks[source, destination] = sum(1 << index for index, item in enumerate(locations) if item["node"] in visited)  # Deduplicate collectible visits.
    initial = (masks[home, home], home)  # Include collectibles snapped directly to HOME.
    best = {initial: (0.0, (home,))}  # Retain minimum cost and deterministic stop order for each state.
    queue = [(0.0, (home,), initial[0])]  # Explore partial routes in nondecreasing actual distance.
    completed = []  # Retain closed candidates for the selected explicit objective.
    required = min(coins or 0, len(locations))  # Return the best available alternative when the requested count is impossible.
    shortest = math.inf  # Coins-only obtains its bound from a real satisfying route.
    maximum = -1  # Track the exact best count achievable under the cap.
    while queue:  # Exhaust eligible states without a reward-biased beam truncation.
        cost, stops, mask = heapq.heappop(queue)  # Prefer shorter routes and deterministic stop order.
        last = stops[-1]  # Read the current terminal.
        if best.get((mask, last)) != (cost, stops):  # Ignore superseded state entries.
            continue  # Expand only the best version of each state.
        if upper is None and cost > shortest:  # All remaining paths already exceed a satisfying closed route.
            break  # Prove minimum distance without an artificial step limit.
        total = cost + distances[last][home]  # Reserve the complete HOME return.
        closed_mask = mask | masks[last, home]  # Count return-leg pickups once.
        count = closed_mask.bit_count()  # Single-account rewards are physical collectibles.
        if upper is None:  # Coins-only prioritizes minimum walking after meeting the count.
            if count >= required and total <= shortest:  # Keep only minimum-distance satisfying alternatives.
                if total < shortest:  # Replace longer candidates immediately.
                    completed = []  # Retain no unnecessary extra walking.
                shortest = total  # Bound further search using a demonstrated route.
                completed.append((total, stops + (home,), count))  # Preserve deterministic equal-distance alternatives.
        elif total <= upper and count >= maximum:  # Steps and combined modes maximize pickups inside the hard cap.
            if count > maximum:  # A larger count outranks target proximity and efficiency.
                completed = []  # Discard lower-reward alternatives.
            maximum = count  # Preserve the proven best reward count.
            completed.append((total, stops + (home,), count))  # Retain target-refinement candidates.
        for node in terminals[1:]:  # Every extension must add at least one new pickup.
            new_mask = mask | masks[last, node]  # Include all traversed collectible nodes.
            if new_mask == mask:  # Rewardless legs can be replaced by shortest paths during minimum-distance search.
                continue  # Leave target padding to the separate refinement phase.
            new_cost = cost + distances[last][node]  # Measure the actual metric-closure leg.
            bound = upper if upper is not None else shortest  # Use only a supplied cap or a real incumbent distance.
            if new_cost + distances[node][home] > bound:  # Reserve mandatory return before accepting a state.
                continue  # Never exceed the hard budget to meet a coin count.
            key, candidate = (new_mask, node), (new_cost, stops + (node,))  # Identify an equivalent position and pickup set.
            if key not in best or candidate < best[key]:  # Shorter equivalent states preserve exact pickup feasibility.
                best[key] = candidate  # Keep deterministic equal-distance ordering.
                heapq.heappush(queue, (*candidate, new_mask))  # Continue the exact distance search.
    ranked = sorted(completed, key=lambda item: (item[0], item[1])) if target is None else sorted(completed, key=lambda item: (abs(item[0] - target), item[1]))[:settings.beam_width]  # ponytail: bound secondary target refinement to beam_width; exhaustive refinement if global proximity is required.
    options = []  # Compare fully expanded valid walks with actual route metrics.
    for _, stops, _ in ranked:  # Expand the selected objective's eligible candidates.
        walk = [home]  # Start every route at HOME.
        for a, b in zip(stops, stops[1:]):  # Resolve ordered metric-closure legs.
            walk.extend(paths[a][b][1:])  # Preserve every actual street transition.
        alternatives = [walk]  # Retain the original route if a distance extension is worse.
        if target is not None:  # Coins-only never receives distance padding.
            alternatives.append(extend_distance(graph, walk, home, target, upper, target))  # Seek the target rather than stopping merely at its lower bound.
        for candidate in alternatives:  # Compare actual reward and distance after refinement.
            distance = route_length(graph, candidate)  # Recompute complete walking length.
            if upper is not None and distance > upper + 1e-7:  # Enforce the final hard cap independently.
                raise AnalysisError("Single route exceeded its reserved HOME-return budget")  # Reject any invariant violation.
            visited = set(candidate)  # Count physical visits once.
            selected = [index for index, item in enumerate(locations) if item["node"] in visited]  # Include incidental extension pickups.
            edges = {frozenset((a, b)) for a, b in zip(candidate, candidate[1:])}  # Deduplicate traversed streets.
            repeated = distance - sum(graph[a][b]["weight"] for edge in edges for a, b in [tuple(edge)])  # Measure repeated walking consistently.
            score = (distance, tuple(candidate)) if target is None else (-len(selected), abs(distance - target), repeated, tuple(candidate))  # Make each objective hierarchy explicit.
            options.append((score, candidate, selected, distance, repeated))  # Compare fully validated routes.
    _, walk, selected, distance, repeated = min(options, key=lambda item: item[0])  # Choose deterministically under the selected policy.
    if walk[0] != home or walk[-1] != home:  # Guard the fixed start and finish requirement.
        raise AnalysisError("Single route did not return HOME")  # Refuse partial routes.
    unmet = []  # Distinguish hard constraints from preferred target range.
    if coins is not None and len(selected) < coins:  # Exact pickup search supports a genuine infeasibility report.
        unmet.append(f"Coin requirement infeasible: requested {coins}; reachable {len(locations)}; maximum collectible count under step cap {upper:.2f} m is {maximum}" if upper is not None else f"Coin requirement infeasible: requested {coins}; only {len(locations)} reachable collectibles")  # Include the actual failing constraint.
    if lower is not None and distance < lower:  # Report preference shortfalls without pretending budget infeasibility.
        unmet.append(f"Distance below preferred lower bound {lower:.2f} m; target refinement found {distance:.2f} m")  # State the refinement limitation honestly.
    if len(walk) == 1 and not selected:  # Preserve a truthful stationary alternative if nothing fits.
        unmet.append("No nonempty HOME-returning route selected within the requested constraints")  # Do not invent walking or pickups.
    return {"mode": "single", "requested_coins": coins, "requested_steps": steps, "walk": walk, "selected": selected, "distance_m": distance, "estimated_steps": math.ceil(distance * 1.3), "target_m": target, "lower_m": lower, "upper_m": upper, "collectibles_collected": len(selected), "distinct_locations": len(selected), "route_nodes": len(set(walk)), "intersections": sum(graph.degree[node] >= 3 for node in set(walk)), "repeated_distance_m": repeated, "constraints_satisfied": not unmet, "coin_requirement_satisfied": coins is None or len(selected) >= coins, "upper_bound_satisfied": upper is None or distance <= upper + 1e-7, "unmet": unmet, "optimizer": "exact minimum-distance pickup-state search; bounded secondary target-distance refinement"}  # Omit misleading couple-specific counts.
