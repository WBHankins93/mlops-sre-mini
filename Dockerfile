FROM python:3.11-slim

ARG MODEL_FILE=model.pkl

# Keep Python predictable in containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install runtime deps first (better layer cache)
COPY app/requirements.txt /app/app/requirements.txt
RUN pip install --no-cache-dir -r /app/app/requirements.txt

# Copy application and baked model
COPY app/ /app/app/
COPY ${MODEL_FILE} /app/model.pkl

EXPOSE 8000

# Serve FastAPI on 0.0.0.0:8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
