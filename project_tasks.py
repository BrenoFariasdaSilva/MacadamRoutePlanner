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


def run_command(arguments: list[str]) -> None:  # Propagate subprocess failures without shell evaluation.
    """Run a project command with the project root as its working directory."""

    subprocess.run(arguments, cwd=ROOT, check=True)  # Preserve native exit status and interactive input.


def application_arguments(mode: str) -> list[str]:  # Translate Make inputs into one unambiguous CLI argument list.
    """Apply documented ARGS precedence and preserve paths containing spaces."""

    raw = os.environ.get("MACADAM_ARGS", "").strip()  # Read explicit arguments without shell expansion.
    if raw:  # Treat ARGS as the complete explicit argument set.
        tokens = [token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'" else token for token in shlex.split(raw, posix=False)]  # Preserve Windows backslashes and remove balanced outer quotes.
        result = []  # Assemble path-aware arguments for the application parser.
        index = 0  # Consume each argument exactly once.
        while index < len(tokens):  # Support the documented unquoted multiword path examples.
            token = tokens[index]  # Read the next option or value.
            result.append(token)  # Preserve arbitrary non-path CLI arguments.
            index += 1  # Advance past this token.
            if token in {"--user", "--girlfriend", "--image", "--output", "--variants"}:  # Join only known path-valued arguments.
                words = []  # Retain spaces within an explicit path.
                while index < len(tokens) and not tokens[index].startswith("--"):  # Stop at the next application option.
                    words.append(tokens[index])  # Preserve path characters without filesystem guessing.
                    index += 1  # Consume this path component.
                if words:  # Leave missing values for argparse to diagnose.
                    result.append(" ".join(words))  # Pass one complete path argument.
        if any(token == "--mode" or token.startswith("--mode=") for token in result):  # The chosen Make target owns mode selection.
            raise ValueError("Do not supply --mode in ARGS; select run-single or run-couple")  # Reject contradictory mode overrides.
        return ["--mode", mode, *result]  # Ignore all other Make run variables when ARGS is supplied.
    result = ["--mode", mode]  # Force the target's mode independently of screenshot count.
    names = ("IMAGE", "COINS", "STEPS") if mode == "single" else ("USER_IMAGE", "GIRLFRIEND_IMAGE", "STEPS", "MINIMUM")  # Keep variable semantics distinct.
    incompatible = ("USER_IMAGE", "GIRLFRIEND_IMAGE", "MINIMUM") if mode == "single" else ("IMAGE", "COINS")  # Detect mistaken mode-specific variables.
    if any(os.environ.get("MACADAM_" + name, "").strip() for name in incompatible):  # Never silently discard a routing requirement.
        raise ValueError(f"Variables {', '.join(incompatible)} do not belong to {mode} mode")  # Explain the selected target's contract.
    options = {"USER_IMAGE": "user", "GIRLFRIEND_IMAGE": "girlfriend"}  # Preserve the existing CLI option names.
    for name in names:  # Pass each explicitly supplied path or objective unchanged.
        value = os.environ.get("MACADAM_" + name, "").strip()  # Preserve filenames containing spaces.
        if value:  # Keep omitted objectives absent rather than supplying defaults.
            result.extend(("--" + options.get(name, name.lower()), value))  # Leave semantic validation to the application.
    debug = os.environ.get("MACADAM_DEBUG", "0").strip()  # Keep debug behavior explicit.
    if debug not in {"0", "1"}:  # Reject accidental truthy strings.
        raise ValueError("DEBUG must be 0 or 1")  # Explain supported Make values.
    if debug == "1":  # Preserve the existing debug switch.
        result.append("--debug")  # Request existing pipeline diagnostics.
    return result  # Let main.py own discovery and business logic.


def main() -> int:  # Dispatch the small portable Make interface.
    """Execute the selected project task and return a meaningful exit status."""

    task = sys.argv[1] if len(sys.argv) > 1 else "help"  # Keep default invocation harmless.
    try:  # Report project task failures without hiding nonzero status.
        if task == "help":  # Avoid requiring installed application dependencies for help.
            print(HELP)  # Display complete daily-use documentation.
            return 0  # Finish without launching the planner.
        if task in {"setup", "install", "dependencies"}:  # Preserve one shared environment installation path.
            if not PYTHON.is_file():  # Reuse a working environment when present.
                venv.EnvBuilder(with_pip=True).create(ROOT / "venv")  # Create the project-local Python environment.
            run_command([str(PYTHON), "-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt"])  # Install only missing or mismatched pinned requirements.
            return 0  # Propagate installation failures through the surrounding handler.
        if not PYTHON.is_file():  # Never accidentally run with unrelated global dependencies.
            raise ValueError("Project venv missing; run make setup first")  # Give an actionable setup instruction.
        if Path(sys.prefix).resolve() != (ROOT / "venv").resolve():  # Run every execution and validation task inside the project environment.
            run_command([str(PYTHON), "-W", "error", str(Path(__file__)), task])  # Reenter this standard-library dispatcher using the project interpreter.
            return 0  # Preserve the child task's success status.
        sources = source_files()  # Discover source modules once for the selected task.
        if task in {"compile", "validate"}:  # Fail on syntax errors and warnings in every source module.
            for source in sources:  # Avoid fragile manually maintained compilation lists.
                py_compile.compile(str(source), doraise=True)  # Compile without executing application modules.
            print(f"Compiled {len(sources)} project Python modules.", flush=True)  # Report actual validation coverage.
        if task == "validate":  # Run independent runtime and dependency validation.
            modules = [source.stem for source in sources if source.parent == ROOT and source.stem.isidentifier()]  # Exclude the archival hyphenated template from runtime imports.
            run_command([str(PYTHON), "-W", "error", "-c", "import importlib; [importlib.import_module(name) for name in " + repr(modules) + "]"])  # Validate all importable top-level application modules.
            from detection import validate_assets  # Load runtime dependencies only inside validation.
            validate_assets(ROOT / ".assets/Collectibles/variants.json", ROOT / ".assets/Sounds/NotificationSound.wav")  # Validate bundled templates and optional sound.
            print("Bundled assets and application imports validated.", flush=True)  # Report successful runtime prerequisites.
            run_command([str(PYTHON), "-m", "pip", "check"])  # Verify installed dependency consistency.
            run_command([str(PYTHON), "main.py", "--help"])  # Exercise the actual CLI parser.
            for module in ("ruff", "pyright"):  # Use optional developer tooling only when installed.
                if importlib.util.find_spec(module) is None:  # Report unavailable tooling honestly.
                    print(f"Skipped {module}: not installed in project venv.")  # Avoid claiming unexecuted static analysis.
                else:  # Propagate genuine installed-tool failures.
                    run_command([str(PYTHON), "-m", module, *(["check"] if module == "ruff" else []), *(str(source) for source in sources)])  # Restrict analysis to discovered project sources.
        elif task in {"run", "run-couple", "run-single"}:  # Execute the existing application unchanged beyond its CLI integration.
            run_command([str(PYTHON), "main.py", *application_arguments("single" if task == "run-single" else "couple")])  # Preserve real pipeline exit status.
        elif task == "clean":  # Remove only verified project bytecode files.
            directories = {source.parent for source in sources}  # Restrict cleanup to source directories outside protected trees.
            for directory in directories:  # Leave screenshots, assets, logs, outputs, and environments untouched.
                cache = directory / "__pycache__"  # Inspect only the conventional bytecode directory.
                paths = list(directory.glob("*.pyc")) + (list(cache.glob("*.pyc")) if cache.is_dir() and not cache.is_symlink() else [])  # Never recursively delete arbitrary directories.
                for path in paths:  # Verify each final target before removing generated bytecode.
                    if not path.is_symlink() and path.resolve().is_relative_to(ROOT):  # Keep every resolved target inside the project.
                        path.unlink()  # Remove this bytecode file only.
                if cache.is_dir() and not cache.is_symlink() and not any(cache.iterdir()):  # Remove empty cache directories only.
                    cache.rmdir()  # Preserve any unexpected cache contents.
            print("Removed project bytecode; Inputs, Outputs, assets, logs and venv preserved.")  # Describe the exact cleanup scope.
        elif task == "generate_requirements":  # Keep dependency export explicitly opt-in.
            result = subprocess.run([str(PYTHON), "-m", "pip", "freeze"], cwd=ROOT, check=True, capture_output=True, text=True)  # Collect a successful dependency snapshot before overwriting.
            (ROOT / "requirements.txt").write_text(result.stdout, encoding="utf-8")  # Preserve the existing export target.
        elif task not in {"compile", "validate"}:  # Reject misspelled internal tasks.
            raise ValueError(f"Unknown project task: {task}")  # Keep failure explicit.
        return 0  # Report successful task completion.
    except subprocess.CalledProcessError as error:  # Preserve application and dependency command failures.
        return error.returncode  # Let Make report a failed target accurately.
    except (OSError, ValueError, py_compile.PyCompileError) as error:  # Normalize actionable task failures.
        print(f"Project task failed: {error}", file=sys.stderr)  # Explain the failing prerequisite.
        return 2  # Return a nonzero task status.


if __name__ == "__main__":  # Keep importing this module free of task execution.
    sys.exit(main())  # Run only the explicitly requested project command.
