"""
================================================================================
Macadam Route Rendering
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Render original-resolution overlays and a standalone walking map.

    Key features include:
        - Consistent account colors, numbered traversal, and direction arrows.
        - Separate JSON statistics and optional diagnostic artifacts.

Usage:
    Call render_outputs after final route validation.

Outputs:
    - overlay.png, clean_map.png, and route.json in a dedicated run directory.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy, NetworkX.

Assumptions & Notes:
    - Route coordinates use normalized pixels until final overlay scaling.
"""

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
