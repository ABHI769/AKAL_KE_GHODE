FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Render sets the PORT env variable automatically
ENV PORT=10000

EXPOSE ${PORT}

# Use gunicorn with eventlet worker for Socket.IO support
CMD gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:${PORT} server:app
