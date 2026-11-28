"""Sends live data to a WebSocket server.

Example:

    stream = Stream("ws://localhost:8000/edge")
    stream.send(data)  # bytes, for example a JPEG frame
    stream.close()
"""

import time

from websockets.exceptions import WebSocketException
from websockets.sync.client import ClientConnection, connect


class Stream:
    """A live connection to the server. Reconnects when the connection is lost.

    Data sent while there's no connection is dropped, so it's for live data,
    not for data that must arrive.
    """

    def __init__(self, url: str, retry_seconds: float = 1, compress: bool = True):
        """Send to the server at a WebSocket URL like ws://localhost:8000/edge.

        Without a connection, send() tries to connect again,
        at most once every retry_seconds.
        Turn compress off for data that's already compressed, like JPEG.
        """
        self._url = url
        self._retry_seconds = retry_seconds
        self._compression = "deflate" if compress else None
        self._websocket: ClientConnection | None = None
        self._retry_at = 0.0  # The earliest time.monotonic() to connect again.

    def send(self, data: bytes) -> None:
        """Send data to the server, or drop it if there's no connection."""
        if self._websocket is None:
            self._connect()
        if self._websocket is None:
            return  # Still no connection.
        try:
            self._websocket.send(data)
        except (OSError, WebSocketException) as error:
            self._disconnected(error)

    def close(self) -> None:
        """Close the connection to the server."""
        if self._websocket is not None:
            self._websocket.close()
            self._websocket = None

    def _connect(self) -> None:
        """Connect to the server, but try at most once every retry_seconds."""
        if time.monotonic() < self._retry_at:
            return
        try:
            self._websocket = connect(self._url, compression=self._compression)
        except (OSError, WebSocketException) as error:
            self._disconnected(error)
            return
        print(f"Streaming to {self._url}")

    def _disconnected(self, error: Exception) -> None:
        """Report the lost connection, and connect again only after retry_seconds."""
        print(f"No connection to {self._url}: {error}")
        print(f"Trying again in {self._retry_seconds:g}s...")
        self.close()
        self._retry_at = time.monotonic() + self._retry_seconds
