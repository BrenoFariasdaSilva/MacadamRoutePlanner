"""
================================================================================
Macadam Map Registration
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Register stable map features into the first account's coordinate system.

    Key features include:
        - SIFT descriptor filtering and RANSAC homography estimation.
        - Independent street agreement inside common visible map coverage.

Usage:
    Call register_maps after independent marker and collectible detection.

Outputs:
    - Validated homography and quantitative registration diagnostics.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy.

Assumptions & Notes:
    - Overlapping stable map content is required.
"""

from typing import Any  # Annotate registration diagnostics.
import cv2  # Estimate robust feature transforms.
import numpy as np  # Validate transformation geometry.
from numpy.typing import NDArray  # Annotate transformation matrices.
from detection import stable_mask  # Exclude dynamic map artwork.
from settings import AnalysisError, Image, MapImage, Point, Settings  # Share analysis contracts.


def transform_points(points: list[Point], matrix: NDArray[np.float64]) -> NDArray[np.float64]:  # Share projective point mapping.
    """
    Transform coordinates into the first screenshot's normalized map.

    :param points: Source map coordinates.
    :param matrix: Source-to-destination homography.
    :return: Transformed coordinate array.
    """

    if not points:  # Preserve an empty detection set.
        return np.empty((0, 2), dtype=np.float64)  # Return a consistently shaped array.
    return cv2.perspectiveTransform(np.asarray(points, dtype=np.float64).reshape(-1, 1, 2), matrix).reshape(-1, 2)  # Apply homogeneous projection.


