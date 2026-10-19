FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create host path compatibility symlink so MLflow artifacts logged on host resolve inside container
RUN mkdir -p /Users/gaurik/Documents && ln -s /app /Users/gaurik/Documents/Mlops_cp

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and scripts
COPY src/ src/
COPY configs/ configs/
COPY run_local_experiment.py .
COPY run_terminal_demo.py .

# Expose ports for API (8000) and MLflow (5000)
EXPOSE 8000 5000

# Default command starts the FastAPI inference server
CMD ["uvicorn", "src.pipeline.serve:app", "--host", "0.0.0.0", "--port", "8000"]

