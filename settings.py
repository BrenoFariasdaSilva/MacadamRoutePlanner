"""
================================================================================
Macadam Routing Configuration
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Central configuration and typed image-analysis records.

    Key features include:
        - Resolution-independent analysis settings and variant definitions.
        - Explicit failure semantics for uncertain map interpretation.

Usage:
    Import from the application modules; no import-time runtime behavior.

Outputs:
    - Configuration and detection records in memory.

Dependencies:
    - Python >= 3.13, NumPy.

Assumptions & Notes:
    - Pixel tolerances refer to the normalized analysis width.
"""

from dataclasses import dataclass, field  # Define shared records.
from pathlib import Path  # Resolve project assets.
from typing import Any  # Describe heterogeneous diagnostics.
import numpy as np  # Represent image arrays.
from numpy.typing import NDArray  # Annotate numerical arrays.


ROOT = Path(__file__).resolve().parent  # Anchor runtime paths to the project.
type Image = NDArray[np.uint8]  # Represent byte images.
type Point = tuple[float, float]  # Store analysis coordinates.


@dataclass(frozen=True)  # Keep thresholds consistent across phases.
class Settings:  # Centralize documented analysis assumptions.
    width: int = 800  # Normalize processing cost independently of input size.
    white_saturation: int = 8  # Exclude the pink location halo whose observed saturation reaches twelve.
    white_value: int = 242  # Retain bright street interiors.
    feature_ratio: float = 0.55  # Reject ambiguous repeated street-label descriptors.
    ransac_pixels: float = 4.0  # Allow antialiasing and label-rendering differences.
    minimum_inliers: int = 10  # Require redundancy beyond four homography points.
    minimum_street_agreement: float = 0.8  # Require bidirectional road support inside shared stable map coverage.
    match_tolerance: float = 22.0  # Keep matching below typical collectible spacing.
    snap_tolerance: float = 45.0  # Allow symbol displacement without crossing a block.
    block_meters: float = 100.0  # Use the user's approximate intersection calibration.
    beam_width: int = 256  # Bound the deterministic route search.


@dataclass  # Preserve detector evidence alongside geometry.
class Detection:  # Describe one image-local collectible.
    point: Point  # Use the visual map anchor.
    box: tuple[int, int, int, int]  # Retain the icon bounds.
    variant: str  # Preserve the configured visual identity.
    confidence: float  # Record template similarity.


@dataclass  # Carry reusable preprocessing results.
class MapImage:  # Store a normalized screenshot and masks.
    image: Image  # Retain normalized color pixels.
    usable: Image  # Exclude interface overlays.
    roads: Image  # Record directly observed street pixels.
    original: Image  # Preserve original-resolution rendering.
    home: Point = (0.0, 0.0)  # Set after marker detection.
    home_box: tuple[int, int, int, int] = (0, 0, 0, 0)  # Store excluded marker geometry.
    detections: list[Detection] = field(default_factory=list)  # Store independent account detections.
    diagnostics: dict[str, Any] = field(default_factory=dict)  # Retain quantitative evidence.


