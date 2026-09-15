FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser && mkdir -p /app/data && chown appuser:appuser /app/data
COPY backend/app ./app
COPY demo /demo
USER appuser
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--workers", "1"]
