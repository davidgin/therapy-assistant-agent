FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/static/css /app/static/js /app/templates

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]