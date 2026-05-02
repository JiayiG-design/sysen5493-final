import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from chartaccess.image_audit import audit_png


def write_test_png(path: Path, width: int, height: int, pixels):
    raw_rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend(pixels[y][x])
        raw_rows.append(bytes(row))

    def chunk(name, data):
        payload = name + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
    png.extend(chunk(b"IDAT", zlib.compress(b"".join(raw_rows))))
    png.extend(chunk(b"IEND", b""))
    path.write_bytes(bytes(png))


class ImageAuditTests(unittest.TestCase):
    def test_png_image_with_high_contrast_marks_passes_core_checks(self):
        width, height = 40, 30
        white = (255, 255, 255)
        blue = (0, 90, 181)
        black = (0, 0, 0)
        pixels = [[white for _ in range(width)] for _ in range(height)]
        for y in range(10, 20):
            for x in range(8, 32):
                pixels[y][x] = blue
        for y in range(3, 6):
            for x in range(4, 25):
                pixels[y][x] = black

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "chart.png"
            write_test_png(path, width, height, pixels)
            findings, metadata = audit_png(path)

        self.assertEqual(metadata["background"], "#ffffff")
        self.assertGreaterEqual(metadata["score"]["passed"], 3)
        self.assertTrue(any(color in metadata["prominent_colors"] for color in ["#000000", "#0060c0"]))
        self.assertTrue(any("contrast" in finding.requirement.lower() for finding in findings))

    def test_png_image_with_low_contrast_content_fails_contrast(self):
        width, height = 30, 20
        white = (255, 255, 255)
        pale = (245, 245, 170)
        pixels = [[white for _ in range(width)] for _ in range(height)]
        for y in range(5, 15):
            for x in range(5, 25):
                pixels[y][x] = pale

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "chart.png"
            write_test_png(path, width, height, pixels)
            findings, _ = audit_png(path)

        contrast_finding = next(
            finding for finding in findings if finding.requirement.startswith("Prominent chart colors")
        )
        self.assertFalse(contrast_finding.passed)


if __name__ == "__main__":
    unittest.main()
