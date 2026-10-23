"""Build README galleries and an animated preview from actual experiment output.

Run `python run.py --extract-every 30` first. Pillow is required for GIF output.
If ffmpeg is installed, also encode a browser-friendly H.264 MP4 demonstration.
"""

from pathlib import Path
import shutil
import subprocess
import sys

import cv2 as cv
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common import read_image, save_image  # noqa: E402

OUTPUT = ROOT / "output"
DEST = ROOT / "docs" / "results"


def gallery(name, panels, columns=3, tile_width=440, tile_height=320):
    """Letterbox images so comparisons never crop or stretch algorithm outputs."""
    label_height = 42
    rows = (len(panels) + columns - 1) // columns
    canvas = np.full((rows * (tile_height + label_height), columns * tile_width, 3),
                     (24, 28, 35), np.uint8)
    for index, (label, image) in enumerate(panels):
        if isinstance(image, (str, Path)):
            image = read_image(image)
        if image.ndim == 2:
            image = cv.cvtColor(image, cv.COLOR_GRAY2BGR)
        scale = min((tile_width - 20) / image.shape[1], (tile_height - 16) / image.shape[0])
        image = cv.resize(image, None, fx=scale, fy=scale, interpolation=cv.INTER_AREA)
        row, col = divmod(index, columns)
        x = col * tile_width + (tile_width - image.shape[1]) // 2
        y = row * (tile_height + label_height) + label_height + (tile_height - image.shape[0]) // 2
        canvas[y:y + image.shape[0], x:x + image.shape[1]] = image
        cv.putText(canvas, label, (col * tile_width + 12, row * (tile_height + label_height) + 28),
                   cv.FONT_HERSHEY_SIMPLEX, 0.56, (225, 232, 240), 1, cv.LINE_AA)
    save_image(DEST, name, canvas)


def result(name):
    return OUTPUT / name


def split_strip(name, labels):
    image = read_image(result(name))
    if image.shape[1] % len(labels):
        raise ValueError(f"Cannot split comparison strip: {name}")
    return list(zip(labels, np.hsplit(image, len(labels))))


