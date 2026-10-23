"""Task 5: edges, pyramids, contours, histograms, template matching, and Hough."""

import cv2 as cv
import numpy as np

from common import parser, preview, read_image, save_image


def contour_results(gray, min_area=100):
    _, binary = cv.threshold(gray, 127, 255, cv.THRESH_BINARY_INV)
    contours, _ = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    base = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
    all_view, filtered, largest_view, boxes = [base.copy() for _ in range(4)]
    cv.drawContours(all_view, contours, -1, (0, 255, 0), 2)
    selected = [contour for contour in contours if cv.contourArea(contour) > min_area]
    cv.drawContours(filtered, selected, -1, (0, 255, 0), 2)
    area = 0.0
    if contours:
        largest = max(contours, key=cv.contourArea)
        area = cv.contourArea(largest)
        cv.drawContours(largest_view, [largest], -1, (0, 0, 255), 2)
        x, y, width, height = cv.boundingRect(largest)
        cv.rectangle(boxes, (x, y), (x + width, y + height), (0, 255, 0), 2)
        rotated = cv.boxPoints(cv.minAreaRect(largest)).astype(np.int32)
        cv.drawContours(boxes, [rotated], -1, (0, 0, 255), 2)
        cv.putText(boxes, f"Area: {area:.1f} px", (10, 30), cv.FONT_HERSHEY_SIMPLEX,
                   0.7, (0, 180, 0), 2, cv.LINE_AA)
    return {"contours.png": all_view, "contours_filtered.png": filtered,
            "contours_largest.png": largest_view, "contour_boxes.png": boxes}, {
                "contours_total": len(contours), "contours_filtered": len(selected),
                "largest_contour_area": area}


def hough_results(image):
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    edges = cv.Canny(gray, 50, 150)
    lines = cv.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)
    line_view, circle_view = image.copy(), image.copy()
    if lines is not None:
        for x1, y1, x2, y2 in lines.reshape(-1, 4):
            cv.line(line_view, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
    circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, 150, param1=500,
                              param2=120, minRadius=0, maxRadius=0)
    if circles is not None:
        for x, y, radius in np.round(circles[0]).astype(int):
            cv.circle(circle_view, (x, y), radius, (0, 255, 0), 2)
            cv.circle(circle_view, (x, y), 2, (0, 0, 255), 3)
    return {"hough_lines.jpg": line_view, "hough_circles.jpg": circle_view}, {
        "hough_lines": 0 if lines is None else len(lines),
        "hough_circles": 0 if circles is None else len(circles[0])}


def run(args):
    gray = read_image(args.assets_dir / "images" / "image.png", cv.IMREAD_GRAYSCALE)
    gaussian = cv.GaussianBlur(gray, (5, 5), 0)
    results = {"gradients.png": cv.hconcat([
        gray, cv.convertScaleAbs(cv.Sobel(gray, cv.CV_64F, 1, 0, ksize=5)),
        cv.convertScaleAbs(cv.Sobel(gray, cv.CV_64F, 0, 1, ksize=5)),
        cv.convertScaleAbs(cv.Laplacian(gray, cv.CV_64F))])}
    for low, high in [(50, 150), (100, 200)]:
        results[f"canny_{low}_{high}.png"] = cv.hconcat([gray, gaussian, cv.Canny(gaussian, low, high)])
    reconstructed = cv.pyrUp(cv.pyrDown(cv.pyrDown(gray)))
    results["pyramid.png"] = cv.hconcat([gray, cv.resize(reconstructed, (gray.shape[1], gray.shape[0]))])
    contour_images, metrics = contour_results(gray)
    results.update(contour_images)
    equalized = cv.equalizeHist(gray)
    results["histogram_equalized.png"] = cv.hconcat([gray, equalized])
    for name, image in [("original", gray), ("equalized", equalized)]:
        histogram = cv.calcHist([image], [0], None, [256], [0, 256]).ravel()
        metrics[f"{name}_histogram_peak_values"] = np.flatnonzero(histogram == histogram.max()).tolist()
        metrics[f"{name}_histogram_peak_count"] = int(histogram.max())
    # This patch is cropped from the same source: matching is a controlled demo.
    template = gray[275:420, 65:260]
    scores = cv.matchTemplate(gray, template, cv.TM_CCOEFF_NORMED)
    _, score, _, location = cv.minMaxLoc(scores)
    matched = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
    x, y = location
    height, width = template.shape
    cv.rectangle(matched, (x, y), (x + width, y + height), (0, 0, 255), 2)
    template_view = np.zeros_like(matched)
    template_view[:height, :width] = cv.cvtColor(template, cv.COLOR_GRAY2BGR)
    results["template_matching.png"] = cv.hconcat([template_view, matched])
    metrics.update({"template_score": score, "template_location": list(location)})
    hough_images, hough_metrics = hough_results(read_image(args.assets_dir / "images" / "nailoong.png"))
    results.update(hough_images)
    metrics.update(hough_metrics)
    for name, result in results.items():
        save_image(args.output_dir, name, result)
    metrics["images_written"] = len(results)
    preview({"Contours": results["contour_boxes.png"], "Template": results["template_matching.png"]}, args.show)
    return metrics


if __name__ == "__main__":
    print(run(parser(__doc__).parse_args()))