def register_maps(first: MapImage, second: MapImage, settings: Settings) -> tuple[NDArray[np.float64], dict[str, Any]]:  # Align using stable map content.
    """
    Estimate and validate a projective map alignment.

    :param first: Destination account image.
    :param second: Source account image.
    :param settings: Matching and validation tolerances.
    :return: Homography and measurable alignment evidence.
    """

    cv2.setRNGSeed(0)  # Make robust estimation reproducible.
    sift = cv2.SIFT_create(nfeatures=7000, contrastThreshold=0.025)  # Retain label and road junction features.
    key_a, desc_a = sift.detectAndCompute(cv2.cvtColor(first.image, cv2.COLOR_BGR2GRAY), stable_mask(first))  # Extract destination features.
    key_b, desc_b = sift.detectAndCompute(cv2.cvtColor(second.image, cv2.COLOR_BGR2GRAY), stable_mask(second))  # Extract source features.
    if desc_a is None or desc_b is None or min(len(desc_a), len(desc_b)) < 10:  # Require sufficient stable content.
        raise AnalysisError("Registration has fewer than ten stable features")  # Report insufficient map evidence.
    pairs = cv2.BFMatcher().knnMatch(desc_b, desc_a, k=2)  # Compare source descriptors with destination descriptors.
    matches = [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < settings.feature_ratio * pair[1].distance]  # Reject ambiguous feature identities.
    reverse = cv2.BFMatcher().knnMatch(desc_a, desc_b, k=2)  # Require reciprocal descriptor agreement.
    reciprocal = {(pair[0].queryIdx, pair[0].trainIdx) for pair in reverse if len(pair) == 2 and pair[0].distance < settings.feature_ratio * pair[1].distance}  # Retain distinctive reverse matches.
    matches = [match for match in matches if (match.trainIdx, match.queryIdx) in reciprocal]  # Remove one-directional repetitive-label matches.
    matches = list({match.trainIdx: match for match in sorted(matches, key=lambda item: -item.distance)}.values())  # Avoid duplicated destination anchors.
    if len(matches) < settings.minimum_inliers:  # Require enough candidates for robust estimation.
        raise AnalysisError(f"Registration has only {len(matches)} filtered matches")  # Report the correspondence count.
    source = np.float64([key_b[match.queryIdx].pt for match in matches])  # Collect source coordinates.
    destination = np.float64([key_a[match.trainIdx].pt for match in matches])  # Collect destination coordinates.
    matrix, mask = cv2.findHomography(source, destination, cv2.USAC_MAGSAC, settings.ransac_pixels)  # Use noise-marginalized robust estimation for repetitive map labels.
    if matrix is None or mask is None or not np.isfinite(matrix).all():  # Reject failed estimation.
        raise AnalysisError("RANSAC did not produce a finite homography")  # Stop before graph fusion.
    errors = np.linalg.norm(transform_points([tuple(point) for point in source], matrix) - destination, axis=1)  # Independently recompute reprojection errors.
    inliers = (mask.ravel() > 0) & (errors <= settings.ransac_pixels)  # Validate returned inlier membership.
    count = int(np.sum(inliers))  # Count supported correspondences.
    home_error = float(np.linalg.norm(transform_points([second.home], matrix)[0] - first.home))  # Report account separation without assuming the people are colocated.
    jacobian = matrix[:2, :2]  # Approximate local scale and orientation.
    scales = np.linalg.svd(jacobian, compute_uv=False)  # Detect collapse, reflection, and extreme distortion.
    rotation = float(np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0])))  # Measure map rotation.
    height, width = second.image.shape[:2]  # Read the source extent.
    corners = np.float64([[0, 0], [width, 0], [width, height], [0, height]])  # Sample transform denominators.
    denominators = corners @ matrix[2, :2] + matrix[2, 2]  # Detect projective poles inside the image.
    coverage = float(cv2.contourArea(cv2.convexHull(source[inliers].astype(np.float32))) / (width * height)) if count >= 3 else 0.0  # Require spatially distributed evidence.
    diagnostics = {"matches": len(matches), "inliers": count, "inlier_ratio": count / len(matches), "median_error_pixels": float(np.median(errors[inliers])) if count else None, "home_error_pixels": home_error, "scales": scales.tolist(), "rotation_degrees": rotation, "inlier_coverage": coverage, "matrix": matrix.tolist()}  # Preserve complete registration evidence.
    valid = count >= settings.minimum_inliers and coverage >= 0.01  # Require distributed feature support; final street evidence validates alignment independently of avatars.
    geometry = np.linalg.det(jacobian) > 0 and min(scales) > 0.3 and max(scales) < 3.0 and max(scales) / min(scales) < 1.6 and abs(rotation) < 35 and min(denominators) > 0.4 and max(denominators) < 1.6  # Bound plausible screenshot transformations.
    if not valid or not geometry:  # Reject low confidence instead of forcing an alignment.
        raise AnalysisError(f"Registration rejected: {diagnostics}")  # Include quantitative rejection evidence.
    matrix, refinement = refine_streets(first, second, matrix, settings)  # Correct label-anchor offsets using observed street geometry.
    diagnostics.update(refinement)  # Preserve initial feature evidence and final road evidence separately.
    diagnostics["home_is_alignment_constraint"] = False  # Distinguish diagnostic account separation from registration acceptance.
    diagnostics["matrix"] = matrix.tolist()  # Report the final source-to-destination transform.
    return matrix, diagnostics  # Return a validated coordinate mapping.


