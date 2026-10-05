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


