"""
================================================================================
Macadam Marker and Collectible Detection
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Detect profile markers and configurable collectible variants independently.

    Key features include:
        - Photo texture and enclosing marker geometry for HOME detection.
        - Multi-scale luminance templates and spatial duplicate suppression.

Usage:
    Import detection functions from the application pipeline.

Outputs:
    - Marker geometry, collectible candidates, and rejection diagnostics.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy.

Assumptions & Notes:
    - Variant templates describe artwork, never screenshot positions.
"""

import json  # Load replaceable visual definitions.
import math  # Validate finite template configuration.
import wave  # Validate optional bundled notification audio.
from dataclasses import asdict  # Preserve complete detector diagnostics.
from pathlib import Path  # Resolve template assets.
from typing import Any  # Annotate configurable visual records.
import cv2  # Match templates and locate marker contours.
import numpy as np  # Calculate geometric and texture statistics.
from settings import AnalysisError, Detection, Image, MapImage  # Share analysis records.


