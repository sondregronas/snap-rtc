FROM python:3.12-alpine AS runtime

WORKDIR /app

# Install ffmpeg
RUN apk add --no-cache ffmpeg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "snaprtc.py"]