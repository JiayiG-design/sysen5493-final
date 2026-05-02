"""Small dependency-free PNG reader for exported chart images."""

from __future__ import annotations

import struct
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class PngImage:
    """Decoded 8-bit PNG image pixels."""

    width: int
    height: int
    pixels: list[tuple[int, int, int]]

    def pixel(self, x: int, y: int) -> tuple[int, int, int]:
        return self.pixels[y * self.width + x]


def read_png(path: str | Path) -> PngImage:
    """Read a non-interlaced 8-bit grayscale, RGB, or RGBA PNG."""
    data = Path(path).read_bytes()
    return decode_png(data)


def decode_png(data: bytes) -> PngImage:
    """Decode a small subset of PNG used by normal chart exports."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("Only PNG images are supported.")

    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    compressed = bytearray()

    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None:
        raise ValueError("PNG is missing an IHDR chunk.")
    if bit_depth != 8:
        raise ValueError("Only 8-bit PNG images are supported.")
    if color_type not in (0, 2, 6):
        raise ValueError("Only grayscale, RGB, and RGBA PNG images are supported.")
    if interlace:
        raise ValueError("Interlaced PNG images are not supported.")

    channels = {0: 1, 2: 3, 6: 4}[color_type]
    stride = width * channels
    raw = zlib.decompress(bytes(compressed))
    rows = []
    previous = [0] * stride
    cursor = 0

    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        row = list(raw[cursor : cursor + stride])
        cursor += stride
        recon = _unfilter(row, previous, channels, filter_type)
        rows.append(recon)
        previous = recon

    pixels: list[tuple[int, int, int]] = []
    for row in rows:
        for index in range(0, len(row), channels):
            if color_type == 0:
                gray = row[index]
                pixels.append((gray, gray, gray))
            else:
                pixels.append((row[index], row[index + 1], row[index + 2]))

    return PngImage(width=width, height=height, pixels=pixels)


def _unfilter(row: list[int], previous: list[int], channels: int, filter_type: int) -> list[int]:
    if filter_type == 0:
        return row

    recon = [0] * len(row)
    for index, value in enumerate(row):
        left = recon[index - channels] if index >= channels else 0
        up = previous[index] if previous else 0
        upper_left = previous[index - channels] if previous and index >= channels else 0

        if filter_type == 1:
            recon[index] = (value + left) & 0xFF
        elif filter_type == 2:
            recon[index] = (value + up) & 0xFF
        elif filter_type == 3:
            recon[index] = (value + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            recon[index] = (value + _paeth(left, up, upper_left)) & 0xFF
        else:
            raise ValueError(f"Unsupported PNG filter type: {filter_type}")
    return recon


def _paeth(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to a hex color."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def quantized_color(rgb: tuple[int, int, int], step: int = 32) -> tuple[int, int, int]:
    """Snap RGB values to a color bucket for palette estimation."""
    return tuple(min(255, round(channel / step) * step) for channel in rgb)


def most_common_color(pixels: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Return the most frequent quantized color in a list of pixels."""
    if not pixels:
        raise ValueError("Cannot estimate color from an empty image.")
    return Counter(quantized_color(pixel) for pixel in pixels).most_common(1)[0][0]
