"""Task 1: image loading, grayscale conversion, drawing, and annotation."""

import cv2 as cv
import numpy as np

from common import parser, preview, read_image, save_image


def run(args):
    image = read_image(args.assets_dir / "images" / "cat.png")
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    canvas = np.zeros((512, 512, 3), np.uint8)
    cv.line(canvas, (10, 5), (416, 511), (255, 0, 0), 5)
    cv.rectangle(canvas, (384, 0), (510, 128), (0, 255, 0), 3)
    cv.circle(canvas, (447, 63), 63, (0, 0, 255), -1)
    cv.ellipse(canvas, (256, 256), (100, 50), 0, 0, 360, (255, 255, 255), -1)
    points = np.array([[10, 5], [100, 80], [100, 120], [50, 100]], np.int32)
    cv.polylines(canvas, [points], True, (0, 255, 255), 5)
    cv.putText(canvas, "I'm Nailoong", (10, 500), cv.FONT_HERSHEY_SIMPLEX,
               1.7, (0, 255, 0), 3, cv.LINE_AA)
    height, width = image.shape[:2]
    cv.rectangle(image, (20, 50), (width - 24, height - 24), (0, 255, 255), 5)
    # This is a drawing exercise: the box is manually specified, not model output.
    cv.putText(image, "Manual annotation", (30, 40), cv.FONT_HERSHEY_SIMPLEX,
               0.8, (0, 255, 255), 2, cv.LINE_AA)
    results = {"canvas.png": canvas, "cat_gray.png": gray,
               "cat_with_rectangle.png": image}
    for name, result in results.items():
        save_image(args.output_dir, name, result)
    preview(results, args.show)
    return {"images_written": len(results)}


if __name__ == "__main__":
    print(run(parser(__doc__).parse_args()))
