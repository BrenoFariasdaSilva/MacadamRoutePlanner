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


def parse_arguments() -> argparse.Namespace:  # Define executable CLI behavior.
    """
    Parse paths, step constraints, and optional analysis configuration.

    :return: Validated command-line arguments.
    """

    parser = argparse.ArgumentParser(description="Plan a single or couple street-following Macadam HOME loop.", allow_abbrev=False)  # Explain application purpose.
    parser.add_argument("--mode", choices=("couple", "single"), default="couple", help="Explicit workflow; default couple preserves existing commands")  # Never infer mode from image count.
    parser.add_argument("--image", type=Path, help="Single-account screenshot; otherwise discover Inputs/Single/")  # Accept one current screenshot.
    parser.add_argument("--coins", type=int, help="Single-account minimum distinct collectibles; without steps minimize distance")  # Expose the minimum-distance objective.
    parser.add_argument("--user", type=Path, help="Your original map screenshot")  # Accept the Android account image.
    parser.add_argument("--girlfriend", type=Path, help="Girlfriend's original map screenshot")  # Accept the iPhone account image.
    parser.add_argument("--steps", type=int, help="Step target; required for couple, optional with single --coins; cap ceil(steps/1.3) * 1.05")  # Define step-budget semantics.
    parser.add_argument("--minimum", type=int, default=None, help="Combined account opportunities; shared sites count twice")  # Define optional collectible minimum.
    parser.add_argument("--output", type=Path, default=ROOT / "Outputs", help="Parent directory for a new run folder")  # Keep generated artifacts inside the project by default.
    parser.add_argument("--variants", type=Path, default=ROOT / ".assets/Collectibles/variants.json", help="Collectible variant manifest")  # Permit future artwork without pipeline rewrites.
    parser.add_argument("--meters-per-pixel", type=float, help="Known meters per pixel at normalized width 800")  # Allow explicit metric calibration.
    parser.add_argument("--match-tolerance", type=float, default=Settings().match_tolerance, help="Cross-account match tolerance in normalized pixels")  # Expose physical matching tolerance.
    parser.add_argument("--verbose", action="store_true", help="Print quantitative stage diagnostics")  # Preserve verbose behavior.
    parser.add_argument("--debug", action="store_true", help="Save intermediate masks in a separate debug directory")  # Keep normal execution artifacts small.
    parser.add_argument("--sound", action="store_true", help="Play existing notification sound on supported non-Windows systems")  # Preserve optional completion behavior.
    arguments = parser.parse_args()  # Parse explicitly supplied inputs.
    if arguments.mode == "single":  # Validate distinct single-account objectives before discovery.
        if arguments.user is not None or arguments.girlfriend is not None or arguments.minimum is not None:  # Reject options belonging to another mode.
            parser.error("Single mode uses --image and --coins, not --user/--girlfriend/--minimum")  # Keep objective semantics explicit.
        if arguments.coins is None and arguments.steps is None:  # Require at least one real objective.
            parser.error("Single mode requires at least one objective: --coins or --steps")  # Never invent a distance budget.
        if any(value is not None and value <= 0 for value in (arguments.coins, arguments.steps)):  # Validate supplied objectives only.
            parser.error("Coins and steps must be positive integers when supplied")  # Reject zero and negative objectives.
    else:  # Preserve existing couple input and prompt behavior.
        if arguments.image is not None or arguments.coins is not None:  # Reject accidental mode mixing.
            parser.error("Couple mode uses --user/--girlfriend and --minimum, not --image/--coins")  # Explain correct account options.
        if (arguments.user is None) != (arguments.girlfriend is None):  # Require a complete explicit pair.
            parser.error("Supply both --user and --girlfriend, or neither for Inputs/ discovery")  # Preserve explicit precedence.
        interactive = sys.stdin.isatty()  # Avoid hanging automated invocations.
        for name, prompt in (("steps", "Desired step limit: "),):  # Retain the existing required step prompt.
            if getattr(arguments, name) is None:  # Fill only missing CLI arguments.
                if not interactive:  # Require explicit inputs in noninteractive use.
                    parser.error(f"--{name} is required when stdin is not interactive")  # Report the missing parameter.
                value = input(prompt).strip().strip('"')  # Accept quoted Windows paths.
                try:  # Validate numeric input before execution.
                    setattr(arguments, name, int(value) if name == "steps" else Path(value))  # Store the typed input.
                except ValueError:  # Reject a malformed step count.
                    parser.error("Steps must be a positive integer")  # Explain the input requirement.
        if arguments.minimum is None:  # Preserve an optional interactive minimum.
            value = input("Desired collectibles (empty = no minimum): ").strip() if interactive else ""  # Request optional opportunity count.
            try:  # Validate the optional integer.
                arguments.minimum = int(value) if value else 0  # Treat empty input as no mandatory minimum.
            except ValueError:  # Reject malformed optional constraints.
                parser.error("Minimum collectibles must be a nonnegative integer")  # Explain valid input.
        if arguments.steps <= 0 or arguments.minimum < 0:  # Validate application constraints.
            parser.error("Steps must be positive and minimum must be nonnegative")  # Reject invalid requests before writing outputs.
    try:  # Validate assets and resolve only the selected mode's inputs.
        validate_assets(arguments.variants, SOUND_FILE if arguments.sound else None)  # Reuse bundled resources.
        if arguments.mode == "single" and arguments.image is None:  # Explicit images always override discovery.
            files = discover_images(ROOT / "Inputs/Single")  # Isolate single screenshots from the existing couple directory.
            if len(files) != 1:  # Never silently choose among multiple screenshots.
                raise AnalysisError(f"Single mode requires exactly one readable screenshot in Inputs/Single; found {len(files)}: {[path.name for path in files]}. Supply --image explicitly.")  # List every candidate.
            arguments.image = files[0]  # Select the only valid screenshot.
        elif arguments.mode == "couple" and arguments.user is None:  # Preserve existing account role discovery.
            arguments.user, arguments.girlfriend = discover_inputs(ROOT / "Inputs")  # Keep the established flat directory.
    except (AnalysisError, OSError) as error:  # Preserve actionable CLI diagnostics.
        parser.error(str(error))  # Fail before output generation.
    for value in (arguments.meters_per_pixel, arguments.match_tolerance):  # Validate floating-point configuration.
        if value is not None and (not math.isfinite(value) or value <= 0):  # Reject NaN, infinity, and nonpositive tolerances.
            parser.error("Scale and tolerance must be finite positive numbers")  # Preserve reliable geometry.
    inputs = (arguments.image,) if arguments.mode == "single" else (arguments.user, arguments.girlfriend)  # Validate only the selected workflow.
    for path in (*inputs, arguments.variants):  # Validate all input paths.
        if not path.is_file():  # Reject missing files.
            parser.error(f"Input file does not exist: {path}")  # Identify the missing input.
    print(f"SINGLE: {arguments.image.resolve()}" if arguments.mode == "single" else f"USER: {arguments.user.resolve()}\nGIRLFRIEND: {arguments.girlfriend.resolve()}", flush=True)  # Report account assignment before pipeline execution.
    return arguments  # Return validated application inputs.


