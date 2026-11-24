"""A simple camera, built on OpenCV.

Example:

    camera = Camera()                    # or Camera(1), Camera("/dev/video2")
    camera.take_picture("photo.jpg")
    camera.record_video(10, "clip.mp4")  # 10 seconds
    camera.preview()
    camera.close()

Run it to try the camera:

    python camera.py                     # show the live video in a window
    python camera.py picture             # take a picture to picture.jpg
    python camera.py picture photo.jpg   # take a picture to photo.jpg
    python camera.py video               # record a 5-second video to video.mp4
    python camera.py video 10            # record a 10-second video to video.mp4
    python camera.py video 10 clip.mp4   # record a 10-second video to clip.mp4
"""

import argparse
import os
import sys
import time

import cv2


class Camera:
    def __init__(self, source: int | str = 0):
        """Open a camera by index (0, 1, ...) or by device path."""
        self._capture = cv2.VideoCapture(source)
        if not self._capture.isOpened():
            raise RuntimeError(f"Could not open camera {source!r}")

    def read(self):
        """Return the next frame from the camera."""
        ok, frame = self._capture.read()
        if not ok:
            raise RuntimeError("Could not read a frame from the camera")
        return frame

    def take_picture(self, path: str = "picture.jpg") -> None:
        """Save a picture, for example picture.jpg or picture.png."""
        self._warm_up()
        if not cv2.imwrite(path, self.read()):
            raise RuntimeError(f"Could not save {path}")

    def record_video(self, seconds: float, path: str = "video.mp4") -> None:
        """Record a video of the given number of seconds to an .mp4 file."""
        fps = self._warm_up()
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(path, codec, fps, (width, height))
        if not writer.isOpened():
            raise RuntimeError(f"Could not create {path}")
        try:
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                writer.write(self.read())
        finally:
            writer.release()  # Also saves the video if recording is interrupted.

    def preview(self) -> None:
        """Show the live video in a window. Press q or close the window to stop."""
        while True:
            cv2.imshow("Camera", self.read())
            key = cv2.waitKey(1) & 0xFF
            try:
                closed = cv2.getWindowProperty("Camera", cv2.WND_PROP_VISIBLE) < 1
            except cv2.error:  # OpenCV's Qt version raises once the window is closed.
                closed = True
            if key == ord("q") or closed:
                break
        cv2.destroyAllWindows()

    def close(self) -> None:
        """Close the camera."""
        self._capture.release()

    def _warm_up(self, seconds: float = 1) -> float:
        """Read frames for a moment, so the camera can adjust its exposure.

        Returns the measured frame rate.
        """
        self.read()  # The first frame can be slow, so start timing after it.
        frames = 0
        start = time.monotonic()
        while time.monotonic() - start < seconds:
            self.read()
            frames += 1
        return frames / (time.monotonic() - start)


def main() -> None:
    parser = argparse.ArgumentParser(description="Try the camera.")
    actions = parser.add_subparsers(dest="action")
    actions.add_parser("preview", help="show the live video in a window (default)")
    picture = actions.add_parser("picture", help="take a picture")
    picture.add_argument(
        "file",
        nargs="?",
        default="picture.jpg",
        help="file name (default: picture.jpg)",
    )
    video = actions.add_parser("video", help="record a video")
    video.add_argument(
        "seconds", nargs="?", type=float, default=5, help="video length (default: 5)"
    )
    video.add_argument(
        "file", nargs="?", default="video.mp4", help="file name (default: video.mp4)"
    )
    args = parser.parse_args()
    # OpenCV's windows need DISPLAY on Linux; without it, OpenCV crashes.
    no_screen = sys.platform == "linux" and not os.environ.get("DISPLAY")
    if args.action in (None, "preview") and no_screen:
        parser.error("no screen to show the video on; use picture or video instead")
    if args.action == "video" and args.seconds <= 0:
        video.error("seconds must be more than 0")

    camera = Camera()
    try:
        if args.action == "picture":
            camera.take_picture(args.file)
            print(f"Saved {args.file}")
        elif args.action == "video":
            print(f"Recording a {args.seconds:g}-second video...")
            camera.record_video(args.seconds, args.file)
            print(f"Saved {args.file}")
        else:
            camera.preview()
    except KeyboardInterrupt:
        pass  # Stop quietly on Ctrl+C.
    finally:
        camera.close()


if __name__ == "__main__":
    main()
