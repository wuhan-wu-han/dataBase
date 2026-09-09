FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLATFORM_DB_PATH=/app/src/python/data/platform.db

WORKDIR /app

COPY src/python/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY src /app/src
COPY models /app/models
COPY output /app/output

EXPOSE 8000

CMD ["uvicorn", "src.python.main:app", "--host", "0.0.0.0", "--port", "8000"]
