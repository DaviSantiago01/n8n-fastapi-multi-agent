# Use Python 3.11 slim para Railway
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for pandas/numpy/scikit-learn
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY vendas_dataset.csv .

# Railway fornece PORT via variável de ambiente
# Usar 8000 como padrão se PORT não estiver definido
ENV PORT=8000

# Expose port
EXPOSE $PORT

# Start uvicorn server usando variável de ambiente
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
