"""
================================================================================
Macadam Map Preprocessing
================================================================================
Author      : Breno Farias da Silva
Created     : 2026-10-01
Description :
    Normalize screenshots and exclude visually detected interface panels.

    Key features include:
        - Neutral-white street segmentation across colored map themes.
        - Dynamic panel geometry and configurable analysis resolution.

Usage:
    Call prepare_map from the application pipeline.

Outputs:
    - Normalized image, usable mask, and observed road mask.

Dependencies:
    - Python >= 3.13, OpenCV, NumPy.

Assumptions & Notes:
    - Roads are bright neutral paths; unsupported map styles fail explicitly.
"""

from pathlib import Path  # Accept filesystem inputs.
import cv2  # Perform image segmentation.
import numpy as np  # Manipulate masks.
from settings import AnalysisError, Image, MapImage, Settings  # Share analysis contracts.


def read_image(path: Path) -> Image:  # Load Unicode paths on Windows.
    """
    Decode a color image without modifying the input.

    :param path: Source image path.
    :return: Decoded color pixels.
    """

    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)  # Decode file bytes.
    if image is None or min(image.shape[:2]) < 200:  # Reject unusable screenshots.
        raise AnalysisError(f"Unreadable or too-small screenshot: {path}")  # Explain the input failure.
    return image  # Return valid image data.


def neutral_mask(image: Image, settings: Settings) -> Image:  # Isolate white street interiors.
    """
    Segment neutral bright pixels independently of map hue.

    :param image: Color image to segment.
    :param settings: Saturation and brightness thresholds.
    :return: Binary white-pixel mask.
    """

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  # Separate brightness from hue.
    return ((hsv[:, :, 1] < settings.white_saturation) & (hsv[:, :, 2] > settings.white_value)).astype(np.uint8) * 255  # Retain neutral paths.


def panel_mask(image: Image, white: Image) -> Image:  # Identify overlay geometry dynamically.
    """
    Exclude broad cards, navigation, status content, and floating controls.

    :param image: Normalized screenshot.
    :param white: Neutral bright pixels.
    :return: Mask of usable map pixels.
    """

    height, width = white.shape  # Read normalized geometry.
    usable = np.full_like(white, 255)  # Initially allow the entire image.
    status_contours, _ = cv2.findContours((cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) < 100).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Identify compact status glyphs.
    glyphs = [cv2.boundingRect(contour) for contour in status_contours]  # Measure candidate status components.
    glyphs = [(x, y, w, h) for x, y, w, h in glyphs if y < height * 0.035 and 10 <= h <= 32 and w < width * 0.13]  # Distinguish glyphs from large balance pills and controls.
    if sum(x < width * 0.25 for x, _, _, _ in glyphs) >= 3 and any(x > width * 0.6 for x, _, _, _ in glyphs):  # Require status content on both sides.
        usable[:max(y + h for _, y, _, h in glyphs) + 4] = 0  # Mask the detected status-row extent.
    opened = cv2.morphologyEx(white, cv2.MORPH_OPEN, np.ones((31, 31), np.uint8))  # Remove narrow roads from card candidates.
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Locate broad neutral regions.
    bottom = height  # Infer navigation boundary from broad low cards.
    for contour in contours:  # Inspect each connected panel candidate.
        x, y, w, h = cv2.boundingRect(contour)  # Measure panel geometry.
        if y > height * 0.72 and w > width * 0.3 and h > 35:  # Identify lower promotional or navigation cards.
            bottom = min(bottom, y - 8)  # Exclude all content below the first broad card.
        if w > width * 0.35 and h > 65:  # Exclude broad progress panels.
            cv2.rectangle(usable, (max(0, x - 8), max(0, y - 8)), (x + w + 8, y + h + 8), 0, -1)  # Mask the complete card footprint.
    usable[bottom:] = 0  # Remove the inferred bottom interface.
    contours, _ = cv2.findContours(white, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)  # Locate rounded floating controls.
    for contour in contours:  # Inspect potential control bounds.
        x, y, w, h = cv2.boundingRect(contour)  # Measure each white contour.
        if x > width * 0.78 and y < height * 0.4 and 45 < w < width * 0.16 and 0.7 < w / h < 1.35:  # Recognize the control stack.
            cv2.rectangle(usable, (x - 5, y - 5), (x + w + 5, y + h + 5), 0, -1)  # Remove control artwork.
    dark = (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) < 45).astype(np.uint8)  # Locate black balance pills.
    contours, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Locate connected dark regions.
    for contour in contours:  # Exclude wide upper balance containers.
        x, y, w, h = cv2.boundingRect(contour)  # Read candidate dimensions.
        if y < height * 0.2 and w > width * 0.12 and w > h * 1.6 and h > 25:  # Identify a balance pill rather than a label.
            cv2.rectangle(usable, (x - 5, y - 5), (x + w + 5, y + h + 5), 0, -1)  # Remove all embedded coin artwork.
    return usable  # Return the dynamically excluded map.


def prepare_map(path: Path, settings: Settings) -> MapImage:  # Prepare one account independently.
    """
    Load, normalize, and segment a screenshot.

    :param path: Source screenshot path.
    :param settings: Shared analysis configuration.
    :return: Prepared map image and diagnostic masks.
    """

    original = read_image(path)  # Preserve source resolution.
    height = round(original.shape[0] * settings.width / original.shape[1])  # Preserve aspect ratio.
    image = cv2.resize(original, (settings.width, height), interpolation=cv2.INTER_AREA)  # Normalize analysis scale.
    white = neutral_mask(image, settings)  # Detect neutral road and interface pixels.
    usable = panel_mask(image, white)  # Exclude interface components.
    roads = cv2.bitwise_and(white, usable)  # Limit roads to the usable map.
    fraction = float(np.count_nonzero(usable) / usable.size)  # Quantify available coverage.
    if fraction < 0.15 or np.count_nonzero(roads) < usable.size * 0.01:  # Reject insufficient visible streets.
        raise AnalysisError(f"Unusable map region: usable fraction={fraction:.3f}")  # Report a measurable failure.
    return MapImage(image, usable, roads, original, diagnostics={"usable_fraction": fraction})  # Retain preprocessing evidence.
