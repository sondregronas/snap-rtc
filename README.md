# snap-rtc 📸🔥

An unnecessary FastAPI abstraction layer to get snapshots from an WebRTC rawvideo stream 🔥🔥FASTER🔥🔥.

## Why?

Getting images from `rawvideo` formats, especially on those with a long keyframe interval (such as Unifi Protect cameras) for Home Assistant automations are often delayed (and the url can be hard to read).
By keeping the stream actively open (in a small buffer, running at 1fps) and using a simple API, the snapshots should be way faster. (From ~5s delay to ~0.5s)

## Config

Run with `docker compose up -d --build`
- Every camera needs to be added by their go2rtc name to the environment variable `CAMERAS` in a comma separated list.
- The RTC_HOST should be pointed to the go2rtc server. The default is `rtsp://127.0.0.1:8554`.

## API

### GET /{camera_id}

Returns a (jpeg) snapshot from the stream. The quality isn't great, but passable for a notification thumbnail.

Example url: http://localhost:8200/Backyard


## Disclaimer

This is a hacky solution to a first world problem. Do not expose to the internet without proper authentication.
