"""Task 4: HSV segmentation, geometry, smoothing, and morphology."""

import cv2 as cv
import numpy as np

from common import parser, preview, read_image, save_image


def run(args):
    image = read_image(args.assets_dir / "images" / "image.png")
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
    height, width = image.shape[:2]
    translation = np.float32([[1, 0, 100], [0, 1, 50]])
    rotation = cv.getRotationMatrix2D(((width - 1) / 2, (height - 1) / 2), 90, 1)
    # Coordinates refer to the four corners of a block in the bundled image.
    source = np.float32([[273, 42], [406, 46], [268, 124], [406, 130]])
    target = np.float32([[0, 0], [299, 0], [0, 299], [299, 299]])
    perspective = cv.getPerspectiveTransform(source, target)
    smoothing = cv.hconcat([image, cv.blur(image, (5, 5)),
                             cv.GaussianBlur(image, (5, 5), 0),
                             cv.medianBlur(image, 5), cv.bilateralFilter(image, 5, 75, 75)])
    _, binary = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    morphology = cv.hconcat([binary, cv.erode(binary, kernel), cv.dilate(binary, kernel),
                              cv.morphologyEx(binary, cv.MORPH_OPEN, kernel),
                              cv.morphologyEx(binary, cv.MORPH_CLOSE, kernel)])
    results = {
        "hsv_mask.png": mask,
        "hsv_blue.png": cv.bitwise_and(image, image, mask=mask),
        "resize_up.png": cv.resize(image, None, fx=2, fy=2, interpolation=cv.INTER_CUBIC),
        "resize_down.png": cv.resize(image, None, fx=0.5, fy=0.5, interpolation=cv.INTER_AREA),
        "translated.png": cv.warpAffine(image, translation, (width, height)),
        "rotated.png": cv.warpAffine(image, rotation, (width, height)),
        "perspective.png": cv.warpPerspective(image, perspective, (300, 300)),
        "smoothing.png": smoothing, "morphology.png": morphology,
    }
    for name, result in results.items():
        save_image(args.output_dir, name, result)
    preview({"HSV blue": results["hsv_blue.png"], "Morphology": morphology}, args.show)
    return {"images_written": len(results), "blue_pixel_count": int(cv.countNonZero(mask))}


if __name__ == "__main__":
    print(run(parser(__doc__).parse_args()))
