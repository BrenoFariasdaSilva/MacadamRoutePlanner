"""
================================================================================
Macadam Marker and Collectible Detection
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Detect profile markers and configurable collectible variants independently.

    Key features include:
        - Photo texture and enclosing marker geometry for HOME detection.
        - Multi-scale luminance templates and spatial duplicate suppression.

Usage:
    Import detection functions from the application pipeline.

Outputs:
    - Marker geometry, collectible candidates, and rejection diagnostics.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy.

Assumptions & Notes:
    - Variant templates describe artwork, never screenshot positions.
"""

import json  # Load replaceable visual definitions.
import math  # Validate finite template configuration.
import wave  # Validate optional bundled notification audio.
from dataclasses import asdict  # Preserve complete detector diagnostics.
from pathlib import Path  # Resolve template assets.
from typing import Any  # Annotate configurable visual records.
import cv2  # Match templates and locate marker contours.
import numpy as np  # Calculate geometric and texture statistics.
from settings import AnalysisError, Detection, Image, MapImage  # Share analysis records.


def detect_home(scene: MapImage) -> None:  # Locate the photograph marker without knowing its pixels.
    """
    Detect a textured photograph enclosed by a large map-marker contour.

    :param scene: Prepared account screenshot to update.
    :return: None.
    """

    gray = cv2.cvtColor(scene.image, cv2.COLOR_BGR2GRAY)  # Measure luminance texture.
    contours, _ = cv2.findContours((gray < 100).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)  # Include nested marker outlines.
    candidates = []  # Collect independently scored marker regions.
    for contour in contours:  # Evaluate marker geometry.
        x, y, w, h = cv2.boundingRect(contour)  # Read enclosing dimensions.
        if not (90 < w < 220 and 90 < h < 230 and 0.7 < w / h < 1.3):  # Reject small icons and large panels.
            continue  # Inspect the next contour.
        if np.mean(scene.usable[y:y + h, x:x + w] > 0) < 0.95:  # Exclude navigation and promotional avatars.
            continue  # Ignore non-map pictures.
        points = contour.reshape(-1, 2)  # Inspect the marker's actual bottom geometry.
        if np.ptp(points[points[:, 1] >= y + h - 3, 0]) > w * 0.2:  # A map pin has a narrow tip; attached distance bubbles have broad rounded bottoms.
            continue  # Prefer the nested pin outline instead of a merged label boundary.
        patch = gray[y + h // 5:y + 4 * h // 5, x + w // 5:x + 4 * w // 5]  # Inspect the photograph interior.
        texture = float(np.std(patch))  # Distinguish photographs from flat symbol fills.
        dark_fraction = float(np.mean(patch < 155))  # Require substantial photographic content.
        if texture > 30 and dark_fraction > 0.35 and cv2.contourArea(contour) > w * h * 0.5:  # Require texture and an enclosed marker.
            candidates.append((texture * dark_fraction, (x, y, w, h)))  # Score candidate evidence.
    candidates.sort(key=lambda item: item[1][2] * item[1][3], reverse=True)  # Prefer enclosing outlines over inner photograph contours.
    distinct = []  # Suppress nested outlines of the same marker.
    for score, box in candidates:  # Keep spatially separate candidates.
        x, y, w, h = box  # Read candidate geometry.
        if all(np.hypot(x + w / 2 - (b[0] + b[2] / 2), y + h / 2 - (b[1] + b[3] / 2)) > 80 for _, b in distinct):  # Merge nested marker boundaries.
            distinct.append((score, box))  # Retain a distinct location.
    scene.diagnostics["home_candidates"] = len(distinct)  # Expose ambiguity quantitatively.
    if len(distinct) != 1:  # Refuse ambiguous HOME locations.
        raise AnalysisError(f"HOME detection requires one reliable marker; found {len(distinct)}: {distinct}")  # Report candidate evidence.
    x, y, w, h = distinct[0][1]  # Select the unique photograph marker.
    scene.home_box = (x, y, w, h)  # Preserve dynamic exclusion geometry.
    outline = next(contour for contour in contours if cv2.boundingRect(contour) == scene.home_box)  # Recover the selected contour.
    tip = outline.reshape(-1, 2)  # Read boundary coordinates.
    scene.home = (float(np.mean(tip[tip[:, 1] >= y + h - 3, 0])), float(y + h))  # Use the actual bottom tip instead of the portrait center.
    scene.diagnostics.update(home=scene.home, home_box=scene.home_box)  # Preserve the independently detected account position.


def detect_collectibles(scene: MapImage, manifest: Path) -> None:  # Load all configured visual variants.
    """
    Find multi-scale collectibles while excluding complete interface regions.

    :param scene: Prepared account screenshot to update.
    :param manifest: JSON list of variant definitions.
    :return: None.
    """

    variants = load_variants(manifest)  # Read validated centralized template definitions.
    edges = cv2.cvtColor(scene.image, cv2.COLOR_BGR2GRAY)  # Match artwork luminance independently of hue.
    candidates = []  # Collect template responses before suppression.
    rejected = []  # Preserve excluded UI and duplicate evidence.
    for variant in variants:  # Activate all configured appearances simultaneously.
        template = read_template(manifest.parent / variant["image"])  # Read a small reusable icon asset.
        threshold = float(variant["threshold"])  # Use the variant's documented similarity floor.
        for scale in variant["scales"]:  # Tolerate device rendering and icon-size differences.
            resized = cv2.resize(template, None, fx=float(scale), fy=float(scale))  # Scale visual artwork only.
            h, w = resized.shape[:2]  # Measure candidate bounds.
            if h >= edges.shape[0] or w >= edges.shape[1]:  # Avoid unsupported template dimensions.
                continue  # Skip an oversized scale.
            response = cv2.matchTemplate(edges, cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY), cv2.TM_CCOEFF_NORMED)  # Correlate normalized artwork structure.
            peaks = (response >= threshold) & (response == cv2.dilate(response, np.ones((11, 11), np.uint8)))  # Retain local maxima.
            for y, x in zip(*np.where(peaks), strict=True):  # Process each local response peak.
                point = (float(x + w * variant["anchor"][0]), float(y + h * variant["anchor"][1]))  # Apply the artwork's map anchor.
                item = Detection(point, (int(x), int(y), w, h), variant["name"], float(response[y, x]))  # Preserve variant confidence.
                if np.mean(scene.usable[y:y + h, x:x + w] > 0) < 0.90:  # Allow small crop-padding overlap while rejecting interface artwork.
                    rejected.append({"variant": item.variant, "point": point, "reason": "interface", "confidence": item.confidence})  # Record the rejected map instance.
                else:  # Keep candidates within the usable map.
                    candidates.append(item)  # Defer duplicate suppression until all scales finish.
    accepted = []  # Retain the strongest response at each location.
    for item in sorted(candidates, key=lambda entry: -entry.confidence):  # Prefer the most reliable scale.
        if all(np.linalg.norm(np.subtract(item.point, other.point)) > min(item.box[2], other.box[2]) * 0.6 for other in accepted):  # Suppress overlapping scales and variants.
            accepted.append(item)  # Preserve a unique collectible.
    scene.detections = sorted(accepted, key=lambda item: (item.point[1], item.point[0]))  # Ensure deterministic traversal order.
    scene.diagnostics["collectibles"] = {variant["name"]: sum(item.variant == variant["name"] for item in accepted) for variant in variants}  # Report counts independently.
    scene.diagnostics["rejected_collectibles"] = rejected  # Preserve UI rejection evidence.
    scene.diagnostics["detections"] = [asdict(item) for item in scene.detections]  # Preserve variant confidences and bounds for auditing.


