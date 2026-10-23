"""Task 3: pixels, ROI, channels, borders, image arithmetic, and masking."""

from time import perf_counter

import cv2 as cv
import numpy as np

from common import parser, preview, read_image, save_image


def invert_blue(image):
    result = image.copy()
    result[:, :, 0] = 255 - result[:, :, 0]
    return result


def run(args):
    image = read_image(args.assets_dir / "images" / "cat.png")
    image[100, 100] = (255, 255, 255)
    roi_copy = image.copy()
    half = image.shape[1] // 2
    roi_copy[:, half:2 * half] = image[:, :half]
    blue, green, red = cv.split(image)
    first = read_image(args.assets_dir / "images" / "frame_0001.png")
    second = read_image(args.assets_dir / "images" / "frame_0030.png")
    if first.shape != second.shape:
        raise ValueError("Image arithmetic requires equally sized input frames")
    size = min(512, *image.shape[:2])
    mask = np.zeros((size, size), np.uint8)
    cv.circle(mask, (size // 2, size // 2), size // 2, 255, -1)
    results = {
        "roi_copy.png": roi_copy,
        "channel_blue.png": blue, "channel_green.png": green, "channel_red.png": red,
        "blue_inverted.png": invert_blue(image),
        "border_constant.png": cv.copyMakeBorder(image, 10, 10, 10, 10,
                                                   cv.BORDER_CONSTANT, value=(0, 0, 255)),
        "border_reflect.png": cv.copyMakeBorder(image, 10, 10, 10, 10, cv.BORDER_REFLECT),
        "addition_saturated.png": cv.add(first, second),
        "addition_wrapped.png": first + second,
        "blended.png": cv.addWeighted(first, 0.3, second, 0.7, 0),
        "masked_roi.png": cv.bitwise_and(image[:size, :size], image[:size, :size], mask=mask),
    }
    sample = image[:64, :64]
    manual_gray = np.empty(sample.shape[:2], np.uint8)
    start = perf_counter()
    for y in range(sample.shape[0]):
        for x in range(sample.shape[1]):
            b, g, r = map(int, sample[y, x])
            manual_gray[y, x] = int(0.114 * b + 0.587 * g + 0.299 * r)
    manual_ms = (perf_counter() - start) * 1000
    start = perf_counter()
    opencv_gray = cv.cvtColor(sample, cv.COLOR_BGR2GRAY)
    opencv_ms = (perf_counter() - start) * 1000
    results.update({"gray_manual.png": manual_gray, "gray_opencv.png": opencv_gray})
    for name, result in results.items():
        save_image(args.output_dir, name, result)
    preview({"ROI": roi_copy, "Mask": results["masked_roi.png"]}, args.show)
    return {"shape": list(image.shape), "dtype": str(image.dtype),
            "images_written": len(results), "manual_gray_ms": manual_ms,
            "opencv_gray_ms": opencv_ms,
            "gray_max_difference": int(np.abs(manual_gray.astype(int) - opencv_gray).max())}


if __name__ == "__main__":
    print(run(parser(__doc__).parse_args()))
