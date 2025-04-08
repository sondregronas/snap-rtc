FROM python:3.12 AS builder

WORKDIR /app

COPY requirements.txt .
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app

# Install ffmpeg
RUN apt-get update && \
    apt-get install --no-install-recommends -y ffmpeg  && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/venv /app/venv
COPY . .

CMD ["venv/bin/python", "snaprtc.py"]