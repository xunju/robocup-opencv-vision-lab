"""Regression checks for numerical semantics, empty detections, and CLI output."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cv2 as cv
import numpy as np

from common import ROOT, read_image, save_image
from task3_core import invert_blue
from task5_advanced import contour_results, hough_results


class VisionTests(unittest.TestCase):
    def test_saturated_and_wrapped_addition(self):
        a = np.array([[250]], np.uint8)
        b = np.array([[10]], np.uint8)
        self.assertEqual(int(cv.add(a, b)[0, 0]), 255)
        self.assertEqual(int((a + b)[0, 0]), 4)

    def test_blue_inversion_preserves_other_channels_and_input(self):
        source = np.array([[[0, 25, 50], [255, 30, 60]]], np.uint8)
        original = source.copy()
        result = invert_blue(source)
        np.testing.assert_array_equal(result[:, :, 0], [[255, 0]])
        np.testing.assert_array_equal(result[:, :, 1:], source[:, :, 1:])
        np.testing.assert_array_equal(source, original)

    def test_unicode_image_roundtrip_and_missing_input(self):
        with tempfile.TemporaryDirectory() as directory:
            image = np.full((16, 20, 3), (10, 20, 30), np.uint8)
            path = save_image(Path(directory) / "测试图片", "结果.png", image)
            np.testing.assert_array_equal(read_image(path), image)
            with self.assertRaises(FileNotFoundError):
                read_image(Path(directory) / "missing.png")

    def test_empty_contours_and_known_area(self):
        blank = np.full((100, 100), 255, np.uint8)
        results, metrics = contour_results(blank)
        self.assertEqual(metrics["contours_total"], 0)
        self.assertEqual(metrics["largest_contour_area"], 0)
        self.assertEqual(len(results), 4)
        blank[20:61, 10:41] = 0
        _, metrics = contour_results(blank)
        self.assertEqual(metrics["contours_total"], 1)
        self.assertEqual(metrics["largest_contour_area"], 1200.0)

    def test_empty_hough_does_not_crash(self):
        blank = np.zeros((100, 100, 3), np.uint8)
        results, metrics = hough_results(blank)
        self.assertEqual(metrics, {"hough_lines": 0, "hough_circles": 0})
        for image in results.values():
            np.testing.assert_array_equal(image, blank)

    def test_cli_all_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "结果"
            completed = subprocess.run(
                [sys.executable, str(ROOT / "run.py"), "--output-dir", str(output),
                 "--max-frames", "12", "--extract-every", "5"],
                cwd=directory, capture_output=True, text=True, timeout=120)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(set(report["tasks"]), {"1", "2", "3", "4", "5"})
            self.assertEqual(report["tasks"]["2"]["frames_written"], 12)
            self.assertEqual(report["tasks"]["2"]["frames_extracted"], 2)
            self.assertEqual(len(list((output / "frames").glob("*.png"))), 2)
            self.assertLessEqual(report["tasks"]["3"]["gray_max_difference"], 1)
            self.assertGreater(report["tasks"]["5"]["template_score"], 0.99)
            self.assertEqual(report["tasks"]["5"]["template_location"], [65, 275])
            images = [path for path in output.iterdir() if path.suffix in {".png", ".jpg"}]
            expected = sum(report["tasks"][task]["images_written"] for task in ["1", "3", "4", "5"])
            self.assertEqual(len(images), expected)
            for path in images:
                self.assertGreater(read_image(path).size, 0)
            capture = cv.VideoCapture(str(output / "annotated_video.mp4"))
            try:
                decoded = 0
                while capture.read()[0]:
                    decoded += 1
                self.assertEqual(decoded, 12)
            finally:
                capture.release()


if __name__ == "__main__":
    unittest.main()
