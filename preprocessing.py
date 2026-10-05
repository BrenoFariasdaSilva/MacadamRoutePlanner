"""
================================================================================
Macadam Map Preprocessing
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Normalize screenshots and exclude visually detected interface panels.

    Key features include:
        - Neutral-white street segmentation across colored map themes.
        - Dynamic panel geometry and configurable analysis resolution.

Usage:
    Call prepare_map from the application pipeline.

Outputs:
    - Normalized image, usable mask, and observed road mask.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy.

Assumptions & Notes:
    - Roads are bright neutral paths; unsupported map styles fail explicitly.
"""

from pathlib import Path  # Accept filesystem inputs.
import cv2  # Perform image segmentation.
import numpy as np  # Manipulate masks.
from settings import AnalysisError, Image, MapImage, Settings  # Share analysis contracts.


