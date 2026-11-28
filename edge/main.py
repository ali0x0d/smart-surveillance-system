"""Runs the edge device: streams the camera's live video to the server.

    python main.py

The settings are read from .env next to this file; .env.example lists them.
Without .env, it streams to the server on this computer.
"""

import os
from pathlib import Path

import cv2
from dotenv import load_dotenv

from camera import Camera
from stream import Stream

ENV_FILE = Path(__file__).parent / ".env"
JPEG_QUALITY = 80  # Lower means less data to send, but a blurrier picture.
RETRY_SECONDS = 2  # How long to wait before connecting to the server again.


def to_jpeg(frame, quality: int) -> bytes:
    """Encode a frame as JPEG, with a quality from 0 to 100."""
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("Could not encode the frame as JPEG")
    return buffer.tobytes()


def main() -> None:
    load_dotenv(ENV_FILE)
    address = os.environ.get("SERVER_ADDRESS", "localhost:8000")

    camera = Camera()
    # JPEG is already compressed, so compressing it again would only cost CPU time.
    stream = Stream(f"ws://{address}/edge", retry_seconds=RETRY_SECONDS, compress=False)
    try:
        while True:
            frame = camera.read()
            stream.send(to_jpeg(frame, JPEG_QUALITY))
    except KeyboardInterrupt:
        pass  # Stop quietly on Ctrl+C.
    finally:
        stream.close()
        camera.close()


if __name__ == "__main__":
    main()
