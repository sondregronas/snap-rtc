# snap-rtc 📸🔥

An unnecessary FastAPI abstraction layer to get snapshots from an WebRTC stream 🔥🔥FASTER🔥🔥.

## Why?

Getting images for Home Assistant automations seem to always be delayed (and the url can be hard to read). 
By keeping the stream open (in a tiny, dynamically allocated buffer) and using a simple API, the snapshots should be way faster. (From ~4s to ~0.5s)

## API

### GET /{camera_id}

Returns a (jpeg) snapshot from the stream.

Example url: http://localhost:8200/Backyard

### GET /start/{camera_id}
Doesn't return anything, but starts the stream for the given camera. Should be called on startup if the environment variable `CAMERAS` is set.


## Disclaimer

This is a hacky solution to a first world problem. Do not expose to the internet without proper authentication.