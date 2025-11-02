FROM python:3.11-slim

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto 5011
EXPOSE 5011

# Comando de inicio
CMD ["gunicorn", "--bind", "0.0.0.0:5011", "--workers", "2", "--timeout", "120", "run:app"]
