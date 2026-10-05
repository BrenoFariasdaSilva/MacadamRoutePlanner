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


