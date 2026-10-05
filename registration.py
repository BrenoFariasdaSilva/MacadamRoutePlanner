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


