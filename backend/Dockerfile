FROM python:3.12-slim

WORKDIR /app

# Dependencias primero (mejor cache de capas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la app.
COPY app ./app

# El host (Render/Railway) inyecta $PORT.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
