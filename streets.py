"""
================================================================================
Macadam Street Graph
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Build a walkable graph from observed and locally occluded street paths.

    Key features include:
        - Conservative collinear gap repair restricted to detected occluders.
        - Skeleton graph with metric calibration and bounded marker snapping.

Usage:
    Call build_graph after map registration.

Outputs:
    - Street graph, road mask, skeleton, and calibration evidence.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy, NetworkX.

Assumptions & Notes:
    - Approximate block calibration is reported explicitly.
"""

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
