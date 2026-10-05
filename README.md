<div align="center">

# [Macadam Route Planner](https://github.com/BrenoFariasdaSilva/MacadamRoutePlanner) <img src="https://github.com/BrenoFariasdaSilva/MacadamRoutePlanner/blob/main/.assets/Icons/GitHub%20Colored%20Icon.svg" width="3%" height="3%">

</div>

<div align="center">

---

Optimized walking routes from Macadam screenshots using collectible and step goals, with single-account and couple routing modes.

---

</div>

<div align="center">

![GitHub Code Size in Bytes](https://img.shields.io/github/languages/code-size/BrenoFariasdaSilva/MacadamRoutePlanner)
![GitHub Commits](https://img.shields.io/github/commit-activity/t/BrenoFariasdaSilva/MacadamRoutePlanner/main)
![GitHub Last Commit](https://img.shields.io/github/last-commit/BrenoFariasdaSilva/MacadamRoutePlanner)
![GitHub Forks](https://img.shields.io/github/forks/BrenoFariasdaSilva/MacadamRoutePlanner)
![GitHub Language Count](https://img.shields.io/github/languages/count/BrenoFariasdaSilva/MacadamRoutePlanner)
![GitHub License](https://img.shields.io/github/license/BrenoFariasdaSilva/MacadamRoutePlanner)
![GitHub Stars](https://img.shields.io/github/stars/BrenoFariasdaSilva/MacadamRoutePlanner)
![GitHub Contributors](https://img.shields.io/github/contributors/BrenoFariasdaSilva/MacadamRoutePlanner)
![GitHub Created At](https://img.shields.io/github/created-at/BrenoFariasdaSilva/MacadamRoutePlanner)
![WakaTime](https://wakatime.com/badge/github/BrenoFariasdaSilva/MacadamRoutePlanner.svg)

</div>

<div align="center">

![RepoBeats Statistics](https://repobeats.axiom.co/api/embed/e30a84803d82f382f9d6d313e3b9a20dd494428b.svg "Repobeats analytics image")

</div>

## Table of Contents

- [Macadam Route Planner ](#macadam-route-planner-)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Requirements](#requirements)
  - [Setup](#setup)
    - [Clone the repository](#clone-the-repository)
  - [Installation](#installation)
    - [Python](#python)
  - [Run Python Code](#run-python-code)
    - [Dependencies](#dependencies)
  - [Usage](#usage)
    - [Execution Modes](#execution-modes)
      - [Couple mode](#couple-mode)
      - [Single-account mode](#single-account-mode)
    - [Single-Account Mode](#single-account-mode-1)
      - [Coins only](#coins-only)
      - [Steps only](#steps-only)
      - [Coins and steps](#coins-and-steps)
    - [Couple Mode](#couple-mode-1)
    - [Input Discovery](#input-discovery)
      - [Single mode](#single-mode)
      - [Couple mode](#couple-mode-2)
    - [Makefile Interface](#makefile-interface)
      - [Argument precedence](#argument-precedence)
    - [Direct CLI](#direct-cli)
  - [Results](#results)
    - [Generated Outputs](#generated-outputs)
      - [`overlay.png`](#overlaypng)
      - [`clean_map.png`](#clean_mappng)
      - [`route.json`](#routejson)
    - [Route Optimization](#route-optimization)
      - [Step conversion](#step-conversion)
    - [Single-account optimization](#single-account-optimization)
      - [Coins only](#coins-only-1)
      - [Steps only](#steps-only-1)
      - [Coins + steps](#coins--steps)
    - [Couple-mode optimization](#couple-mode-optimization)
    - [Image Interpretation](#image-interpretation)
    - [HOME Detection](#home-detection)
    - [Collectible Detection](#collectible-detection)
    - [Registration and Street Topology](#registration-and-street-topology)
    - [Calibration](#calibration)
    - [Limitations](#limitations)
  - [Validation](#validation)
  - [Project Structure](#project-structure)
  - [How to Cite?](#how-to-cite)
  - [Contributing](#contributing)
  - [Collaborators](#collaborators)
  - [License](#license)
    - [Apache License 2.0](#apache-license-20)

## Introduction

MacadamRoutePlanner is a Python application that analyzes Macadam map screenshots and generates optimized closed walking routes that start and finish at the detected HOME position.

The application supports two explicit execution modes:

- **Single-account mode:** processes one screenshot and optimizes a route according to collectible and/or step objectives.
- **Couple mode:** processes one screenshot from each account, aligns both maps, detects collectible locations independently, identifies user-only, girlfriend-only, and shared collectibles, and generates one optimized walking route.

The application performs screenshot preprocessing, HOME detection, collectible recognition, street-network extraction, graph construction, route optimization, route rendering, and structured JSON reporting.

It is derived from the project's `main-template.py` conventions and reuses the existing Logger, assets, Makefile workflow, notification infrastructure, and project organization.

## Requirements

- Python **3.13+**.
- GNU Make available on `PATH`.
- Windows, macOS, or Linux shell environment compatible with the existing Makefile workflow.
- One current Macadam screenshot for single-account mode.
- Two current Macadam screenshots for couple mode.
- Bundled runtime assets under `.assets/`.
- Dependencies listed in `requirements.txt`.

Main runtime dependencies include:

- OpenCV.
- NumPy.
- NetworkX.
- Colorama and the existing project Logger infrastructure.

The application does **not** require:

- OCR frameworks.
- Machine-learning frameworks.
- Separate profile-picture files.
- Original development screenshots during normal runtime.
- Manual collectible template input.

## Setup

### Clone the repository

1. Clone the repository with the following command:

   ```bash
   git clone https://github.com/BrenoFariasdaSilva/MacadamRoutePlanner.git
   cd MacadamRoutePlanner
   ```

## Installation

### Python

The recommended installation method uses the included Makefile.

```bash
make setup
```

or:

```bash
make install
```

The setup process creates the project virtual environment when necessary and installs the dependencies from `requirements.txt`.

No manual virtual-environment activation is required for normal Makefile usage.

## Run Python Code

The Makefile is the primary user interface.

For help:

```bash
make help
```

For couple mode:

```bash
make run-couple STEPS=5000 MINIMUM=0
```

For single-account mode:

```bash
make run-single COINS=5
```

or:

```bash
make run-single STEPS=5000
```

or:

```bash
make run-single COINS=5 STEPS=5000
```

### Dependencies

Install or update the project dependencies with:

```bash
make dependencies
```

Equivalent supported setup targets include:

```bash
make setup
make install
```

## Usage

### Execution Modes

MacadamRoutePlanner has two explicit modes.

#### Couple mode

Use:

```bash
make run-couple
```

The existing:

```bash
make run
```

remains an alias for couple mode for backward compatibility.

Couple mode:

1. Processes one screenshot from each account.
2. Detects each account independently.
3. Aligns stable map content.
4. Detects HOME and collectibles.
5. Extracts the street network.
6. Matches physical collectible locations across both accounts.
7. Classifies collectibles as:
   - User-only.
   - Girlfriend-only.
   - Shared.
8. Generates a closed HOME-returning route.

#### Single-account mode

Use:

```bash
make run-single
```

Single mode:

1. Processes one screenshot.
2. Performs no cross-account registration.
3. Detects HOME.
4. Detects collectibles.
5. Extracts the street graph.
6. Snaps HOME and collectible sites to the graph.
7. Optimizes a closed HOME-returning route.

At least one of `COINS` or `STEPS` must be supplied.

### Single-Account Mode

Single mode supports three optimization objectives.

#### Coins only

```bash
make run-single COINS=5
```

The application:

1. Requires at least the requested number of distinct collectibles.
2. Finds the minimum-distance HOME-returning route satisfying that requirement.
3. Uses deterministic tie-breaking.
4. Does not introduce an artificial step target or distance padding.

Example with explicit screenshot:

```bash
make run-single IMAGE="../1. General.jpg" COINS=5
```

#### Steps only

```bash
make run-single STEPS=5000
```

The application:

1. Converts the requested steps into a distance target.
2. Respects the hard upper distance limit.
3. Maximizes the number of distinct collectible pickups.
4. Prefers routes closer to the requested distance target when collectible counts are equal.
5. Then prefers less repeated walking and deterministic ordering.

Explicit screenshot:

```bash
make run-single IMAGE="../1. General.jpg" STEPS=5000
```

#### Coins and steps

```bash
make run-single COINS=5 STEPS=5000
```

The application:

1. Prioritizes satisfying the requested collectible minimum.
2. Enforces the hard step/distance upper limit.
3. Maximizes additional collectible pickups among feasible routes.
4. Prefers routes closer to the requested step target.
5. Then prefers less repeated walking and deterministic ordering.

Explicit screenshot:

```bash
make run-single IMAGE="../1. General.jpg" COINS=5 STEPS=5000
```

Debug mode:

```bash
make run-single IMAGE="../1. General.jpg" COINS=5 STEPS=5000 DEBUG=1
```

Single-mode collectible markers are **blue only**.

No girlfriend/shared ownership statistics or legend entries are generated in this mode.

### Couple Mode

Automatic input discovery:

```bash
make run-couple STEPS=5000 MINIMUM=0
```

Debug:

```bash
make run-couple STEPS=5000 MINIMUM=0 DEBUG=1
```

Explicit screenshots:

```bash
make run-couple USER_IMAGE="../1. General.jpg" GIRLFRIEND_IMAGE="../6. Girlfriend General.jpeg" STEPS=5000 MINIMUM=0 DEBUG=1
```

Explicit CLI passthrough:

```bash
make run-couple ARGS="--user ../1. General.jpg --girlfriend ../6. Girlfriend General.jpeg --steps 5000 --minimum 0 --debug"
```

Couple-mode colors are:

- **Blue:** user-only collectible.
- **Pink:** girlfriend-only collectible.
- **Green:** shared collectible.

A shared physical collectible can use different artwork in each screenshot. Matching is based on aligned physical map position rather than icon identity.

### Input Discovery

#### Single mode

Single-account discovery uses:

```text
Inputs/Single/
```

Exactly one readable screenshot must be present.

Supported image extensions include:

- `.png`
- `.jpg`
- `.jpeg`

Matching is case-insensitive.

If zero or multiple candidate images are found, execution fails clearly and reports the discovered filenames.

An explicit `IMAGE` value overrides discovery:

```bash
make run-single IMAGE="path/to/screenshot.jpg" COINS=5
```

#### Couple mode

Couple discovery scans the top level of:

```text
Inputs/
```

Exactly two valid screenshots are expected.

Recommended filenames:

```text
user.jpg
girlfriend.jpeg
```

Supported role tokens include:

User:

- `user`
- `me`
- `mine`

Girlfriend:

- `girlfriend`
- `gf`

Examples:

```text
user-2026.PNG
gf_current.jpeg
```

Role identification is case-insensitive and token-based.

The application never silently assigns ownership based only on alphabetical ordering.

If ownership cannot be determined safely:

- Interactive execution asks for the assignment.
- Noninteractive execution fails and requests explicit paths or clearer filenames.

Explicit `USER_IMAGE` and `GIRLFRIEND_IMAGE` values bypass discovery.

### Makefile Interface

Run:

```bash
make help
```

to display targets, variables, discovery rules, directories, examples, and CLI parameters.

GNU Make does not accept unknown application options such as:

```bash
make --steps 5000
```

Use:

```bash
make run STEPS=5000
```

instead.

Available targets include:

| Target | Behavior |
| --- | --- |
| `help`, `all`, bare `make` | Display usage |
| `setup` | Create environment and install dependencies |
| `install` | Install project dependencies |
| `dependencies` | Install dependencies from `requirements.txt` |
| `run` | Couple-mode alias |
| `run-couple` | Run two-account routing |
| `run-single` | Run single-account routing |
| `compile` | Compile all project Python modules |
| `validate` | Run compilation, imports, assets, dependency and CLI validation |
| `clean` | Remove project `.pyc` and empty `__pycache__` directories |
| `generate_requirements` | Explicitly regenerate `requirements.txt` using `pip freeze` |

Couple-mode variables:

```text
USER_IMAGE
GIRLFRIEND_IMAGE
STEPS
MINIMUM
DEBUG
ARGS
```

Single-mode variables:

```text
IMAGE
COINS
STEPS
DEBUG
ARGS
```

Shared bootstrap variable:

```text
PYTHON_CMD
```

#### Argument precedence

When `ARGS` is nonempty:

1. It supplies the complete CLI argument set except the mode owned by the Make target.
2. Other run variables are ignored.

Otherwise:

1. Explicit image variables override automatic discovery.
2. Without explicit paths, the corresponding `Inputs/` location is used.
3. `STEPS`, `MINIMUM`, `COINS`, and `DEBUG` are appended according to the selected mode.

Examples:

```bash
make help

make setup

make run-couple STEPS=5000 MINIMUM=0

make run-couple USER_IMAGE="../1. General.jpg" GIRLFRIEND_IMAGE="../6. Girlfriend General.jpeg" STEPS=5000 MINIMUM=0 DEBUG=1

make run-single COINS=5

make run-single STEPS=5000

make run-single COINS=8 STEPS=5000

make run-single IMAGE="../1. General.jpg" COINS=5 DEBUG=1

make run-single IMAGE="../1. General.jpg" STEPS=5000 DEBUG=1

make run-single IMAGE="../1. General.jpg" COINS=5 STEPS=5000 DEBUG=1

make compile

make validate

make clean
```

### Direct CLI

Direct CLI execution remains available for advanced use.

Couple mode:

```bash
python main.py --mode couple --user "../1. General.jpg" --girlfriend "../6. Girlfriend General.jpeg" --steps 5000 --minimum 0
```

Single mode — coins only:

```bash
python main.py --mode single --image "../1. General.jpg" --coins 5
```

Single mode — steps only:

```bash
python main.py --mode single --image "../1. General.jpg" --steps 5000
```

Single mode — both:

```bash
python main.py --mode single --image "../1. General.jpg" --coins 5 --steps 5000
```

Additional CLI options include:

- `--verbose`
- `--output`
- `--variants`
- `--meters-per-pixel`
- `--match-tolerance`
- `--sound`

Use:

```bash
python main.py --help
```

for complete parameter descriptions.

## Results

### Generated Outputs

Successful runs are written under:

```text
Outputs/run-*/
```

Each run produces:

#### `overlay.png`

Contains:

- Route drawn on the original screenshot.
- Selected collectible markers.
- HOME.
- Route arrows.
- Sequential navigation numbers.
- Statistics.

Navigation numbers correspond to meaningful route corners, turns, intersections, or turnaround points.

Repeated visits can share one badge, for example:

```text
10/16
```

Leader lines are not used for normal route numbering.

#### `clean_map.png`

Contains:

- Simplified detected street graph.
- HOME.
- Selected route.
- Route direction/order.
- Collectible markers.
- Route statistics.

#### `route.json`

Contains structured routing and diagnostic information including:

- Execution mode.
- Ordered graph-node walk.
- Selected collectible sites.
- Distance.
- Estimated steps.
- Repeated walking.
- Constraint satisfaction.
- Navigation points.
- Detection evidence.
- Graph statistics.
- Registration information in couple mode.
- Rejected candidates.
- Unmet requirements when applicable.

Rejected image-analysis runs write:

```text
failure.json
```

rather than claiming a valid route.

### Route Optimization

Every valid route:

- Starts at HOME.
- Ends at HOME.
- Follows street-graph edges.
- Uses actual graph shortest-path distances.
- Reserves enough distance to return HOME when a distance cap exists.

#### Step conversion

The project uses:

```text
1 meter = 1.3 steps
```

Therefore:

```text
target_m = ceil(steps / 1.3)
lower_m = target_m * 0.95
upper_m = target_m * 1.05
estimated_steps = ceil(actual_graph_distance_m * 1.3)
```

For 5000 steps:

```text
target = 3847 m
preferred lower bound = 3654.65 m
hard upper bound = 4039.35 m
```

### Single-account optimization

#### Coins only

Primary objective:

```text
minimum total graph distance satisfying requested collectible count
```

#### Steps only

Priority:

```text
1. Respect hard upper distance limit.
2. Maximize collectible count.
3. Prefer target-distance proximity.
4. Reduce repeated walking.
5. Deterministic ordering.
```

#### Coins + steps

Priority:

```text
1. Satisfy collectible minimum.
2. Respect hard upper distance limit.
3. Maximize collectible count.
4. Prefer target-distance proximity.
5. Reduce repeated walking.
6. Deterministic ordering.
```

The single-account search performs exact shortest-state exploration over collectible sets/current terminals for pickup feasibility and minimum pickup-loop distances.

Its state space is exponential in the number of collectible terminals, so unusually large visible collectible sets may require substantial time or memory.

Secondary target-distance refinement is bounded and does not prove a globally closest possible distance.

### Couple-mode optimization

Couple mode caches NetworkX weighted Dijkstra paths between HOME and collectible terminals.

Its bounded beam search considers:

- User opportunities.
- Girlfriend opportunities.
- Shared rewards.
- Route distance.
- Return-to-HOME feasibility.
- Repeated traversal.
- Step/distance target.

Every partial route reserves enough distance to return HOME.

Beam width is currently bounded to control computation, so couple optimization is heuristic rather than a proof of global reward optimality.
