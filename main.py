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


def discover_images(directory: Path) -> list[Path]:  # Select two screenshots without changing source files.
    """
    Discover readable screenshots without assigning account roles.

    :param directory: Project-local screenshot input directory.
    :return: Deterministically ordered readable screenshot paths.
    """

    files = []  # Collect only supported top-level screenshot images.
    for path in sorted(directory.iterdir(), key=lambda item: (item.name.casefold(), item.name)) if directory.is_dir() else []:  # Keep candidate presentation deterministic.
        attributes = getattr(path.stat(), "st_file_attributes", 0)  # Read native hidden and system attributes.
        if not path.is_file() or path.name.startswith(".") or attributes & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM):  # Exclude hidden and system entries.
            continue  # Leave all source entries untouched.
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"} or path.stem.lower() in {"overlay", "clean_map", "registered", "roads", "skeleton"} or path.stem.lower().endswith(("_usable", "_observed_roads")):  # Exclude unsupported files and known generated artifacts.
            continue  # Inspect another input entry.
        try:  # Ignore files that merely have an image extension.
            image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)  # Verify that the screenshot can be decoded.
        except (OSError, cv2.error):  # Ignore unreadable or empty candidate images.
            image = None  # Exclude the invalid candidate.
        if image is not None:  # Retain only actual image files.
            files.append(path)  # Preserve deterministic candidate ordering.
    return files  # Share deterministic image discovery across explicit modes.


def discover_inputs(directory: Path) -> tuple[Path, Path]:  # Preserve couple account assignment.
    """Discover exactly two screenshots and resolve their account roles."""

    files = discover_images(directory)  # Reuse readable top-level candidates.
    if len(files) != 2:  # Never silently choose among ambiguous image sets.
        raise AnalysisError(f"Inputs requires exactly two readable screenshots; found {len(files)} in {directory}: {[path.name for path in files]}. Supply --user and --girlfriend explicitly or keep only two screenshots.")  # Explain how to resolve discovery failure.
    roles = []  # Infer roles from complete filename tokens rather than substrings.
    for path in files:  # Support documented account filename patterns.
        tokens = set(re.split(r"[^a-z0-9]+", path.stem.lower()))  # Recognize user-2026 and girlfriend_current names safely.
        roles.append({role for role, names in (("user", {"user", "me", "mine"}), ("girlfriend", {"girlfriend", "gf"})) if tokens & names})  # Detect conflicting as well as unique naming evidence.
    if all(len(role) <= 1 for role in roles):  # Accept only consistent role hints.
        if (roles[0] == {"user"} and roles[1] != {"user"}) or (roles[1] == {"girlfriend"} and roles[0] != {"girlfriend"}):  # Infer the complementary account when one name is clear.
            return files[0], files[1]  # Keep the named user as the registration destination.
        if (roles[1] == {"user"} and roles[0] != {"user"}) or (roles[0] == {"girlfriend"} and roles[1] != {"girlfriend"}):  # Handle reversed alphabetical order.
            return files[1], files[0]  # Preserve ownership colors and overlay account semantics.
    if not sys.stdin.isatty():  # Account assignment affects the overlay and ownership labels.
        raise AnalysisError(f"Cannot infer account roles safely: {[path.name for path in files]}. Name files user.* and girlfriend.* or supply both explicit paths.")  # Avoid silently swapping account identities.
    print(f"Select YOUR screenshot: 1 = {files[0].name}; 2 = {files[1].name}")  # Present deterministic interactive choices.
    answer = input("Your screenshot [1/2]: ").strip()  # Request only the missing account identity.
    if answer not in {"1", "2"}:  # Reject an ambiguous selection.
        raise AnalysisError("Choose 1 or 2, or use explicit --user and --girlfriend paths")  # Explain accepted account selection.
    index = int(answer) - 1  # Convert the selected account index.
    return files[index], files[1 - index]  # Assign the other screenshot to the girlfriend account.


