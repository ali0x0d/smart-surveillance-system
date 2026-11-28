"""The server: receives the live video from the edge device."""

from fastapi import FastAPI, WebSocket

app = FastAPI()


@app.websocket("/edge")
async def edge(websocket: WebSocket) -> None:
    """Receive JPEG frames from the edge device."""
    await websocket.accept()
    # One message is one frame. The loop ends when the edge device disconnects.
    async for frame in websocket.iter_bytes():
        print(f"Frame from the edge: {len(frame)} bytes")
    print("The edge device disconnected")
