# --- Stage 1: Builder ---
# Usamos una imagen completa de Python para instalar dependencias.
FROM python:3.11-slim AS builder

WORKDIR /build

# Copiamos solo requirements.txt primero para aprovechar la cache de Docker
COPY requirements.txt .

# Instalamos dependencias en un directorio temporal.
# --no-cache-dir reduce el tamaño de la imagen.
# --user instala en ~/.local que después copiamos a la imagen final.
RUN pip install --no-cache-dir --user -r requirements.txt


# --- Stage 2: Runtime ---
# Imagen final minimalista, solo con lo necesario para correr la app
FROM python:3.11-slim

# Variables de entorno para Python:
# - PYTHONUNBUFFERED=1: logs en tiempo real (sin buffering)
# - PYTHONDONTWRITEBYTECODE=1: no genera .pyc (reduce tamaño y ruido)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copiamos las dependencias instaladas desde el builder
COPY --from=builder /root/.local /root/.local

# Nos aseguramos de que los binarios instalados estén en el PATH
ENV PATH=/root/.local/bin:$PATH

# Copiamos el código de la aplicación
COPY ./app ./app

# Exponemos el puerto en el que corre uvicorn
EXPOSE 8000

# Comando para arrancar la aplicación.
# --host 0.0.0.0 permite conexiones desde fuera del contenedor.
# --port 8000 es el puerto estándar que exponemos.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]