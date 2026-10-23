"""Shared CLI, Unicode-safe image I/O, and optional preview helpers."""

import argparse
from pathlib import Path

import cv2 as cv
import numpy as np

ROOT = Path(__file__).resolve().parent


def parser(description):
    cli = argparse.ArgumentParser(description=description)
    cli.add_argument("--assets-dir", type=Path, default=ROOT,
                     help="Directory containing images/ and videos/ (default: project root)")
    cli.add_argument("--output-dir", type=Path, default=ROOT / "output")
    cli.add_argument("--show", action="store_true", help="Open preview windows; press any key to close")
    return cli


def read_image(path, flags=cv.IMREAD_COLOR):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    image = cv.imdecode(np.fromfile(path, dtype=np.uint8), flags)
    if image is None:
        raise ValueError(f"Unable to decode image: {path}")
    return image


def save_image(output_dir, name, image):
    path = Path(output_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv.imencode(path.suffix, image)
    if not ok:
        raise OSError(f"Unable to encode image: {path}")
    encoded.tofile(path)
    return path


def preview(images, enabled):
    if enabled:
        try:
            for name, image in images.items():
                cv.imshow(name, image)
            cv.waitKey(0)
        finally:
            cv.destroyAllWindows()
