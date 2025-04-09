import os
import subprocess
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response

RTC_HOST = os.getenv("RTC_HOST", "rtsp://127.0.0.1:8554")
CAMERAS = os.getenv("CAMERAS", "").split(",")

print(f"RTC_HOST: {RTC_HOST}")
print(f"CAMERAS: {CAMERAS}")

if CAMERAS == [""]:
    raise ValueError(
        "No cameras specified. Set the CAMERAS environment variable with a comma-separated list of camera names."
    )

latest_frames = {}
frame_lock = threading.Lock()


def ffmpeg_reader(camera_name: str):
    """
    Opens the RTSP stream for the given camera using ffmpeg. If the process ends (e.g., due to a disconnect),
    the function restarts the FFmpeg process.
    """
    while True:
        stream_url = f"{RTC_HOST}/{camera_name}"
        cmd = [
            "ffmpeg",
            "-rtsp_transport",
            "tcp",
            "-i",
            stream_url,
            "-vf",
            "fps=1",
            "-f",
            "mjpeg",
            "pipe:1",
        ]

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        if process.stdout is None:
            print(f"Failed to open stream for camera {camera_name}")
            time.sleep(5)
            continue

        print(f"Started FFmpeg process for camera {camera_name}")
        buffer = bytearray()
        SOI = b"\xff\xd8"  # Start Of Image.
        EOI = b"\xff\xd9"  # End Of Image.
        last_data_time = time.time()
        try:
            while True:
                chunk = process.stdout.read(1024 * 8)
                if chunk:
                    last_data_time = time.time()
                    buffer.extend(chunk)
                else:
                    # If no data is received for a while, break to restart process.
                    if time.time() - last_data_time > 5:
                        print(
                            f"No data received for camera {camera_name}, restarting FFmpeg process."
                        )
                        process.kill()
                        break
                    time.sleep(0.1)
                    continue

                while True:
                    # Look for a complete JPEG image in the buffer.
                    start = buffer.find(SOI)
                    if start == -1:
                        break  # No start marker found yet.
                    end = buffer.find(EOI, start + 2)
                    if end == -1:
                        break  # End marker not found; wait for more data.
                    end += 2
                    jpeg_bytes = bytes(buffer[start:end])
                    buffer = buffer[end:]

                    with frame_lock:
                        latest_frames[camera_name] = jpeg_bytes
        except Exception as e:
            print(f"Error processing stream for camera {camera_name}: {e}")
            process.kill()

        # Wait briefly before restarting the process.
        time.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager. Starts background threads for each camera
    when the app starts up and performs any cleanup on shutdown if needed.
    """
    for camera in CAMERAS:
        thread = threading.Thread(target=ffmpeg_reader, args=(camera,), daemon=True)
        thread.start()
        print(f"Started background FFmpeg thread for camera: {camera}")
    yield
    print("Shutting down application.")


app = FastAPI(lifespan=lifespan)


@app.get("/{camera_name}")
def get_latest_frame(camera_name: str):
    """
    Endpoint that returns the most recent JPEG image for the requested camera.
    """
    if camera_name not in CAMERAS:
        raise HTTPException(status_code=404, detail="Camera not found")

    with frame_lock:
        frame = latest_frames.get(camera_name)

    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available yet")

    return Response(content=frame, media_type="image/jpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
