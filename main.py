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

import argparse  # Parse application-level inputs.
import datetime  # Report execution timestamps.
import json  # Save failure diagnostics.
import math  # Validate finite calibration values.
import platform  # Preserve platform-specific sound behavior.
import re  # Recognize account roles in screenshot filenames.
import stat  # Exclude hidden and system input files on Windows.
import shutil  # Locate optional system audio players.
import subprocess  # Play completion audio without shell interpolation.
import sys  # Read interactive execution context.
from contextlib import redirect_stderr, redirect_stdout  # Centralize runtime logging.
from dataclasses import replace  # Apply explicit tolerance overrides.
from pathlib import Path  # Anchor paths to the project root.
from typing import Any, TextIO, cast  # Annotate logger and diagnostic contracts.
import cv2  # Fuse aligned street masks.
import networkx as nx  # Retain the HOME-connected graph.
import numpy as np  # Clean small fusion artifacts.
from colorama import Style  # Preserve terminal color conventions.
from Logger import Logger  # Reuse the existing dual-output logger.
from detection import detect_collectibles, detect_home, validate_assets  # Detect account-local objects and validate bundled resources.
from preprocessing import prepare_map  # Load and exclude screenshot interface content.
from registration import common_map_mask, register_maps  # Validate alignment and shared visible map coverage.
from rendering import render_outputs, save_image  # Write final and optional diagnostic images.
from routing import match_locations, optimize_route, optimize_single_route, snap_locations  # Match account opportunities and route them.
from settings import ROOT, AnalysisError, Settings  # Share configuration and failure semantics.
from streets import build_graph, repair_roads, snap_point  # Construct and calibrate street topology.


class BackgroundColors:  # Preserve the template's terminal palette.
    CYAN = "\033[96m"  # Color path and timing values.
    GREEN = "\033[92m"  # Color successful execution messages.
    YELLOW = "\033[93m"  # Color explicit alternative-route notices.
    RED = "\033[91m"  # Color rejected analysis messages.
    BOLD = "\033[1m"  # Emphasize completion status.


VERBOSE = False  # Keep diagnostic output opt-in.
SOUND_FILE = ROOT / ".assets/Sounds/NotificationSound.wav"  # Reuse the template asset.


