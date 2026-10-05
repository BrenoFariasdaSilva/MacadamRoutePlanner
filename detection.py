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

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
