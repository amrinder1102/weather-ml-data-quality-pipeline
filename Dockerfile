FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.health_check import HealthCheck; import os; h = HealthCheck(os.getenv('API_KEY'), os.getenv('DB_HOST', 'localhost'), os.getenv('DB_NAME', 'weather_pipeline'), os.getenv('DB_USER', 'postgres'), os.getenv('DB_PASSWORD', '')); h.run_all()[0] or exit(1)"

# Run pipeline
CMD ["python", "run.py"]
