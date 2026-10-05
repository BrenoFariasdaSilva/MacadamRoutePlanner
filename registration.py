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

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
