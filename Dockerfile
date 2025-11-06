# Use Python 3.11 slim
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .
COPY run.py .

# Railway fornece PORT dinamicamente
EXPOSE 8000

# Usar script Python que lê PORT programaticamente
CMD ["python", "run.py"]
