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

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
