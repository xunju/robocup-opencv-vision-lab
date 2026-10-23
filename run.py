"""Run one or all OpenCV exercises and write a machine-readable report."""

import json
import platform

import cv2 as cv
import numpy as np

import task1_gui_draw
import task2_video
import task3_core
import task4_basic
import task5_advanced

TASKS = {"1": task1_gui_draw, "2": task2_video, "3": task3_core,
         "4": task4_basic, "5": task5_advanced}


def main():
    cli = task2_video.video_parser()
    cli.description = __doc__
    cli.add_argument("--task", choices=["all", *TASKS], default="all")
    args = cli.parse_args()
    if args.extract_every < 0 or args.max_frames < 0:
        cli.error("--extract-every and --max-frames must be nonnegative")
    report = {"environment": {"python": platform.python_version(),
                               "opencv": cv.__version__, "numpy": np.__version__}, "tasks": {}}
    selected = TASKS if args.task == "all" else {args.task: TASKS[args.task]}
    for name, module in selected.items():
        print(f"Running task {name}: {module.__name__}", flush=True)
        report["tasks"][name] = module.run(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Completed. Report: {report_path}")


if __name__ == "__main__":
    main()