def video_previews():
    source = result("annotated_video.mp4")
    capture = cv.VideoCapture(str(source))
    frames = []
    snapshots = []
    try:
        if not capture.isOpened():
            raise OSError(f"Run the video task first: {source}")
        fps = capture.get(cv.CAP_PROP_FPS)
        frame_count = int(capture.get(cv.CAP_PROP_FRAME_COUNT))
        sample_frames = {0, frame_count // 2, frame_count - 1}
        index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if index in sample_frames:
                snapshots.append((f"Frame {index + 1} / {index / fps:.2f}s", frame.copy()))
            if index / fps < 8 and index >= round(len(frames) * fps / 8):
                width = 360
                height = round(frame.shape[0] * width / frame.shape[1])
                small = cv.resize(frame, (width, height), interpolation=cv.INTER_AREA)
                # Redraw the actual frame index for readability in the small GIF.
                cv.rectangle(small, (0, 0), (width, 27), (24, 28, 35), -1)
                cv.putText(small, f"Frame {index + 1} | {index / fps:.2f}s", (8, 19),
                           cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv.LINE_AA)
                frames.append(Image.fromarray(cv.cvtColor(small, cv.COLOR_BGR2RGB)))
            index += 1
    finally:
        capture.release()
    if not frames:
        raise ValueError("No preview frames were decoded")
    durations = [round((i + 1) * 12.5) * 10 - round(i * 12.5) * 10 for i in range(len(frames))]
    frames[0].save(DEST / "task2_video.gif", save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    gallery("task2_frames.png", snapshots, tile_height=390)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "26",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        str(DEST / "task2_annotated.mp4")], check=True)
    else:
        print("ffmpeg is unavailable; GIF and galleries generated, H.264 MP4 skipped.")


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    gallery("task1_drawing.png", [
        ("01  Drawing primitives", result("canvas.png")),
        ("02  Grayscale conversion", result("cat_gray.png")),
        ("03  Manual annotation", result("cat_with_rectangle.png"))])
    video_previews()
    gallery("task3_core.png", [
        ("01  ROI copy", result("roi_copy.png")),
        ("02  Blue channel inverted", result("blue_inverted.png")),
        ("03  Weighted blend: 0.3 / 0.7", result("blended.png")),
        ("04  Circular ROI mask", result("masked_roi.png"))], columns=2)
    gallery("task3_channels.png", [(f"0{i}  {label} channel", result(f"channel_{color}.png"))
                                   for i, label, color in [(1, "Blue", "blue"), (2, "Green", "green"), (3, "Red", "red")]])
    gallery("task3_arithmetic.png", [
        ("01  OpenCV: saturated addition", result("addition_saturated.png")),
        ("02  NumPy: uint8 wraparound", result("addition_wrapped.png")),
        ("03  Weighted blend", result("blended.png"))])
    gallery("task3_borders_gray.png", [
        ("01  Constant border", result("border_constant.png")),
        ("02  Reflect border", result("border_reflect.png")),
        ("03  Manual gray: 64 x 64", result("gray_manual.png")),
        ("04  OpenCV gray: 64 x 64", result("gray_opencv.png"))], columns=2)
    gallery("task4_geometry.png", [
        ("01  Input image", ROOT / "images" / "image.png"),
        ("02  HSV blue segmentation", result("hsv_blue.png")),
        ("03  HSV binary mask", result("hsv_mask.png")),
        ("04  Translation: (100, 50)", result("translated.png")),
        ("05  Rotation: 90 degrees", result("rotated.png")),
        ("06  Perspective: 300 x 300", result("perspective.png"))])
    gallery("task4_resize.png", [
        ("01  Input image", ROOT / "images" / "image.png"),
        ("02  Cubic resize: 2x", result("resize_up.png")),
        ("03  Area resize: 0.5x", result("resize_down.png"))])
    gallery("task4_smoothing.png", split_strip("smoothing.png", [
        "01  Input", "02  Mean blur", "03  Gaussian blur", "04  Median blur", "05  Bilateral filter"]),
        columns=5, tile_width=300, tile_height=290)
    gallery("task4_morphology.png", split_strip("morphology.png", [
        "01  Binary", "02  Erosion", "03  Dilation", "04  Opening", "05  Closing"]),
        columns=5, tile_width=300, tile_height=290)
    gallery("task5_contours.png", [
        ("01  All contours", result("contours.png")),
        ("02  Area > 100 px^2", result("contours_filtered.png")),
        ("03  Largest contour", result("contours_largest.png")),
        ("04  Axis-aligned / rotated boxes", result("contour_boxes.png"))], columns=2)
    gallery("task5_gradients.png", split_strip("gradients.png", [
        "01  Grayscale", "02  Sobel X", "03  Sobel Y", "04  Laplacian"]),
        columns=4, tile_width=330)
    canny = split_strip("canny_50_150.png", ["Gray", "Gaussian", "01  Canny: 50 / 150"])[2]
    stricter = split_strip("canny_100_200.png", ["Gray", "Gaussian", "02  Canny: 100 / 200"])[2]
    gallery("task5_canny.png", [canny, stricter], columns=2)
    gallery("task5_pyramid_histogram.png",
            split_strip("pyramid.png", ["01  Input", "02  Pyramid reconstruction"]) +
            split_strip("histogram_equalized.png", ["03  Grayscale", "04  Histogram equalization"]),
            columns=2)
    gallery("task5_matching.png", split_strip("template_matching.png", [
        "01  Template (top-left)", "02  Best matching location"]), columns=2)
    gallery("task5_hough.png", [
        ("01  Hough line segments", result("hough_lines.jpg")),
        ("02  Hough circle candidates", result("hough_circles.jpg"))], columns=2, tile_height=390)
    print(f"Showcase generated: {DEST}")


if __name__ == "__main__":
    main()
