FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose both REST and WebSocket ports
EXPOSE ${REST_PORT:-8000}
EXPOSE ${WS_PORT:-8001}

# Start both servers using Python multiprocessing
CMD ["python", "-m", "browser_use.api.server"] 