import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, HTTPException

# Environment Variables
RTC_HOST = os.getenv("RTC_HOST", "rtsp://127.0.0.1:8554")
CAMERAS = os.getenv("CAMERAS", "").split(",")  # e.g., "Camera1,Camera2" for preloading
FPS = int(os.getenv("FPS", 12))  # Default FPS stream, 12 seems to be a good compromise
QUALITY = int(os.getenv("QUALITY", 8))  # Fast and "Ok" quality

INVOCATION = (
    "ffmpeg -rtsp_transport tcp "
    "-fflags nobuffer "
    "-flags low_delay "
    "-strict experimental "
    "-flags2 +fast "
    "-fflags +discardcorrupt "
    "-analyzeduration 0 "
    "-probesize 32 "
    "-i {input_url} "
    "-f mjpeg "
    f"-q:v {QUALITY} -r {FPS} -update 1 -"
)

# FastAPI Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))


stream_readers = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    for camera in CAMERAS:
        if not camera:
            continue
        print(f"Preloading camera: {camera}")
        await ensure_ffmpeg_stream(camera)

    yield

    for reader in stream_readers.values():
        reader.running = False


app = FastAPI(lifespan=lifespan)


async def ensure_ffmpeg_stream(camera_name: str):
    if camera_name in stream_readers:
        return stream_readers[camera_name]

    input_url = f"{RTC_HOST}/{camera_name}"
    cmd = INVOCATION.format(input_url=input_url)

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    if not process.stdout:
        raise HTTPException(status_code=500, detail="Failed to open ffmpeg stream")

    reader = MJPEGReader(process.stdout)
    stream_readers[camera_name] = reader
    asyncio.create_task(reader.run())
    return reader


class MJPEGReader:
    def __init__(self, stdout):
        self.stdout = stdout
        self.buffer = b""
        self.running = True
        self.latest_frame = None
        self.frame_event = asyncio.Event()
        self.max_buffer_size = 0
        self._frame_samples = []

    async def run(self):
        try:
            while self.running:
                chunk = await self.stdout.read(max(self.max_buffer_size, 4096))
                if not chunk:
                    break

                self.buffer += chunk

                if len(self.buffer) > self.max_buffer_size > 0:
                    self.buffer = b""

                lf = None
                while True:
                    start = self.buffer.find(b"\xff\xd8")
                    end = self.buffer.find(b"\xff\xd9", start)
                    if start != -1 and end != -1 and end > start:
                        frame = self.buffer[start : end + 2]
                        self.buffer = self.buffer[end + 2 :]

                        # Set the max buffer to 1.2x the size of the last frame
                        self.max_buffer_size = max(
                            int(len(frame) * 1.2), self.max_buffer_size
                        )

                        lf = frame
                    else:
                        await asyncio.sleep(0.01)  # Yield control to avoid busy waiting
                        break
                if lf:
                    self.latest_frame = lf
                    self.frame_event.set()
        except Exception as e:
            print(f"[MJPEGReader] Error: {e}")

    async def get_fresh_frame(self, timeout=1, _attempts=0):
        try:
            await asyncio.wait_for(self.frame_event.wait(), timeout)
            self.frame_event.clear()
            return self.latest_frame
        except asyncio.TimeoutError:
            if _attempts > 15:
                raise HTTPException(
                    status_code=504, detail="Timeout waiting for fresh frame"
                )
            else:
                return await self.get_fresh_frame(timeout, _attempts + 1)


@app.get("/{camera_name}")
async def snap_frame(camera_name: str):
    reader = await ensure_ffmpeg_stream(camera_name)
    frame = await reader.get_fresh_frame()
    return Response(content=frame, media_type="image/jpeg")


@app.get("/start/{camera_name}")
async def start_stream(camera_name: str):
    await ensure_ffmpeg_stream(camera_name)
    return {"status": "stream started", "camera_name": camera_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
