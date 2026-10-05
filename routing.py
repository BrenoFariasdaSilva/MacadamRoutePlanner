"""
================================================================================
Macadam Two-Account Route Optimization
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Match physical collectible locations and search for bounded HOME loops.

    Key features include:
        - Artwork-independent spatial matching with graph-context validation.
        - Deterministic beam search using actual weighted shortest paths.

Usage:
    Call match_locations and optimize_route from the main pipeline.

Outputs:
    - Classified collectible locations and a validated closed street walk.

Dependencies:
    - Python >= 3.13, NumPy, NetworkX.

Assumptions & Notes:
    - Bounded search is heuristic and never claims global optimality.
"""

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
