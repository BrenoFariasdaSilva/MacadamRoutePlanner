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

import atexit  # For playing a sound when the program finishes
import datetime  # For getting the current date and time
import os  # For running a command in the terminal
import platform  # For getting the operating system name
import sys  # For system-specific parameters and functions
from colorama import Style  # For coloring the terminal
from Logger import Logger  # For logging output to both terminal and file
from pathlib import Path  # For handling file paths
