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


