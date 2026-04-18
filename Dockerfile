FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/vishalkonduru/devops-dashboard
LABEL org.opencontainers.image.description="Personal DevOps Dashboard"

WORKDIR /app

# Install deps first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py \
    FLASK_DEBUG=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 60 app:app