def load_variants(manifest: Path) -> list[dict[str, Any]]:  # Validate replaceable visual definitions centrally.
    """
    Load a nonempty list of usable collectible-template definitions.

    :param manifest: JSON variant manifest path.
    :return: Validated variant definitions.
    """

    variants = json.loads(manifest.read_text(encoding="utf-8"))  # Read configured visual appearances.
    if not isinstance(variants, list) or not variants:  # Require an active detector.
        raise AnalysisError("No collectible variants configured")  # Reject an empty configuration.
    names = set()  # Require unambiguous variant identities.
    for item in variants:  # Validate every configured visual definition.
        if not isinstance(item, dict) or not {"name", "image", "threshold", "scales", "anchor"}.issubset(item):  # Require a complete record.
            raise AnalysisError("Each variant requires name, image, threshold, scales, and anchor")  # Explain the manifest schema.
        if not isinstance(item["name"], str) or not item["name"] or item["name"] in names or not isinstance(item["image"], str):  # Validate unique names and asset paths.
            raise AnalysisError("Variant names must be unique nonempty strings and image must be a path")  # Reject ambiguous configuration.
        names.add(item["name"])  # Reserve the unique variant name.
        values = [item["threshold"]] + (item["scales"] if isinstance(item["scales"], list) else []) + (item["anchor"] if isinstance(item["anchor"], list) else [])  # Collect numerical settings for validation.
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):  # Reject invalid and nonfinite values.
            raise AnalysisError(f"Nonfinite or nonnumeric variant configuration: {item['name']}")  # Identify the invalid variant.
        if not 0 < item["threshold"] <= 1 or not isinstance(item["scales"], list) or not item["scales"] or not all(0.1 <= value <= 5 for value in item["scales"]):  # Bound template scores and resampling dimensions.
            raise AnalysisError(f"Invalid threshold or scales: {item['name']}")  # Reject unsafe matching configuration.
        if not isinstance(item["anchor"], list) or len(item["anchor"]) != 2 or not all(0 <= value <= 1 for value in item["anchor"]):  # Keep the visual anchor inside the artwork.
            raise AnalysisError(f"Invalid normalized anchor: {item['name']}")  # Explain the geometric configuration failure.
    return variants  # Return complete usable definitions.


