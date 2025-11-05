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

# Expose port for Railway
EXPOSE 8000

# Start uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
