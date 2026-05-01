"""Color contrast utilities for chart accessibility checks."""

from __future__ import annotations


def normalize_hex(value: str) -> str:
    """Return a six-digit lowercase hex color without the leading hash."""
    raw = value.strip().lower()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6 or any(ch not in "0123456789abcdef" for ch in raw):
        raise ValueError(f"Invalid hex color: {value!r}")
    return raw


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Convert a hex color such as #3366cc to an RGB tuple."""
    raw = normalize_hex(value)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def relative_luminance(value: str) -> float:
    """Calculate WCAG relative luminance for a hex color."""
    def channel(part: int) -> float:
        linear = part / 255
        if linear <= 0.03928:
            return linear / 12.92
        return ((linear + 0.055) / 1.055) ** 2.4

    red, green, blue = hex_to_rgb(value)
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    """Return the WCAG contrast ratio between two hex colors."""
    light = max(relative_luminance(first), relative_luminance(second))
    dark = min(relative_luminance(first), relative_luminance(second))
    return (light + 0.05) / (dark + 0.05)
