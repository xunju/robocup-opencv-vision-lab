"""Task 2: video metadata, frame annotation, optional extraction, and encoding."""

from pathlib import Path

import cv2 as cv

from common import parser, save_image


def video_parser():
    cli = parser(__doc__)
    cli.add_argument("--video", type=Path, help="Override the bundled input video")
    cli.add_argument("--extract-every", type=int, default=0,
                     help="Save every Nth annotated frame; 0 disables extraction")
    cli.add_argument("--max-frames", type=int, default=0,
                     help="Limit processing to N frames; 0 processes the whole video")
    return cli


def run(args):
    if args.extract_every < 0 or args.max_frames < 0:
        raise ValueError("--extract-every and --max-frames must be nonnegative")
    source = args.video if args.video is not None else args.assets_dir / "videos" / "nailoong.mp4"
    capture = cv.VideoCapture(str(source))
    writer = None
    frames = extracted = 0
    try:
        if not capture.isOpened():
            raise OSError(f"Unable to open video: {source}")
        width = int(capture.get(cv.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv.CAP_PROP_FRAME_HEIGHT))
        fps = capture.get(cv.CAP_PROP_FPS)
        if width <= 0 or height <= 0 or not 0 < fps < 1000:
            raise ValueError(f"Invalid video metadata: {width}x{height}, fps={fps}")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        target = args.output_dir / "annotated_video.mp4"
        if source.resolve() == target.resolve():
            raise ValueError("Input video and output video must be different files")
        writer = cv.VideoWriter(str(target), cv.VideoWriter_fourcc(*"mp4v"),
                                fps, (width, height))
        if not writer.isOpened():
            raise OSError(f"Unable to create video writer: {target}")
        while not args.max_frames or frames < args.max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            frames += 1
            cv.putText(frame, f"Frame: {frames}", (10, 30), cv.FONT_HERSHEY_SIMPLEX,
                       0.7, (0, 255, 0), 2, cv.LINE_AA)
            writer.write(frame)
            if args.extract_every and frames % args.extract_every == 0:
                save_image(args.output_dir, f"frames/frame_{frames:04d}.png", frame)
                extracted += 1
            if args.show:
                cv.imshow("Video (q to stop)", frame)
                if cv.waitKey(max(1, round(1000 / fps))) & 0xFF == ord("q"):
                    break
        if not frames:
            raise ValueError(f"No decodable video frames: {source}")
        return {"width": width, "height": height, "fps": fps,
                "frames_written": frames, "frames_extracted": extracted}
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if args.show:
            cv.destroyAllWindows()


if __name__ == "__main__":
    print(run(video_parser().parse_args()))