def refine_streets(first: MapImage, second: MapImage, matrix: NDArray[np.float64], settings: Settings) -> tuple[NDArray[np.float64], dict[str, Any]]:  # Refine feature alignment against road interiors.
    """
    Refine a validated initialization using masked street correlation.

    :param first: Destination screenshot.
    :param second: Source screenshot.
    :param matrix: Validated feature initialization.
    :param settings: Independent street agreement requirements.
    :return: Refined transform and independent road metrics.
    """

    height, width = second.image.shape[:2]  # Read source mask geometry.
    mask = cv2.bitwise_and(stable_mask(second), cv2.warpPerspective(stable_mask(first), np.linalg.inv(matrix), (width, height), flags=cv2.INTER_NEAREST))  # Use mutually visible stable map content.
    try:  # Refuse uncertain refinement rather than silently keeping doubled streets.
        correlation, inverse = cv2.findTransformECC(first.roads.astype(np.float32) / 255, second.roads.astype(np.float32) / 255, np.linalg.inv(matrix).astype(np.float32), cv2.MOTION_HOMOGRAPHY, (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 150, 1e-6), mask, 9)  # Align street geometry despite displaced label anchors.
    except cv2.error as error:  # Preserve explicit refinement failure.
        raise AnalysisError(f"Street registration refinement failed: {error}") from error  # Reject unsupported road fusion.
    refined = np.linalg.inv(inverse).astype(np.float64)  # Recover source-to-destination coordinates.
    refined /= refined[2, 2]  # Normalize projective scale.
    home_error = float(np.linalg.norm(transform_points([second.home], refined)[0] - first.home))  # Keep account separation as diagnostic information only.
    corners = [(0.0, 0.0), (float(width), 0.0), (float(width), float(height)), (0.0, float(height))]  # Inspect the full source domain.
    denominators = np.asarray(corners) @ refined[2, :2] + 1  # Reject projective poles and severe perspective distortion.
    scales = np.linalg.svd(refined[:2, :2], compute_uv=False)  # Revalidate final local scale.
    valid = np.isfinite(refined).all() and correlation >= 0.65 and min(denominators) > 0.4 and max(denominators) < 1.6 and min(scales) > 0.3 and max(scales) < 3 and max(scales) / min(scales) < 1.6 and np.linalg.det(refined[:2, :2]) > 0  # Require plausible final geometry and strong road evidence without forcing shared HOME coordinates.
    if not valid:  # Refuse a visually inconsistent fused graph.
        raise AnalysisError(f"Street refinement rejected: correlation={correlation:.3f}, scales={scales.tolist()}")  # Report map evidence rather than unrelated account separation.
    shape = (first.image.shape[1], first.image.shape[0])  # Validate both accounts in the destination coordinate system.
    warped_roads = cv2.warpPerspective(second.roads, refined, shape, flags=cv2.INTER_NEAREST)  # Align independently observed streets.
    common = cv2.bitwise_and(stable_mask(first), cv2.warpPerspective(stable_mask(second), refined, shape, flags=cv2.INTER_NEAREST)) > 0  # Exclude UI and dynamic artwork from both accounts.
    observed_a, observed_b = (first.roads > 0) & common, (warped_roads > 0) & common  # Measure road support only where both maps are visible.
    distance_a = cv2.distanceTransform((first.roads == 0).astype(np.uint8), cv2.DIST_L2, 5)  # Measure distance to destination road evidence.
    distance_b = cv2.distanceTransform((warped_roads == 0).astype(np.uint8), cv2.DIST_L2, 5)  # Measure distance to source road evidence.
    agreement = [float(np.mean(distance_b[observed_a] <= settings.ransac_pixels)) if np.any(observed_a) else 0.0, float(np.mean(distance_a[observed_b] <= settings.ransac_pixels)) if np.any(observed_b) else 0.0]  # Require support in both directions rather than accepting a small accidental overlap.
    if min(agreement) < settings.minimum_street_agreement:  # Preserve a strong independent registration gate.
        raise AnalysisError(f"Street registration lacks common-map agreement: {agreement}; required {settings.minimum_street_agreement}")  # Reject uncertain map fusion.
    return refined, {"street_correlation": correlation, "street_agreement": agreement, "final_home_error_pixels": home_error, "final_scales": scales.tolist()}  # Keep final alignment diagnostics explicit.


def common_map_mask(first: MapImage, second: MapImage, matrix: NDArray[np.float64]) -> Image:  # Restrict couple routing to map coverage visible in both screenshots.
    """Intersect usable map masks in the user's coordinate system, excluding interface panels."""

    warped = cv2.warpPerspective(second.usable, matrix, (first.image.shape[1], first.image.shape[0]), flags=cv2.INTER_NEAREST)  # Exclude source borders as well as source interface content.
    common = cv2.bitwise_and(first.usable, warped)  # Keep only the shared visible map footprint.
    if not np.any(common):  # Never substitute one account's map for missing common coverage.
        raise AnalysisError("Screenshots have no common usable map area")  # Request overlapping screenshot evidence.
    return common  # Use one coverage mask for roads, collectibles, and output display.
