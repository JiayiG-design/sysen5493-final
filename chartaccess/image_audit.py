"""Image-based chart accessibility audit."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .audit import AuditFinding, summarize
from .color import contrast_ratio
from .png_image import PngImage, most_common_color, quantized_color, read_png, rgb_to_hex

MIN_IMAGE_CONTRAST = 3.0
MIN_TEXTLIKE_PIXEL_SHARE = 0.01
MAX_LOW_CONTRAST_SHARE = 0.35


def audit_png(path: str | Path) -> tuple[list[AuditFinding], dict[str, object]]:
    """Audit an uploaded PNG chart image and return findings plus extracted metadata."""
    image = read_png(path)
    return audit_image(image)


def audit_image(image: PngImage) -> tuple[list[AuditFinding], dict[str, object]]:
    """Estimate accessibility signals directly from decoded PNG pixels."""
    background_rgb = _estimate_background(image)
    background_hex = rgb_to_hex(background_rgb)
    palette = _estimate_palette(image, background_rgb)
    palette_hex = [rgb_to_hex(color) for color in palette]
    contrast_values = [contrast_ratio(color, background_hex) for color in palette_hex]

    low_contrast = [
        f"{color} ({ratio:.2f}:1)"
        for color, ratio in zip(palette_hex, contrast_values)
        if ratio < MIN_IMAGE_CONTRAST
    ]
    textlike_share = _textlike_pixel_share(image, background_hex)
    low_contrast_share = _low_contrast_pixel_share(image, background_hex)

    findings = [
        AuditFinding(
            "Uploaded chart has enough non-background content to audit",
            len(palette_hex) >= 1,
            f"Detected {len(palette_hex)} prominent non-background color(s).",
        ),
        AuditFinding(
            "Prominent chart colors meet minimum contrast against the estimated background",
            not low_contrast,
            "Low-contrast prominent colors: " + ", ".join(low_contrast)
            if low_contrast
            else f"Prominent colors meet {MIN_IMAGE_CONTRAST}:1 contrast.",
        ),
        AuditFinding(
            "Chart appears to contain readable text or axis marks",
            textlike_share >= MIN_TEXTLIKE_PIXEL_SHARE,
            f"High-contrast text/mark pixel share is {textlike_share:.1%}; target is at least {MIN_TEXTLIKE_PIXEL_SHARE:.1%}.",
        ),
        AuditFinding(
            "Low-contrast pixels do not dominate the chart",
            low_contrast_share <= MAX_LOW_CONTRAST_SHARE,
            f"Low-contrast non-background pixel share is {low_contrast_share:.1%}; target is at most {MAX_LOW_CONTRAST_SHARE:.0%}.",
        ),
    ]

    metadata = {
        "width": image.width,
        "height": image.height,
        "background": background_hex,
        "prominent_colors": palette_hex,
        "score": summarize(findings),
        "textlike_pixel_share": round(textlike_share, 4),
        "low_contrast_pixel_share": round(low_contrast_share, 4),
        "limitation": "Image mode estimates color and text visibility from pixels; it does not OCR chart titles or axis labels.",
    }
    return findings, metadata


def _estimate_background(image: PngImage) -> tuple[int, int, int]:
    corner_pixels: list[tuple[int, int, int]] = []
    sample_w = max(1, image.width // 10)
    sample_h = max(1, image.height // 10)
    ranges = [
        (range(0, sample_w), range(0, sample_h)),
        (range(image.width - sample_w, image.width), range(0, sample_h)),
        (range(0, sample_w), range(image.height - sample_h, image.height)),
        (range(image.width - sample_w, image.width), range(image.height - sample_h, image.height)),
    ]
    for xs, ys in ranges:
        for y in ys:
            for x in xs:
                corner_pixels.append(image.pixel(x, y))
    return most_common_color(corner_pixels)


def _estimate_palette(image: PngImage, background: tuple[int, int, int], limit: int = 5) -> list[tuple[int, int, int]]:
    counts: Counter[tuple[int, int, int]] = Counter()
    background_bucket = quantized_color(background)
    sample_step = max(1, min(image.width, image.height) // 250)

    for y in range(0, image.height, sample_step):
        for x in range(0, image.width, sample_step):
            bucket = quantized_color(image.pixel(x, y))
            if bucket != background_bucket and _color_distance(bucket, background_bucket) > 35:
                counts[bucket] += 1
    return [color for color, _ in counts.most_common(limit)]


def _textlike_pixel_share(image: PngImage, background_hex: str) -> float:
    total = 0
    strong = 0
    sample_step = max(1, min(image.width, image.height) // 300)
    for y in range(0, image.height, sample_step):
        for x in range(0, image.width, sample_step):
            total += 1
            color_hex = rgb_to_hex(image.pixel(x, y))
            if contrast_ratio(color_hex, background_hex) >= 4.5:
                strong += 1
    return strong / total if total else 0.0


def _low_contrast_pixel_share(image: PngImage, background_hex: str) -> float:
    total_non_background = 0
    low = 0
    background = tuple(int(background_hex[i : i + 2], 16) for i in (1, 3, 5))
    sample_step = max(1, min(image.width, image.height) // 300)
    for y in range(0, image.height, sample_step):
        for x in range(0, image.width, sample_step):
            pixel = image.pixel(x, y)
            if _color_distance(pixel, background) <= 25:
                continue
            total_non_background += 1
            if contrast_ratio(rgb_to_hex(pixel), background_hex) < MIN_IMAGE_CONTRAST:
                low += 1
    return low / total_non_background if total_non_background else 0.0


def _color_distance(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    return sum((a - b) ** 2 for a, b in zip(first, second)) ** 0.5
