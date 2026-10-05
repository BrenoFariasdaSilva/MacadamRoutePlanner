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
