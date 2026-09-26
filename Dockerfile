FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and scripts
COPY src/ src/
COPY run_local_experiment.py .

# Expose port for MLflow if needed within this container (though usually we run MLflow in a separate service)
EXPOSE 5000

# Default command
CMD ["python", "run_local_experiment.py"]