def read_template(path: Path) -> Image:  # Accept small artwork assets independently of screenshot sizing.
    """
    Read and validate an icon template.

    :param path: Icon asset path.
    :return: Decoded color template.
    """

    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)  # Load a Unicode asset path.
    if image is None or min(image.shape[:2]) < 8:  # Reject empty or unusably small assets.
        raise AnalysisError(f"Invalid collectible template: {path}")  # Identify the broken variant asset.
    if float(np.std(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))) < 5:  # Require usable appearance contrast for normalized correlation.
        raise AnalysisError(f"Collectible template has insufficient visual contrast: {path}")  # Reject uniform artwork that would match everywhere.
    return image  # Return usable artwork.


def stable_mask(scene: MapImage) -> Image:  # Remove dynamic objects before registration.
    """
    Mask collectibles and the profile picture from stable map features.

    :param scene: Prepared and detected account screenshot.
    :return: Stable-map feature mask.
    """

    mask = scene.usable.copy()  # Retain existing interface exclusions.
    for x, y, w, h in [scene.home_box] + [item.box for item in scene.detections]:  # Exclude dynamic marker bounds.
        cv2.rectangle(mask, (x - 10, y - 10), (x + w + 10, y + h + 10), 0, -1)  # Add antialiasing and shadow margin.
    hsv = cv2.cvtColor(scene.image, cv2.COLOR_BGR2HSV)  # Locate saturated annotation ink.
    ink = (((hsv[:, :, 0] < 8) | (hsv[:, :, 0] > 165)) & (hsv[:, :, 1] > 180)).astype(np.uint8)  # Exclude bright red and magenta drawings.
    mask[cv2.dilate(ink, np.ones((9, 9), np.uint8)) > 0] = 0  # Avoid interpreting annotations as anchors.
    return mask  # Return only stable visible map content.
