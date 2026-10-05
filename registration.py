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


