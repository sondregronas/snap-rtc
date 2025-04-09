# snap-rtc 📸🔥

An unnecessary FastAPI abstraction layer to get snapshots from an WebRTC rawvideo stream 🔥🔥FASTER🔥🔥.

## Why?

Getting images from `rawvideo` formats for Home Assistant automations seem to always be delayed (and the url can be hard to read). 
By keeping the stream open (in a small buffer) and using a simple API, the snapshots should be way faster. (From ~4s to ~0.5s)

## Config

Every camera needs to be added by their go2rtc name to the environment variable `CAMERAS` in a comma separated list.

The RTC_HOST should be pointed to the go2rtc server. The default is `rtsp://127.0.0.1:8554`.

## API

### GET /{camera_id}

Returns a (jpeg) snapshot from the stream.

Example url: http://localhost:8200/Backyard


## Disclaimer

This is a hacky solution to a first world problem. Do not expose to the internet without proper authentication.