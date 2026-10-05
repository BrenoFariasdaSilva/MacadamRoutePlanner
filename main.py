"""
================================================================================
Macadam Single and Couple Walking Routes
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Generate a single-account or aligned couple collectible-aware HOME loop.

    Key features include:
        - Independent multi-variant detection and validated map registration.
        - Street-following routing with a hard distance cap and explicit alternatives.
        - Original screenshot overlay, clean map, and quantitative JSON report.
        - Existing Logger integration and execution-time reporting.
        - Optional completion sound using the existing notification asset.

Usage:
    1. Install requirements.txt into the project virtual environment.
    2. Run python main.py --user IMAGE --girlfriend IMAGE --steps 5000.
    3. Inspect the generated Outputs/run-* directory and Logs/main.log.

Outputs:
    - Outputs/run-*/overlay.png, clean_map.png, and route.json.
    - Optional separate debug images and Logs/main.log.

Dependencies:
    - Python >= 3.13, colorama, OpenCV, NumPy, NetworkX.

Assumptions & Notes:
    - Metric distances are approximate unless explicit scale is supplied.
    - Unreliable image analysis fails rather than emitting an invented route.
"""

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
