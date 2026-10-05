"""
================================================================================
Macadam Project Commands
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-02
Description : Portable Make orchestration using the standard library.
Usage       : make help
Outputs     : Project environment, validation diagnostics, or application outputs.
Dependencies: Python >= 3.13; runtime dependencies remain in requirements.txt.
Assumptions : Source screenshots and generated routes are never cleanup targets.
"""

import importlib.util  # Detect optional developer tools without installing them.
import os  # Read Make variables without shell interpolation.
from pathlib import Path  # Resolve all project resources relative to this module.
import py_compile  # Compile discovered source modules with explicit failures.
import shlex  # Parse explicit application arguments without invoking a shell.
import subprocess  # Execute argument lists safely on every platform.
import sys  # Report task errors and invoke the selected interpreter.
import venv  # Create the existing project-local environment convention.


ROOT = Path(__file__).resolve().parent  # Anchor project tasks independently of the caller's directory.
PYTHON = ROOT / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")  # Use the project environment for application commands.
EXCLUDED = {"venv", ".venv", "env", ".git", ".agents", ".codex", ".assets", "Inputs", "Outputs", "Logs", "__pycache__", ".ruff_cache", ".pytest_cache", ".mypy_cache"}  # Protect runtime data and third-party directories.
HELP = """Macadam: single-account and couple screenshot walking routes with HOME return.

Targets:
  help (also bare make/all)   Show this guide without running the planner.
  setup / install            Create venv if missing; install requirements.txt.
  dependencies               Alias for install.
  run / run-couple           Execute couple mode with the project venv.
  run-single                 Execute single mode; require COINS and/or STEPS.
  compile                    Compile all project Python sources, excluding runtime directories.
  validate                   Compile, import application modules, validate bundled assets,
                             run pip check and CLI help; run Ruff/Pyright if installed.
  clean                      Remove project bytecode only; keep Inputs, Outputs, assets and venv.
  generate_requirements      Explicitly replace requirements.txt with the environment's pip freeze.

Couple daily use: place exactly two readable PNG/JPG/JPEG screenshots in Inputs/.
Name them user.* (also me/mine tokens) and girlfriend.* (also gf token).
One unambiguous role determines the other. Unknown/conflicting roles require
interactive selection, or explicit paths in noninteractive execution.
Hidden/system/non-image files and known generated map files are ignored.
More/fewer than two screenshots fail clearly. Inputs are never modified.
Results: Outputs/run-*/overlay.png, clean_map.png, route.json; --debug adds debug/.

Couple variables: STEPS, MINIMUM, DEBUG=0|1, USER_IMAGE, GIRLFRIEND_IMAGE, ARGS,
           PYTHON_CMD (bootstrap Python; default python on Windows, python3 elsewhere).
Precedence: nonempty ARGS is the complete argument set except target-owned mode; other run variables are ignored.
Otherwise both image variables override discovery; STEPS/MINIMUM/DEBUG add options.
In couple mode, omitted STEPS prompts interactively; noninteractive execution fails.
Without MINIMUM, the existing interactive prompt remains; otherwise default is zero.

Examples (run from the project directory):
  make setup
  make install
  make run
  make run STEPS=5000 MINIMUM=0
  make run STEPS=5000 MINIMUM=0 DEBUG=1
  make run USER_IMAGE="../1. General.jpg" GIRLFRIEND_IMAGE="../6. Girlfriend General.jpeg" STEPS=5000 MINIMUM=0
  make run ARGS="--user ../1. General.jpg --girlfriend ../6. Girlfriend General.jpeg --steps 5000 --minimum 0 --debug"
  make compile
  make validate
  make clean

ARGS supports single/double-quoted path values. For the path options --user,
--girlfriend, --image, --output and --variants, unquoted words up to the next --option
are also joined as one path. Prefer image variables for filenames containing spaces.
No shell commands or expansions inside ARGS are executed.
GNU Make does NOT accept application options such as make --steps 5000.
Use make run STEPS=5000 or make run ARGS="--steps 5000" instead.

CLI options: --user, --girlfriend, --steps, --minimum, --debug, --verbose,
--output, --variants, --meters-per-pixel, --match-tolerance, --sound, --help.
Advanced CLI help: make run ARGS=--help
Required assets are bundled under .assets/Collectibles/. No profile image or
original development screenshots are required; HOME is detected from each input.

COUPLE MODE
-----------
make run is an alias for run-couple; two screenshots in Inputs/.
  make run-couple STEPS=5000 MINIMUM=0
  make run-couple STEPS=5000 MINIMUM=0 DEBUG=1
  make run-couple USER_IMAGE="../1. General.jpg" GIRLFRIEND_IMAGE="../6. Girlfriend General.jpeg" STEPS=5000 MINIMUM=0
  make run-couple ARGS="--user ../1. General.jpg --girlfriend ../6. Girlfriend General.jpeg --steps 5000 --minimum 0 --debug"

SINGLE MODE
-----------
Exactly one readable screenshot in Inputs/Single/, or explicit IMAGE.
Zero/multiple candidates fail; explicit IMAGE overrides discovery.
Require positive integer COINS and/or STEPS. Wrong-mode options fail.
Coins only: minimum-distance HOME loop collecting at least COINS; no step cap.
Steps only: maximize pickups within hard +5% cap, then target proximity, then efficiency.
Both: meet COINS within hard cap, then maximize pickups, proximity, efficiency.
Target = ceil(STEPS/1.3) meters; preferred lower 95%, hard maximum 105%.
  make run-single COINS=5
  make run-single STEPS=5000
  make run-single COINS=8 STEPS=5000
  make run-single IMAGE="../1. General.jpg" COINS=5
  make run-single IMAGE="../1. General.jpg" STEPS=5000
  make run-single IMAGE="../1. General.jpg" COINS=8 STEPS=5000 DEBUG=1
  make run-single ARGS="--image ../1. General.jpg --coins 8 --steps 5000 --debug"
Single variables: IMAGE, COINS, STEPS, DEBUG, ARGS.
The Make target forces --mode; supplying --mode in ARGS is rejected.
CLI: --mode couple|single (default couple), --image, --coins plus existing options.
Single uses blue collectibles only; no girlfriend/shared stats or registration.
Exact pickup-state search has exponential cost; secondary target refinement is bounded.
Infeasible coin requests report reachable counts/cap; valid alternatives exit 3.
Both modes preserve HOME return, corner numbers, grouped repeat visits and arrows.
Single debug masks/roads/skeleton omit registration; HOME/detections appear in JSON.
"""  # Keep help identical across shells and platforms.


def source_files() -> list[Path]:  # Discover project sources without entering runtime directories.
    """Return source modules eligible for compilation and bounded cleanup."""

    sources = []  # Retain deterministic source paths.
    for directory, folders, files in os.walk(ROOT, followlinks=False):  # Avoid following directory links outside the project.
        folders[:] = sorted(name for name in folders if name not in EXCLUDED and not (Path(directory) / name).is_symlink())  # Prune protected trees before recursion.
        sources.extend(Path(directory) / name for name in sorted(files) if name.endswith(".py") and not (Path(directory) / name).is_symlink())  # Include all real project Python modules.
    return sources  # Share source discovery across compile, validation, and cleanup.


